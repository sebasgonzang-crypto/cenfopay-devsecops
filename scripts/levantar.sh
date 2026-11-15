#!/usr/bin/env bash
# Levanta CenfoPay (base de datos + aplicación) con la configuración de tu semana.
# Uso: bash scripts/levantar.sh          -> según proyecto.yml
#      bash scripts/levantar.sh vault    -> semana 4: la app pide sus contraseñas a Vault
source "$(dirname "$0")/_comun.sh"
necesita_docker
[[ -f .env ]] || cp .env.example .env
archivos_compose
if [[ "${1:-}" == "vault" ]]; then
  [[ -s .secrets/role_id && -s .secrets/secret_id ]] || falla "Primero prepara Vault: docker compose --profile secretos up -d vault && bash scripts/vault-configurar.sh"
  info "Levantando con: ${ARCHIVOS[*]} -f compose.vault.yml"
  docker compose --profile secretos "${ARCHIVOS[@]}" -f compose.vault.yml up -d --build db vault app
else
  info "Levantando con: ${ARCHIVOS[*]}"
  docker compose "${ARCHIVOS[@]}" up -d --build db app
fi
info "Esperando a que CenfoPay responda…"
for _ in $(seq 1 45); do
  if curl -fsS http://127.0.0.1:8000/salud >/dev/null 2>&1; then
    ok "CenfoPay está viva: $(curl -fsS http://127.0.0.1:8000/salud)"
    info "Para verla en el navegador: pestaña PUERTOS (PORTS) → fila 8000 → ícono del globo 🌐"
    exit 0
  fi
  sleep 2
done
alerta "CenfoPay no respondió. Mira sus mensajes con:  docker compose logs app"
exit 1
