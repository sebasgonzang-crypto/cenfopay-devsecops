"""Pruebas funcionales: deben pasar SIEMPRE (antes y después de corregir)."""


def test_salud(cliente):
    respuesta = cliente.get("/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["estado"] == "ok"


def test_inicio(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert b"CenfoPay" in respuesta.data


def test_saludo(cliente):
    respuesta = cliente.get("/saludo", query_string={"nombre": "Ana"})
    assert respuesta.status_code == 200
    assert b"Ana" in respuesta.data


def test_login_correcto(cliente):
    respuesta = cliente.post("/api/login", json={"usuario": "ana.mora", "password": "Ana2026!"})
    assert respuesta.status_code == 200
    assert respuesta.get_json()["usuario"] == "ana.mora"


def test_login_incorrecto(cliente):
    respuesta = cliente.post("/api/login", json={"usuario": "ana.mora", "password": "otra"})
    assert respuesta.status_code == 401


def test_movimientos_filtrados_por_fecha(cliente):
    respuesta = cliente.get("/api/cuentas/1/movimientos", query_string={"desde": "2026-01-10"})
    assert respuesta.status_code == 200
    assert len(respuesta.get_json()["movimientos"]) == 2


def test_resolver_host_valido(cliente):
    respuesta = cliente.get("/api/diagnostico/resolver", query_string={"host": "localhost"})
    assert respuesta.status_code == 200
    assert respuesta.get_json()["host"] == "localhost"


def test_importar_lote_valido(cliente):
    lote = "- {origen: 1, destino: 2, monto: 1000}\n- {origen: 1, destino: 3, monto: 2500}\n"
    respuesta = cliente.post("/api/transferencias/importar", data=lote)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["transferencias_recibidas"] == 2


def test_reporte_publico(cliente):
    respuesta = cliente.get("/api/reportes", query_string={"archivo": "resumen.txt"})
    assert respuesta.status_code == 200
    assert "Resumen" in respuesta.get_json()["contenido"]
