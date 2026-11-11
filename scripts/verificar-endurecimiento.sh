#!/usr/bin/env bash
# Semana 2 · Verificación POST-endurecimiento de la imagen y del contenedor.
# No basta con "creer" que el Dockerfile quedó bien: se comprueba sobre el
# artefacto real. Genera reportes/endurecimiento.json (lo evalúa la compuerta)
# y una tabla legible en la consola.
#
# Uso:  bash scripts/verificar-endurecimiento.sh <imagen> [contenedor-en-ejecución]
#   ej: bash scripts/verificar-endurecimiento.sh cenfopay:local cenfopay-app-1
source "$(dirname "$0")/_comun.sh"

IMAGEN="${1:?Indica la imagen, por ejemplo cenfopay:local}"
CONTENEDOR="${2:-}"
TAMANO_MAX_MB="${TAMANO_MAX_MB:-250}"
mkdir -p reportes
SALIDA="reportes/endurecimiento.json"
RESULTADOS=()

registrar() {  # registrar <id> <control> <PASA|FALLA|NO_APLICA> <severidad> <detalle>
  local marca="✅"; [[ "$3" == "FALLA" ]] && marca="❌"; [[ "$3" == "NO_APLICA" ]] && marca="➖"
  printf '%s %-6s %-48s %s\n' "$marca" "$1" "$2" "$5"
  RESULTADOS+=("$(python3 -c 'import json,sys;print(json.dumps(dict(zip(["id","control","resultado","severidad","detalle"],sys.argv[1:]))))' "$1" "$2" "$3" "$4" "$5")")
}

docker image inspect "$IMAGEN" >/dev/null 2>&1 || falla "No existe la imagen $IMAGEN (constrúyela primero)."
info "Imagen: $IMAGEN"

USUARIO="$(docker image inspect -f '{{.Config.User}}' "$IMAGEN")"
if [[ -n "$USUARIO" && "$USUARIO" != "0" && "$USUARIO" != "root" && "$USUARIO" != 0:* ]]; then
  registrar END-01 "La imagen define un usuario no root (USER)" PASA ALTA "USER=$USUARIO"
else
  registrar END-01 "La imagen define un usuario no root (USER)" FALLA ALTA "USER='${USUARIO:-<vacío>}' (root)"
fi

SENSIBLES="$(docker image inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$IMAGEN" \
  | grep -Ei '^[A-Z_]*(PASSWORD|SECRET|TOKEN|KEY)[A-Z_]*=.+' | cut -d= -f1 | grep -v '_FILE$' | tr '\n' ' ' || true)"
if [[ -z "$SENSIBLES" ]]; then
  registrar END-02 "Sin secretos en variables ENV de la imagen" PASA ALTA "ninguna variable sensible"
else
  registrar END-02 "Sin secretos en variables ENV de la imagen" FALLA ALTA "variables: $SENSIBLES"
fi

if [[ "$(docker image inspect -f '{{if .Config.Healthcheck}}si{{end}}' "$IMAGEN")" == "si" ]]; then
  registrar END-03 "HEALTHCHECK definido" PASA BAJA "presente"
else
  registrar END-03 "HEALTHCHECK definido" FALLA BAJA "ausente"
fi

MB=$(( $(docker image inspect -f '{{.Size}}' "$IMAGEN") / 1024 / 1024 ))
if (( MB <= TAMANO_MAX_MB )); then
  registrar END-04 "Tamaño de la imagen <= ${TAMANO_MAX_MB} MB" PASA MEDIA "${MB} MB"
else
  registrar END-04 "Tamaño de la imagen <= ${TAMANO_MAX_MB} MB" FALLA MEDIA "${MB} MB (superficie de ataque mayor)"
fi

HERRAMIENTAS="$(docker run --rm --entrypoint sh "$IMAGEN" -c \
  'for h in curl wget vim nc ping apt-get gcc; do command -v $h >/dev/null 2>&1 && printf "%s " $h; done' 2>/dev/null || echo "__sin_shell__")"
if [[ "$HERRAMIENTAS" == "__sin_shell__" ]]; then
  registrar END-05 "Sin herramientas innecesarias en runtime" PASA MEDIA "imagen sin shell (distroless)"
