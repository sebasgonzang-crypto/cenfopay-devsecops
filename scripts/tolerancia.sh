#!/usr/bin/env bash
# Semana 1: pone la compuerta en modo «bloquear» con tu «límite de tolerancia»:
# el máximo permitido es la cantidad de fallas que hay HOY y solo puede bajar.
# Uso: bash scripts/tolerancia.sh <ERROR de semgrep> <Medium de zap>
#   Ejemplo: bash scripts/tolerancia.sh 14 3
# Los números salen de la tabla «Herramienta | Severidad | Abiertos» del resumen
# de la Compuerta de seguridad en GitHub (columna Abiertos).
source "$(dirname "$0")/_comun.sh"
[[ $# -eq 2 ]] || falla "Uso: bash scripts/tolerancia.sh <ERROR de semgrep> <Medium de zap>   (ej.: bash scripts/tolerancia.sh 14 3)"
python3 tools/semana.py tolerancia "$1" "$2"
