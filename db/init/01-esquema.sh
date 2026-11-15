#!/bin/sh
# Inicializa la base de datos de CenfoPay (lo ejecuta la imagen oficial de PostgreSQL
# la primera vez que arranca con el volumen vacío).
set -eu
psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -v app_pw="$APP_DB_PASSWORD" \
     -v vault_pw="$VAULT_ADMIN_PASSWORD" \
     -f /opt/cenfopay/esquema.sql
echo "CenfoPay: esquema y datos de prueba cargados."
