from __future__ import annotations

import json
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any


# ==========================================================
# ALMACENAMIENTO DE USUARIOS
# ==========================================================
#
# Las cuentas se guardan en un JSON local con la forma:
#
#     {
#         "ana": {"display": "Ana", "password": "1234"}
#     }
#
# La clave es el nombre normalizado (minúsculas, sin espacios)
# para evitar duplicados como "Ana" y "ana". El campo display
# conserva el nombre tal como se escribió y es lo que se muestra
# en la interfaz.
#
# IMPORTANTE: las contraseñas se guardan en TEXTO PLANO por
# decisión explícita para la demo escolar. La comparación de
# contraseña está aislada en registrar_usuario y
# verificar_credenciales: migrar a hash (PBKDF2) en el futuro
# solo requiere cambiar esas dos funciones.

RUTA_USUARIOS = Path("data/auth/usuarios.json")


def clave_usuario(nombre: Any) -> str:
    """Normaliza un nombre a su clave interna (minúsculas, sin espacios)."""
    return str(nombre or "").strip().lower()


def cargar_usuarios(ruta: Path = RUTA_USUARIOS) -> dict[str, dict[str, str]]:
    """
    Lee el archivo de usuarios y lo devuelve como diccionario.

    Retorna un diccionario vacío cuando el archivo no existe o
    está corrupto, sin lanzar excepciones, para que la página de
    login funcione incluso en una instalación nueva.
    """
    ruta = Path(ruta)

    if not ruta.exists():
        return {}

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}

    return datos if isinstance(datos, dict) else {}


def guardar_usuarios(
    usuarios: MutableMapping[str, dict[str, str]],
    ruta: Path = RUTA_USUARIOS,
) -> None:
    """
    Escribe el diccionario de usuarios en disco.

    Crea el directorio padre si todavía no existe.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    ruta.write_text(
        json.dumps(dict(usuarios), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def usuario_existe(
    nombre: Any,
    usuarios: MutableMapping[str, dict[str, str]],
) -> bool:
    """Indica si ya existe una cuenta con ese nombre (sin distinguir mayúsculas)."""
    return clave_usuario(nombre) in usuarios


def registrar_usuario(
    nombre: Any,
    password: Any,
    usuarios: MutableMapping[str, dict[str, str]],
) -> tuple[bool, str]:
    """
    Registra una cuenta nueva dentro del diccionario recibido.

    Valida que el nombre y la contraseña no estén vacíos y que la
    cuenta no exista ya. Muta el diccionario en memoria; el llamador
    es responsable de persistirlo con guardar_usuarios().

    Retorna (exito, mensaje). Cuando exito es False, mensaje explica
    el motivo del rechazo.
    """
    nombre_limpio = str(nombre or "").strip()
    password_texto = str(password or "")

    if not nombre_limpio:
        return False, "Escribe un nombre de usuario."

    if not password_texto:
        return False, "Escribe una contraseña."

    if usuario_existe(nombre_limpio, usuarios):
        return False, "Ese usuario ya existe. Elige otro nombre."

    usuarios[clave_usuario(nombre_limpio)] = {
        "display": nombre_limpio,
        "password": password_texto,
    }

    return True, "Cuenta creada correctamente."


def verificar_credenciales(
    nombre: Any,
    password: Any,
    usuarios: MutableMapping[str, dict[str, str]],
) -> bool:
    """
    Comprueba si el nombre y la contraseña coinciden con una cuenta.

    Retorna False cuando el usuario no existe o la contraseña no
    coincide.
    """
    cuenta = usuarios.get(clave_usuario(nombre))

    if not isinstance(cuenta, dict):
        return False

    return cuenta.get("password") == str(password or "")


def nombre_para_mostrar(
    nombre: Any,
    usuarios: MutableMapping[str, dict[str, str]],
) -> str:
    """
    Devuelve el nombre visible (display) almacenado para la cuenta.

    Si la cuenta no se encuentra, retorna el nombre tal como se
    recibió, sin espacios sobrantes.
    """
    cuenta = usuarios.get(clave_usuario(nombre))

    if isinstance(cuenta, dict):
        display = str(cuenta.get("display") or "").strip()
        if display:
            return display

    return str(nombre or "").strip()
