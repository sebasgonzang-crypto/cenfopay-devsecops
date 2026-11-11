#!/usr/bin/env python3
"""Compara dos corridas del pipeline (antes / después) a partir de los CSV
normalizados que genera tools/security_gate.py.

Uso:
  python tools/comparar_reportes.py reportes/antes/hallazgos-normalizados.csv \
      reportes/despues/hallazgos-normalizados.csv -o docs/comparativo.md

Clasifica cada hallazgo (por su huella estable) en:
  corregido  -> estaba antes y ya no aparece
  nuevo      -> no estaba antes y aparece ahora (¡regresión o herramienta nueva!)
  persistente-> sigue presente
"""
import argparse
import csv
from collections import Counter
from pathlib import Path

ORDEN = ["CRITICA", "ALTA", "MEDIA", "BAJA", "INFO"]


def leer(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return {fila["huella"]: fila for fila in csv.DictReader(archivo)}


def tabla_conteo(titulo, antes, despues):
    filas = [f"### {titulo}", "", "| Herramienta | Severidad | Antes | Después | Variación |",
             "|---|---|---:|---:|---:|"]
    claves = sorted({(f["herramienta"], f["severidad_normalizada"]) for f in list(antes.values()) + list(despues.values())},
                    key=lambda c: (c[0], ORDEN.index(c[1]) if c[1] in ORDEN else 9))
    ca = Counter((f["herramienta"], f["severidad_normalizada"]) for f in antes.values())
    cd = Counter((f["herramienta"], f["severidad_normalizada"]) for f in despues.values())
    for clave in claves:
        variacion = cd[clave] - ca[clave]
        signo = f"{variacion:+d}" if variacion else "0"
        filas.append(f"| {clave[0]} | {clave[1]} | {ca[clave]} | {cd[clave]} | {signo} |")
    filas.append(f"| **Total** | | **{len(antes)}** | **{len(despues)}** | **{len(despues) - len(antes):+d}** |")
    return filas


def lista(titulo, filas):
    salida = ["", f"### {titulo} ({len(filas)})", ""]
    if not filas:
        return salida + ["_Ninguno._"]
    salida += ["| Herramienta | Regla | Severidad | Ubicación |", "|---|---|---|---|"]
    for f in sorted(filas, key=lambda x: (x["herramienta"], ORDEN.index(x["severidad_normalizada"])
                                          if x["severidad_normalizada"] in ORDEN else 9)):
        salida.append(f'| {f["herramienta"]} | `{f["regla"]}` | {f["severidad_normalizada"]} | `{f["ubicacion"]}` |')
    return salida


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("antes")
    p.add_argument("despues")
    p.add_argument("-o", "--salida", help="archivo Markdown de salida")
    args = p.parse_args()
    antes, despues = leer(args.antes), leer(args.despues)
    corregidos = [antes[h] for h in antes.keys() - despues.keys()]
    nuevos = [despues[h] for h in despues.keys() - antes.keys()]
    persistentes = [despues[h] for h in despues.keys() & antes.keys()]
    texto = ["## Comparativo de hallazgos: antes vs. después", "",
             f"- Antes: `{args.antes}`", f"- Después: `{args.despues}`", ""]
    texto += tabla_conteo("Conteo por herramienta y severidad", antes, despues)
    texto += lista("Corregidos", corregidos)
    texto += lista("Nuevos (revisar: posible regresión o herramienta añadida)", nuevos)
    texto += lista("Persistentes (deben justificarse como riesgo residual o corregirse)", persistentes)
    salida = "\n".join(texto) + "\n"
    if args.salida:
        Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
        Path(args.salida).write_text(salida, encoding="utf-8")
        print(f"Comparativo escrito en {args.salida}")
    else:
        print(salida)


if __name__ == "__main__":
    main()
