#!/usr/bin/env bash
# Se ejecuta SOLO al crear el codespace (.devcontainer/devcontainer.json).
# Deja instaladas las herramientas del curso con versión fija; no necesitas ejecutarlo tú.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
source security/versiones-herramientas.env
[[ -f .env ]] || cp .env.example .env
git config --global pull.rebase false
chmod +x scripts/*.sh 2>/dev/null || true
echo "[i] Instalando Semgrep, Bandit y PyYAML (versiones fijas)…"
pip install --quiet --user pyyaml "semgrep==${SEMGREP_VERSION}" "bandit==${BANDIT_VERSION}" \
  || pip install --quiet pyyaml "semgrep==${SEMGREP_VERSION}" "bandit==${BANDIT_VERSION}" \
  || echo "[!] No se pudieron instalar ahora; los scripts lo reintentarán cuando hagan falta."
echo "[i] Instalando Trivy, Hadolint y Gitleaks (con verificación de huella SHA-256)…"
bash scripts/instalar-herramientas.sh trivy hadolint gitleaks \
  || echo "[!] No se pudieron instalar ahora; los scripts lo reintentarán cuando hagan falta."
echo
echo "✅ Codespace de CenfoPay listo. Primer paso (solo una vez):  bash scripts/iniciar.sh"
