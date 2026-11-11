#!/usr/bin/env bash
# Fija las imágenes base de app/Dockerfile por su digest («código de barras» exacto).
# Cambia, por ejemplo:  ARG PYTHON_IMAGE=python:3.13-slim-trixie
#               por:    ARG PYTHON_IMAGE=python:3.13-slim-trixie@sha256:abcd…
source "$(dirname "$0")/_comun.sh"
necesita_docker
dockerfile=app/Dockerfile
mapfile -t lineas < <(grep -E '^ARG [A-Z_]+=[a-z0-9./_-]+:[A-Za-z0-9._-]+$' "$dockerfile" || true)
[[ ${#lineas[@]} -gt 0 ]] || { ok "Las imágenes de $dockerfile ya están fijadas por digest (o no hay ARG de imagen)."; exit 0; }
for linea in "${lineas[@]}"; do
  variable="${linea#ARG }"; variable="${variable%%=*}"
  imagen="${linea#*=}"
  info "Buscando el digest de ${imagen}…"
  digest="$(docker buildx imagetools inspect "$imagen" | awk '/^Digest:/ {print $2; exit}')"
  [[ "$digest" == sha256:* ]] || falla "No pude obtener el digest de ${imagen}. Revisa tu conexión y reintenta."
  sed -i "s|^ARG ${variable}=${imagen}\$|ARG ${variable}=${imagen}@${digest}|" "$dockerfile"
  ok "${variable} = ${imagen}@${digest:0:19}…"
done
info "Mira el cambio con:  git diff app/Dockerfile"
