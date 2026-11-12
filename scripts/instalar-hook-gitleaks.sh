#!/usr/bin/env bash
# Semana 4 · Instala un hook pre-commit que ejecuta Gitleaks sobre lo que vas a
# confirmar (staged). Si detecta un secreto, el commit se cancela ANTES de que
# llegue al historial: es el control más barato de toda la cadena.
#
# Usa el binario local si existe (scripts/instalar-herramientas.sh gitleaks) o,
# si no, la imagen oficial de Docker.
source "$(dirname "$0")/_comun.sh"
[[ -d .git ]] || falla "Ejecuta esto en la raíz del repositorio git."
command -v gitleaks >/dev/null || bash scripts/instalar-herramientas.sh gitleaks

cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# Hook instalado por scripts/instalar-hook-gitleaks.sh (CIB-665)
RAIZ="$(git rev-parse --show-toplevel)"
source "$RAIZ/security/versiones-herramientas.env"
if [[ -x "$RAIZ/.herramientas/bin/gitleaks" ]]; then
  GITLEAKS=("$RAIZ/.herramientas/bin/gitleaks")
elif command -v gitleaks >/dev/null; then
  GITLEAKS=(gitleaks)
else
  export MSYS_NO_PATHCONV=1
  GITLEAKS=(docker run --rm -v "$RAIZ:/src" -w /src "ghcr.io/gitleaks/gitleaks:v${GITLEAKS_VERSION}")
fi
if ! "${GITLEAKS[@]}" git --pre-commit --staged --redact --no-banner \
     --config security/gitleaks.toml; then
  echo ""
  echo "✋ Gitleaks detectó un posible secreto en los cambios preparados."
  echo "   Quítalo, usa una variable de entorno o un gestor de secretos y vuelve a intentar."
  echo "   (Solo si es un falso positivo confirmado: agrega su huella a .gitleaksignore)"
  exit 1
fi
HOOK
chmod +x .git/hooks/pre-commit
ok "Hook pre-commit instalado en .git/hooks/pre-commit"
info 'Pruébalo:  echo "API_TOKEN=cfp_live_$(openssl rand -hex 12)" > prueba.env && git add prueba.env && git commit -m prueba'
