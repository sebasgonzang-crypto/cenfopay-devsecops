"""CenfoPay — billetera digital FICTICIA (CORREGIDA EN LA SEMANA 3).

Cada corrección está marcada con "FIX (CWE-xxx)". Compárala con la versión
anterior con:  git diff main -- app/cenfopay/__init__.py
Pendiente para la semana 4: SECRET_KEY todavía viene de config.py.
"""
import datetime
import logging
import os
import re
import socket

import yaml
from flask import Flask, jsonify, render_template, render_template_string, request, session
from werkzeug.utils import safe_join

from . import auth, config, db

_HOST_VALIDO = re.compile(r"^(?=.{1,253}$)[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?$")
_REPORTE_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,64}\.txt$")


def create_app(config_extra=None):
    app = Flask(__name__)
    # Pendiente (semana 4): la llave sigue en el código (CWE-798).
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["CENFOPAY"] = config.cargar()
    if config_extra:
        app.config["CENFOPAY"].update(config_extra)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("cenfopay")

    db.init_app(app)

    @app.after_request
    def cabeceras_de_seguridad(respuesta):
        # FIX (hallazgos DAST): cabeceras de endurecimiento.
        respuesta.headers["X-Content-Type-Options"] = "nosniff"
        respuesta.headers["X-Frame-Options"] = "DENY"
        respuesta.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; form-action 'self'; "
            "base-uri 'none'; object-src 'none'"
        )
        respuesta.headers["Referrer-Policy"] = "no-referrer"
        respuesta.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        respuesta.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if request.path.startswith("/api/"):
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    @app.errorhandler(500)
    def error_interno(_error):
        # FIX (CWE-209): sin trazas internas hacia el cliente.
        return jsonify(error="error interno"), 500

    @app.get("/")
    def inicio():
        return render_template("index.html")

    @app.get("/salud")
    def salud():
        return jsonify(estado="ok", servicio="cenfopay")

    @app.get("/saludo")
    def saludo():
        nombre = request.args.get("nombre", "cliente")
        # FIX (CWE-1336 / CWE-79): plantilla fija; el dato viaja como variable
        # y Jinja lo escapa automáticamente.
        return render_template_string(
            "<h1>Hola {{ nombre }}, bienvenido a CenfoPay</h1>", nombre=nombre
        )

    @app.post("/api/login")
    def login():
        datos = request.get_json(silent=True) or request.form
        usuario = str(datos.get("usuario", ""))[:64]
        password = str(datos.get("password", ""))
        # FIX (CWE-532): nunca se registra la contraseña.
        log.info("Intento de login usuario=%s", usuario)
        # FIX (CWE-89): consulta parametrizada.
        fila = db.consultar_uno(
            "SELECT id, usuario, rol, password_hash FROM usuarios WHERE usuario = ?", (usuario,)
        )
        if not fila or not auth.verificar(password, fila[3]):
            return jsonify(error="credenciales inválidas"), 401
        # FIX (CWE-916): migración del hash heredado en el primer login exitoso.
        if auth.es_hash_legado(fila[3]):
            db.ejecutar(
                "UPDATE usuarios SET password_hash = ? WHERE id = ?",
                (auth.generar_hash(password), fila[0]),
            )
        session.clear()
        session["usuario_id"] = fila[0]
        return jsonify(mensaje="bienvenido", usuario=fila[1], rol=fila[2])

    @app.get("/api/cuentas/<int:cuenta_id>/movimientos")
    def movimientos(cuenta_id):
        # FIX (CWE-20 / CWE-89): validación de formato + consulta parametrizada.
        try:
            desde = datetime.date.fromisoformat(request.args.get("desde", "2000-01-01"))
        except ValueError:
            return jsonify(error="el parámetro 'desde' debe tener formato AAAA-MM-DD"), 400
        filas = db.consultar(
            "SELECT fecha, descripcion, monto FROM movimientos "
            "WHERE cuenta_id = ? AND fecha >= ? ORDER BY fecha",
            (cuenta_id, desde.isoformat()),
        )
        return jsonify(
            cuenta=cuenta_id,
            movimientos=[{"fecha": str(f[0]), "descripcion": f[1], "monto": float(f[2])} for f in filas],
        )

    @app.get("/api/diagnostico/resolver")
    def resolver():
        host = request.args.get("host", "localhost")
        # FIX (CWE-78): lista blanca de caracteres y API de sockets, sin shell.
        if not _HOST_VALIDO.match(host):
            return jsonify(error="host inválido"), 400
        try:
            direcciones = sorted({info[4][0] for info in socket.getaddrinfo(host, None)})
        except socket.gaierror:
            direcciones = []
        return jsonify(host=host, resultado=direcciones)

    @app.post("/api/transferencias/importar")
    def importar():
        # FIX (CWE-502): safe_load solo construye tipos básicos de YAML.
        try:
            lote = yaml.safe_load(request.get_data(as_text=True))
        except yaml.YAMLError:
            return jsonify(error="YAML inválido"), 400
        if not isinstance(lote, list) or not all(isinstance(t, dict) for t in lote):
            return jsonify(error="se espera una lista de transferencias"), 400
        return jsonify(transferencias_recibidas=len(lote))

    @app.get("/api/reportes")
    def reportes():
        archivo = request.args.get("archivo", "resumen.txt")
        # FIX (CWE-22): lista blanca de nombres + safe_join dentro de la carpeta.
        if not _REPORTE_VALIDO.match(archivo):
            return jsonify(error="nombre de reporte inválido"), 400
        ruta = safe_join(app.config["CENFOPAY"]["REPORTES_DIR"], archivo)
        if ruta is None or not os.path.isfile(ruta):
            return jsonify(error="reporte no encontrado"), 404
        with open(ruta, encoding="utf-8") as manejador:
            return jsonify(archivo=archivo, contenido=manejador.read())

    return app
