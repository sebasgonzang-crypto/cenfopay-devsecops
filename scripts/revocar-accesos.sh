#!/usr/bin/env bash
# Semana 4 · Demuestra la REVOCACIÓN de accesos:
#   1. Pide una credencial dinámica (usuario temporal de PostgreSQL) y la usa.
#   2. Revoca su lease: Vault borra el usuario de la base de datos al instante.
#   3. Destruye el secret_id del AppRole (como harías si se filtró) y emite uno nuevo.
#   4. Destruye una versión antigua de la SECRET_KEY (fin del ciclo de vida).
source "$(dirname "$0")/_comun.sh"
: "${VAULT_DEV_ROOT_TOKEN:?Define VAULT_DEV_ROOT_TOKEN en .env}"

mkdir -p reportes
EVIDENCIA="reportes/evidencia-revocacion-$(date +%Y%m%d-%H%M%S).txt"
registrar() { printf '%s\n' "$*" | tee -a "$EVIDENCIA"; }
registrar "# Evidencia de revocación · CenfoPay · $(date -Iseconds)"

# ------------------------------------------------ 1-2. Credencial dinámica
JSON="$(vault_cli read -format=json database/creds/cenfopay-app-dinamico)"
LEASE="$(printf '%s' "$JSON" | python3 -c 'import json,sys;print(json.load(sys.stdin)["lease_id"])')"
USUARIO="$(printf '%s' "$JSON" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["username"])')"
CLAVE="$(printf '%s' "$JSON" | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["password"])')"
registrar "Credencial dinámica emitida: usuario=${USUARIO} lease=${LEASE%%/*}/... ttl=15m"

if psql_como "$USUARIO" "$CLAVE" "SELECT COUNT(*) FROM movimientos" >/dev/null 2>&1; then
  registrar "[OK] El usuario temporal puede consultar movimientos."
else
  registrar "[FALLA] El usuario temporal no pudo conectarse."
fi

vault_cli lease revoke "$LEASE" >/dev/null
sleep 2
if psql_como "$USUARIO" "$CLAVE" "SELECT 1" >/dev/null 2>&1; then
  registrar "[FALLA] La credencial sigue funcionando después de revocarla."
  exit 1
else
  registrar "[OK] Lease revocado: el usuario ${USUARIO} ya no existe en PostgreSQL."
fi

# ---------------------------------------------- 3. Revocar secret_id filtrado
if [[ -f .secrets/secret_id ]]; then
  vault_cli write auth/approle/role/cenfopay-dev/secret-id/destroy \
    secret_id="$(cat .secrets/secret_id)" >/dev/null
  registrar "[OK] secret_id anterior destruido (huella $(enmascarar "$(cat .secrets/secret_id)"))."
  if vault_cli write auth/approle/login role_id="$(cat .secrets/role_id)" \
       secret_id="$(cat .secrets/secret_id)" >/dev/null 2>&1; then
    registrar "[FALLA] El secret_id destruido todavía permite autenticarse."
  else
    registrar "[OK] El secret_id destruido ya no permite autenticarse."
  fi
  vault_cli write -f -field=secret_id auth/approle/role/cenfopay-dev/secret-id > .secrets/secret_id
  chmod 644 .secrets/secret_id
  registrar "[OK] Nuevo secret_id emitido (huella $(enmascarar "$(cat .secrets/secret_id)")). Reinicia la app para usarlo."
fi

# ------------------------------------------- 4. Destruir versión antigua
VERSION_ACTUAL="$(vault_cli kv metadata get -format=json secret/cenfopay/dev \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["current_version"])')"
if [[ "$VERSION_ACTUAL" -gt 1 ]]; then
  vault_cli kv destroy -versions=1 secret/cenfopay/dev >/dev/null
  registrar "[OK] Versión 1 de secret/cenfopay/dev destruida de forma permanente (actual: v${VERSION_ACTUAL})."
fi

ok "Evidencia guardada en ${EVIDENCIA}"
