"""Acceso a datos de CenfoPay (SQLite para pruebas, PostgreSQL en Docker)."""
import sqlite3

from flask import current_app, g

from . import seed

try:  # psycopg2 solo es necesario cuando DB_ENGINE=postgres
    import psycopg2
except ImportError:  # pragma: no cover
    psycopg2 = None


def _cfg():
    return current_app.config["CENFOPAY"]


def _es_postgres():
    return _cfg()["DB_ENGINE"] == "postgres"


def _conectar():
    cfg = _cfg()
    if _es_postgres():
        return psycopg2.connect(
            host=cfg["DB_HOST"],
            port=cfg["DB_PORT"],
            dbname=cfg["DB_NAME"],
            user=cfg["DB_USER"],
            password=cfg["DB_PASSWORD"],
            connect_timeout=5,
        )
    return sqlite3.connect(cfg["SQLITE_PATH"])


def get_db():
    if "db" not in g:
        g.db = _conectar()
    return g.db


def close_db(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def _adaptar(sql):
    """Convierte los marcadores '?' (estilo SQLite) a '%s' (estilo psycopg2)."""
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
    """Crea el esquema y carga los datos ficticios (solo SQLite).

    En PostgreSQL el esquema lo crea db/init/01-esquema.sql al levantar
    el contenedor de base de datos.
    """
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
