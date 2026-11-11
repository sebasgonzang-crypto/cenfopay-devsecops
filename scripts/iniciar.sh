#!/usr/bin/env bash
# PRIMER PASO (una sola vez). Deja tu proyecto listo para empezar la semana 1:
#   1. Comprueba que Docker y git funcionan dentro de tu codespace.
#   2. Crea tu archivo .env con contraseñas de laboratorio.
#   3. Agrega el «historial heredado»: dos commits de otro equipo que subió por
#      error un archivo de credenciales de QA y luego lo «borró». El archivo ya
#      no se ve, pero SIGUE en el historial: lo vas a encontrar en la semana 4.
#   4. Sube esos commits a tu repositorio en GitHub.
# Todas las credenciales son FICTICIAS y solo existen para el ejercicio.
source "$(dirname "$0")/_comun.sh"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || falla "Esta carpeta no es un repositorio git. ¿Abriste el codespace desde TU repositorio?"
necesita_docker
ok "Docker funciona ($(docker --version | cut -d, -f1))"
ok "git funciona ($(git --version))"

[[ -f .env ]] || { cp .env.example .env; ok "Archivo .env creado (contraseñas de laboratorio)"; }

if git log --format=%s | grep -qx "Eliminar archivo de credenciales (se subió por error)"; then
  ok "El historial heredado ya existe: no hay nada que agregar."
else
  git config user.name  >/dev/null || git config user.name  "Estudiante CIB-665"
  git config user.email >/dev/null || git config user.email "estudiante@cenfopay.invalid"
  autor="Equipo CenfoPay (simulado) <equipo@cenfopay.invalid>"
  mkdir -p despliegue
  # Codificado en base64 para que este script no sea, él mismo, un hallazgo de
  # Gitleaks: lo que debes encontrar es el commit, no el script.
  echo "IyBDcmVkZW5jaWFsZXMgZGVsIGFtYmllbnRlIGRlIFFBIChOTyBTVUJJUikgIDwtIGFsZ3VpZW4gbm8gbGV5w7MgZXN0YSBsw61uZWEKQ0ZQX1RPS0VOX1FBPWNmcF9xYV9adDhtSzJwUTl2WDRyTDduQjN3WTZoSjFjRjVkUzBnQQpEQl9QQVNTV09SRF9RQT1RYUNlbmZvUGF5ITIwMjYK" | base64 -d > despliegue/credenciales-qa.env
  git add despliegue/credenciales-qa.env
  git commit -q --no-verify --author="$autor" -m "Agregar configuración de despliegue a QA"
  git rm -q -r despliegue
  git commit -q --no-verify --author="$autor" -m "Eliminar archivo de credenciales (se subió por error)"
  ok "Historial heredado agregado (2 commits del «equipo anterior»)."
  info "Subiendo a GitHub…"
  git push -q origin HEAD || falla "No se pudo subir. Revisa la tabla de errores de la guía (sección 11)."
  ok "Historial subido a GitHub."
fi

echo
info "Tu historial (lo más nuevo arriba):"
git log --oneline -n 5
echo
ok "Todo listo. Siguiente paso:  bash scripts/semana.sh 1"
