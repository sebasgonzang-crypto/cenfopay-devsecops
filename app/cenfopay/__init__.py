"""CenfoPay — billetera digital FICTICIA para practicar DevSecOps.

LÍNEA BASE VULNERABLE: este código contiene fallas intencionales que los
estudiantes detectan (SAST/DAST), corrigen y verifican a lo largo del curso
CIB-665. Cada falla está marcada con un comentario "VULN (CWE-xxx)".
NUNCA despliegues esta aplicación en un entorno real.
"""
import hashlib
import logging
import os
import subprocess

import yaml
from flask import Flask, jsonify, render_template, render_template_string, request, session

from . import config, db


def create_app(config_extra=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["CENFOPAY"] = config.cargar()
    if config_extra:
        app.config["CENFOPAY"].update(config_extra)

    logging.basicConfig(level=logging.INFO)
    log = logging.getLogger("cenfopay")

    db.init_app(app)

    @app.get("/")
    def inicio():
        return render_template("index.html")

    @app.get("/salud")
    def salud():
        return jsonify(estado="ok", servicio="cenfopay")

    @app.get("/saludo")
    def saludo():
        nombre = request.args.get("nombre", "cliente")
        # VULN (CWE-1336 / CWE-79): plantilla construida con la entrada del usuario
        # (inyección de plantillas del lado del servidor y XSS reflejado).
        return render_template_string(f"<h1>Hola {nombre}, bienvenido a CenfoPay</h1>")

    @app.post("/api/login")
    def login():
        datos = request.get_json(silent=True) or request.form
        usuario = datos.get("usuario", "")
        password = datos.get("password", "")
        # VULN (CWE-532): la contraseña queda escrita en los registros.
        log.info(f"Intento de login usuario={usuario} password={password}")
        # VULN (CWE-327 / CWE-916): MD5 sin sal para contraseñas.
        password_hash = hashlib.md5(password.encode()).hexdigest()
        # VULN (CWE-89): consulta SQL construida concatenando la entrada.
        sql = (
            "SELECT id, usuario, rol FROM usuarios "
            f"WHERE usuario = '{usuario}' AND password_hash = '{password_hash}'"
        )
        fila = db.consultar_uno(sql)
        if not fila:
            return jsonify(error="credenciales inválidas"), 401
        session["usuario_id"] = fila[0]
        return jsonify(mensaje="bienvenido", usuario=fila[1], rol=fila[2])

    @app.get("/api/cuentas/<int:cuenta_id>/movimientos")
    def movimientos(cuenta_id):
        desde = request.args.get("desde", "2000-01-01")
        # VULN (CWE-89): inyección SQL en el filtro de fecha.
        sql = (
            "SELECT fecha, descripcion, monto FROM movimientos "
            f"WHERE cuenta_id = {cuenta_id} AND fecha >= '{desde}' ORDER BY fecha"
        )
        filas = db.consultar(sql)
        return jsonify(
            cuenta=cuenta_id,
            movimientos=[{"fecha": f[0], "descripcion": f[1], "monto": f[2]} for f in filas],
        )

    @app.get("/api/diagnostico/resolver")
    def resolver():
        host = request.args.get("host", "localhost")
        # VULN (CWE-78): inyección de comandos del sistema operativo.
        try:
            salida = subprocess.check_output(
                f"getent hosts {host}", shell=True, text=True, stderr=subprocess.STDOUT
            )
        except subprocess.CalledProcessError as error:
            salida = error.output
        return jsonify(host=host, resultado=salida)

    @app.post("/api/transferencias/importar")
    def importar():
        # VULN (CWE-502): deserialización insegura de YAML.
        lote = yaml.load(request.get_data(as_text=True), Loader=yaml.Loader)
        cantidad = len(lote) if isinstance(lote, list) else 1
        return jsonify(transferencias_recibidas=cantidad, detalle=str(lote)[:200])

    @app.get("/api/reportes")
    def reportes():
        archivo = request.args.get("archivo", "resumen.txt")
        # VULN (CWE-22): recorrido de rutas (path traversal).
        ruta = os.path.join(app.config["CENFOPAY"]["REPORTES_DIR"], archivo)
        try:
            with open(ruta, encoding="utf-8") as manejador:
                return jsonify(archivo=archivo, contenido=manejador.read())
        except OSError:
            return jsonify(error="reporte no encontrado"), 404

    @app.get("/api/diagnostico/ping")
    def ping():
        destino = request.args.get("destino", "localhost")
        # Página insegura agregada A PROPÓSITO para probar la compuerta (no la fusiones)
        salida = subprocess.check_output(f"ping -c 1 {destino}", shell=True, text=True)
        return jsonify(resultado=salida)

    return app
