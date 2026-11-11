"""Punto de entrada de CenfoPay (línea base vulnerable)."""
from cenfopay import create_app

app = create_app()

if __name__ == "__main__":
    # VULN (CWE-489 / CWE-1188): servidor de desarrollo con depurador activo
    # y expuesto en todas las interfaces.
    app.run(host="0.0.0.0", port=8000, debug=True)
