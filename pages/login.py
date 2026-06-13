import streamlit as st

from src.navigation import inicializar_sesion
from src.styles import BASE_CSS

st.set_page_config(page_title="The Data Machine · Login", layout="centered")
# Garantiza que existan todas las claves necesarias.
sesion = inicializar_sesion()

# Si la sesión ya está iniciada, no se vuelve a mostrar
# el formulario de acceso.
if bool(sesion["authenticated"]):
    destino = (
        "pages/analisis.py"
        if sesion.get("selected_appid") is not None
        else "pages/homepage.py"
    )

    st.switch_page(destino)
st.markdown(BASE_CSS, unsafe_allow_html=True)

st.markdown("""
<div class="tdm-page" style="padding:2rem;text-align:center;">
  <div class="tdm-logo" style="font-size:24px;margin-bottom:0.5rem;">⬡ THE DATA MACHINE</div>
  <div class="tdm-section-sub" style="margin-bottom:1.5rem;">Inicia sesión para acceder al catálogo</div>
</div>
""", unsafe_allow_html=True)

username = st.text_input("Usuario", placeholder="tu nombre")
password = st.text_input("Contraseña", type="password", placeholder="••••••")

if st.button("⟡ Entrar"):
    if username and password:
        st.session_state["authenticated"] = True
        st.session_state["username"] = username.strip()

        # Si la persona abrió un enlace con ?appid= antes
        # de iniciar sesión, se respeta esa selección.
        destino = (
            "pages/analisis.py"
            if st.session_state.get(
                "selected_appid"
            ) is not None
            else "pages/homepage.py"
        )

        st.switch_page(destino)

    else:
        st.warning(
            "Completa ambos campos."
        )
