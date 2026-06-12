from __future__ import annotations

import ast
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.navigation import (
    establecer_juego,
    requerir_autenticacion,
)
from src.styles import BASE_CSS


st.set_page_config(
    page_title="The Data Machine",
    page_icon="🎮",
    layout="wide",

    # La navegación principal del proyecto es personalizada.
    # La barra lateral comienza colapsada, pero su flecha se conserva.
    initial_sidebar_state="collapsed",
)

# Impide acceder al catálogo sin una sesión iniciada.
# Si el usuario no está autenticado, se redirige al login.
requerir_autenticacion()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(BASE_CSS + """
<style>
/* ── Hero ── */
.tdm-hero { position: relative; z-index: 1; text-align: center; margin-bottom: 5rem; }
.tdm-hero-eyebrow {
    font-size: 11px; letter-spacing: 4px; text-transform: uppercase;
    color: #7c6af5; margin-bottom: 4px;
    animation: glitchEyebrow 3s ease-in-out infinite;
}
@keyframes glitchEyebrow {
    0%, 90%, 100% { text-shadow: 0 0 0 transparent; }
    92% { text-shadow: -2px 0 #f06292, 2px 0 #26c6da; }
    94% { text-shadow: 2px 0 #f06292, -2px 0 #26c6da; }
    96% { text-shadow: -1px 0 #f06292, 1px 0 #26c6da; }
}
.tdm-hero-title {
    font-family: 'Rajdhani', sans-serif; font-size: 52px; font-weight: 700;
    line-height: 1.05; margin-bottom: 6px; opacity: 0;
    animation: fadeInUp 0.8s ease forwards;
    text-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
.tdm-hero-grad {
    background: linear-gradient(90deg, #f06292, #7c6af5, #26c6da);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    animation: gradienteLogo 5s ease-in-out infinite alternate;
}
.tdm-hero-sub {
    font-size: 16px; color: #e8eaf6; opacity: 0;
    animation: fadeInUp 0.8s ease 0.15s forwards;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Entry animations ── */
.tdm-stats { opacity: 0; animation: fadeInUp 0.8s ease 0.3s forwards; }
.info-card { opacity: 0; transform: translateY(30px); animation: fadeInUp 0.6s ease forwards; }
.info-card:nth-child(2) { animation-delay: 0.15s; }
.info-card:nth-child(3) { animation-delay: 0.3s; }
.cat-track .game-card { opacity: 0; transform: translateY(30px); animation: catStagger 0.5s ease forwards; animation-delay: calc(var(--i, 0) * 60ms); }
@keyframes catStagger { to { opacity: 1; transform: translateY(0); } }

/* ── Scroll indicator ── */
.tdm-scroll {
    text-align: center; margin-top: 1.5rem; opacity: 0;
    animation: fadeIn 1s ease 0.6s forwards;
}
.tdm-scroll-arrow {
    display: inline-block; font-size: 14px; color: #e8eaf6;
    animation: bounceArrow 2s ease-in-out infinite;
}
@keyframes bounceArrow {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(8px); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* ── Featured game ── */
.tdm-featured {
    position: relative; z-index: 1; border-radius: 16px; overflow: hidden;
    margin-bottom: 4rem; height: 320px; cursor: pointer;
}
.tdm-featured img {
    width: 100%; height: 100%; object-fit: cover; display: block;
}
.tdm-featured-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(90deg, rgba(11,14,26,0.85) 0%, transparent 50%, rgba(11,14,26,0.85) 100%);
}
.tdm-featured-body {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    justify-content: center; padding: 2rem 3rem;
}
.tdm-featured-label {
    font-family: 'Orbitron', monospace; font-size: 10px; letter-spacing: 3px;
    color: #e8eaf6; text-transform: uppercase;
}
.tdm-featured-title {
    font-family: 'Rajdhani', sans-serif; font-size: 36px; font-weight: 700;
    color: #f0f2ff; text-shadow: 0 2px 16px rgba(0,0,0,0.5); margin: 4px 0;
}
.tdm-featured-btn {
    display: inline-block; margin-top: 0.8rem; padding: 8px 24px;
    border-radius: 8px; border: 1px solid rgba(124,106,245,0.4);
    background: rgba(124,106,245,0.15); color: #c7c0f0;
    font-family: 'Rajdhani', sans-serif; font-size: 14px; font-weight: 700;
    cursor: pointer; transition: all 0.2s; width: fit-content;
}
.tdm-featured-btn:hover {
    background: rgba(124,106,245,0.3); border-color: #7c6af5;
    box-shadow: 0 0 20px rgba(124,106,245,0.3); color: #f0f2ff;
}
.tdm-featured:hover .tdm-featured-btn {
    background: rgba(124,106,245,0.3); border-color: #7c6af5;
}

/* ── Tech stack ── */
.tdm-tech {
    position: relative; z-index: 1; text-align: center;
    padding: 1rem 0; margin-bottom: 1.5rem;
}
.tdm-tech-label {
    font-family: 'Orbitron', monospace; font-size: 9px; letter-spacing: 2px;
    color: #e8eaf6; text-transform: uppercase; margin-bottom: 0.8rem;
}
.tdm-tech-badge {
    display: inline-block; margin: 4px 5px; padding: 4px 12px;
    border-radius: 6px; font-size: 11px; font-family: 'Inter', sans-serif;
    font-weight: 500; border: 1px solid rgba(124,106,245,0.35);
    background: #0b0e1a; color: #e8eaf6;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.tdm-filter-box {
    position: relative; z-index: 1;
    background: #0b0e1a;
    border: 1px solid rgba(124,106,245,0.5);
    border-radius: 12px;
    padding: 1.2rem 1.5rem 0.8rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.tdm-filter-box .stTextInput > div > div > input,
.tdm-filter-box .stMultiSelect > div > div {
    background: #0b0e1a !important;
    border: 1px solid rgba(124,106,245,0.5) !important;
    color: #fff !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
.tdm-filter-box .stTextInput > div > div > input:focus,
.tdm-filter-box .stMultiSelect > div > div:focus-within {
    border-color: #7c6af5 !important;
    box-shadow: 0 0 16px rgba(124,106,245,0.35) !important;
}
.tdm-filter-box .stTextInput > div > div > input::placeholder {
    color: rgba(232,234,246,0.5) !important;
}
.tdm-filter-box label {
    color: #fff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    text-shadow: 0 1px 6px rgba(0,0,0,0.6) !important;
}
.tdm-filter-clear {
    display: flex; align-items: flex-end; height: 100%;
    padding-bottom: 2px;
}
.tdm-filter-clear button {
    background: rgba(124,106,245,0.2) !important;
    border: 1px solid rgba(124,106,245,0.5) !important;
    color: #fff !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    padding: 0.25rem 1rem !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    text-shadow: 0 1px 4px rgba(0,0,0,0.4) !important;
}
.tdm-filter-clear button:hover {
    background: rgba(124,106,245,0.35) !important;
    border-color: #7c6af5 !important;
    box-shadow: 0 0 12px rgba(124,106,245,0.3) !important;
}
.game-card-img { height: 200px !important; }

/* ── Botones reales de Streamlit para abrir cada análisis ── */
div[data-testid="stButton"] > button {
    width: 100%;
    min-height: 40px;
    margin-top: -2px;
    margin-bottom: 12px;
    border-radius: 0 0 12px 12px;
    border: 1px solid rgba(124,106,245,0.55);
    background: linear-gradient(
        90deg,
        rgba(124,106,245,0.18),
        rgba(38,198,218,0.10)
    );
    color: #f0f2ff;
    font-family: 'Rajdhani', sans-serif;
    font-weight: 700;
    transition: all 0.2s ease;
}

div[data-testid="stButton"] > button:hover {
    border-color: #7c6af5;
    background: linear-gradient(
        90deg,
        rgba(124,106,245,0.34),
        rgba(38,198,218,0.22)
    );
    box-shadow: 0 0 18px rgba(124,106,245,0.28);
    color: #ffffff;
}

/* Conserva visible la flecha que abre la barra lateral colapsada. */
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Datos ─────────────────────────────────────────────────────────────────────

# ==========================================================
# RUTAS Y COLUMNAS DEL CATÁLOGO OFICIAL
# ==========================================================

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

RUTA_DATASET = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "dataset_limpio.csv"
)

RUTA_CATALOGO = (
    RAIZ_PROYECTO
    / "config"
    / "catalogo.json"
)

COLUMNAS_HOMEPAGE = {
    "appid",
    "name",
    "header_image",
    "price",
    "pct_pos_total",
    "genres",
    "tags",
    "metacritic_score",
    "estimated_owners",
    "release_date",
    "discount",
    "average_playtime_forever",
    "average_playtime_2weeks",
    "num_reviews_total",
}


@st.cache_data(show_spinner=False)
def load_catalog() -> pd.DataFrame:
    """
    Carga solamente los 10 videojuegos activos definidos
    en config/catalogo.json.

    El dataset original nunca se modifica. Solo se leen las
    columnas necesarias para construir la Homepage.
    """
    if not RUTA_DATASET.exists():
        raise FileNotFoundError(
            f"No se encontró el dataset: {RUTA_DATASET}"
        )

    if not RUTA_CATALOGO.exists():
        raise FileNotFoundError(
            f"No se encontró el catálogo: {RUTA_CATALOGO}"
        )

    # ------------------------------------------------------
    # Leer el catálogo oficial
    # ------------------------------------------------------

    with RUTA_CATALOGO.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        contenido_catalogo = json.load(archivo)

    juegos_activos = [
        juego
        for juego in contenido_catalogo.get("juegos", [])
        if juego.get("activo", True)
    ]

    if not juegos_activos:
        raise ValueError(
            "config/catalogo.json no contiene juegos activos."
        )

    appids_catalogo = [
        int(juego["appid"])
        for juego in juegos_activos
    ]

    orden_catalogo = {
        int(juego["appid"]): int(juego["orden"])
        for juego in juegos_activos
    }

    # ------------------------------------------------------
    # Leer únicamente las columnas necesarias
    # ------------------------------------------------------

    df = pd.read_csv(
        RUTA_DATASET,
        usecols=lambda columna: (
            columna in COLUMNAS_HOMEPAGE
        ),
        low_memory=False,
    )

    columnas_faltantes = sorted(
        COLUMNAS_HOMEPAGE.difference(df.columns)
    )

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas para construir la Homepage: "
            + ", ".join(columnas_faltantes)
        )

    # ------------------------------------------------------
    # Filtrar exclusivamente los 10 appids oficiales
    # ------------------------------------------------------

    df["appid"] = pd.to_numeric(
        df["appid"],
        errors="coerce",
    )

    df = df[
        df["appid"].isin(appids_catalogo)
    ].copy()

    df["appid"] = df["appid"].astype("int64")

    df = df.drop_duplicates(
        subset="appid",
        keep="first",
    )

    appids_encontrados = set(
        df["appid"].tolist()
    )

    appids_faltantes = sorted(
        set(appids_catalogo).difference(
            appids_encontrados
        )
    )

    if appids_faltantes:
        raise ValueError(
            "Los siguientes appids no existen en el dataset: "
            + ", ".join(map(str, appids_faltantes))
        )

    # ------------------------------------------------------
    # Normalizar columnas numéricas
    # ------------------------------------------------------

    columnas_numericas = [
        "price",
        "pct_pos_total",
        "metacritic_score",
        "discount",
        "average_playtime_forever",
        "average_playtime_2weeks",
        "num_reviews_total",
    ]

    for columna in columnas_numericas:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce",
        ).fillna(0)

    # ------------------------------------------------------
    # Preparar etiquetas visibles
    # ------------------------------------------------------

    def parsear_generos(valor: object) -> str:
        """Convierte la lista de géneros a texto legible."""
        if valor is None:
            return ""

        if isinstance(valor, float) and pd.isna(valor):
            return ""

        texto = str(valor).strip()

        if not texto:
            return ""

        try:
            generos = ast.literal_eval(texto)

            if isinstance(generos, list):
                return ", ".join(
                    str(genero).strip()
                    for genero in generos
                    if str(genero).strip()
                )

        except (ValueError, SyntaxError):
            pass

        return texto

    df["display_tags"] = (
        df["genres"]
        .apply(parsear_generos)
    )

    # ------------------------------------------------------
    # Ordenar como fue definido en catalogo.json
    # ------------------------------------------------------

    df["catalog_order"] = (
        df["appid"]
        .map(orden_catalogo)
    )

    df = df.sort_values(
        "catalog_order"
    ).reset_index(drop=True)

    if len(df) != len(appids_catalogo):
        raise ValueError(
            "El número de juegos cargados no coincide "
            "con el catálogo oficial."
        )

    return df


def sentiment_label(pct):
    if pct >= 85: return '<span class="rating-pill r-pos">Muy positivo</span>'
    elif pct >= 65: return '<span class="rating-pill r-mix">Mixto</span>'
    return '<span class="rating-pill r-neg">Negativo</span>'

def price_display(price):
    if price == 0: return '<span class="game-price price-free">Gratis</span>'
    mxn = price * 20
    return f'<span class="game-price">MX${mxn:,.0f}</span>'


def get_all_genres(df: pd.DataFrame) -> list:
    genres = set()
    for g in df["genres"].dropna():
        try:
            parsed = ast.literal_eval(str(g))
            if isinstance(parsed, list):
                for item in parsed:
                    if item.strip():
                        genres.add(item.strip())
        except:
            for part in str(g).split(","):
                part = part.strip().strip("[]'\"{}")
                if part:
                    genres.add(part)
    return sorted(genres)


def _game_card_html(row):
    """
    Construye únicamente la parte visual de una tarjeta.

    La navegación no se realiza con enlaces HTML ni JavaScript.
    El botón Streamlit se agrega después de esta tarjeta.
    """
    appid = int(row["appid"])
    name = row["name"]
    img = row.get("header_image", "")
    tags = row.get("display_tags", "")
    pct = row["pct_pos_total"]
    price = row["price"]
    mc = row.get("metacritic_score", "—")

    etiquetas = "".join(
        f'<span class="game-tag">{tag.strip()}</span>'
        for tag in str(tags).split(",")[:3]
        if tag.strip()
    )

    return f"""
<div class="game-card" data-appid="{appid}">
  <div class="game-card-inner">
    <img
      class="game-card-img"
      src="{img}"
      onerror="this.src='https://via.placeholder.com/300x200/0b0e1a/7c6af5?text=TDM'"
      alt="{name}"
    />
    <div class="game-card-body">
      <div class="game-tags">{etiquetas}</div>
      <div class="game-card-title">{name}</div>
      <div class="game-meta">
        {sentiment_label(pct)}
        {price_display(price)}
      </div>
      <div style="
        font-size:10px;
        color:#e8eaf6;
        margin-top:5px;
        font-family:'Orbitron',monospace;
        text-shadow:0 1px 8px rgba(0,0,0,0.5);
      ">
        &#11088; {pct}% · METACORE {mc}
      </div>
    </div>
  </div>
</div>
"""


def abrir_analisis(
    appid: int,
    nombre: str,
) -> None:
    """
    Guarda la selección en la sesión actual y abre el dashboard.

    Al usar st.button + st.switch_page no se recarga el navegador
    completo, por lo que la autenticación permanece activa.
    """
    establecer_juego(
        appid=int(appid),
        nombre=str(nombre),
    )

    st.switch_page(
        "pages/analisis.py"
    )


def renderizar_categoria(
    icono: str,
    titulo: str,
    juegos: pd.DataFrame,
    clave_categoria: str,
    max_juegos: int = 10,
    columnas_por_fila: int = 4,
) -> None:
    """
    Renderiza una categoría mediante componentes Streamlit.

    Cada tarjeta incluye un botón real. Esto evita perder la sesión,
    problema que ocurría al usar enlaces HTML con href.
    """
    juegos = juegos.head(max_juegos).reset_index(drop=True)

    if juegos.empty:
        return

    st.markdown(
        f'<div class="cat-title">{icono} {titulo}</div>',
        unsafe_allow_html=True,
    )

    for inicio in range(
        0,
        len(juegos),
        columnas_por_fila,
    ):
        fila = juegos.iloc[
            inicio:inicio + columnas_por_fila
        ]

        columnas = st.columns(
            columnas_por_fila,
            gap="small",
        )

        for indice_columna, columna in enumerate(columnas):
            if indice_columna >= len(fila):
                continue

            juego = fila.iloc[indice_columna]
            appid = int(juego["appid"])
            nombre = str(juego["name"])

            with columna:
                st.markdown(
                    _game_card_html(juego),
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Ver análisis →",
                    key=(
                        f"abrir_{clave_categoria}_"
                        f"{inicio}_{appid}"
                    ),
                    use_container_width=True,
                ):
                    abrir_analisis(
                        appid=appid,
                        nombre=nombre,
                    )


df = load_catalog()



st.markdown('<!-- tdm-page --><div class="tdm-page">', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
user = st.session_state.get("username", "usuario")
st.markdown(f"""
<div class="tdm-topbar">
  <div class="tdm-logo">⬡ THE DATA MACHINE</div>
  <div class="tdm-actions">
    <span class="tdm-music-btn" id="tdmMusicBtn">🎵</span>
    <span class="tdm-user">◆ {user}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-hero">
  <div class="tdm-hero-eyebrow">⟡ La Máquina de Datos</div>
  <div class="tdm-hero-title">
    Millones de reseñas.<br>
    <span class="tdm-hero-grad">Una máquina para entenderlas todas.</span>
  </div>
  <div class="tdm-hero-sub">5,000 reseñas recientes · 10 videojuegos · VADER · TF-IDF · Dashboard interactivo</div>
  <div class="tdm-scroll"><span class="tdm-scroll-arrow">⟡</span></div>
</div>
""", unsafe_allow_html=True)


# ── Stats ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="tdm-stats">
  <div class="tdm-stat-item">
    <div class="tdm-stat-num" data-count="{len(df)}">{len(df)}</div>
    <div class="tdm-stat-lbl">Juegos analizados</div>
  </div>
  <div class="tdm-stat-item">
    <div class="tdm-stat-num" data-count="5000">5,000</div>
    <div class="tdm-stat-lbl">Reseñas recientes analizadas</div>
  </div>
  <div class="tdm-stat-item">
    <div class="tdm-stat-num">VADER</div>
    <div class="tdm-stat-lbl">Modelo NLP</div>
  </div>
  <div class="tdm-stat-item">
    <div class="tdm-stat-num">TF-IDF</div>
    <div class="tdm-stat-lbl">Extracción temas</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ¿Qué es? ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-section-title">▸ ¿Qué es The Data Machine?</div>
<div class="tdm-section-sub">Procesamos 5,000 reseñas recientes de Steam con NLP. Sentimiento, temas y métricas de un vistazo.</div>
""", unsafe_allow_html=True)

