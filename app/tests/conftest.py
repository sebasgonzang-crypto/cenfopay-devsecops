import os

import pytest

# Llave SOLO para pruebas (la versión corregida la exige desde el entorno).
os.environ.setdefault("SECRET_KEY", "clave-solo-para-pruebas")

from cenfopay import create_app


@pytest.fixture()
def app(tmp_path):
    aplicacion = create_app({"DB_ENGINE": "sqlite", "SQLITE_PATH": str(tmp_path / "prueba.db")})
    aplicacion.config.update(TESTING=True)
    yield aplicacion


@pytest.fixture()
def cliente(app):
    return app.test_client()
