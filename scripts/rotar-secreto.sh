#!/usr/bin/env bash
# Semana 4 · Demuestra la ROTACIÓN de un secreto y deja evidencia sin exponerlo.
#   1. Lee la credencial actual de cenfopay_app (rol estático de Vault).
#   2. Pide a Vault que la rote.
#   3. Comprueba que la contraseña ANTERIOR ya no sirve y la NUEVA sí.
#   4. Comprueba que CenfoPay sigue respondiendo (pide credenciales nuevas sola).
#   5. Rota también la SECRET_KEY (nueva versión en KV v2) y muestra el historial.
# La evidencia se guarda en reportes/evidencia-rotacion-<fecha>.txt con huellas
# SHA-256 parciales: nunca con el valor del secreto.
source "$(dirname "$0")/_comun.sh"
: "${VAULT_DEV_ROOT_TOKEN:?Define VAULT_DEV_ROOT_TOKEN en .env}"

APP_URL="${APP_URL:-http://127.0.0.1:8000}"
mkdir -p reportes
EVIDENCIA="reportes/evidencia-rotacion-$(date +%Y%m%d-%H%M%S).txt"
registrar() { printf '%s\n' "$*" | tee -a "$EVIDENCIA"; }

registrar "# Evidencia de rotación de secretos · CenfoPay · $(date -Iseconds)"

leer_password() { vault_cli read -field=password database/static-creds/cenfopay-app-estatico; }
leer_rotacion() { vault_cli read -field=last_vault_rotation database/static-creds/cenfopay-app-estatico; }

ANTERIOR="$(leer_password)"
registrar "Credencial antes:   $(enmascarar "$ANTERIOR")  (última rotación: $(leer_rotacion))"

info "Solicitando rotación a Vault..."
vault_cli write -f database/rotate-role/cenfopay-app-estatico >/dev/null
sleep 2
NUEVA="$(leer_password)"
registrar "Credencial después: $(enmascarar "$NUEVA")  (última rotación: $(leer_rotacion))"
[[ "$ANTERIOR" != "$NUEVA" ]] || falla "La contraseña no cambió."

if psql_como cenfopay_app "$ANTERIOR" "SELECT 1" >/dev/null 2>&1; then
  registrar "[FALLA] La contraseña anterior todavía funciona."
  exit 1
else
  registrar "[OK] La contraseña anterior fue rechazada por PostgreSQL."
fi
psql_como cenfopay_app "$NUEVA" "SELECT 1" >/dev/null && registrar "[OK] La contraseña nueva funciona."

if command -v curl >/dev/null; then
  CODIGO="$(curl -s -o /dev/null -w '%{http_code}' "${APP_URL}/api/cuentas/1/movimientos" || true)"
  registrar "CenfoPay después de la rotación: HTTP ${CODIGO} (se espera 200 sin reiniciar la app)"
fi

info "Rotando la SECRET_KEY de dev (nueva versión en KV v2)..."
vault_cli kv patch secret/cenfopay/dev SECRET_KEY="$(openssl rand -hex 32)" >/dev/null
registrar "Versiones de secret/cenfopay/dev:"
vault_cli kv metadata get -format=json secret/cenfopay/dev | python3 -c '
import json, sys
datos = json.load(sys.stdin)["data"]
print("  versión actual:", datos["current_version"])
for numero, v in sorted(datos["versions"].items(), key=lambda x: int(x[0])):
    estado = "destruida" if v["destroyed"] else ("eliminada" if v["deletion_time"] else "activa")
    print("  v" + numero + ": creada " + v["created_time"][:19] + "Z · " + estado)
' | tee -a "$EVIDENCIA"
alerta "La app usa la SECRET_KEY nueva al reiniciarse: las sesiones firmadas con la anterior dejan de ser válidas."

ok "Evidencia guardada en ${EVIDENCIA}"
