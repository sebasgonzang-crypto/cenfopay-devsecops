# Informe final del proyecto · Pipeline DevSecOps de CenfoPay

**Estudiante(s):** ______  ·  **Curso:** CIB-665 Automatización y DevSecOps  ·  **Profesor:** Carlos Cantero Granados
**Repositorio:** https://github.com/______/______  ·  **Fecha:** ______

## 1. Resumen ejecutivo (media página)
Qué se construyó, cuántos hallazgos había al inicio, cuántos quedan y qué riesgo residual se acepta.

## 2. Arquitectura del pipeline
Diagrama de etapas (pruebas → SAST → contenedor → DAST → secretos → compuerta) y disparadores.
Enlace a la versión final de `.github/workflows/devsecops.yml` y a la corrida aprobada.

## 3. Comparativo antes vs. después
Inserta `docs/comparativo.md` (generado con `tools/comparar_reportes.py`) y comenta los cambios más relevantes.

## 4. Escaneo de imágenes y SAST
Resumen de `docs/inventario-imagen.md` y `docs/triage-hallazgos.md`: decisiones, falsos positivos y correcciones.

## 5. Gestión y rotación de secretos
Evidencia de rotación (`reportes/evidencia-rotacion-*.txt`), revocación y del hallazgo en el historial de git:
qué se rotó, qué se revocó y por qué el secreto quedó en `.gitleaksignore`.

## 6. Umbrales y riesgos residuales
Resumen de `docs/umbrales-y-riesgo-residual.md`.

## 7. Uso ético de datos y de la IA
Declaración de que solo se usaron datos y credenciales de prueba, y resumen de `docs/bitacora-ia.md`.

## 8. Conclusiones y lecciones aprendidas

## Anexos
Enlaces a los artefactos `evidencia-seguridad-<n>` de las corridas inicial y final.
