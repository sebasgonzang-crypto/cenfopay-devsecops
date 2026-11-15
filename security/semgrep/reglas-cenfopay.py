# Casos de prueba de las reglas personalizadas (ejecuta: semgrep --test security/semgrep/)
# "ruleid:" = la regla DEBE disparar en la línea siguiente.
# "ok:"     = la regla NO debe disparar en la línea siguiente.
import datetime
import logging
import os

from flask import render_template_string, request
from werkzeug.utils import safe_join

from cenfopay import db

log = logging.getLogger(__name__)


def login_vulnerable():
    usuario = request.args.get("usuario")
    sql = f"SELECT * FROM usuarios WHERE usuario = '{usuario}'"
    # ruleid: cenfopay-sql-injection
    return db.consultar_uno(sql)


def login_seguro():
    usuario = request.args.get("usuario")
    # ok: cenfopay-sql-injection
    return db.consultar_uno("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))


def movimientos_seguro(cuenta_id):
    desde = datetime.date.fromisoformat(request.args.get("desde"))
    # ok: cenfopay-sql-injection
    return db.consultar(f"SELECT * FROM movimientos WHERE fecha >= '{desde}'")


def reporte_vulnerable():
    archivo = request.args.get("archivo")
    # ruleid: cenfopay-path-traversal
    return open(os.path.join("/srv/reportes", archivo)).read()


def reporte_seguro():
    archivo = request.args.get("archivo")
    # ok: cenfopay-path-traversal
    return open(safe_join("/srv/reportes", archivo)).read()


def saludo_vulnerable(nombre):
    # ruleid: cenfopay-ssti-render-template-string
    return render_template_string(f"<h1>Hola {nombre}</h1>")


def saludo_seguro(nombre):
    # ok: cenfopay-ssti-render-template-string
    return render_template_string("<h1>Hola {{ nombre }}</h1>", nombre=nombre)


def registro(usuario, password):
    # ruleid: cenfopay-secreto-en-logs
    log.info(f"login usuario={usuario} password={password}")
    # ok: cenfopay-secreto-en-logs
    log.info("login usuario=%s", usuario)


def arrancar(app):
    # ruleid: cenfopay-flask-debug-activo
    app.run(host="0.0.0.0", debug=True)
    # ok: cenfopay-flask-debug-activo
    app.run(host="127.0.0.1", debug=False)


# ruleid: cenfopay-secreto-embebido
API_TOKEN = "cfp_test_0123456789abcdefghij"
# ok: cenfopay-secreto-embebido
API_TOKEN_ENV = "API_TOKEN"
# ruleid: cenfopay-secreto-embebido
CLAVE_BD = os.getenv("DB_PASSWORD", "CenfoPay#2026")
# ok: cenfopay-secreto-embebido
CLAVE_BD_SEGURA = os.getenv("DB_PASSWORD")
