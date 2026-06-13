from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any, Iterable

import streamlit as st


# ==========================================================
# VALORES PREDETERMINADOS DE LA SESIÓN
# ==========================================================

VALORES_SESION = {
    "authenticated": False,
    "username": "",
    "selected_appid": None,
    "selected_game": None,
}


def _obtener_estado(
    estado: MutableMapping[str, Any] | None = None,
) -> MutableMapping[str, Any]:
    """
    Retorna el estado recibido o st.session_state.

    El parámetro opcional permite probar la lógica con un
    diccionario normal, sin levantar un servidor Streamlit.
    """
    return st.session_state if estado is None else estado


def inicializar_sesion(
    estado: MutableMapping[str, Any] | None = None,
) -> MutableMapping[str, Any]:
    """
    Crea únicamente las claves de sesión que todavía no existan.

    No sobrescribe una sesión ya autenticada ni una selección
    de videojuego realizada previamente.
    """
    sesion = _obtener_estado(estado)

    for clave, valor in VALORES_SESION.items():
        sesion.setdefault(clave, valor)

    return sesion


def normalizar_parametro_consulta(valor: Any) -> str | None:
    """
    Normaliza un valor obtenido desde st.query_params.

    Streamlit normalmente devuelve texto, pero esta función
    también soporta listas o tuplas para evitar errores.
    """
    if valor is None:
        return None

    if isinstance(valor, (list, tuple)):
        if not valor:
            return None
        valor = valor[-1]

    texto = str(valor).strip()

    return texto or None


def convertir_appid(valor: Any) -> int | None:
    """
    Convierte un parámetro a appid entero positivo.

    Retorna None cuando el valor no representa un appid válido.
    """
    texto = normalizar_parametro_consulta(valor)

    if texto is None:
        return None

    try:
        appid = int(texto)
    except (TypeError, ValueError):
        return None

    return appid if appid > 0 else None


def establecer_juego(
    appid: int,
    nombre: str | None = None,
    estado: MutableMapping[str, Any] | None = None,
) -> None:
    """
    Guarda el videojuego seleccionado en la sesión.

    appid es la llave principal. selected_game se conserva
    temporalmente para mantener compatibilidad con la homepage.
    """
    appid_normalizado = convertir_appid(appid)

    if appid_normalizado is None:
        raise ValueError("El appid debe ser un entero positivo.")

    sesion = inicializar_sesion(estado)
    sesion["selected_appid"] = appid_normalizado

    if nombre is not None:
        sesion["selected_game"] = str(nombre).strip() or None


def limpiar_seleccion(
    estado: MutableMapping[str, Any] | None = None,
) -> None:
    """Elimina únicamente la selección actual de videojuego."""
    sesion = inicializar_sesion(estado)
    sesion["selected_appid"] = None
    sesion["selected_game"] = None


def cerrar_sesion(
    estado: MutableMapping[str, Any] | None = None,
) -> None:
    """
    Cierra la sesión y elimina la selección del videojuego.

    Se conserva la estructura de claves para evitar KeyError.
    """
    sesion = inicializar_sesion(estado)
    sesion["authenticated"] = False
    sesion["username"] = ""
    sesion["selected_appid"] = None
    sesion["selected_game"] = None


def requerir_autenticacion(
    pagina_login: str = "pages/login.py",
) -> None:
    """
    Redirige al login cuando la sesión no está autenticada.

    Debe llamarse después de st.set_page_config().
    """
    sesion = inicializar_sesion()

    if not bool(sesion["authenticated"]):
        st.switch_page(pagina_login)
        st.stop()


def consumir_appid_query(
    appids_validos: Iterable[int] | None = None,
    limpiar_url: bool = True,
) -> int | None:
    """
    Lee ?appid=... desde la URL y lo guarda en sesión.

    Si se proporciona appids_validos, se rechazan identificadores
    que no pertenezcan al catálogo oficial.
    """
    appid = convertir_appid(st.query_params.get("appid"))

    if appid is None:
        return None

    if appids_validos is not None:
        permitidos = {int(valor) for valor in appids_validos}

        if appid not in permitidos:
            if limpiar_url:
                st.query_params.clear()
            return None

    establecer_juego(appid)

    if limpiar_url:
        st.query_params.clear()

    return appid
