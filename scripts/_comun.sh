#!/usr/bin/env bash
# Funciones comunes de los scripts del laboratorio CIB-665.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"
# Herramientas instaladas por scripts/preparar-codespace.sh (versiones fijas y verificadas)
export PATH="$RAIZ/.herramientas/bin:$HOME/.local/bin:$PATH"

# Carga .env (valores de laboratorio) si existe.
if [[ -f .env ]]; then
  set -a; source ./.env; set +a
fi

info()  { printf '\033[1;34m[i]\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m[✓]\033[0m %s\n' "$*"; }
alerta(){ printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
falla() { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

# Semana activa del proyecto (proyecto.yml).
semana_activa() { sed -n 's/^semana:[[:space:]]*\([0-9]\).*/\1/p' proyecto.yml 2>/dev/null | head -n 1 || true; }

# Archivos de docker compose que corresponden a la semana activa.
#   semana 0-1: docker-compose.yml
#   semana 2-3: + compose.endurecido.yml (menos permisos)
#   semana 4  : + compose.secretos.yml   (contraseñas como archivos)
archivos_compose() {
  local s; s="$(semana_activa)"; s="${s:-0}"
  ARCHIVOS=(-f docker-compose.yml)
  if (( s >= 2 )); then ARCHIVOS+=(-f compose.endurecido.yml); fi
  if (( s >= 4 )); then ARCHIVOS+=(-f compose.secretos.yml); fi
}

necesita_docker() {
  command -v docker >/dev/null || falla "Docker no está disponible. ¿Estás dentro de tu codespace?"
  docker info >/dev/null 2>&1 || falla "Docker todavía está arrancando. Espera 30 segundos y vuelve a intentar."
}

# Muestra solo un fragmento de un secreto: nunca lo imprimas completo.
enmascarar() { local s="$1"; printf '%s****%s' "${s:0:3}" "$(printf '%s' "$s" | sha256sum | cut -c1-8)"; }

# Ejecuta el CLI de Vault dentro del contenedor (o el binario local si VAULT_CMD está definido).
vault_cli() {
  if [[ -n "${VAULT_CMD:-}" ]]; then
    VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}" VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN}" $VAULT_CMD "$@"
  else
    docker compose exec -T -e VAULT_ADDR=http://127.0.0.1:8200 \
      -e VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN}" vault vault "$@"
  fi
}

# psql dentro del contenedor de base de datos (o local si PSQL_CMD está definido).
psql_como() {  # psql_como <usuario> <password> <sql>
  if [[ -n "${PSQL_CMD:-}" ]]; then
    PGPASSWORD="$2" $PSQL_CMD -h "${PGHOST:-127.0.0.1}" -U "$1" -d cenfopay -tAc "$3"
  else
    docker compose exec -T -e PGPASSWORD="$2" db psql -h 127.0.0.1 -U "$1" -d cenfopay -tAc "$3"
  fi
}
