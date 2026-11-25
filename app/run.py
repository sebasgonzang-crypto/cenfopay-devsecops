"""Ejecución local para desarrollo (CORREGIDO EN LA SEMANA 3).

En el contenedor la aplicación se sirve con gunicorn (CMD del Dockerfile: run:app).
"""
import os

from cenfopay import create_app

app = create_app()

if __name__ == "__main__":
    # FIX (CWE-489): sin depurador y solo en la interfaz local por defecto.
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")), debug=False)
