import streamlit as st
from src.styles import BASE_CSS

st.set_page_config(page_title="The Data Machine · An\u00e1lisis", layout="wide")
st.markdown(BASE_CSS, unsafe_allow_html=True)

game = st.session_state.get("selected_game", "Desconocido")

st.markdown(f"""
<div class="tdm-page">
  <div class="tdm-topbar">
    <div class="tdm-logo">\u2b61 THE DATA MACHINE</div>
    <div class="tdm-actions">
      <span class="tdm-user">\u25c6 {st.session_state.get("username", "usuario")}</span>
    </div>
  </div>
  <div class="tdm-section-title">\u25b8 {game}</div>
  <div class="tdm-section-sub">An\u00e1lisis de rese\u00f1as — en construcci\u00f3n.</div>
</div>
""", unsafe_allow_html=True)
