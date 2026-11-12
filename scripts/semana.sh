#!/usr/bin/env bash
# Activa una semana del proyecto: bash scripts/semana.sh <1|2|3|4>
# Escribe la semana en proyecto.yml, aplica las correcciones listas de esa semana
# (carpeta correcciones/) y actualiza la política de umbrales. Luego te dice qué hacer.
source "$(dirname "$0")/_comun.sh"
[[ $# -eq 1 ]] || falla "Uso: bash scripts/semana.sh <1|2|3|4>"
python3 tools/semana.py semana "$1"
