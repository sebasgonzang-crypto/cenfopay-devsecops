#!/usr/bin/env python3
"""Avanza el proyecto CenfoPay de semana y aplica los cambios preparados.

Lo usan los scripts:
  bash scripts/semana.sh <1-4>                  -> activa una semana
  bash scripts/tolerancia.sh <ERROR> <Medium>   -> fija el límite de tolerancia (semana 1)

Qué hace «semana N»:
  1. Escribe la semana en proyecto.yml (el pipeline enciende las etapas de esa semana).
  2. Copia las correcciones listas de correcciones/semana-N/ (semanas 2, 3 y 4).
  3. Actualiza security/politica-umbrales.yml con las reglas de esa semana.
  4. Muestra qué archivos cambiaron y qué hacer después.
Nada se sube a GitHub: eso lo haces tú con git (así queda en tu historial).
"""
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
POLITICA = RAIZ / "security/politica-umbrales.yml"
PROYECTO = RAIZ / "proyecto.yml"
REGLAS = RAIZ / "security/semgrep/reglas-cenfopay.yml"
EJEMPLOS = RAIZ / "security/semgrep/reglas-cenfopay.py"

AZUL, VERDE, AMARILLO, ROJO, FIN = "\033[1;34m", "\033[1;32m", "\033[1;33m", "\033[1;31m", "\033[0m"


def info(t): print(f"{AZUL}[i]{FIN} {t}")
def ok(t): print(f"{VERDE}[✓]{FIN} {t}")
def alerta(t): print(f"{AMARILLO}[!]{FIN} {t}")


def falla(t):
    print(f"{ROJO}[x]{FIN} {t}", file=sys.stderr)
    sys.exit(1)


# ------------------------------------------------------------------ proyecto.yml
def semana_actual():
    if not PROYECTO.exists():
        return 0
    m = re.search(r"^semana:\s*(\d)", PROYECTO.read_text(encoding="utf-8"), re.M)
    return int(m.group(1)) if m else 0


def escribir_semana(n):
    texto = PROYECTO.read_text(encoding="utf-8")
    nuevo, cambios = re.subn(r"^semana:\s*\d+.*$", f"semana: {n}", texto, count=1, flags=re.M)
    if not cambios:
        falla("proyecto.yml no tiene la línea «semana: N». Recupéralo con: git checkout -- proyecto.yml")
    PROYECTO.write_text(nuevo, encoding="utf-8")
    ok(f"proyecto.yml → semana: {n} (el pipeline encenderá las etapas de la semana {n})")


# ------------------------------------------------------------------ política
def leer_politica():
    return POLITICA.read_text(encoding="utf-8")


def guardar_politica(texto):
    POLITICA.write_text(texto, encoding="utf-8")


def activar_bloque(texto, herramienta):
    """Quita el comentario («# ») del bloque de una herramienta. Si ya está activo, no hace nada."""
    if re.search(rf"^  {re.escape(herramienta)}:", texto, re.M):
        return texto, False
    lineas = texto.split("\n")
    for i, linea in enumerate(lineas):
        if re.match(rf"^  # {re.escape(herramienta)}:", linea):
            lineas[i] = "  " + linea[4:]
            j = i + 1
            while j < len(lineas) and lineas[j].startswith("  #   "):
                lineas[j] = "    " + lineas[j][6:]
                j += 1
            return "\n".join(lineas), True
    falla(f"No encontré el bloque «{herramienta}» en security/politica-umbrales.yml. "
          "Recupera el archivo original con: git checkout -- security/politica-umbrales.yml")


def fijar_valor(texto, herramienta, clave, valor, comentario=""):
    """Cambia «clave: N» dentro del bloque de una herramienta activa."""
    patron = re.compile(rf"(^  {re.escape(herramienta)}:.*?\n(?:    .*\n)*?      {re.escape(clave)}:)[^\n]*", re.M)
    nuevo, n = patron.subn(lambda m: f"{m.group(1)} {valor}" + (f"{comentario}" if comentario else ""), texto, count=1)
    if not n:
        falla(f"No encontré «{clave}» dentro de «{herramienta}» en la política.")
    return nuevo


def fijar_modo(texto, modo):
    nuevo, n = re.subn(r"^modo:.*$", f"modo: {modo}           # cambiado por scripts (ver historial de git)",
                       texto, count=1, flags=re.M)
    if not n:
        falla("No encontré la línea «modo:» en la política.")
    return nuevo


EXCEPCION_FP = """excepciones:
  - herramienta: semgrep
    id: useless-inner-function
    tipo: falso_positivo
    justificacion: >-
      Las funciones internas de create_app() son páginas de Flask registradas con
      @app.get/@app.post: el framework sí las usa. La regla no entiende esa forma de
      registrar páginas. Revisado en la semana 3.
    responsable: "Equipo CenfoPay"
    vence: 2027-06-30"""


