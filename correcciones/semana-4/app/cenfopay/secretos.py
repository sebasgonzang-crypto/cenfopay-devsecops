"""Obtención segura de secretos en tiempo de ejecución (semana 4).

Proveedores disponibles (variable SECRETS_PROVIDER):
  entorno -> lee NOMBRE o, preferiblemente, NOMBRE_FILE (archivo montado en
             tmpfs, por ejemplo Docker secrets). Es el modo por defecto.
  vault   -> se autentica en HashiCorp Vault con AppRole y obtiene:
               * SECRET_KEY desde el motor KV v2 (secret/cenfopay/<entorno>)
               * credenciales de PostgreSQL desde el motor de base de datos
                 (rol estático rotado por Vault o rol dinámico con TTL).

Reglas: los valores de los secretos nunca se registran; se guardan solo en
memoria; y ante un fallo de autenticación se pueden volver a pedir (rotación
sin reiniciar la aplicación).
"""
import logging
import os
import threading

log = logging.getLogger("cenfopay.secretos")


def _leer_archivo(ruta):
    with open(ruta, encoding="utf-8") as manejador:
        return manejador.read().strip()


class ProveedorEntorno:
    nombre = "entorno"

    def obtener(self, clave):
        ruta = os.getenv(f"{clave}_FILE")
        if ruta:
            return _leer_archivo(ruta)
        return os.getenv(clave)

    def credenciales_db(self, forzar=False):
        return self.obtener("DB_USER") or "cenfopay_app", self.obtener("DB_PASSWORD")


class ProveedorVault:
    nombre = "vault"

    def __init__(self):
        import hvac  # importación diferida: solo se necesita en este modo

        self._hvac = hvac
        self._bloqueo = threading.Lock()
        self._cliente = None
        self._kv = None
        self._credenciales = None
        self.entorno = os.getenv("APP_ENTORNO", "dev")
        self.rol_db = os.getenv("VAULT_DB_ROLE", "cenfopay-app-estatico")
        self.tipo_rol = os.getenv("VAULT_DB_ROLE_TYPE", "static")  # static | dynamic

    def _autenticar(self):
        cliente = self._hvac.Client(url=os.environ["VAULT_ADDR"])
        cliente.auth.approle.login(
            role_id=_leer_archivo(os.environ["VAULT_ROLE_ID_FILE"]),
            secret_id=_leer_archivo(os.environ["VAULT_SECRET_ID_FILE"]),
        )
        log.info("Autenticado en Vault con AppRole (entorno=%s)", self.entorno)
        self._cliente = cliente

    def _cliente_valido(self):
        if self._cliente is None or not self._cliente.is_authenticated():
            self._autenticar()
        return self._cliente

    def obtener(self, clave):
        with self._bloqueo:
            if self._kv is None:
                respuesta = self._cliente_valido().secrets.kv.v2.read_secret_version(
                    path=f"cenfopay/{self.entorno}",
                    mount_point="secret",
                    raise_on_deleted_version=True,
                )
                self._kv = respuesta["data"]["data"]
            return self._kv.get(clave)

    def credenciales_db(self, forzar=False):
        with self._bloqueo:
            if forzar or self._credenciales is None:
                motor = self._cliente_valido().secrets.database
                if self.tipo_rol == "dynamic":
                    datos = motor.generate_credentials(name=self.rol_db)["data"]
                else:
                    datos = motor.get_static_credentials(name=self.rol_db)["data"]
                self._credenciales = (datos["username"], datos["password"])
                log.info(
                    "Credenciales de BD obtenidas de Vault (rol=%s, usuario=%s)",
                    self.rol_db,
                    datos["username"],
                )
            return self._credenciales


def crear_proveedor():
    modo = os.getenv("SECRETS_PROVIDER", "entorno").lower()
    if modo == "vault":
        return ProveedorVault()
    return ProveedorEntorno()
