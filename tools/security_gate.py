#!/usr/bin/env python3
"""Compuerta de seguridad (security gate) de CenfoPay · CIB-665.

Lee los reportes de las herramientas, los normaliza a un formato común,
aplica la política de umbrales (security/politica-umbrales.yml) con sus
excepciones y decide si el pipeline continúa o se bloquea.

Uso:
  python tools/security_gate.py --reportes reportes \
      --politica security/politica-umbrales.yml \
      --csv reportes/hallazgos-normalizados.csv

Reportes reconocidos (nombre de archivo dentro de --reportes):
  semgrep.json      semgrep scan --json
  bandit.json       bandit -f json
  zap-baseline.json zap-baseline.py -J  (también zap-full.json)
  trivy-so.json            trivy image --pkg-types os -f json
  trivy-dependencias.json  trivy image --pkg-types library -f json
  trivy-config.json        trivy config -f json
  hadolint.json     hadolint -f json
  gitleaks.json     gitleaks git|dir -f json
  endurecimiento.json      scripts/verificar-endurecimiento.sh
  registros.json           prueba "canario" de registros del pipeline (semana 4)

Códigos de salida: 0 = aprobado (o modo auditar), 1 = bloqueado, 2 = error de uso.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Falta PyYAML: pip install pyyaml")

NORMALIZADA = {
    # semgrep
    "ERROR": "ALTA", "WARNING": "MEDIA", "INFO": "BAJA",
    # bandit / trivy
    "CRITICAL": "CRITICA", "HIGH": "ALTA", "MEDIUM": "MEDIA", "LOW": "BAJA", "UNKNOWN": "INFO",
    # zap
    "High": "ALTA", "Medium": "MEDIA", "Low": "BAJA", "Informational": "INFO",
    # hadolint
    "error": "ALTA", "warning": "MEDIA", "info": "BAJA", "style": "INFO",
    # gitleaks
    "SECRETO": "CRITICA",
    # verificación de endurecimiento (scripts/verificar-endurecimiento.sh)
    "ALTA": "ALTA", "MEDIA": "MEDIA", "BAJA": "BAJA",
}
ORDEN = ["CRITICA", "ALTA", "MEDIA", "BAJA", "INFO"]
ZAP_RIESGO = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}


def huella(*partes):
    """Identificador estable de un hallazgo (sin números de línea) para comparar corridas."""
    return hashlib.sha256("|".join(str(p) for p in partes).encode()).hexdigest()[:16]


def hallazgo(herramienta, regla, severidad, titulo, ubicacion, cwe="", extra="", clave=None):
    return {
        "herramienta": herramienta,
        "regla": regla,
        "severidad": severidad,
        "severidad_normalizada": NORMALIZADA.get(severidad, "INFO"),
        "titulo": " ".join(str(titulo).split())[:160],
        "ubicacion": ubicacion,
        "cwe": cwe,
        "detalle": extra,
        "huella": huella(herramienta, regla, clave if clave is not None else ubicacion),
    }


# --------------------------------------------------------------- lectores
SEMGREP_LEGADO = {"CRITICAL": "ERROR", "HIGH": "ERROR", "MEDIUM": "WARNING", "LOW": "INFO"}


def leer_semgrep(datos):
    for r in datos.get("results", []):
        severidad = r["extra"]["severity"]
        severidad = SEMGREP_LEGADO.get(severidad, severidad)  # versiones nuevas de Semgrep
        meta = r.get("extra", {}).get("metadata", {})
        cwe = meta.get("cwe", "")
        cwe = cwe[0] if isinstance(cwe, list) and cwe else cwe
        regla = r["check_id"].split(".")[-1]
        yield hallazgo("semgrep", regla, severidad, r["extra"].get("message", ""),
                       f'{r["path"]}:{r["start"]["line"]}', str(cwe).split(":")[0],
                       clave=r["path"])


def leer_bandit(datos):
    for r in datos.get("results", []):
        cwe = r.get("issue_cwe", {}).get("id", "")
        yield hallazgo("bandit", r["test_id"], r["issue_severity"], r["issue_text"],
                       f'{r["filename"]}:{r["line_number"]}', f"CWE-{cwe}" if cwe else "",
                       clave=r["filename"])


def leer_zap(datos):
    for sitio in datos.get("site", []):
        for a in sitio.get("alerts", []):
            riesgo = ZAP_RIESGO.get(str(a.get("riskcode")), "Informational")
            instancias = a.get("instances", [])
            uri = instancias[0].get("uri", sitio.get("@name", "")) if instancias else sitio.get("@name", "")
            cwe = a.get("cweid", "")
            yield hallazgo("zap", a.get("pluginid", "?"), riesgo, a.get("name") or a.get("alert", ""),
                           uri, f"CWE-{cwe}" if cwe not in ("", "-1", "0") else "",
                           extra=f'{len(instancias)} instancia(s)', clave=a.get("pluginid"))


def leer_trivy(datos, herramienta="trivy"):
    for res in datos.get("Results", []) or []:
        objetivo = res.get("Target", "")
        for v in res.get("Vulnerabilities", []) or []:
            corregida = v.get("FixedVersion", "")
            extra = f'{v.get("PkgName")} {v.get("InstalledVersion")} -> {corregida or "sin corrección"}'
            cwe = ",".join(v.get("CweIDs", []) or [])
            item = hallazgo(herramienta, v["VulnerabilityID"], v.get("Severity", "UNKNOWN"),
                            v.get("Title", v["VulnerabilityID"]), objetivo, cwe, extra,
                            clave=f'{v.get("PkgName")}')
            item["con_correccion"] = bool(corregida)
            yield item
        for m in res.get("Misconfigurations", []) or []:
            if m.get("Status", "FAIL") != "FAIL":
                continue
            yield hallazgo(herramienta, m.get("ID") or m.get("AVDID"), m.get("Severity", "UNKNOWN"),
                           m.get("Title", ""), objetivo, clave=objetivo)
        for s in res.get("Secrets", []) or []:
            yield hallazgo(herramienta, s.get("RuleID"), s.get("Severity", "UNKNOWN"),
                           s.get("Title", "secreto"), f'{objetivo}:{s.get("StartLine", "")}',
                           "CWE-798", clave=objetivo)


def leer_hadolint(datos):
    for r in datos:
        yield hallazgo("hadolint", r["code"], r["level"], r["message"],
                       f'{r.get("file", "Dockerfile")}:{r.get("line", "")}', clave=r.get("file"))


def leer_gitleaks(datos):
    for r in datos or []:
        commit = (r.get("Commit") or "")[:8]
        ubicacion = f'{r.get("File")}:{r.get("StartLine")}' + (f" @{commit}" if commit else "")
        yield hallazgo("gitleaks", r.get("RuleID"), "SECRETO", r.get("Description", "secreto"),
                       ubicacion, "CWE-798", clave=f'{r.get("File")}{commit}')


def leer_controles(datos, herramienta):
    """Controles propios (endurecimiento, registros): solo cuentan los que FALLAN."""
    for r in datos or []:
        if r.get("resultado") != "FALLA":
            continue
        yield hallazgo(herramienta, r["id"], r.get("severidad", "MEDIA"), r["control"],
                       herramienta, extra=r.get("detalle", ""), clave=r["id"])


LECTORES = [
    ("semgrep.json", "semgrep", leer_semgrep),
    ("bandit.json", "bandit", leer_bandit),
    ("zap-baseline.json", "zap", leer_zap),
    ("zap-full.json", "zap", leer_zap),
    ("trivy-so.json", "trivy-so", lambda d: leer_trivy(d, "trivy-so")),
    ("trivy-dependencias.json", "trivy-dependencias", lambda d: leer_trivy(d, "trivy-dependencias")),
    ("trivy-config.json", "trivy-config", lambda d: leer_trivy(d, "trivy-config")),
    ("hadolint.json", "hadolint", leer_hadolint),
    ("gitleaks.json", "gitleaks", leer_gitleaks),
    ("endurecimiento.json", "endurecimiento", lambda d: leer_controles(d, "endurecimiento")),
    ("registros.json", "registros", lambda d: leer_controles(d, "registros")),
]


def cargar_hallazgos(carpeta, solo=None):
    hallazgos, leidos = [], []
    for archivo, herramienta, lector in LECTORES:
        ruta = Path(carpeta) / archivo
        if not ruta.exists() or (solo and herramienta not in solo):
            continue
        texto = ruta.read_text(encoding="utf-8").strip()
        datos = json.loads(texto) if texto else []
        hallazgos.extend(lector(datos))
        leidos.append(archivo)
    # Si una misma regla aparece varias veces en el mismo archivo, numera las
    # repeticiones para que la comparación antes/después cuente cada ocurrencia.
    vistos = {}
    for item in hallazgos:
        n = vistos.get(item["huella"], 0)
        vistos[item["huella"]] = n + 1
        if n:
            item["huella"] = f'{item["huella"]}-{n}'
    return hallazgos, leidos


# ------------------------------------------------------------- política
def excepcion_vigente(item, excepciones, hoy):
    for exc in excepciones:
        if exc.get("herramienta") != item["herramienta"] or str(exc.get("id")) != str(item["regla"]):
            continue
        if exc.get("ubicacion") and exc["ubicacion"] not in item["ubicacion"]:
            continue
        vence = exc.get("vence")
        if isinstance(vence, str):
            vence = datetime.date.fromisoformat(vence)
        if vence and vence < hoy:
            return None, f'excepción VENCIDA el {vence} ({exc.get("id")})'
        return exc, None
    return None, None


def evaluar(hallazgos, politica, hoy=None):
    hoy = hoy or datetime.date.today()
    reglas = politica.get("herramientas", {})
    excepciones = politica.get("excepciones", []) or []
    avisos, resumen = [], {}
    for item in hallazgos:
        conf = reglas.get(item["herramienta"], {})
        item["estado"] = "abierto"
        exc, aviso = excepcion_vigente(item, excepciones, hoy)
        if aviso:
            avisos.append(aviso)
        if exc:
            item["estado"] = "excepción aprobada"
        elif conf.get("solo_con_correccion") and item.get("con_correccion") is False:
            item["estado"] = "sin corrección disponible (riesgo residual)"
        datos = resumen.setdefault(item["herramienta"], {})
        if item["estado"] == "abierto":
            datos[item["severidad"]] = datos.get(item["severidad"], 0) + 1

    violaciones = []
    for herramienta, conf in reglas.items():
        for severidad, maximo in (conf.get("umbrales") or {}).items():
            encontrados = resumen.get(herramienta, {}).get(severidad, 0)
            if encontrados > int(maximo):
                violaciones.append((herramienta, severidad, encontrados, int(maximo)))
    return resumen, violaciones, avisos


def markdown(hallazgos, resumen, violaciones, avisos, politica, leidos, modo):
    lineas = ["## Compuerta de seguridad · CenfoPay", ""]
    estado = "❌ BLOQUEADO" if violaciones and modo == "bloquear" else (
        "⚠️ UMBRALES SUPERADOS (modo auditar: no bloquea)" if violaciones else "✅ APROBADO")
    lineas += [f"**Resultado:** {estado}  ·  **Modo:** `{modo}`  ·  **Reportes:** {', '.join(leidos) or 'ninguno'}", ""]
    lineas += ["| Herramienta | Severidad | Abiertos | Umbral | Estado |", "|---|---|---:|---:|---|"]
    for herramienta, conf in (politica.get("herramientas") or {}).items():
        if herramienta not in {h["herramienta"] for h in hallazgos} and not any(
                herramienta in a for a in leidos):
            continue
        for severidad, maximo in (conf.get("umbrales") or {}).items():
            n = resumen.get(herramienta, {}).get(severidad, 0)
            marca = "❌" if n > int(maximo) else "✅"
            lineas.append(f"| {herramienta} | {severidad} | {n} | {maximo} | {marca} |")
    lineas += ["", "### Hallazgos por herramienta (severidad normalizada)", "",
               "| Herramienta | " + " | ".join(ORDEN) + " | Excepciones | Sin corrección |",
               "|---|" + "---:|" * (len(ORDEN) + 2)]
    for herramienta in sorted({h["herramienta"] for h in hallazgos}):
        propios = [h for h in hallazgos if h["herramienta"] == herramienta]
        conteo = [sum(1 for h in propios if h["severidad_normalizada"] == s and h["estado"] == "abierto")
                  for s in ORDEN]
        exc = sum(1 for h in propios if h["estado"] == "excepción aprobada")
        sin = sum(1 for h in propios if h["estado"].startswith("sin corrección"))
        lineas.append(f"| {herramienta} | " + " | ".join(map(str, conteo)) + f" | {exc} | {sin} |")
    if avisos:
        lineas += ["", "### Avisos"] + [f"- {a}" for a in sorted(set(avisos))]
    criticos = [h for h in hallazgos if h["estado"] == "abierto" and h["severidad_normalizada"] in ("CRITICA", "ALTA")]
    if criticos:
        lineas += ["", "### Hallazgos críticos y altos abiertos (máx. 25)", "",
                   "| Herramienta | Regla | Sev. | Ubicación | Título |", "|---|---|---|---|---|"]
        for h in criticos[:25]:
            lineas.append(f'| {h["herramienta"]} | `{h["regla"]}` | {h["severidad_normalizada"]} | '
                          f'`{h["ubicacion"]}` | {h["titulo"][:90]} |')
    return "\n".join(lineas) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--reportes", default="reportes")
    p.add_argument("--politica", default="security/politica-umbrales.yml")
    p.add_argument("--csv", help="ruta del CSV normalizado (trazabilidad)")
    p.add_argument("--herramientas", help="lista separada por comas para evaluar solo esas")
    p.add_argument("--modo", choices=["auditar", "bloquear"], help="sobrescribe el modo de la política")
    args = p.parse_args()

    if not Path(args.politica).exists():
        print(f"No existe la política {args.politica}", file=sys.stderr)
        return 2
    politica = yaml.safe_load(Path(args.politica).read_text(encoding="utf-8")) or {}
    modo = args.modo or politica.get("modo", "auditar")
    solo = set(args.herramientas.split(",")) if args.herramientas else None
    if solo:
        politica["herramientas"] = {k: v for k, v in (politica.get("herramientas") or {}).items() if k in solo}

    hallazgos, leidos = cargar_hallazgos(args.reportes, solo)
    resumen, violaciones, avisos = evaluar(hallazgos, politica)
    texto = markdown(hallazgos, resumen, violaciones, avisos, politica, leidos, modo)
    print(texto)

    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as resumen_gh:
            resumen_gh.write(texto)
    if args.csv:
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        campos = ["huella", "herramienta", "regla", "severidad", "severidad_normalizada", "estado",
                  "ubicacion", "cwe", "titulo", "detalle"]
        with open(args.csv, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos, extrasaction="ignore")
            escritor.writeheader()
            escritor.writerows(hallazgos)
        print(f"CSV normalizado: {args.csv} ({len(hallazgos)} hallazgos)")

    if violaciones and modo == "bloquear":
        for herramienta, severidad, n, maximo in violaciones:
            print(f"::error title=Umbral superado::{herramienta} {severidad}: {n} > {maximo}")
        return 1
    for herramienta, severidad, n, maximo in violaciones:
        print(f"::warning title=Umbral superado (auditar)::{herramienta} {severidad}: {n} > {maximo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