elif [[ -z "${HERRAMIENTAS// /}" ]]; then
  registrar END-05 "Sin herramientas innecesarias en runtime" PASA MEDIA "ninguna encontrada"
else
  registrar END-05 "Sin herramientas innecesarias en runtime" FALLA MEDIA "encontradas: $HERRAMIENTAS"
fi

if [[ -n "$CONTENEDOR" ]]; then
  info "Contenedor en ejecución: $CONTENEDOR"
  docker inspect "$CONTENEDOR" >/dev/null 2>&1 || falla "No existe el contenedor $CONTENEDOR"
  campo() { docker inspect -f "$1" "$CONTENEDOR"; }

  [[ "$(campo '{{.HostConfig.ReadonlyRootfs}}')" == "true" ]] \
    && registrar END-06 "Sistema de archivos raíz de solo lectura" PASA MEDIA "read_only: true" \
    || registrar END-06 "Sistema de archivos raíz de solo lectura" FALLA MEDIA "escribible"

  [[ "$(campo '{{.HostConfig.CapDrop}}')" == *ALL* ]] \
    && registrar END-07 "Capacidades Linux eliminadas (cap_drop ALL)" PASA ALTA "$(campo '{{.HostConfig.CapDrop}}')" \
    || registrar END-07 "Capacidades Linux eliminadas (cap_drop ALL)" FALLA ALTA "CapDrop=$(campo '{{.HostConfig.CapDrop}}')"

  [[ "$(campo '{{.HostConfig.SecurityOpt}}')" == *no-new-privileges* ]] \
    && registrar END-08 "no-new-privileges activo" PASA ALTA "activo" \
    || registrar END-08 "no-new-privileges activo" FALLA ALTA "ausente"

  [[ "$(campo '{{.HostConfig.Privileged}}')" == "false" ]] \
    && registrar END-09 "Contenedor no privilegiado" PASA ALTA "privileged=false" \
    || registrar END-09 "Contenedor no privilegiado" FALLA ALTA "privileged=true"

  PUERTOS="$(campo '{{range $p, $b := .HostConfig.PortBindings}}{{range $b}}{{.HostIp}}:{{.HostPort}} {{end}}{{end}}')"
  EXPUESTOS=""
  for enlace in $PUERTOS; do [[ "$enlace" == 127.0.0.1:* ]] || EXPUESTOS+="$enlace "; done
  if [[ -z "$EXPUESTOS" ]]; then
    registrar END-10 "Puertos publicados solo en 127.0.0.1" PASA MEDIA "${PUERTOS:-sin puertos publicados}"
  else
    registrar END-10 "Puertos publicados solo en 127.0.0.1" FALLA MEDIA "expuestos en todas las interfaces: $EXPUESTOS"
  fi

  UID_PROC="$(docker exec "$CONTENEDOR" id -u 2>/dev/null || true)"
  if [[ -z "$UID_PROC" ]]; then   # imagen sin "id" (distroless): se usa la configuración
    UID_PROC="$(campo '{{.Config.User}}')"; UID_PROC="${UID_PROC%%:*}"
  fi
  [[ -n "$UID_PROC" && "$UID_PROC" != "0" && "$UID_PROC" != "root" ]] \
    && registrar END-11 "El proceso corre con UID distinto de 0" PASA ALTA "uid=$UID_PROC" \
    || registrar END-11 "El proceso corre con UID distinto de 0" FALLA ALTA "uid=${UID_PROC:-0}"

  [[ -n "$(campo '{{.HostConfig.Memory}}' | grep -v '^0$')" ]] \
    && registrar END-12 "Límite de memoria definido" PASA BAJA "$(( $(campo '{{.HostConfig.Memory}}') / 1024 / 1024 )) MB" \
    || registrar END-12 "Límite de memoria definido" FALLA BAJA "sin límite"
else
  registrar END-06 "Controles de ejecución (read_only, cap_drop, ...)" NO_APLICA MEDIA "indica un contenedor para verificarlos"
fi

printf '[%s]\n' "$(IFS=,; echo "${RESULTADOS[*]}")" > "$SALIDA"
ok "Resultados en $SALIDA"
