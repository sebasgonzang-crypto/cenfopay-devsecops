# Inventario y clasificación de vulnerabilidades del contenedor · CenfoPay (semana 2)

## 1. Inventario (SBOM)
- Archivo: `reportes/sbom-cyclonedx.json`   · Componentes totales: ____
- Imagen base: ________________  · Digest: `sha256:________________`
- Sistema operativo y versión: __________  · Paquetes del SO: ____  · Librerías Python: ____

## 2. Clasificación (antes / después del endurecimiento)
| Origen | Severidad | Antes | Después | Con corrección | Sin corrección | En CISA KEV |
|--------|-----------|------:|--------:|---------------:|---------------:|------------:|
| SO (trivy-so) | CRITICAL | | | | | |
| SO (trivy-so) | HIGH | | | | | |
| Dependencias (trivy-dependencias) | CRITICAL | | | | | |
| Dependencias (trivy-dependencias) | HIGH | | | | | |
| Configuración (trivy-config / hadolint) | ALTA | | | | | |

## 3. Top 5 para priorizar
| CVE | Paquete | CVSS | EPSS | ¿KEV? | ¿Se usa la función vulnerable? | Prioridad |
|-----|---------|------|------|-------|--------------------------------|-----------|
| | | | | | | |

## 4. Selección de la imagen base
| Criterio | Opción A | Opción B | Opción C |
|----------|----------|----------|----------|
| Imagen | `python:3.9` (actual) | | |
| Mantenida / con soporte | | | |
| Tamaño (MB) | | | |
| Vulnerabilidades C/H | | | |
| Tiene shell / gestor de paquetes | | | |
| Origen verificado (oficial, firmado) | | | |
| Compatibilidad con la app | | | |
| **Decisión y justificación** | | | |

## 5. Verificación post-endurecimiento
Pega aquí la salida de `bash scripts/verificar-endurecimiento.sh cenfopay:local cenfopay-app-1`.
