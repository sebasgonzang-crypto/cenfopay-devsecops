# CenfoPay · Proyecto DevSecOps · CIB-665 Automatización y DevSecOps

**Universidad Cenfotec · Programa Técnico · Prof. Carlos Cantero Granados**

Este repositorio es tu proyecto del curso. Durante cuatro semanas vas a construir,
paso a paso, un **pipeline DevSecOps** para **CenfoPay**, una billetera digital
**ficticia y con fallas puestas a propósito**. La **guía paso a paso** (documento Word
que entrega el docente) explica cada clic y cada comando.

> ⚠️ **Uso ético.** CenfoPay tiene vulnerabilidades reales a propósito. Úsala solo dentro
> de tu codespace o del pipeline de tu repositorio. Todas las contraseñas y datos del
> proyecto son de prueba. Nunca uses datos, tokens ni contraseñas reales.

## Cómo se trabaja: todo en el navegador (GitHub Codespaces)

No instalas nada en tu computadora. Solo necesitas una cuenta gratuita de GitHub.

1. En la página de la plantilla: **Use this template → Create a new repository**
   (nombre `cenfopay-devsecops`, visibilidad **Public**).
2. En tu repositorio nuevo: **Code → Codespaces → Create codespace on main**.
   La primera vez tarda unos 5 minutos (instala Docker y las herramientas del curso).
3. En la terminal de abajo, una sola vez:
   ```bash
   bash scripts/iniciar.sh
   ```
4. Cada semana sigue la guía. El comando principal de cada semana es:
   ```bash
   bash scripts/semana.sh 1      # luego 2, 3 y 4
   ```

> 💡 Cuando termines de trabajar, detén el codespace: en github.com/codespaces, botón **…**
> junto a tu codespace → **Stop codespace**. Tu cuenta gratuita incluye 120 horas-núcleo y
> 15 GB al mes (unas 60 horas en la máquina de 2 núcleos). Para volver, entra al mismo
> enlace y ábrelo de nuevo: tus archivos siguen ahí.

## Proyecto bola de nieve: una semana a la vez

| Semana | Tema | Comando | Lo que se enciende en el pipeline |
|---|---|---|---|
| 1 | Revisiones automáticas | `bash scripts/semana.sh 1` | Pruebas, Semgrep (SAST), ZAP (DAST) y compuerta |
| 2 | Contenedores Docker | `bash scripts/semana.sh 2` | Hadolint, Trivy, SBOM y verificación del endurecimiento |
| 3 | Revisión del código | `bash scripts/semana.sh 3` | Reglas propias, Bandit y pruebas de seguridad |
| 4 | Contraseñas y llaves | `bash scripts/semana.sh 4` | Gitleaks, secretos del environment y prueba canario |

`semana.sh` escribe la semana en `proyecto.yml` (el pipeline la lee y enciende las
revisiones que corresponden), aplica las **correcciones listas** de esa semana
(carpeta `correcciones/`) y actualiza la política de umbrales. Después **tú** revisas
los cambios (`git diff`), los explicas y los subes con un pull request.

Usuarios de prueba de CenfoPay: `ana.mora / Ana2026!` · `luis.vega / Luis2026!` · `admin / Admin2026!`

## Comandos de todos los días

| Necesito… | Comando |
|---|---|
| Levantar CenfoPay | `bash scripts/levantar.sh` (luego pestaña **PUERTOS** → 8000 → 🌐) |
| Apagar el laboratorio | `bash scripts/apagar.sh` (`bash scripts/apagar.sh borrar` para empezar de cero) |
| Correr las pruebas | `bash scripts/probar.sh` · `bash scripts/probar.sh seguridad` |
| Fijar el límite de tolerancia (semana 1) | `bash scripts/tolerancia.sh <ERROR> <Medium>` |
| Probar que la compuerta bloquea (semana 1) | `bash scripts/prueba-compuerta.sh` · luego `… borrar` |
| Foto de la seguridad (todas las herramientas) | `bash scripts/foto.sh antes` · `bash scripts/foto.sh despues` |
| Comparar antes y después | `bash scripts/comparar.sh` → `docs/comparativo.md` |
| Fijar la imagen base por digest (semanas 2 y 3) | `bash scripts/fijar-digest.sh` |
| Verificar el endurecimiento (semana 2) | `bash scripts/verificar-endurecimiento.sh cenfopay:local cenfopay-app-1` |
| Probar las reglas propias (semana 3) | `bash scripts/probar-reglas.sh` |
| Vault, rotar y revocar (semana 4) | `bash scripts/vault-configurar.sh` · `bash scripts/rotar-secreto.sh` · `bash scripts/revocar-accesos.sh` |
| Registrar hallazgos ya atendidos (semana 4) | `bash scripts/registrar-huellas.sh` |

## Estructura

```
.devcontainer/           Configuración del codespace (Docker, Python y herramientas del curso)
.github/workflows/       El pipeline (uno solo para todo el curso; no lo editas)
proyecto.yml             En qué semana vas (lo cambia scripts/semana.sh)
app/                     Código de CenfoPay (Flask), Dockerfile y pruebas
correcciones/            Archivos corregidos de las semanas 2, 3 y 4 (los aplica semana.sh)
db/                      Base de datos con datos ficticios
docker-compose.yml       Laboratorio: base de datos, app, ZAP y Vault
compose.endurecido.yml   Semana 2: el contenedor con menos permisos
compose.secretos.yml     Semana 4: contraseñas como archivos (/run/secrets)
compose.vault.yml        Semana 4: contraseñas desde HashiCorp Vault
security/                Política de umbrales y reglas de las herramientas (versiones fijas)
tools/                   Compuerta, comparativo y el asistente de semanas
scripts/                 Los comandos del curso (cada uno explica qué hace al inicio)
docs/                    Plantillas que completas para tu informe final
reportes/                Resultados de los escaneos (no se suben a GitHub)
```