info_cols = st.columns(3)
for col, (letter, grad, title, desc) in zip(info_cols, [
    ("S", "linear-gradient(135deg,#f06292,#7c6af5)", "Análisis de Sentimiento", "Clasificamos cada reseña como positiva, neutral o negativa usando VADER (NLTK). Una gráfica clara de lo que opina la comunidad."),
    ("T", "linear-gradient(135deg,#7c6af5,#a99cf5)", "Extracción de Temas", "TF-IDF detecta palabras y conceptos más repetidos. Bugs, historia, precio, multijugador — sin leer ni una línea."),
    ("D", "linear-gradient(135deg,#26c6da,#7c6af5)", "Dashboard Interactivo", "Gráficas Plotly, nubes de palabras y tablas. Descarga el análisis en CSV o exporta las gráficas en PNG."),
]):
    with col:
        st.markdown(f"""
<div class="info-card">
  <div class="info-card-inner">
    <span class="info-card-letter" style="background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{letter}</span>
    <div class="info-card-title">{title}</div>
    <div class="info-card-desc">{desc}</div>
  </div>
</div>""", unsafe_allow_html=True)


st.markdown('<div class="tdm-divider"></div>', unsafe_allow_html=True)


# ── Featured game ──────────────────────────────────────────────────────────────
featured = df.sample(
    n=1,
    random_state=2026,
).iloc[0]

