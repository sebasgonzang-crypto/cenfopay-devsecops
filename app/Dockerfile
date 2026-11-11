# Dockerfile de CenfoPay — LÍNEA BASE VULNERABLE (semana 2: no lo copies a producción).
# Cada línea marcada con "PROBLEMA" es un hallazgo que debes detectar con
# Hadolint/Trivy, clasificar y corregir durante el semana 2.

# PROBLEMA: imagen base completa (cientos de paquetes) y versión de Python sin soporte.
FROM python:3.9

# PROBLEMA: herramientas innecesarias en tiempo de ejecución, sin versión fija
# y sin limpiar la caché de apt.
RUN apt-get update
RUN apt-get install -y curl vim netcat-openbsd iputils-ping

WORKDIR /app

# PROBLEMA: ADD copia TODO el contexto (pruebas, archivos ocultos...) y no hay .dockerignore.
ADD . /app

# PROBLEMA: pip sin --no-cache-dir; la caché queda dentro de la capa.
RUN pip install -r requirements.txt

# PROBLEMA: secretos en variables de entorno de la imagen (visibles con docker inspect/history).
ENV DB_PASSWORD=CenfoPay#2026
ENV SECRET_KEY=cenfopay-dev-9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c

EXPOSE 8000

# PROBLEMA: sin USER (corre como root), sin HEALTHCHECK y con servidor de desarrollo.
CMD python run.py
