"""Datos de prueba FICTICIOS para CenfoPay.

Ningún dato corresponde a personas, cuentas o entidades reales. Las
contraseñas de los usuarios de prueba están documentadas en el README del kit.
Los hashes MD5 son intencionalmente débiles (línea base vulnerable).
"""

USUARIOS = [
    # (id, usuario, hash de contraseña, rol)
    (1, "ana.mora", "e820f35786bd60d3a1e30ecb4331ae53", "cliente"),
    (2, "luis.vega", "342ad7a12246c84b597f7b5f483cb9d9", "cliente"),
    (3, "admin", "7da80690c8a437586fe8c8763f44ce92", "administrador"),
]

CUENTAS = [
    # (id, usuario_id, número de cuenta ficticio, saldo)
    (1, 1, "CR00-0000-0000-0000-0001", 1250000.00),
    (2, 2, "CR00-0000-0000-0000-0002", 380500.50),
    (3, 3, "CR00-0000-0000-0000-0003", 0.00),
]

MOVIMIENTOS = [
    # (id, cuenta_id, fecha, descripción, monto)
    (1, 1, "2026-01-05", "Depósito de planilla", 950000.00),
    (2, 1, "2026-01-12", "Pago de servicios", -45300.00),
    (3, 1, "2026-02-01", "Transferencia recibida", 120000.00),
    (4, 2, "2026-01-08", "Depósito de planilla", 610000.00),
    (5, 2, "2026-01-20", "Compra en comercio", -85250.00),
    (6, 2, "2026-02-03", "Pago de tarjeta", -144249.50),
]

ESQUEMA_SQLITE = [
    """CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        usuario TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY,
        usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
        numero TEXT NOT NULL,
        saldo REAL NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY,
        cuenta_id INTEGER NOT NULL REFERENCES cuentas(id),
        fecha TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        monto REAL NOT NULL)""",
]