featured_appid = int(
    featured["appid"]
)

featured_nombre = str(
    featured["name"]
)

ftags = "".join(
    f'<span class="game-tag">{tag.strip()}</span>'
    for tag in str(
        featured.get(
            "display_tags",
            "",
        )
    ).split(",")[:3]
    if tag.strip()
)

st.markdown(
    f"""
<div class="tdm-featured" data-appid="{featured_appid}">
  <img
    src="{featured['header_image']}"
    onerror="this.src='https://via.placeholder.com/600x320/0b0e1a/7c6af5?text=⟡'"
    alt="{featured_nombre}"
  >
  <div class="tdm-featured-overlay"></div>
  <div class="tdm-featured-body">
    <div class="tdm-featured-label">
      ⟡ JUEGO DESTACADO
    </div>
    <div class="tdm-featured-title">
      {featured_nombre}
    </div>
    <div style="display:flex;gap:6px;margin:4px 0;">
      {ftags}
    </div>
    <div style="
      color:#e8eaf6;
      font-size:13px;
      text-shadow:0 1px 8px rgba(0,0,0,0.4);
    ">
      ★ {featured['pct_pos_total']}% positivo ·
      {price_display(featured['price'])}
    </div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

if st.button(
    f"Ver análisis de {featured_nombre} →",
    key=f"abrir_destacado_{featured_appid}",
    use_container_width=True,
):
    abrir_analisis(
        appid=featured_appid,
        nombre=featured_nombre,
    )


st.markdown('<div class="tdm-divider"></div>', unsafe_allow_html=True)


# ── Filtros de búsqueda ──────────────────────────────────────────────────────
st.markdown('<div class="tdm-section-title">▸ Buscar juegos</div>', unsafe_allow_html=True)

all_genres = get_all_genres(df)
max_price_mxn = int(df["price"].max() * 20)

st.markdown('<div class="tdm-filter-box">', unsafe_allow_html=True)

r1 = st.columns([2, 3, 1])
with r1[0]:
    search_name = st.text_input("⟡ Nombre", placeholder="Ej: Dark Souls", key="filter_name")
with r1[1]:
    search_genres = st.multiselect("◆ Género", all_genres, placeholder="Selecciona géneros...", key="filter_genres")
with r1[2]:
    st.markdown('<div class="tdm-filter-clear">', unsafe_allow_html=True)
    if st.button("⟡ Limpiar"):
        for k in ["filter_name", "filter_genres", "filter_price", "filter_rating"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

r2 = st.columns(2)
with r2[0]:
    price_range = st.slider("★ Precio MXN", 0, max_price_mxn, (0, max_price_mxn), key="filter_price")
with r2[1]:
    min_rating = st.select_slider("▲ Rating mín.", options=[0, 50, 65, 75, 85, 95], value=0, key="filter_rating")

st.markdown('</div>', unsafe_allow_html=True)

filters_active = bool(search_name) or bool(search_genres) or price_range != (0, max_price_mxn) or min_rating > 0

if filters_active:
    filtered = df.copy()
    if search_name:
        filtered = filtered[filtered["name"].str.contains(search_name, case=False, na=False)]
    if search_genres:
        filtered = filtered[filtered["genres"].apply(
            lambda g: any(sg in str(g) for sg in search_genres) if pd.notna(g) else False
        )]
    if price_range[0] > 0 or price_range[1] < max_price_mxn:
        filtered = filtered[
            (filtered["price"] * 20 >= price_range[0]) &
            (filtered["price"] * 20 <= price_range[1])
        ]
    if min_rating > 0:
        filtered = filtered[filtered["pct_pos_total"] >= min_rating]

    if len(filtered) > 0:
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin:0.5rem 0;">
  <span class="tdm-section-title" style="margin-bottom:0;font-size:25px;">▸ Resultados</span>
  <span style="font-size:11px;color:#e8eaf6;font-family:'Orbitron',monospace;text-shadow:0 1px 8px rgba(0,0,0,0.5);">{len(filtered)} COINCIDENCIAS</span>
</div>""", unsafe_allow_html=True)
        renderizar_categoria(
            icono="",
            titulo=f"Resultados ({len(filtered)})",
            juegos=filtered,
            clave_categoria="resultados",
            max_juegos=50,
        )
    else:
        st.markdown("""
<div style="text-align:center;padding:3rem 1rem;color:#e8eaf6;font-size:14px;">
  ⟡ No se encontraron juegos con esos filtros.
</div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
  <span class="tdm-section-title" style="margin-bottom:0;">▸ Explora {len(df)} juegos</span>
  <span style="font-size:11px;color:#e8eaf6;font-family:'Orbitron',monospace;text-shadow:0 1px 8px rgba(0,0,0,0.5);">{len(df)} TÍTULOS</span>
</div>""", unsafe_allow_html=True)

    try:
        renderizar_categoria(
            icono="⟡",
            titulo="Nuestra selección para ti",
            juegos=df.sample(
                n=min(10, len(df)),
                random_state=2026,
            ),
            clave_categoria="seleccion",
        )

        top10 = df.nlargest(10, "pct_pos_total")
        renderizar_categoria(
            icono="◆",
            titulo="Top 10 Mejor Valorados",
            juegos=top10,
            clave_categoria="top",
        )

        try:
            recientes = df.sort_values("release_date", ascending=False).head(15)
        except:
            recientes = df.head(15)
        renderizar_categoria(
            icono="▸",
            titulo="Recién Llegados",
            juegos=recientes,
            clave_categoria="recientes",
        )

        gratis = df[df["price"] == 0].head(15)
        if len(gratis) >= 3:
            renderizar_categoria(
                icono="Gratis",
                titulo="Juegos Gratis",
                juegos=gratis,
                clave_categoria="gratis",
            )

        aburrimiento = df.nlargest(10, "average_playtime_forever")
        renderizar_categoria(
            icono="▲",
            titulo="Para aniquilar el aburrimiento",
            juegos=aburrimiento,
            clave_categoria="aburrimiento",
        )

        calidad = df[df["pct_pos_total"] >= 85].nsmallest(10, "price")
        if len(calidad) >= 3:
            renderizar_categoria(
                icono="★",
                titulo="Mejor relación calidad-precio",
                juegos=calidad,
                clave_categoria="calidad",
            )

        populares = df.nlargest(10, "num_reviews_total")
        renderizar_categoria(
            icono="⟐",
            titulo="Más Populares",
            juegos=populares,
            clave_categoria="populares",
        )

        criticos = df[df["metacritic_score"] >= 80].nlargest(10, "metacritic_score")
        if len(criticos) >= 3:
            renderizar_categoria(
                icono="⬡",
                titulo="Recomendados por la crítica",
                juegos=criticos,
                clave_categoria="critica",
            )

        indies = df[df["genres"].str.contains("Indie", na=False, case=False)].nlargest(15, "pct_pos_total")
        if len(indies) >= 3:
            renderizar_categoria(
                icono="⊡",
                titulo="Indies Imperdibles",
                juegos=indies,
                clave_categoria="indies",
            )

        descuento = df[df["discount"] > 0].head(15)
        if len(descuento) >= 3:
            renderizar_categoria(
                icono="⏷",
                titulo="En Descuento",
                juegos=descuento,
                clave_categoria="descuento",
            )
    except Exception as e:
        st.error(f"Error al cargar categorías: {e}")


