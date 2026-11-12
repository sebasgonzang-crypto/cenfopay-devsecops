#!/usr/bin/env bash
# Toma una «foto» de la seguridad de CenfoPay con TODAS las herramientas del curso
# (Semgrep, Bandit, Hadolint, Trivy, ZAP y Gitleaks) y la guarda en reportes/<nombre>/.
# Uso: bash scripts/foto.sh antes     -> semana 1: tu línea base
#      bash scripts/foto.sh despues   -> semanas 3 y 4: para comparar
# Tarda unos 10 minutos (ZAP y Trivy son los más lentos).
source "$(dirname "$0")/_comun.sh"
necesita_docker
nombre="${1:-}"
[[ "$nombre" == "antes" || "$nombre" == "despues" ]] || falla "Uso: bash scripts/foto.sh antes|despues"
s="$(semana_activa)"; s="${s:-0}"
mkdir -p reportes
find reportes -maxdepth 1 -type f ! -name .gitkeep -delete
export USAR_ENDURECIDO=0 COMPOSE_EXTRA=""
if (( s >= 2 )); then USAR_ENDURECIDO=1; fi
if (( s >= 4 )); then COMPOSE_EXTRA="compose.secretos.yml"; fi
info "Foto «${nombre}» (semana ${s}). Esto tarda unos 10 minutos: puedes seguir leyendo la guía."
bash scripts/escanear-local.sh todo
rm -rf "reportes/${nombre}"; mkdir -p "reportes/${nombre}"
find reportes -maxdepth 1 -type f ! -name .gitkeep -exec mv {} "reportes/${nombre}/" \;
ok "Foto guardada en reportes/${nombre}/ (no se sube a GitHub)."
info "Para ver el reporte de ZAP: en el Explorador, clic derecho en reportes/${nombre}/zap-baseline.html → Download, y ábrelo en tu navegador."
