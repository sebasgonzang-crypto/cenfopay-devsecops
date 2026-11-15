# Registro de triage de hallazgos · CenfoPay

> Una fila por hallazgo revisado. La **huella** es la columna `huella` de
> `reportes/hallazgos-normalizados.csv` (la genera `tools/security_gate.py`).
> Decisión: **VP** verdadero positivo · **FP** falso positivo · **RA** riesgo aceptado (con excepción y vencimiento).

| # | Huella | Herramienta | Regla / CVE | Ubicación | Severidad | Decisión | Justificación (contexto, explotabilidad, evidencia) | Acción | Responsable | Fecha |
|---|--------|-------------|-------------|-----------|-----------|----------|------------------------------------------------------|--------|-------------|-------|
| 1 |        |             |             |           |           |          |                                                      |        |             |       |
| 2 |        |             |             |           |           |          |                                                      |        |             |       |
| 3 |        |             |             |           |           |          |                                                      |        |             |       |

## Criterios de decisión usados
- **FP**: la regla dispara pero el flujo de datos no es explotable en este contexto (explica por qué).
- **RA**: es real, pero se acepta temporalmente: existe un control compensatorio y una fecha de vencimiento.
- Todo FP o RA se refleja en el código (`# nosemgrep: <regla>` / `# nosec <id>`) **o** en
  `security/politica-umbrales.yml > excepciones`, nunca solo en este documento.
