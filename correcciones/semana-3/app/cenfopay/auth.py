"""Hash y verificación de contraseñas (CWE-916 corregido)."""
import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

_MD5_LEGADO = re.compile(r"[0-9a-f]{32}")


def generar_hash(password):
    """Hash robusto con sal (scrypt en Werkzeug 3)."""
    return generate_password_hash(password)


def es_hash_legado(password_hash):
    return bool(_MD5_LEGADO.fullmatch(password_hash))


def verificar(password, password_hash):
    """Verifica la contraseña. Acepta hashes MD5 heredados SOLO para migrarlos.

    Riesgo residual documentado: mientras existan cuentas con hash MD5, su
    verificación usa MD5. El login reemplaza el hash por uno robusto en el
    primer acceso exitoso (rehash-on-login).
    """
    if es_hash_legado(password_hash):
        # Excepción revisada (semana 3): MD5 solo se usa para verificar y migrar hashes heredados.
        # nosemgrep: insecure-hash-algorithm-md5, md5-used-as-password
        calculado = hashlib.md5(password.encode()).hexdigest()  # nosec B324
        return hmac.compare_digest(calculado, password_hash)
    return check_password_hash(password_hash, password)
