# Justificación de umbrales de bloqueo y riesgos residuales · CenfoPay

> Este documento acompaña a `security/politica-umbrales.yml`. Cada número de la
> política debe tener aquí su razón. Se evalúa en el criterio 4 de la rúbrica del proyecto.

## 1. Contexto de riesgo de la aplicación
- Tipo de datos que maneja (ficticios en el curso, pero tratados como si fueran reales):
- Exposición (Internet / red interna / solo laboratorio):
- Marco de referencia aplicable (p. ej. PCI-DSS 6.2-6.3, Ley 8968, normativa SUGEF de TI):

Justificación: Una filtración de estos datos podría comprometer la privacidad de los usuarios, permitir accesos no autorizados o facilitar ataques de suplantación de identidad.

Exposición:

Aplicación web expuesta a Internet.

Justificación: Al estar disponible desde Internet, puede recibir ataques de diferentes orígenes, como intentos de explotación de vulnerabilidades, ataques de fuerza bruta, inyección SQL y robo de credenciales. 

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
| registros   | ALTA      | 0      |      |           
Se establecen umbrales estrictos para las vulnerabilidades críticas y altas porque pueden comprometer la confidencialidad, integridad y disponibilidad de la aplicación.

Se permite un máximo de cinco vulnerabilidades medias en ZAP y tres altas en los escaneos de Trivy como tolerancia inicial controlada. Esto permite mantener el desarrollo sin ignorar los riesgos existentes.

Los hallazgos permitidos deben documentarse, asignarse a un responsable y tener una fecha límite de corrección                                                                |

## 3. Disparadores
| Evento | Qué corre | Por qué |
|--------|-----------|---------|
| pull_request a main | | |
| push a main | | |
| schedule semanal | | |
| workflow_dispatch | | |
1. pull_request a main

Es importante porque revisa los cambios antes de incorporarlos al proyecto. Así se evita que un desarrollador introduzca accidentalmente una vulnerabilidad.

2. push a main

Permite comprobar que la versión integrada mantiene los controles de seguridad establecidos. También ayuda a detectar problemas que pudieron pasar inadvertidos durante la revisión.

3. schedule semanal

Las vulnerabilidades no aparecen únicamente cuando se modifica el código. Pueden descubrirse nuevas fallas en librerías, dependencias y componentes del sistema. Por eso se realizan revisiones periódicas.

4. workflow_dispatch

Permite que un responsable ejecute manualmente los análisis cuando sea necesario, por ejemplo, después de corregir una vulnerabilidad o antes de realizar una entrega importante.

## 4. Riesgos residuales (lo que queda abierto después de corregir)
| # | Riesgo | Origen (hallazgo/huella) | Por qué no se corrige ahora | Control compensatorio | Dueño | Revisión |
|---|--------|--------------------------|-----------------------------|-----------------------|-------|----------|


Permite que un responsable ejecute manualmente los análisis cuando sea necesario, por ejemplo, después de corregir una vulnerabilidad o antes de realizar una entrega importante.
| 1 | | | | | | |

## 5. Excepciones aprobadas
| Herramienta | ID | Justificación | Responsable | Vence |
|-------------|----|---------------|-------------|-------|
| | | | | |
