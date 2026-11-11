-- Esquema y datos FICTICIOS de CenfoPay para PostgreSQL.
-- Lo ejecuta db/init/01-esquema.sh una sola vez, cuando el volumen de datos está vacío.
-- Las contraseñas llegan como variables de psql (:'app_pw', :'vault_pw') desde el .env:
-- no quedan escritas en el repositorio.

-- Usuario con el que se conecta la aplicación (mínimo privilegio: solo DML).
CREATE ROLE cenfopay_app LOGIN PASSWORD :'app_pw';

-- Usuario administrativo que usará HashiCorp Vault en el Módulo 4 para rotar
-- la contraseña de cenfopay_app y crear credenciales dinámicas.
CREATE ROLE vault_admin LOGIN CREATEROLE PASSWORD :'vault_pw';
GRANT cenfopay_app TO vault_admin WITH ADMIN OPTION;

CREATE TABLE usuarios (
    id            INTEGER PRIMARY KEY,
    usuario       TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol           TEXT NOT NULL
);

CREATE TABLE cuentas (
    id         INTEGER PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    numero     TEXT NOT NULL,
    saldo      NUMERIC(14,2) NOT NULL
);

CREATE TABLE movimientos (
    id          INTEGER PRIMARY KEY,
    cuenta_id   INTEGER NOT NULL REFERENCES cuentas(id),
    fecha       DATE NOT NULL,
    descripcion TEXT NOT NULL,
    monto       NUMERIC(14,2) NOT NULL
);

INSERT INTO usuarios VALUES
  (1, 'ana.mora',  'e820f35786bd60d3a1e30ecb4331ae53', 'cliente'),
  (2, 'luis.vega', '342ad7a12246c84b597f7b5f483cb9d9', 'cliente'),
  (3, 'admin',     '7da80690c8a437586fe8c8763f44ce92', 'administrador');

INSERT INTO cuentas VALUES
  (1, 1, 'CR00-0000-0000-0000-0001', 1250000.00),
  (2, 2, 'CR00-0000-0000-0000-0002',  380500.50),
  (3, 3, 'CR00-0000-0000-0000-0003',       0.00);

INSERT INTO movimientos VALUES
  (1, 1, '2026-01-05', 'Depósito de planilla',    950000.00),
  (2, 1, '2026-01-12', 'Pago de servicios',       -45300.00),
  (3, 1, '2026-02-01', 'Transferencia recibida',  120000.00),
  (4, 2, '2026-01-08', 'Depósito de planilla',    610000.00),
  (5, 2, '2026-01-20', 'Compra en comercio',      -85250.00),
  (6, 2, '2026-02-03', 'Pago de tarjeta',        -144249.50);

-- Privilegios mínimos para la aplicación.
GRANT CONNECT ON DATABASE cenfopay TO cenfopay_app;
GRANT USAGE ON SCHEMA public TO cenfopay_app;
GRANT SELECT, INSERT, UPDATE ON usuarios, cuentas, movimientos TO cenfopay_app;

-- Vault necesita poder otorgar esos mismos privilegios a las credenciales dinámicas.
GRANT CONNECT ON DATABASE cenfopay TO vault_admin WITH GRANT OPTION;
GRANT USAGE ON SCHEMA public TO vault_admin WITH GRANT OPTION;
GRANT SELECT, INSERT, UPDATE ON usuarios, cuentas, movimientos TO vault_admin WITH GRANT OPTION;
