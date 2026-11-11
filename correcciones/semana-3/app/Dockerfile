# syntax=docker/dockerfile:1
# Dockerfile PROTEGIDO de CenfoPay · corrección de la SEMANA 3 (Python 3.13, librerías al día).
#
# Fija la imagen por su digest con:  bash scripts/fijar-digest.sh
ARG PYTHON_IMAGE=python:3.13-slim-trixie

# ---------------------------------------------------------------- 1. construcción
# Instala las dependencias en un entorno virtual aislado. Nada de esta etapa
# (pip, caché, compiladores) llega a la imagen final.
FROM ${PYTHON_IMAGE} AS construccion
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir --require-virtualenv -r requirements.txt

# ---------------------------------------------------------------- 2. ejecución
FROM ${PYTHON_IMAGE}
LABEL org.opencontainers.image.title="CenfoPay" \
      org.opencontainers.image.description="Billetera ficticia del curso CIB-665 (Universidad Cenfotec)" \
      org.opencontainers.image.licenses="MIT"

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Parches de seguridad del sistema operativo disponibles al construir la imagen.
# hadolint ignore=DL3005
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 cenfopay \
 && useradd --system --uid 10001 --gid cenfopay --no-create-home \
            --home-dir /nonexistent --shell /usr/sbin/nologin cenfopay

WORKDIR /app
COPY --from=construccion /opt/venv /opt/venv
# El código pertenece a root y es de solo lectura para el usuario de la app.
COPY --chown=root:root --chmod=0755 cenfopay/ ./cenfopay/
COPY --chown=root:root --chmod=0644 run.py ./

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=2).status == 200 else 1)"]

# Servidor de producción (no el de desarrollo), en formato JSON para recibir señales.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "run:app"]
