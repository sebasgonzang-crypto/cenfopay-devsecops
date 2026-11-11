# Justificación de umbrales de bloqueo y riesgos residuales · CenfoPay

> Este documento acompaña a `security/politica-umbrales.yml`. Cada número de la
> política debe tener aquí su razón. Se evalúa en el criterio 4 de la rúbrica del proyecto.

## 1. Contexto de riesgo de la aplicación
- Tipo de datos que maneja (ficticios en el curso, pero tratados como si fueran reales):
- Exposición (Internet / red interna / solo laboratorio):
- Marco de referencia aplicable (p. ej. PCI-DSS 6.2-6.3, Ley 8968, normativa SUGEF de TI):

## 2. Umbrales por herramienta
| Herramienta | Severidad | Umbral | Modo | Por qué este número (impacto, explotabilidad, ruido, costo de bloquear) |
|-------------|-----------|-------:|------|--------------------------------------------------------------------------|
| semgrep     | ERROR     | 0      |      |                                                                          |
| zap         | High      | 0      |      |                                                                          |
| zap         | Medium    |        |      |                                                                          |
| hadolint    | error     |        |      |                                                                          |
| trivy-so    | CRITICAL / HIGH |  |      |                                                                          |
| trivy-dependencias | CRITICAL / HIGH | |  |                                                                          |
| bandit      | HIGH      |        |      |                                                                          |
| gitleaks    | SECRETO   | 0      |      |                                                                          |
| endurecimiento | ALTA   |        |      |                                                                          |
| registros   | ALTA      | 0      |      |                                                                          |

## 3. Disparadores
| Evento | Qué corre | Por qué |
|--------|-----------|---------|
| pull_request a main | | |
| push a main | | |
| schedule semanal | | |
| workflow_dispatch | | |

## 4. Riesgos residuales (lo que queda abierto después de corregir)
| # | Riesgo | Origen (hallazgo/huella) | Por qué no se corrige ahora | Control compensatorio | Dueño | Revisión |
|---|--------|--------------------------|-----------------------------|-----------------------|-------|----------|
| 1 | | | | | | |

## 5. Excepciones aprobadas
| Herramienta | ID | Justificación | Responsable | Vence |
|-------------|----|---------------|-------------|-------|
| | | | | |
