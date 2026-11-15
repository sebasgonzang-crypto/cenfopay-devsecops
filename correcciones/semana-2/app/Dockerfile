# syntax=docker/dockerfile:1
# Dockerfile PROTEGIDO de CenfoPay · corrección de la SEMANA 2.
# Dos etapas: la «cocina» (construccion) instala las librerías; la «caja limpia» final solo
# recibe el resultado y corre sin privilegios (USER 10001).
# Mantiene Python 3.9 porque las librerías heredadas (psycopg2-binary 2.9.3, PyYAML 5.3.1)
# no funcionan con versiones nuevas: riesgo residual (Python 3.9 sin soporte desde octubre
# de 2025) que se elimina en la semana 3.
# Fija las imágenes por su digest con:  bash scripts/fijar-digest.sh
ARG IMAGEN_CONSTRUCCION=python:3.9-bookworm
ARG IMAGEN_EJECUCION=python:3.9-slim-bookworm

FROM ${IMAGEN_CONSTRUCCION} AS construccion
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM ${IMAGEN_EJECUCION}
ENV PATH="/opt/venv/bin:${PATH}" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# hadolint ignore=DL3005
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd --system --gid 10001 cenfopay \
 && useradd --system --uid 10001 --gid cenfopay --no-create-home \
            --home-dir /nonexistent --shell /usr/sbin/nologin cenfopay
WORKDIR /app
COPY --from=construccion /opt/venv /opt/venv
COPY --chown=root:root --chmod=0755 cenfopay/ ./cenfopay/
COPY --chown=root:root --chmod=0644 run.py ./
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/salud', timeout=2).status == 200 else 1)"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "run:app"]
