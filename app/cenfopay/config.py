"""Configuración de CenfoPay.

LÍNEA BASE VULNERABLE — aplicación ficticia, solo para el curso CIB-665
(Automatización y DevSecOps, Universidad Cenfotec). No la despliegues fuera
de tu laboratorio local.
"""
import os

# VULN (CWE-798): secreto embebido en el código fuente.
SECRET_KEY = "cenfopay-dev-9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c"

# VULN (CWE-798): token de integración embebido (se detecta en el semana 4).
TOKEN_TIPO_CAMBIO = "cfp_test_Q7mZ2vK9pL4xR8tB1nW6yH3cD5sF0gJa"


def cargar():
    """Lee la configuración desde variables de entorno (con valores por defecto)."""
    return {
        "DB_ENGINE": os.getenv("DB_ENGINE", "sqlite"),
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": int(os.getenv("DB_PORT", "5432")),
        "DB_NAME": os.getenv("DB_NAME", "cenfopay"),
        "DB_USER": os.getenv("DB_USER", "cenfopay_app"),
        # VULN (CWE-798): contraseña por defecto embebida.
        "DB_PASSWORD": os.getenv("DB_PASSWORD", "CenfoPay#2026"),
        "SQLITE_PATH": os.getenv("SQLITE_PATH", "/tmp/cenfopay.db"),
        "REPORTES_DIR": os.getenv(
            "REPORTES_DIR",
            os.path.join(os.path.dirname(__file__), "reportes_publicos"),
        ),
    }
