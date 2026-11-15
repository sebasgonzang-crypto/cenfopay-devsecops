# Imagen del codespace del curso CIB-665.
# Parte de la imagen oficial de Python y quita el repositorio de Yarn que trae
# preinstalado: su llave de firma venció y hace fallar «apt-get update», lo que
# impedía instalar Docker dentro del codespace (el curso no usa Yarn).
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
RUN find /etc/apt/sources.list.d -name '*yarn*' -delete \
 && sed -i '/yarnpkg/d' /etc/apt/sources.list 2>/dev/null || true
