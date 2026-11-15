"""Acceso a datos de CenfoPay (CORREGIDO EN LA SEMANA 4).

Cambios frente a la línea base:
  * Las credenciales de PostgreSQL se piden al proveedor de secretos.
  * Si la contraseña fue rotada (fallo de autenticación), se piden de nuevo
    y se reintenta una vez: la rotación no exige reiniciar la aplicación.
"""
import logging
import sqlite3

from flask import current_app, g

from . import seed

try:
    import psycopg2
except ImportError:  # pragma: no cover
    psycopg2 = None

log = logging.getLogger("cenfopay.db")


def _cfg():
    return current_app.config["CENFOPAY"]


def _es_postgres():
    return _cfg()["DB_ENGINE"] == "postgres"


def _conectar_postgres(forzar_credenciales=False):
    cfg = _cfg()
    usuario, password = current_app.extensions["secretos"].credenciales_db(forzar_credenciales)
    return psycopg2.connect(
        host=cfg["DB_HOST"],
        port=cfg["DB_PORT"],
        dbname=cfg["DB_NAME"],
        user=usuario,
        password=password,
        connect_timeout=5,
    )


def _conectar():
    if not _es_postgres():
        return sqlite3.connect(_cfg()["SQLITE_PATH"])
    try:
        return _conectar_postgres()
    except psycopg2.OperationalError as error:
        if "authentication failed" not in str(error):
            raise
        log.warning("Autenticación rechazada por PostgreSQL: se solicitan credenciales nuevas")
        return _conectar_postgres(forzar_credenciales=True)


def get_db():
    if "db" not in g:
        g.db = _conectar()
    return g.db


def close_db(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def _adaptar(sql):
    return sql.replace("?", "%s") if _es_postgres() else sql


def consultar(sql, parametros=()):
    cursor = get_db().cursor()
    cursor.execute(_adaptar(sql), parametros)
    return cursor.fetchall()


def consultar_uno(sql, parametros=()):
    filas = consultar(sql, parametros)
    return filas[0] if filas else None


def ejecutar(sql, parametros=()):
    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute(_adaptar(sql), parametros)
    conexion.commit()


def inicializar_sqlite():
    if _es_postgres():
        return
    conexion = get_db()
    for ddl in seed.ESQUEMA_SQLITE:
        conexion.execute(ddl)
    if conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        conexion.executemany("INSERT INTO usuarios VALUES (?, ?, ?, ?)", seed.USUARIOS)
        conexion.executemany("INSERT INTO cuentas VALUES (?, ?, ?, ?)", seed.CUENTAS)
        conexion.executemany("INSERT INTO movimientos VALUES (?, ?, ?, ?, ?)", seed.MOVIMIENTOS)
    conexion.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        inicializar_sqlite()
