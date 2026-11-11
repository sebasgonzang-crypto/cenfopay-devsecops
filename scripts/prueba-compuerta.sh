#!/usr/bin/env bash
# Semana 1 · Demuestra que la compuerta detiene un cambio inseguro.
# Uso: bash scripts/prueba-compuerta.sh          -> crea la rama con una página insegura y la sube
#      bash scripts/prueba-compuerta.sh borrar   -> limpia (vuelve a main y borra la rama)
source "$(dirname "$0")/_comun.sh"
rama="prueba-compuerta"
if [[ "${1:-}" == "borrar" ]]; then
  git checkout -q main
  git branch -D "$rama" >/dev/null 2>&1 || true
  git push -q origin --delete "$rama" >/dev/null 2>&1 || true
  ok "Rama de prueba borrada. Estás de nuevo en main."
  exit 0
fi
[[ -z "$(git status --porcelain)" ]] || falla "Tienes cambios sin guardar. Haz commit (o descártalos) antes de la prueba."
git checkout -q main && git pull -q --ff-only origin main
git checkout -q -b "$rama"
python3 - <<'PY'
from pathlib import Path
ruta = Path("app/cenfopay/__init__.py")
texto = ruta.read_text(encoding="utf-8")
nuevo = '''    @app.get("/api/diagnostico/ping")
    def ping():
        destino = request.args.get("destino", "localhost")
        # Página insegura agregada A PROPÓSITO para probar la compuerta (no la fusiones)
        salida = subprocess.check_output(f"ping -c 1 {destino}", shell=True, text=True)
        return jsonify(resultado=salida)

    return app'''
i = texto.rindex("    return app")
ruta.write_text(texto[:i] + nuevo + texto[i + len("    return app"):], encoding="utf-8")
PY
git commit -q -am "Prueba: nueva página de diagnóstico (insegura a propósito)"
git push -q -u origin "$rama"
ok "Rama «$rama» subida con una página insegura (inyección de comandos)."
info "Ahora en GitHub: botón amarillo «Compare & pull request» → «Create pull request»."
info "Al terminar la prueba:  bash scripts/prueba-compuerta.sh borrar"
