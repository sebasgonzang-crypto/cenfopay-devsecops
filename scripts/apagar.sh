#!/usr/bin/env bash
# Apaga el laboratorio. Uso: bash scripts/apagar.sh          -> apaga (conserva datos)
#                            bash scripts/apagar.sh borrar   -> apaga y borra la base de datos
source "$(dirname "$0")/_comun.sh"
necesita_docker
archivos_compose
extra=()
[[ "${1:-}" == "borrar" ]] && extra=(-v)
docker compose --profile secretos --profile dast "${ARCHIVOS[@]}" down "${extra[@]}" --remove-orphans
ok "Laboratorio apagado${extra:+ y datos borrados}."
