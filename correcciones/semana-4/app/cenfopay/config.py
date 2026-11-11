"""Configuración de CenfoPay (CORREGIDA EN LA SEMANA 4).

Ningún secreto vive en el código: SECRET_KEY y las credenciales de la base de
datos se obtienen en tiempo de ejecución mediante cenfopay.secretos
(variables de entorno, archivos montados o HashiCorp Vault).
"""
import os


def _booleano(valor, por_defecto):
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes")


def cargar():
    return {
        "DB_ENGINE": os.getenv("DB_ENGINE", "sqlite"),
        "DB_HOST": os.getenv("DB_HOST", "localhost"),
        "DB_PORT": int(os.getenv("DB_PORT", "5432")),
        "DB_NAME": os.getenv("DB_NAME", "cenfopay"),
        # Falso positivo revisado (Bandit B108): SQLite solo se usa en pruebas locales;
        # en el contenedor DB_ENGINE=postgres y esta ruta nunca se abre.
        "SQLITE_PATH": os.getenv("SQLITE_PATH", "/tmp/cenfopay.db"),  # nosec B108
        "REPORTES_DIR": os.getenv(
            "REPORTES_DIR",
            os.path.join(os.path.dirname(__file__), "reportes_publicos"),
        ),
        # En el laboratorio se sirve por HTTP; en producción debe ser True (TLS).
        "COOKIE_SEGURA": _booleano(os.getenv("COOKIE_SEGURA"), True),
    }
