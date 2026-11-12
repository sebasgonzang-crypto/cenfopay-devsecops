#!/usr/bin/env bash
# Compara la foto «antes» con la foto «despues» y escribe docs/comparativo.md
source "$(dirname "$0")/_comun.sh"
antes=reportes/antes/hallazgos-normalizados.csv
despues=reportes/despues/hallazgos-normalizados.csv
[[ -f "$antes" ]] || falla "No existe $antes. Toma la foto inicial con: bash scripts/foto.sh antes"
[[ -f "$despues" ]] || falla "No existe $despues. Toma la foto final con: bash scripts/foto.sh despues"
python3 tools/comparar_reportes.py "$antes" "$despues" -o docs/comparativo.md
ok "Comparativo listo: docs/comparativo.md (ábrelo en el editor)."
