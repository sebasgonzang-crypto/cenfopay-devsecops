# Inventario y clasificación de vulnerabilidades del contenedor · CenfoPay (semana 2)

## 1. Inventario (SBOM)
- Archivo: `reportes/sbom-cyclonedx.json`   · Componentes totales: __512__
- Imagen base: ___debian13.1_____________  · Digest: `sha256:sha256:414fc4229befd1c740922b120b832761a6629d9562a0428a6d94baceaa7247f3
- Sistema operativo y versión: _debian13.1_________  · Paquetes del SO: ____  · Librerías Python: (wheel 0.45.1____

## 2. Clasificación (antes / después del endurecimiento)
| Origen | Severidad | Antes | Después | Con corrección | Sin corrección | En CISA KEV |
|--------|-----------|------:|--------:|---------------:|---------------:|------------:|
| SO (trivy-so) | CRITICAL | | | | | |235
| SO (trivy-so) | HIGH | | | | | |2599
| Dependencias (trivy-dependencias) | CRITICAL | | | | | | 0
| Dependencias (trivy-dependencias) | HIGH | | | | | | 16
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
