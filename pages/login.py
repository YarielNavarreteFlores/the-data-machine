import streamlit as st

from src.auth import (
    cargar_usuarios,
    guardar_usuarios,
    nombre_para_mostrar,
    registrar_usuario,
    verificar_credenciales,
)
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

# Vista actual del formulario: "login" o "registro".
st.session_state.setdefault("auth_vista", "login")

# Usuarios registrados (texto plano en data/auth/usuarios.json).
usuarios = cargar_usuarios()

st.markdown(BASE_CSS, unsafe_allow_html=True)

# Elimina la nebulosa que el homepage pudo dejar incrustada en el <body>, para
# que no quede congelada sobre la pantalla de login (p. ej. al cerrar sesión).
st.components.v1.html(
    """
    <script>
    (function () {
      try {
        var win = window.parent, doc = win.document;
        win.__tdmNebulaGen = (win.__tdmNebulaGen || 0) + 1;
        var nebula = doc.getElementById('tdm-nebula');
        if (nebula) { nebula.remove(); }
        if (win.__tdmNebulaResize) {
          win.removeEventListener('resize', win.__tdmNebulaResize);
          win.__tdmNebulaResize = null;
        }
      } catch (e) {}
    })();
    </script>
    """,
    height=0,
)


def _destino_tras_login() -> str:
    """Respeta una selección de juego previa (?appid=...)."""
    return (
        "pages/analisis.py"
        if st.session_state.get("selected_appid") is not None
        else "pages/homepage.py"
    )


def _iniciar_sesion(nombre_visible: str) -> None:
    """Marca la sesión como autenticada y entra a la app."""
    st.session_state["authenticated"] = True
    st.session_state["username"] = nombre_visible
    st.switch_page(_destino_tras_login())


# ==========================================================
# ENCABEZADO DE MARCA
# ==========================================================

if st.session_state["auth_vista"] == "registro":
    subtitulo = "Crea una cuenta para acceder al catálogo"
else:
    subtitulo = "Inicia sesión para acceder al catálogo"

st.markdown(f"""
<div class="tdm-page" style="padding:2rem;text-align:center;">
  <div class="tdm-logo" style="font-size:24px;margin-bottom:0.5rem;">⬡ THE DATA MACHINE</div>
  <div class="tdm-section-sub" style="margin-bottom:1.5rem;">{subtitulo}</div>
</div>
""", unsafe_allow_html=True)


# ==========================================================
# VISTA: INICIAR SESIÓN
# ==========================================================

if st.session_state["auth_vista"] == "login":
    username = st.text_input("Usuario", placeholder="tu nombre")
    password = st.text_input("Contraseña", type="password", placeholder="••••••")

    if st.button("⟡ Entrar", use_container_width=True):
        if not (username and password):
            st.warning("Completa ambos campos.")
        elif verificar_credenciales(username, password, usuarios):
            _iniciar_sesion(nombre_para_mostrar(username, usuarios))
        else:
            st.error("Usuario o contraseña incorrectos.")

    if st.button("¿No tienes cuenta? Crear una", type="tertiary", use_container_width=True):
        st.session_state["auth_vista"] = "registro"
        st.rerun()


# ==========================================================
# VISTA: CREAR CUENTA (REGISTRO)
# ==========================================================

else:
    nuevo_usuario = st.text_input("Usuario", placeholder="elige un nombre")
    nueva_password = st.text_input(
        "Contraseña", type="password", placeholder="••••••"
    )
    confirmar_password = st.text_input(
        "Confirmar contraseña", type="password", placeholder="••••••"
    )

    if st.button("⟡ Crear cuenta", use_container_width=True):
        if not (nuevo_usuario and nueva_password and confirmar_password):
            st.warning("Completa todos los campos.")
        elif nueva_password != confirmar_password:
            st.error("Las contraseñas no coinciden.")
        else:
            exito, mensaje = registrar_usuario(
                nuevo_usuario, nueva_password, usuarios
            )

            if exito:
                guardar_usuarios(usuarios)
                # Auto-inicio de sesión tras un registro exitoso.
                _iniciar_sesion(nombre_para_mostrar(nuevo_usuario, usuarios))
            else:
                st.error(mensaje)

    if st.button("¿Ya tienes cuenta? Inicia sesión", type="tertiary", use_container_width=True):
        st.session_state["auth_vista"] = "login"
        st.rerun()
