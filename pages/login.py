import streamlit as st
from src.styles import BASE_CSS

st.set_page_config(page_title="The Data Machine · Login", layout="centered")
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
        st.session_state["username"] = username
        st.switch_page("pages/homepage.py")
    else:
        st.warning("Completa ambos campos.")
