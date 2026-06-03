import streamlit as st

# Debug temporal — quitar antes de entregar
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = True
    st.session_state["username"] = "Sandra"

# Navegación por click en tarjeta (vía ?game=...)
game = st.query_params.get("game")
if game:
    st.session_state["selected_game"] = game
    st.switch_page("pages/analisis.py")

st.switch_page("pages/homepage.py")