def politica_semana(n):
    texto = leer_politica()
    cambios = []
    if n == 2:
        for h in ("hadolint", "trivy-config", "trivy-so", "trivy-dependencias", "endurecimiento"):
            texto, c = activar_bloque(texto, h)
            if c:
                cambios.append(f"se activó «{h}»")
    if n == 3:
        texto = fijar_modo(texto, "bloquear")
        texto = fijar_valor(texto, "semgrep", "ERROR", 0, "           # semana 3: código corregido → el límite de tolerancia baja a 0")
        texto, c = activar_bloque(texto, "bandit")
        if c:
            cambios.append("se activó «bandit» (HIGH: 0)")
        if re.search(r"^  trivy-dependencias:.*\n    solo_con_correccion: true\n    umbrales: \{\}", texto, re.M):
            texto = re.sub(r"(^  trivy-dependencias:.*\n    solo_con_correccion: true\n)    umbrales: \{\}",
                           r"\1    umbrales:              # semana 3: las librerías se actualizaron → ahora detiene\n"
                           r"      CRITICAL: 0\n      HIGH: 0", texto, count=1, flags=re.M)
            cambios.append("«trivy-dependencias» ahora detiene (CRITICAL: 0, HIGH: 0)")
        if "excepciones: []" in texto:
            texto = texto.replace("excepciones: []", EXCEPCION_FP, 1)
            cambios.append("se registró la falsa alarma «useless-inner-function» como excepción con vencimiento")
        cambios.append("semgrep ERROR: 0 y modo: bloquear")
    if n == 4:
        for h in ("gitleaks", "registros"):
            texto, c = activar_bloque(texto, h)
            if c:
                cambios.append(f"se activó «{h}»")
    guardar_politica(texto)
    for c in cambios:
        ok(f"Política: {c}")


# ------------------------------------------------------------------ correcciones
def copiar_correcciones(n):
    origen = RAIZ / f"correcciones/semana-{n}"
    if not origen.exists():
        return []
    copiados = []
    for archivo in sorted(p for p in origen.rglob("*") if p.is_file()):
        relativo = archivo.relative_to(origen)
        destino = RAIZ / relativo
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archivo, destino)
        copiados.append(str(relativo))
    for c in copiados:
        ok(f"Corrección aplicada: {c}")
    return copiados


def nosec_config():
    """Semana 3: marca la falsa alarma B108 de Bandit en config.py (sin tocar nada más)."""
    ruta = RAIZ / "app/cenfopay/config.py"
    texto = ruta.read_text(encoding="utf-8")
    if "# nosec B108" in texto:
        return
    viejo = '        "SQLITE_PATH": os.getenv("SQLITE_PATH", "/tmp/cenfopay.db"),\n'
    if viejo not in texto:
        alerta("No encontré la línea SQLITE_PATH en config.py: agrega «# nosec B108» a mano (ver la guía).")
        return
    texto = texto.replace(viejo,
        "        # Falso positivo revisado (Bandit B108): SQLite solo se usa en pruebas locales;\n"
        "        # en el contenedor DB_ENGINE=postgres y esta ruta nunca se abre.\n"
        '        "SQLITE_PATH": os.getenv("SQLITE_PATH", "/tmp/cenfopay.db"),  # nosec B108\n', 1)
    ruta.write_text(texto, encoding="utf-8")
    ok("Corrección aplicada: app/cenfopay/config.py (falsa alarma B108 anotada con su motivo)")


def refinar_regla_secretos():
    """Semana 4: «entorno» no es un secreto; la regla solo avisa si el valor tiene dígitos o símbolos."""
    texto = REGLAS.read_text(encoding="utf-8")
    if "(?=.*[0-9#!$%&@*])" not in texto:
        viejo = "              regex: ^.{6,}$"
        if viejo not in texto:
            alerta("No encontré la regla cenfopay-secreto-embebido original: revisa la guía (semana 4).")
            return
        texto = texto.replace(viejo,
            "              # Mejora de la semana 4: un secreto real mezcla letras con dígitos o\n"
            "              # símbolos; «entorno» o «vault» (nombres de modo) no son secretos.\n"
            "              regex: ^(?=.*[0-9#!$%&@*]).{6,}$", 1)
        REGLAS.write_text(texto, encoding="utf-8")
        ok("Regla cenfopay-secreto-embebido mejorada (ya no confunde «entorno» con una contraseña)")
    ejemplos = EJEMPLOS.read_text(encoding="utf-8")
    if "MODO_SECRETOS" not in ejemplos:
        ejemplos = ejemplos.rstrip("\n") + ('\n\n\n# ok: cenfopay-secreto-embebido\n'
                                            'MODO_SECRETOS = os.getenv("SECRETS_PROVIDER", "entorno")\n')
        EJEMPLOS.write_text(ejemplos, encoding="utf-8")
        ok("Ejemplo nuevo «ok:» agregado a security/semgrep/reglas-cenfopay.py")


