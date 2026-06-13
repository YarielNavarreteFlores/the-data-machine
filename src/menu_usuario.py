from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import streamlit as st

from src.navigation import (
    cerrar_sesion,
    inicializar_sesion,
)


# ==========================================================
# FUNCIONES PURAS PARA DATOS DE SESIÓN
# ==========================================================

def obtener_nombre_usuario(
    estado: MutableMapping[str, Any] | None = None,
) -> str:
    """
    Obtiene el nombre visible de la sesión.

    Retorna "usuario" cuando la cadena está vacía para evitar
    encabezados sin contenido dentro de la barra lateral.
    """
    sesion = inicializar_sesion(estado)

    nombre = str(
        sesion.get("username")
        or ""
    ).strip()

    return nombre or "usuario"


def hay_juego_seleccionado(
    estado: MutableMapping[str, Any] | None = None,
) -> bool:
    """
    Indica si existe un appid válido dentro de la sesión.
    """
    sesion = inicializar_sesion(estado)

    try:
        return int(
            sesion.get("selected_appid")
        ) > 0

    except (
        TypeError,
        ValueError,
    ):
        return False


def obtener_nombre_juego(
    estado: MutableMapping[str, Any] | None = None,
) -> str:
    """
    Obtiene el nombre del videojuego seleccionado.

    Si todavía no existe nombre, se muestra una etiqueta
    genérica sin inventar información.
    """
    sesion = inicializar_sesion(estado)

    nombre = str(
        sesion.get("selected_game")
        or ""
    ).strip()

    return nombre or "Juego seleccionado"


# ==========================================================
# MENÚ LATERAL AUTENTICADO
# ==========================================================

def renderizar_menu_usuario(
    pagina_actual: str,
) -> None:
    """
    Renderiza la navegación lateral limpia de la aplicación.

    La navegación técnica automática de Streamlit se oculta
    mediante .streamlit/config.toml. Este menú muestra solo:

    - Usuario autenticado.
    - Acceso al catálogo.
    - Acceso al análisis actual, cuando existe selección.
    - Botón de cierre de sesión.

    Args:
        pagina_actual:
            Identificador utilizado para que la llave del botón
            de logout sea única en cada página.
    """
    sesion = inicializar_sesion()
    usuario = obtener_nombre_usuario(sesion)

    with st.sidebar:
        st.markdown("## ◈ THE DATA MACHINE")
        st.caption(
            f"Sesión activa: **{usuario}**"
        )

        st.divider()

        st.page_link(
            "pages/homepage.py",
            label="Catálogo",
            icon="🎮",
            use_container_width=True,
        )

        if hay_juego_seleccionado(sesion):
            nombre_juego = obtener_nombre_juego(
                sesion
            )

            st.page_link(
                "pages/analisis.py",
                label=f"Análisis: {nombre_juego}",
                icon="📊",
                use_container_width=True,
            )

        st.divider()

        if st.button(
            "Cerrar sesión",
            key=f"cerrar_sesion_{pagina_actual}",
            use_container_width=True,
            type="secondary",
        ):
            # Elimina autenticación y selección del videojuego.
            cerrar_sesion()

            # Evita conservar parámetros de consulta antiguos.
            st.query_params.clear()

            # Regresa al formulario de acceso.
            st.switch_page(
                "pages/login.py"
            )
