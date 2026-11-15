#!/usr/bin/env bash
# Corre las pruebas de CenfoPay dentro de un contenedor de Python (no instalas nada).
# Uso: bash scripts/probar.sh              -> todas
#      bash scripts/probar.sh funcionales  -> solo las de funciones (deben pasar siempre)
#      bash scripts/probar.sh seguridad    -> las 9 que atacan fallas del código
#      bash scripts/probar.sh secretos     -> las 2 de contraseñas (semana 4)
source "$(dirname "$0")/_comun.sh"
necesita_docker
s="$(semana_activa)"; s="${s:-0}"
# Las librerías originales solo funcionan con Python 3.9; en la semana 3 se actualizan.
if (( s >= 3 )); then version="3.13"; else version="3.9"; fi
case "${1:-todo}" in
  funcionales) marcador='-m "not seguridad and not secretos"' ;;
  seguridad)   marcador='-m seguridad' ;;
  secretos)    marcador='-m secretos' ;;
  todo)        marcador='' ;;
  *) falla "Uso: bash scripts/probar.sh [funcionales|seguridad|secretos|todo]" ;;
esac
info "Pruebas con Python ${version} (${1:-todo}). La primera vez tarda ~1 minuto."
docker run --rm -v "$RAIZ/app":/app -w /app -v cenfopay-pip-cache:/root/.cache/pip \
  -e PYTHONDONTWRITEBYTECODE=1 "python:${version}-slim" sh -c \
  "pip install -q --disable-pip-version-check --root-user-action=ignore -r requirements.txt -r requirements-dev.txt && pytest -q -p no:cacheprovider ${marcador}"
