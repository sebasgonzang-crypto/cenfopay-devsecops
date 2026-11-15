"""Pruebas de regresión de seguridad.

En la línea base vulnerable estas pruebas FALLAN a propósito: cada una
demuestra una vulnerabilidad real. Cuando corriges el código (semana 3 y
semana 4) deben pasar, y desde ese momento el pipeline las ejecuta en cada
cambio para que la vulnerabilidad no regrese.

Marcadores:
  seguridad -> fallas de código (semana 3)
  secretos  -> manejo de secretos y registros (semana 4)
"""
import logging
import os
import re

import pytest

from cenfopay import create_app


# --------------------------------------------------------------- Semana 3
@pytest.mark.seguridad
def test_login_resiste_inyeccion_sql(cliente):
    """CWE-89: 'admin' --' no debe saltarse la verificación de contraseña."""
    respuesta = cliente.post("/api/login", json={"usuario": "admin' --", "password": "x"})
    assert respuesta.status_code == 401


@pytest.mark.seguridad
def test_movimientos_resisten_inyeccion_sql(cliente):
    """CWE-89: el filtro de fecha no debe devolver movimientos de otras cuentas."""
    respuesta = cliente.get(
        "/api/cuentas/1/movimientos", query_string={"desde": "2000-01-01' OR '1'='1"}
    )
    if respuesta.status_code == 200:
        assert len(respuesta.get_json()["movimientos"]) <= 3
    else:
        assert respuesta.status_code == 400


@pytest.mark.seguridad
def test_resolver_no_ejecuta_comandos(cliente):
    """CWE-78: el parámetro host no debe llegar a una shell."""
    respuesta = cliente.get(
        "/api/diagnostico/resolver", query_string={"host": "localhost; echo INYECTADO"}
    )
    assert "INYECTADO" not in respuesta.get_data(as_text=True)


@pytest.mark.seguridad
def test_saludo_no_evalua_plantillas(cliente):
    """CWE-1336: {{7*7}} no debe evaluarse en el servidor."""
    respuesta = cliente.get("/saludo", query_string={"nombre": "{{7*7}}"})
    assert "49" not in respuesta.get_data(as_text=True)


@pytest.mark.seguridad
def test_saludo_escapa_html(cliente):
    """CWE-79: la entrada debe escaparse antes de devolverse como HTML."""
    respuesta = cliente.get("/saludo", query_string={"nombre": "<script>alert(1)</script>"})
    assert "<script>" not in respuesta.get_data(as_text=True)


@pytest.mark.seguridad
def test_importar_rechaza_objetos_python(cliente):
    """CWE-502: YAML con etiquetas de objetos Python debe rechazarse."""
    respuesta = cliente.post(
        "/api/transferencias/importar", data="!!python/object/apply:os.getcwd []"
    )
    assert respuesta.status_code == 400
    assert os.getcwd() not in respuesta.get_data(as_text=True)


@pytest.mark.seguridad
def test_reportes_no_permite_path_traversal(cliente):
    """CWE-22: no se debe poder leer archivos fuera de la carpeta de reportes."""
    respuesta = cliente.get("/api/reportes", query_string={"archivo": "../__init__.py"})
    assert respuesta.status_code in (400, 404)
    assert "create_app" not in respuesta.get_data(as_text=True)


@pytest.mark.seguridad
def test_contrasenas_con_hash_robusto(app, cliente):
    """CWE-916: tras un login exitoso el hash almacenado no debe ser MD5."""
    cliente.post("/api/login", json={"usuario": "ana.mora", "password": "Ana2026!"})
    with app.app_context():
        from cenfopay import db

        (hash_guardado,) = db.consultar_uno(
            "SELECT password_hash FROM usuarios WHERE usuario = ?", ("ana.mora",)
        )
    assert not re.fullmatch(r"[0-9a-f]{32}", hash_guardado)


@pytest.mark.seguridad
def test_cabeceras_de_seguridad(cliente):
    """Hallazgos de DAST: la respuesta debe incluir cabeceras de endurecimiento."""
    respuesta = cliente.get("/")
    assert respuesta.headers.get("X-Content-Type-Options") == "nosniff"
    assert "Content-Security-Policy" in respuesta.headers
    assert "frame-ancestors" in respuesta.headers["Content-Security-Policy"]


# --------------------------------------------------------------- Semana 4
@pytest.mark.secretos
def test_password_no_se_registra_en_logs(cliente, caplog):
    """CWE-532: las contraseñas nunca deben quedar en los registros."""
    caplog.set_level(logging.DEBUG)
    cliente.post("/api/login", json={"usuario": "ana.mora", "password": "SuperSecreta123"})
    assert "SuperSecreta123" not in caplog.text


@pytest.mark.secretos
def test_secret_key_se_inyecta_desde_el_entorno(monkeypatch, tmp_path):
    """CWE-798: la llave de sesión debe venir del entorno, no del código."""
    monkeypatch.setenv("SECRET_KEY", "clave-inyectada-por-el-pipeline")
    app = create_app({"DB_ENGINE": "sqlite", "SQLITE_PATH": str(tmp_path / "k.db")})
    assert app.config["SECRET_KEY"] == "clave-inyectada-por-el-pipeline"