st.markdown('<div class="tdm-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="tdm-tech">
  <div class="tdm-tech-label">⟡ STACK TECNOLÓGICO</div>
  <div>
    <span class="tdm-tech-badge">Python</span>
    <span class="tdm-tech-badge">Streamlit</span>
    <span class="tdm-tech-badge">VADER</span>
    <span class="tdm-tech-badge">TF-IDF</span>
    <span class="tdm-tech-badge">Pandas</span>
    <span class="tdm-tech-badge">Plotly</span>
    <span class="tdm-tech-badge">NLTK</span>
    <span class="tdm-tech-badge">BeautifulSoup</span>
    <span class="tdm-tech-badge">NumPy</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-footer">
  <div class="tdm-footer-line">© 2026 <span class="tdm-footer-grad">The Data Machine</span> · IPN ESCOM · Semestre IV</div>
  <div class="tdm-footer-line">Hecho con ⟡ por el equipo La Máquina de Datos</div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── JS ────────────────────────────────────────────────────────────────────────
st.components.v1.html("""
<script>
(function() {
  try {
    var doc = window.parent.document;
    var win = window.parent;

    // ══════════════════════════════════════════════════════════════════════
    // NEBULA BACKGROUND — Canvas incrustado en body, fixed
    // ══════════════════════════════════════════════════════════════════════
    var canvas = doc.createElement('canvas');
    canvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;width:100%;height:100%';
    doc.body.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    var W, H, CX, CY;

    function resize() {
      var dpr = Math.min(win.devicePixelRatio || 1, 2);
      W = win.innerWidth * dpr;
      H = win.innerHeight * dpr;
      canvas.width = W; canvas.height = H;
      canvas.style.width = win.innerWidth + 'px';
      canvas.style.height = win.innerHeight + 'px';
      CX = W / 2; CY = H / 2;
      initParticles();
      initStars();
    }

    var particles = [];
    var mouse = { x: -1000, y: -1000 };
    var shockwave = { active: false, x: 0, y: 0, radius: 0, maxRadius: 0 };

    function spawnParticle() {
      var angle = Math.random() * Math.PI * 2;
      var dist = 30 + Math.random() * Math.min(W, H) * 0.45;
      var orbitSpeed = (0.3 + Math.random() * 1.2) * (Math.random() > 0.5 ? 1 : -1);
      var size = 0.5 + Math.random() * 1.5;
      var colors = ['#f06292', '#7c6af5', '#26c6da', '#a99cf5', '#e8eaf6'];
      var col = colors[Math.floor(Math.random() * colors.length)];
      return {
        angle: angle, dist: dist, orbitSpeed: orbitSpeed,
        size: size, color: col,
        baseY: (Math.random() - 0.5) * 60,
        trail: []
      };
    }

    function initParticles() {
      particles = [];
      for (var i = 0; i < 400; i++) particles.push(spawnParticle());
    }

    var stars = [];
    function initStars() {
      stars = [];
      for (var i = 0; i < 60; i++) {
        stars.push({
          x: Math.random() * W, y: Math.random() * H,
          r: 0.5 + Math.random() * 1.5,
          speed: 0.3 + Math.random() * 0.8,
          phase: Math.random() * Math.PI * 2
        });
      }
    }

    doc.addEventListener('mousemove', function(e) {
      mouse.x = e.clientX * 2;
      mouse.y = e.clientY * 2;
    });

    doc.addEventListener('click', function(e) {
      shockwave.active = true;
      shockwave.x = e.clientX * 2;
      shockwave.y = e.clientY * 2;
      shockwave.radius = 0;
      shockwave.maxRadius = Math.min(W, H) * 0.7;
    });

    function draw() {
      ctx.clearRect(0, 0, W, H);

      var t = Date.now() / 1000;
      for (var i = 0; i < stars.length; i++) {
        var s = stars[i];
        var a = 0.2 + 0.8 * (0.5 + 0.5 * Math.sin(t * s.speed + s.phase));
        ctx.fillStyle = 'rgba(255,255,255,' + a + ')';
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
      }

      var glow = ctx.createRadialGradient(CX, CY, 0, CX, CY, Math.min(W, H) * 0.5);
      glow.addColorStop(0, 'rgba(124,106,245,0.08)');
      glow.addColorStop(1, 'transparent');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, W, H);

      if (shockwave.active) {
        shockwave.radius += 12;
        if (shockwave.radius > shockwave.maxRadius) shockwave.active = false;
        var swAlpha = 1 - (shockwave.radius / shockwave.maxRadius);
        ctx.strokeStyle = 'rgba(124,106,245,' + swAlpha * 0.6 + ')';
        ctx.lineWidth = 3 * swAlpha;
        ctx.beginPath();
        ctx.arc(shockwave.x, shockwave.y, shockwave.radius, 0, Math.PI * 2);
        ctx.stroke();
        var swGlow = ctx.createRadialGradient(shockwave.x, shockwave.y, 0, shockwave.x, shockwave.y, shockwave.radius);
        swGlow.addColorStop(0, 'rgba(38,198,218,' + swAlpha * 0.1 + ')');
        swGlow.addColorStop(1, 'transparent');
        ctx.fillStyle = swGlow;
        ctx.beginPath(); ctx.arc(shockwave.x, shockwave.y, shockwave.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.angle += p.orbitSpeed * 0.008;

        var dx = mouse.x - (CX + Math.cos(p.angle) * p.dist);
        var dy = mouse.y - (CY + Math.sin(p.angle) * p.dist * 0.5 + p.baseY);
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          var force = (200 - dist) / 200 * 3;
          p.angle -= (dx / dist) * force * 0.003;
          p.dist += force * (dist < 100 ? 0.5 : -0.3);
          p.dist = Math.max(20, Math.min(Math.min(W, H) * 0.45, p.dist));
        }

        var px = CX + Math.cos(p.angle) * p.dist;
        var py = CY + Math.sin(p.angle) * p.dist * 0.5 + p.baseY;

        p.trail.push({ x: px, y: py });
        if (p.trail.length > 3) p.trail.shift();

        for (var j = 0; j < p.trail.length; j++) {
          var a = (j / p.trail.length) * 0.25;
          ctx.fillStyle = p.color.replace(')', ',' + a + ')').replace('rgb', 'rgba');
          ctx.beginPath();
          ctx.arc(p.trail[j].x, p.trail[j].y, p.size * (j / p.trail.length) * 0.5, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.shadowBlur = 1.5;
        ctx.shadowColor = p.color;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    function update() {
      draw();
      requestAnimationFrame(update);
    }

    resize();
    win.addEventListener('resize', resize);
    update();

    // ══════════════════════════════════════════════════════════════════════
    // MÚSICA SYNTHWAVE
    // ══════════════════════════════════════════════════════════════════════
    var audioCtx = null, playing = false, loopTimers = [];

    function kick(time) {
      var osc = audioCtx.createOscillator(), g = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(150, time);
      osc.frequency.exponentialRampToValueAtTime(40, time + 0.08);
      g.gain.setValueAtTime(0.3, time);
      g.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
      osc.connect(g); g.connect(audioCtx.destination);
      osc.start(time); osc.stop(time + 0.1);
    }
    function snare(time) {
      var len = audioCtx.sampleRate * 0.1, buf = audioCtx.createBuffer(1, len, audioCtx.sampleRate);
      var d = buf.getChannelData(0);
      for (var i = 0; i < len; i++) d[i] = (Math.random()*2-1) * Math.pow(1-i/len, 3);
      var src = audioCtx.createBufferSource(); src.buffer = buf;
      var g = audioCtx.createGain();
      g.gain.setValueAtTime(0.15, time);
      g.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
      src.connect(g); g.connect(audioCtx.destination);
      src.start(time); src.stop(time + 0.1);
    }
    function arp(time, f) {
      var notes = [f, f*1.25, f*1.5, f*2, f*1.5, f*1.25];
      for (var i = 0; i < notes.length; i++) {
        var osc = audioCtx.createOscillator(), g = audioCtx.createGain();
        osc.type = 'square'; osc.frequency.value = notes[i];
        g.gain.setValueAtTime(0.04, time + i*0.06);
        g.gain.exponentialRampToValueAtTime(0.001, time + i*0.06 + 0.05);
        osc.connect(g); g.connect(audioCtx.destination);
        osc.start(time + i*0.06); osc.stop(time + i*0.06 + 0.05);
      }
    }
    function pad(time, f) {
      var osc = audioCtx.createOscillator(), g = audioCtx.createGain();
      osc.type = 'sawtooth'; osc.frequency.value = f;
      g.gain.setValueAtTime(0.02, time);
      g.gain.linearRampToValueAtTime(0.04, time + 0.3);
      g.gain.linearRampToValueAtTime(0.02, time + 1.8);
      g.gain.linearRampToValueAtTime(0.001, time + 2);
      osc.connect(g); g.connect(audioCtx.destination);
      osc.start(time); osc.stop(time + 2);
    }
    function scheduleSynthwave() {
      var t = audioCtx.currentTime + 0.05, beat = 0.5;
      var chords = [
        { arp: 261.63, pad: 130.81 }, { arp: 329.63, pad: 164.81 },
        { arp: 293.66, pad: 146.83 }, { arp: 349.23, pad: 174.61 },
        { arp: 329.63, pad: 164.81 }, { arp: 392.00, pad: 196.00 },
        { arp: 261.63, pad: 130.81 }, { arp: 293.66, pad: 146.83 },
      ];
      for (var bar = 0; bar < 8; bar++) {
        var ch = chords[bar];
        for (var b = 0; b < 4; b++) {
          var bt = t + (bar * 4 + b) * beat;
          if (b === 0 || b === 2) kick(bt);
          if (b === 1 || b === 3) snare(bt);
          if (b === 0 || b === 2) arp(bt + 0.02, ch.arp);
        }
        pad(t + bar * 4 * beat, ch.pad);
      }
    }
    function loopSynthwave() { if (!playing) return; scheduleSynthwave(); loopTimers.push(setTimeout(loopSynthwave, 16000)); }

    var btn = doc.getElementById('tdmMusicBtn');
    if (btn) {
      btn.addEventListener('click', function() {
        if (!audioCtx) audioCtx = new (win.AudioContext || win.webkitAudioContext)();
        if (playing) {
          playing = false; loopTimers.forEach(function(t) { clearTimeout(t); }); loopTimers = [];
          btn.textContent = '🎵'; btn.classList.remove('playing');
        } else {
          playing = true; btn.textContent = '⏸'; btn.classList.add('playing');
          scheduleSynthwave(); loopTimers.push(setTimeout(loopSynthwave, 16000));
        }
      });
    }

    // ══════════════════════════════════════════════════════════════════════
    // CATEGORY ROWS — per-track scroll arrows
    // ══════════════════════════════════════════════════════════════════════
    doc.querySelectorAll('.cat-wrapper').forEach(function(wrapper) {
      var track = wrapper.querySelector('.cat-track');
      var leftArrow = wrapper.querySelector('.cat-arrow-left');
      var rightArrow = wrapper.querySelector('.cat-arrow-right');
      if (!track) return;

      function scrollBy(dir) {
        var cardEl = track.querySelector('.game-card');
        var w = cardEl ? cardEl.offsetWidth + 16 : 260;
        track.scrollLeft += dir * w * 4;
      }

      if (leftArrow) leftArrow.addEventListener('click', function() { scrollBy(-1); });
      if (rightArrow) rightArrow.addEventListener('click', function() { scrollBy(1); });
    });

    // ══════════════════════════════════════════════════════════════════════
    // STAGGER (CSS native via --i) + TILT 3D + CLICK + COUNTERS
    // ══════════════════════════════════════════════════════════════════════
    doc.querySelectorAll('.game-card, .info-card').forEach(function(card, i) {
      card.style.setProperty('--i', i);
    });

    doc.querySelectorAll('.game-card, .info-card').forEach(function(card) {
      var inner = card.querySelector('.game-card-inner') || card.querySelector('.info-card-inner');
      if (!inner) return;
      card.addEventListener('mousemove', function(e) {
        var rect = card.getBoundingClientRect();
        var x = e.clientX - rect.left, y = e.clientY - rect.top;
        var cx = rect.width/2, cy = rect.height/2;
        inner.style.transform = 'rotateX(' + ((y-cy)/cy*-8) + 'deg) rotateY(' + ((x-cx)/cx*8) + 'deg)';
      });
      card.addEventListener('mouseleave', function() {
        inner.style.transform = 'rotateX(0deg) rotateY(0deg)';
      });
    });

    // La navegación utiliza st.button + st.switch_page.
    // Este script conserva exclusivamente animaciones visuales.

    doc.querySelectorAll('.tdm-stat-num[data-count]').forEach(function(el) {
      var target = parseInt(el.getAttribute('data-count'), 10);
      if (isNaN(target)) return;
      var start = performance.now();
      function step(now) {
        var p = Math.min((now - start) / 1000, 1);
        var cur = Math.round(p * target);
        el.textContent = target >= 1000000 ? (cur/1000000).toFixed(1) + 'M+' : cur;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  } catch(e) {}
})();
</script>
""", height=0)
