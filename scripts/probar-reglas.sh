#!/usr/bin/env bash
# Semana 3 · Comprueba que las reglas propias de Semgrep funcionan con sus ejemplos.
# (líneas «ruleid:» deben avisar; líneas «ok:» no deben avisar)
source "$(dirname "$0")/_comun.sh"
source security/versiones-herramientas.env
command -v semgrep >/dev/null || pip install --quiet --user "semgrep==${SEMGREP_VERSION}"
semgrep --test --metrics=off security/semgrep/
