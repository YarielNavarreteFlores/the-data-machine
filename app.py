from __future__ import annotations

import streamlit as st

from src.navigation import (
    consumir_appid_query,
    inicializar_sesion,
)


# ==========================================================
# PUNTO DE ENTRADA DE THE DATA MACHINE
# ==========================================================

# app.py funciona únicamente como enrutador.
# Las páginas mantienen su propio diseño y configuración.
sesion = inicializar_sesion()

# Permite abrir un enlace como:
# http://localhost:8501/?appid=570
#
# Si el usuario ya inició sesión, se abre directamente el
# dashboard. Si no, el appid queda guardado y se solicita login.
appid_url = consumir_appid_query(
    appids_validos=None,
    limpiar_url=True,
)

if bool(sesion["authenticated"]):
    if appid_url is not None:
        st.switch_page("pages/analisis.py")

    st.switch_page("pages/homepage.py")

# Se eliminó el bypass de depuración que autenticaba
# automáticamente como "Sandra".
st.switch_page("pages/login.py")
