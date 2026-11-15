#!/usr/bin/env bash
# Ejecuta en tu codespace los mismos escaneos del pipeline. Los reportes quedan
# en ./reportes y al final se evalúa la misma compuerta que en GitHub Actions.
#
# Uso:  bash scripts/escanear-local.sh [sast|contenedor|dast|secretos|todo]   (por defecto: todo)
# Usa las herramientas instaladas en el codespace (versión fija y huella verificada);
# si alguna falta, la instala con scripts/instalar-herramientas.sh.
source "$(dirname "$0")/_comun.sh"
source security/versiones-herramientas.env

ETAPA="${1:-todo}"
mkdir -p reportes
[[ -f .env ]] || { cp .env.example .env; alerta "Se creó .env a partir de .env.example"; }

asegurar() {  # asegurar <binario>: instala la herramienta verificada si no está
  command -v "$1" >/dev/null || bash scripts/instalar-herramientas.sh "$1"
}

asegurar_python() {  # semgrep y bandit con versión fija, en el usuario del codespace
  command -v semgrep >/dev/null && command -v bandit >/dev/null && return
  info "Instalando Semgrep ${SEMGREP_VERSION} y Bandit ${BANDIT_VERSION} (solo la primera vez)…"
  pip install --quiet --user "semgrep==${SEMGREP_VERSION}" "bandit==${BANDIT_VERSION}" \
    || pip install --quiet "semgrep==${SEMGREP_VERSION}" "bandit==${BANDIT_VERSION}"
}

sast() {
  asegurar_python
  info "SAST · Semgrep ${SEMGREP_VERSION} (reglas generales + reglas de CenfoPay)"
  semgrep scan --config p/python --config p/flask --config security/semgrep/reglas-cenfopay.yml \
    --metrics=off --quiet --json-output=reportes/semgrep.json --sarif-output=reportes/semgrep.sarif app/ >/dev/null || true
  info "SAST · Bandit ${BANDIT_VERSION}"
  bandit -q -r app -x app/tests -f json -o reportes/bandit.json --exit-zero || true
}

contenedor() {
  necesita_docker
  asegurar hadolint; asegurar trivy
  info "Dockerfile · Hadolint ${HADOLINT_VERSION}"
  hadolint --config security/hadolint.yaml --no-fail -f json app/Dockerfile > reportes/hadolint.json || true
  info "Construyendo la imagen cenfopay:local"
  docker build -q -t cenfopay:local app/ >/dev/null
  info "Imagen · Trivy ${TRIVY_VERSION} (SBOM, sistema operativo, librerías, configuración)"
  trivy image -q --format cyclonedx --output reportes/sbom-cyclonedx.json cenfopay:local
  trivy image -q --pkg-types os --scanners vuln -f json -o reportes/trivy-so.json cenfopay:local
  trivy image -q --pkg-types library --scanners vuln,secret -f json -o reportes/trivy-dependencias.json cenfopay:local
  trivy config -q -f json -o reportes/trivy-config.json app/
  trivy convert --format table -o reportes/trivy-so.txt reportes/trivy-so.json || true
  trivy convert --format table -o reportes/trivy-dependencias.txt reportes/trivy-dependencias.json || true
  bash scripts/verificar-endurecimiento.sh cenfopay:local || true
}

dast() {
  necesita_docker
  local archivos=(-f docker-compose.yml)
  [[ -f compose.endurecido.yml && "${USAR_ENDURECIDO:-1}" == "1" ]] && archivos+=(-f compose.endurecido.yml)
  [[ -n "${COMPOSE_EXTRA:-}" ]] && for f in $COMPOSE_EXTRA; do archivos+=(-f "$f"); done
  info "DAST · levantando CenfoPay con: ${archivos[*]}"
  docker compose "${archivos[@]}" up -d --build db app
  for _ in $(seq 1 45); do curl -fsS http://127.0.0.1:8000/salud >/dev/null 2>&1 && break; sleep 2; done
  chmod 777 reportes
  info "DAST · OWASP ZAP baseline (1-3 minutos)"
  docker compose "${archivos[@]}" --profile dast run --rm zap || true
  docker compose "${archivos[@]}" logs app > reportes/app.log 2>&1 || true
  ok "Reporte HTML: reportes/zap-baseline.html"
}

secretos() {
  asegurar gitleaks
  info "Secretos · Gitleaks ${GITLEAKS_VERSION} (historial completo)"
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || falla "No hay repositorio git."
  gitleaks git . --config security/gitleaks.toml --redact --exit-code 0 --no-banner \
    --report-format json --report-path reportes/gitleaks.json
}

case "$ETAPA" in
  sast) sast ;;
  contenedor) contenedor ;;
  dast) dast ;;
  secretos) secretos ;;
  todo) sast; contenedor; dast; secretos ;;
  *) falla "Etapa desconocida: $ETAPA (usa sast|contenedor|dast|secretos|todo)" ;;
esac

info "Compuerta de seguridad (misma política que en GitHub)"
python3 tools/security_gate.py --reportes reportes --csv reportes/hallazgos-normalizados.csv || true
