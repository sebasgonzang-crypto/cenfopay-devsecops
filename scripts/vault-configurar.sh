#!/usr/bin/env bash
# Semana 4 · Configura HashiCorp Vault (modo desarrollo) para CenfoPay:
#   1. KV v2 con la SECRET_KEY por entorno (dev y prod aislados).
#   2. Motor de base de datos con un rol ESTÁTICO (Vault rota la contraseña de
#      cenfopay_app) y un rol DINÁMICO (credenciales temporales con TTL).
#   3. Políticas de mínimo privilegio por entorno.
#   4. AppRole para la aplicación; role_id y secret_id quedan en .secrets/
#      (carpeta ignorada por git) para montarse como archivos en el contenedor.
#
# Uso:  docker compose --profile secretos up -d vault
#       bash scripts/vault-configurar.sh
source "$(dirname "$0")/_comun.sh"

: "${VAULT_DEV_ROOT_TOKEN:?Define VAULT_DEV_ROOT_TOKEN en .env}"
: "${VAULT_ADMIN_PASSWORD:?Define VAULT_ADMIN_PASSWORD en .env}"
DB_HOST_PARA_VAULT="${DB_HOST_PARA_VAULT:-db}"

info "Verificando que Vault responde..."
vault_cli status >/dev/null || falla "Vault no responde. ¿Levantaste: docker compose --profile secretos up -d vault?"

# ---------------------------------------------------------------- 1. KV v2
if ! vault_cli secrets list -format=json | grep -q '"secret/"'; then
  vault_cli secrets enable -path=secret kv-v2 >/dev/null
fi
for entorno in dev prod; do
  vault_cli kv put "secret/cenfopay/${entorno}" \
    SECRET_KEY="$(openssl rand -hex 32)" \
    TOKEN_TIPO_CAMBIO="cfp_${entorno}_$(openssl rand -hex 16)" >/dev/null
done
ok "KV v2: secret/cenfopay/dev y secret/cenfopay/prod creados (valores aleatorios)."

# ------------------------------------------------- 2. Motor de base de datos
if ! vault_cli secrets list -format=json | grep -q '"database/"'; then
  vault_cli secrets enable database >/dev/null
fi
vault_cli write database/config/cenfopay \
  plugin_name=postgresql-database-plugin \
  connection_url="postgresql://{{username}}:{{password}}@${DB_HOST_PARA_VAULT}:5432/cenfopay?sslmode=disable" \
  username=vault_admin \
  password="${VAULT_ADMIN_PASSWORD}" \
  allowed_roles="cenfopay-app-estatico,cenfopay-app-dinamico" >/dev/null
ok "Conexión de Vault a PostgreSQL configurada (usuario vault_admin)."

# Rol estático: Vault administra (y rota) la contraseña del usuario existente cenfopay_app.
vault_cli write database/static-roles/cenfopay-app-estatico \
  db_name=cenfopay username=cenfopay_app rotation_period=24h >/dev/null
ok "Rol estático cenfopay-app-estatico (rotación automática cada 24 h)."
alerta "Vault acaba de ROTAR la contraseña de cenfopay_app: el DB_PASSWORD del .env ya no funciona."

# Rol dinámico: cada solicitud crea un usuario nuevo de PostgreSQL que caduca.
vault_cli write database/roles/cenfopay-app-dinamico \
  db_name=cenfopay \
  creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE ON usuarios, cuentas, movimientos TO \"{{name}}\";" \
  default_ttl=15m max_ttl=1h >/dev/null
ok "Rol dinámico cenfopay-app-dinamico (TTL 15 min, máximo 1 h)."

# ------------------------------------------------------------- 3. Políticas
for entorno in dev prod; do
  vault_cli policy write "cenfopay-${entorno}" - >/dev/null <<POLITICA
# Política de mínimo privilegio para CenfoPay en ${entorno}
path "secret/data/cenfopay/${entorno}" {
  capabilities = ["read"]
}
path "database/static-creds/cenfopay-app-estatico" {
  capabilities = ["read"]
}
path "database/creds/cenfopay-app-dinamico" {
  capabilities = ["read"]
}
POLITICA
done
ok "Políticas cenfopay-dev y cenfopay-prod (cada una solo lee su entorno)."

# ---------------------------------------------------------------- 4. AppRole
if ! vault_cli auth list -format=json | grep -q '"approle/"'; then
  vault_cli auth enable approle >/dev/null
fi
vault_cli write auth/approle/role/cenfopay-dev \
  token_policies=cenfopay-dev token_ttl=30m token_max_ttl=2h \
  secret_id_ttl=24h secret_id_num_uses=0 >/dev/null

mkdir -p .secrets && chmod 700 .secrets
vault_cli read -field=role_id auth/approle/role/cenfopay-dev/role-id > .secrets/role_id
vault_cli write -f -field=secret_id auth/approle/role/cenfopay-dev/secret-id > .secrets/secret_id
# Los archivos se montan como Docker secrets: el usuario no root del contenedor debe poder leerlos.
chmod 644 .secrets/role_id .secrets/secret_id
ok "AppRole cenfopay-dev listo. Identificadores guardados en .secrets/ (ignorada por git)."

info "Resumen:"
vault_cli secrets list
vault_cli read database/static-creds/cenfopay-app-estatico -format=json \
  | grep -E '"(username|last_vault_rotation|ttl)"' || true
ok "Configuración terminada. Siguiente paso:  bash scripts/levantar.sh vault"
