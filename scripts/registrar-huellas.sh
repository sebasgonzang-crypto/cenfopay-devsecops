#!/usr/bin/env bash
# Semana 4 · Registra en .gitleaksignore los hallazgos del historial que YA atendiste.
# Úsalo SOLO después de rotar y revocar (bash scripts/rotar-secreto.sh y revocar-accesos.sh):
# borrar no es revocar, y registrar una huella sin rotar sería esconder el problema.
source "$(dirname "$0")/_comun.sh"
evidencia="$(ls -1t reportes/evidencia-*.txt 2>/dev/null | head -n 1 || true)"
[[ -n "$evidencia" ]] || alerta "No encontré evidencia de rotación o revocación en reportes/. ¿Ya ejecutaste los scripts?"
read -r -p "¿Ya cambiaste (rotaste) y cancelaste (revocaste) estas credenciales? Escribe «si» para continuar: " respuesta
[[ "$respuesta" == "si" || "$respuesta" == "sí" ]] || falla "Cancelado. Primero rota y revoca; luego vuelve a ejecutar este script."
info "Buscando hallazgos pendientes en todo el historial…"
bash scripts/escanear-local.sh secretos >/dev/null 2>&1 || true
[[ -f reportes/gitleaks.json ]] || falla "No se pudo generar reportes/gitleaks.json."
python3 - reportes/gitleaks.json "${evidencia:-reportes/evidencia-*.txt}" <<'PY'
import datetime, json, sys
from pathlib import Path
nuevas = {h["Fingerprint"] for h in json.load(open(sys.argv[1], encoding="utf-8"))}
archivo = Path(".gitleaksignore")
previas = set()
if archivo.exists():
    previas = {l.strip() for l in archivo.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
todas = sorted(previas | nuevas)
hoy = datetime.date.today().isoformat()
encabezado = ("# Huellas de hallazgos de Gitleaks YA ATENDIDOS (semana 4 · CIB-665).\n"
              f"# Incidente INC-001 · actualizado el {hoy}, DESPUÉS de rotar y revocar.\n"
              f"# Evidencia: {sys.argv[2]}\n"
              "# Regla del curso: una huella solo entra aquí después de cambiar y cancelar ese secreto.\n")
archivo.write_text(encabezado + "".join(h + "\n" for h in todas), encoding="utf-8")
print(f"[✓] {len(nuevas)} huellas nuevas · {len(todas)} en total en .gitleaksignore")
PY
info "Comprobando: Gitleaks ya no debería reportar nada…"
bash scripts/escanear-local.sh secretos >/dev/null 2>&1 || true
python3 -c "import json;print('[✓] Hallazgos pendientes:', len(json.load(open('reportes/gitleaks.json'))))"
info "Sube el archivo:  git add .gitleaksignore && git commit -m \"Semana 4: hallazgos atendidos (INC-001)\" && git push"
