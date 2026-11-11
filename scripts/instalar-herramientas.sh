#!/usr/bin/env bash
# Descarga versiones fijas de Trivy, Gitleaks y Hadolint y VERIFICA su SHA-256
# antes de usarlas. Pensado para Linux x86_64 (tu codespace y GitHub Actions).
# Si la huella no coincide, NO se instala: así te proteges de una descarga alterada.
#
# Uso:  bash scripts/instalar-herramientas.sh trivy gitleaks hadolint
source "$(dirname "$0")/_comun.sh"
source security/versiones-herramientas.env

[[ "$(uname -s)-$(uname -m)" == "Linux-x86_64" ]] || \
  falla "Este instalador es para Linux x86_64 (tu codespace)."

DESTINO="${DESTINO:-$RAIZ/.herramientas/bin}"
mkdir -p "$DESTINO"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

verificar() {  # verificar <archivo> <sha256 esperado>
  echo "$2  $1" | sha256sum -c --quiet - \
    || falla "La huella SHA-256 de $(basename "$1") NO coincide. No se instala (posible manipulación)."
}

if [[ $# -eq 0 ]]; then set -- trivy gitleaks hadolint; fi
for herramienta in "$@"; do
  case "$herramienta" in
    trivy)
      archivo="$TMP/trivy.tgz"
      curl -fsSL -o "$archivo" "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz"
      verificar "$archivo" "$TRIVY_SHA256"
      tar -xzf "$archivo" -C "$DESTINO" trivy ;;
    gitleaks)
      archivo="$TMP/gitleaks.tgz"
      curl -fsSL -o "$archivo" "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
      verificar "$archivo" "$GITLEAKS_SHA256"
      tar -xzf "$archivo" -C "$DESTINO" gitleaks ;;
    hadolint)
      archivo="$TMP/hadolint"
      curl -fsSL -o "$archivo" "https://github.com/hadolint/hadolint/releases/download/v${HADOLINT_VERSION}/hadolint-linux-x86_64"
      verificar "$archivo" "$HADOLINT_SHA256"
      install -m 0755 "$archivo" "$DESTINO/hadolint" ;;
    *) falla "Herramienta desconocida: $herramienta" ;;
  esac
  ok "$herramienta instalado y verificado en $DESTINO"
done

# En GitHub Actions, agrega la carpeta al PATH de los pasos siguientes.
if [[ -n "${GITHUB_PATH:-}" ]]; then echo "$DESTINO" >> "$GITHUB_PATH"; fi