def llave_en_env():
    """Semana 4: la app ya no trae SECRET_KEY en el código; se genera una al azar en .env."""
    env = RAIZ / ".env"
    if not env.exists():
        shutil.copyfile(RAIZ / ".env.example", env)
    texto = env.read_text(encoding="utf-8")
    m = re.search(r"^SECRET_KEY=(.*)$", texto, re.M)
    if m and m.group(1).strip():
        info("Tu .env ya tiene una SECRET_KEY: se conserva.")
        return
    llave = secrets.token_hex(32)
    if m:
        texto = texto[:m.start()] + f"SECRET_KEY={llave}" + texto[m.end():]
    else:
        texto = texto.rstrip("\n") + f"\nSECRET_KEY={llave}\n"
    env.write_text(texto, encoding="utf-8")
    ok(f"SECRET_KEY nueva generada al azar en .env ({llave[:3]}****). .env nunca se sube a GitHub.")


# ------------------------------------------------------------------ resumen
SIGUIENTE = {
    1: ["git add -A && git commit -m \"Semana 1: activar el pipeline\" && git push",
        "Mira la corrida en la pestaña Actions de tu repositorio (tarda 5-10 minutos).",
        "Mientras tanto:  bash scripts/levantar.sh   y   bash scripts/probar.sh"],
    2: ["bash scripts/fijar-digest.sh        (fija la imagen base por su «código de barras»)",
        "bash scripts/levantar.sh && bash scripts/verificar-endurecimiento.sh cenfopay:local cenfopay-app-1",
        "git add -A && git commit -m \"Semana 2: contenedor protegido\" && git push -u origin semana-2",
        "Abre el pull request en GitHub y espera la compuerta."],
    3: ["git diff --stat        (lista de archivos corregidos)",
        "bash scripts/fijar-digest.sh",
        "bash scripts/probar.sh seguridad     (deben pasar las 9 pruebas de seguridad)",
        "git add -A && git commit -m \"Semana 3: código corregido\" && git push -u origin semana-3"],
    4: ["bash scripts/levantar.sh    (ahora con las contraseñas como archivos)",
        "bash scripts/probar.sh       (deben pasar las 20 pruebas)",
        "Crea el environment «laboratorio» con sus 4 secretos en GitHub (guía, semana 4).",
        "git add -A && git commit -m \"Semana 4: secretos fuera del código\" && git push -u origin semana-4"],
}


def resumen(n):
    print()
    info("Archivos que cambiaron (compáralos con:  git diff):")
    subprocess.run(["git", "status", "--short"], cwd=RAIZ, check=False)
    print()
    info(f"Próximos pasos de la semana {n}:")
    for i, paso in enumerate(SIGUIENTE[n], 1):
        print(f"    {i}. {paso}")


def cmd_semana(n):
    if n not in (1, 2, 3, 4):
        falla("Uso: bash scripts/semana.sh <1|2|3|4>")
    actual = semana_actual()
    if n > actual + 1:
        falla(f"Vas en la semana {actual}. Primero activa la semana {actual + 1} (las semanas van en orden).")
    if n < actual:
        alerta(f"Ya estás en la semana {actual}. Volver a una semana anterior no deshace las correcciones.")
    info(f"Activando la semana {n} del proyecto…")
    escribir_semana(max(n, actual))
    copiar_correcciones(n)
    if n == 3:
        nosec_config()
    if n == 4:
        refinar_regla_secretos()
        llave_en_env()
    if n >= 2:
        politica_semana(n)
    resumen(n)


def cmd_tolerancia(error, medium):
    texto = leer_politica()
    texto = fijar_modo(texto, "bloquear")
    texto = fijar_valor(texto, "semgrep", "ERROR", error, "           # límite de tolerancia: hallazgos ERROR de hoy")
    texto = fijar_valor(texto, "zap", "Medium", medium, "         # límite de tolerancia: alertas Medium de hoy")
    guardar_politica(texto)
    ok(f"Política en modo «bloquear» con límite de tolerancia: semgrep ERROR ≤ {error} · zap Medium ≤ {medium} · zap High = 0")
    info("Revisa el cambio con:  git diff security/politica-umbrales.yml")
    info("Luego:  git add -A && git commit -m \"Semana 1: límite de tolerancia en modo bloquear\" && git push")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "semana" and len(sys.argv) == 3 and sys.argv[2].isdigit():
        cmd_semana(int(sys.argv[2]))
    elif len(sys.argv) == 4 and sys.argv[1] == "tolerancia" and sys.argv[2].isdigit() and sys.argv[3].isdigit():
        cmd_tolerancia(int(sys.argv[2]), int(sys.argv[3]))
    else:
        falla("Uso: semana.py semana <1-4>  |  semana.py tolerancia <ERROR> <Medium>")
