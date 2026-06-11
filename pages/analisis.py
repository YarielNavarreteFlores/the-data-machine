from __future__ import annotations

import html
import json
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard import (
    cargar_metadata_catalogo,
    cargar_resultados_nlp,
    construir_distribucion_sentimiento,
    construir_matriz_confusion,
    dataframe_a_csv_bytes,
    filtrar_reviews,
    formatear_minutos,
    formatear_numero,
    formatear_porcentaje,
    formatear_precio,
    formatear_proporcion,
    generar_nube_palabras,
    nombre_archivo_seguro,
    obtener_appids_disponibles,
    obtener_datos_juego,
    parsear_lista_texto,
)
from src.styles import BASE_CSS


# ==========================================================
# CONFIGURACIÓN GENERAL DE STREAMLIT
# ==========================================================

st.set_page_config(
    page_title="The Data Machine · Análisis",
    page_icon="◈",
    layout="wide",
)

# CSS local de esta página. No se modifica src/styles.py,
# porque ese archivo pertenece al diseño compartido del equipo.
DASHBOARD_CSS = """
<style>
.tdm-dashboard-header {
    padding: 1.2rem 1.4rem;
    border: 1px solid rgba(124,106,245,0.35);
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(124,106,245,0.12), rgba(38,198,218,0.05));
    margin-bottom: 1rem;
}
.tdm-dashboard-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}
.tdm-dashboard-subtitle {
    color: #b8b8cf;
    margin-top: 0.25rem;
}
.tdm-chip {
    display: inline-block;
    padding: 0.25rem 0.65rem;
    margin: 0.15rem 0.25rem 0.15rem 0;
    border-radius: 999px;
    border: 1px solid rgba(124,106,245,0.45);
    background: rgba(124,106,245,0.10);
    font-size: 0.82rem;
}
.tdm-note {
    border-left: 4px solid #7c6af5;
    background: rgba(124,106,245,0.08);
    padding: 0.8rem 1rem;
    border-radius: 0 10px 10px 0;
}
</style>
"""

st.markdown(BASE_CSS + DASHBOARD_CSS, unsafe_allow_html=True)


# ==========================================================
# CARGA CON CACHÉ
# ==========================================================

@st.cache_data(show_spinner=False)
def cargar_datos_dashboard() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Carga los resultados NLP y la metadata una sola vez por sesión."""
    reviews, metricas, temas, tags = cargar_resultados_nlp()
    metadata = cargar_metadata_catalogo(metricas["appid"].tolist())
    return reviews, metricas, temas, tags, metadata


@st.cache_data(show_spinner=False)
def crear_nube_cacheada(appid: int, textos: tuple[str, ...]) -> Any:
    """Evita recalcular la nube de palabras en cada interacción."""
    _ = appid  # El appid forma parte de la clave del caché.
    return generar_nube_palabras(textos)


# ==========================================================
# FUNCIONES VISUALES DE LA PÁGINA
# ==========================================================

def aplicar_tema_plotly(fig: go.Figure, altura: int = 420) -> go.Figure:
    """Aplica un formato coherente con el diseño oscuro del proyecto."""
    fig.update_layout(
        height=altura,
        margin=dict(l=20, r=20, t=55, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8eaf6"),
        legend_title_text="",
        hoverlabel=dict(font_size=13),
    )
    return fig


def obtener_valor(fila: pd.Series, columna: str) -> Any:
    """Obtiene una métrica sin fallar cuando el campo no existe."""
    return fila[columna] if columna in fila.index else None


def mostrar_estado_modelo(metricas: pd.Series) -> None:
    """Explica si VADER cumple el objetivo y supera el baseline."""
    accuracy = obtener_valor(metricas, "accuracy_non_neutral")
    baseline = obtener_valor(metricas, "majority_baseline_non_neutral")

    if pd.isna(accuracy) or pd.isna(baseline):
        st.info("No hay suficientes reseñas no neutrales para evaluar el modelo.")
        return

    accuracy = float(accuracy)
    baseline = float(baseline)

    if accuracy >= 0.75 and accuracy > baseline:
        st.success(
            "VADER alcanza la meta de 75 % y supera el baseline mayoritario."
        )
    elif accuracy >= 0.75:
        st.warning(
            "VADER alcanza 75 %, pero no supera el baseline de la clase mayoritaria."
        )
    elif accuracy > baseline:
        st.warning(
            "VADER no alcanza 75 %, aunque sí supera el baseline mayoritario."
        )
    else:
        st.error(
            "VADER no alcanza 75 % ni supera el baseline para este videojuego."
        )


# ==========================================================
# CARGA Y CONTROL DE ERRORES
# ==========================================================

try:
    reviews, metricas, temas, tags, metadata = cargar_datos_dashboard()
except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError) as error:
    st.error("No fue posible cargar los resultados necesarios para el dashboard.")
    st.code(
        "python -m src.scraper --limite 500 --pausa 1\n"
        "python -m src.nlp --top-temas 15",
        language="bash",
    )
    st.exception(error)
    st.stop()

appids_disponibles = obtener_appids_disponibles(metadata, metricas, reviews)

if not appids_disponibles:
    st.error("No hay videojuegos comunes entre metadata, métricas y reseñas.")
    st.stop()

metadata_disponible = metadata[
    metadata["appid"].isin(appids_disponibles)
].copy()
metadata_disponible = metadata_disponible.sort_values("name")

nombre_por_appid = dict(
    zip(metadata_disponible["appid"], metadata_disponible["name"])
)
appid_por_nombre = {
    str(nombre): int(appid)
    for appid, nombre in nombre_por_appid.items()
}


# ==========================================================
# RESOLUCIÓN DEL JUEGO SELECCIONADO
# ==========================================================

appid_sesion = st.session_state.get("selected_appid")

# Compatibilidad temporal con el homepage actual, que todavía
# utiliza selected_game. En el Bloque 5 se estandarizará appid.
if appid_sesion not in appids_disponibles:
    nombre_sesion = st.session_state.get("selected_game")
    appid_sesion = appid_por_nombre.get(str(nombre_sesion))

if appid_sesion not in appids_disponibles:
    appid_sesion = appids_disponibles[0]

col_regresar, col_selector = st.columns([1, 3])

with col_regresar:
    if st.button("← Volver al catálogo", use_container_width=True):
        try:
            st.switch_page("pages/homepage.py")
        except Exception:
            st.info("Abre la aplicación desde: streamlit run app.py")

with col_selector:
    appid_seleccionado = st.selectbox(
        "Videojuego analizado",
        options=appids_disponibles,
        index=appids_disponibles.index(int(appid_sesion)),
        format_func=lambda appid: nombre_por_appid.get(appid, str(appid)),
    )

st.session_state["selected_appid"] = int(appid_seleccionado)
st.session_state["selected_game"] = nombre_por_appid[int(appid_seleccionado)]

datos = obtener_datos_juego(
    appid=int(appid_seleccionado),
    metadata=metadata,
    reviews=reviews,
    metricas=metricas,
    temas=temas,
    tags=tags,
)

meta = datos["metadata"]
metrica = datos["metricas"]
reviews_juego = datos["reviews"]
temas_juego = datos["temas"]
tags_juego = datos["tags"]

nombre_juego = str(meta["name"])
nombre_escapado = html.escape(nombre_juego)
usuario = html.escape(str(st.session_state.get("username", "usuario")))


# ==========================================================
# ENCABEZADO Y RESUMEN
# ==========================================================

st.markdown(
    f"""
    <div class="tdm-topbar">
        <div class="tdm-logo">⬡ THE DATA MACHINE</div>
        <div class="tdm-actions">
            <span class="tdm-user">◆ {usuario}</span>
        </div>
    </div>
    <div class="tdm-dashboard-header">
        <div class="tdm-dashboard-title">▸ {nombre_escapado}</div>
        <div class="tdm-dashboard-subtitle">
            Análisis de 500 reseñas recientes mediante VADER y TF-IDF.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_portada, col_resumen = st.columns([1, 2])

with col_portada:
    imagen = obtener_valor(meta, "header_image")
    if imagen is not None and not pd.isna(imagen) and str(imagen).strip():
        st.image(str(imagen), use_container_width=True)
    else:
        st.info("Este videojuego no tiene imagen de portada disponible.")

with col_resumen:
    generos = parsear_lista_texto(obtener_valor(meta, "genres"))
    if generos:
        chips = "".join(
            f'<span class="tdm-chip">{html.escape(genero)}</span>'
            for genero in generos[:8]
        )
        st.markdown(chips, unsafe_allow_html=True)

    fila_1 = st.columns(4)
    fila_1[0].metric(
        "Aprobación histórica",
        formatear_porcentaje(obtener_valor(meta, "pct_pos_total")),
    )
    fila_1[1].metric(
        "Aprobación de la muestra",
        formatear_porcentaje(
            obtener_valor(metrica, "steam_positive_pct_sample")
        ),
    )
    fila_1[2].metric(
        "Positivas según VADER",
        formatear_porcentaje(
            obtener_valor(metrica, "vader_positive_pct_all")
        ),
    )
    fila_1[3].metric(
        "Reseñas analizadas",
        formatear_numero(obtener_valor(metrica, "reviews_total")),
    )

    fila_2 = st.columns(4)
    fila_2[0].metric("Precio", formatear_precio(obtener_valor(meta, "price")))
    fila_2[1].metric(
        "Metacritic",
        formatear_numero(obtener_valor(meta, "metacritic_score")),
    )
    fila_2[2].metric(
        "Propietarios estimados",
        str(obtener_valor(meta, "estimated_owners") or "No disponible"),
    )
    fila_2[3].metric(
        "Tiempo promedio",
        formatear_minutos(obtener_valor(meta, "average_playtime_forever")),
    )


# ==========================================================
# PESTAÑAS DEL DASHBOARD
# ==========================================================

pestana_resumen, pestana_sentimiento, pestana_temas, pestana_reviews = st.tabs(
    [
        "Resumen",
        "Sentimiento",
        "Temas y nube",
        "Reseñas y descarga",
    ]
)


# ----------------------------------------------------------
# PESTAÑA 1: RESUMEN
# ----------------------------------------------------------

with pestana_resumen:
    st.subheader("Comparación general de sentimiento")

    distribucion = construir_distribucion_sentimiento(reviews_juego)
    etiquetas_sentimiento = {
        "positive": "Positivo",
        "neutral": "Neutral",
        "negative": "Negativo",
    }
    distribucion["sentiment_label"] = distribucion["sentiment"].map(
        etiquetas_sentimiento
    )

    fig_distribucion = px.bar(
        distribucion,
        x="sentiment_label",
        y="percentage",
        color="source",
        barmode="group",
        text_auto=".1f",
        category_orders={
            "sentiment_label": ["Positivo", "Neutral", "Negativo"]
        },
        labels={
            "sentiment_label": "Sentimiento",
            "percentage": "Porcentaje de reseñas",
            "source": "Fuente",
        },
        title="Distribución de VADER frente a la recomendación de Steam",
    )
    fig_distribucion.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
    aplicar_tema_plotly(fig_distribucion)
    st.plotly_chart(
        fig_distribucion,
        use_container_width=True,
        config={"displaylogo": False},
    )

    col_eval_1, col_eval_2, col_eval_3, col_eval_4 = st.columns(4)
    col_eval_1.metric(
        "Cobertura no neutral",
        formatear_proporcion(obtener_valor(metrica, "coverage_non_neutral")),
    )
    col_eval_2.metric(
        "Accuracy",
        formatear_proporcion(obtener_valor(metrica, "accuracy_non_neutral")),
    )
    col_eval_3.metric(
        "Balanced accuracy",
        formatear_proporcion(
            obtener_valor(metrica, "balanced_accuracy_non_neutral")
        ),
    )
    col_eval_4.metric(
        "Baseline mayoritario",
        formatear_proporcion(
            obtener_valor(metrica, "majority_baseline_non_neutral")
        ),
    )

    mostrar_estado_modelo(metrica)

    st.markdown(
        """
        <div class="tdm-note">
        La accuracy se calcula únicamente sobre reseñas que VADER clasificó
        como positivas o negativas. La cobertura indica qué proporción de la
        muestra quedó disponible para esa evaluación binaria.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------
# PESTAÑA 2: SENTIMIENTO
# ----------------------------------------------------------

with pestana_sentimiento:
    st.subheader("Evaluación detallada de VADER")

    col_matriz, col_metricas = st.columns([1.1, 1])

    with col_matriz:
        matriz_df = construir_matriz_confusion(
            obtener_valor(metrica, "confusion_matrix")
        )

        fig_matriz = go.Figure(
            data=go.Heatmap(
                z=matriz_df.values,
                x=matriz_df.columns.tolist(),
                y=matriz_df.index.tolist(),
                text=matriz_df.values,
                texttemplate="%{text}",
                colorscale="Purples",
                hovertemplate=(
                    "Real: %{y}<br>Predicción: %{x}<br>Reseñas: %{z}<extra></extra>"
                ),
            )
        )
        fig_matriz.update_layout(title="Matriz de confusión")
        aplicar_tema_plotly(fig_matriz, altura=430)
        st.plotly_chart(
            fig_matriz,
            use_container_width=True,
            config={"displaylogo": False},
        )

    with col_metricas:
        tabla_metricas = pd.DataFrame(
            {
                "Métrica": [
                    "Accuracy",
                    "Balanced accuracy",
                    "Precisión positiva",
                    "Recall positivo",
                    "F1 positivo",
                    "Baseline mayoritario",
                    "Cobertura no neutral",
                ],
                "Valor": [
                    formatear_proporcion(
                        obtener_valor(metrica, "accuracy_non_neutral")
                    ),
                    formatear_proporcion(
                        obtener_valor(
                            metrica,
                            "balanced_accuracy_non_neutral",
                        )
                    ),
                    formatear_proporcion(
                        obtener_valor(
                            metrica,
                            "precision_positive_non_neutral",
                        )
                    ),
                    formatear_proporcion(
                        obtener_valor(
                            metrica,
                            "recall_positive_non_neutral",
                        )
                    ),
                    formatear_proporcion(
                        obtener_valor(
                            metrica,
                            "f1_positive_non_neutral",
                        )
                    ),
                    formatear_proporcion(
                        obtener_valor(
                            metrica,
                            "majority_baseline_non_neutral",
                        )
                    ),
                    formatear_proporcion(
                        obtener_valor(metrica, "coverage_non_neutral")
                    ),
                ],
            }
        )

        st.dataframe(
            tabla_metricas,
            hide_index=True,
            use_container_width=True,
        )

        error_vader = obtener_valor(
            metrica,
            "absolute_error_vader_vs_dataset_pct",
        )
        error_muestra = obtener_valor(
            metrica,
            "absolute_error_sample_vs_dataset_pct",
        )

        st.metric(
            "Error absoluto VADER vs. histórico",
            formatear_porcentaje(error_vader),
        )
        st.metric(
            "Error absoluto muestra vs. histórico",
            formatear_porcentaje(error_muestra),
        )


# ----------------------------------------------------------
# PESTAÑA 3: TEMAS Y NUBE
# ----------------------------------------------------------

with pestana_temas:
    st.subheader("Temas dominantes en las reseñas")

    col_tfidf, col_tags = st.columns(2)

    with col_tfidf:
        top_temas = temas_juego.head(10).sort_values("tfidf_score")

        fig_temas = px.bar(
            top_temas,
            x="tfidf_score",
            y="term",
            orientation="h",
            color="ngram_type",
            labels={
                "tfidf_score": "Puntuación TF-IDF",
                "term": "Término",
                "ngram_type": "Tipo",
            },
            title="Top 10 de términos calculados",
        )
        aplicar_tema_plotly(fig_temas, altura=480)
        st.plotly_chart(
            fig_temas,
            use_container_width=True,
            config={"displaylogo": False},
        )

        st.download_button(
            "Descargar temas TF-IDF",
            data=dataframe_a_csv_bytes(temas_juego),
            file_name=(
                f"temas_tfidf_{nombre_archivo_seguro(nombre_juego)}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    with col_tags:
        top_tags = tags_juego.head(10).sort_values("tag_votes")

        fig_tags = px.bar(
            top_tags,
            x="tag_votes",
            y="tag",
            orientation="h",
            labels={
                "tag_votes": "Votos de la comunidad",
                "tag": "Tag",
            },
            title="Top 10 de tags de Steam",
        )
        aplicar_tema_plotly(fig_tags, altura=480)
        st.plotly_chart(
            fig_tags,
            use_container_width=True,
            config={"displaylogo": False},
        )

        st.download_button(
            "Descargar tags de Steam",
            data=dataframe_a_csv_bytes(tags_juego),
            file_name=(
                f"tags_steam_{nombre_archivo_seguro(nombre_juego)}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    st.subheader("Nube de palabras")

    try:
        nube = crear_nube_cacheada(
            int(appid_seleccionado),
            tuple(reviews_juego["text"].astype(str).tolist()),
        )
        st.image(nube, use_container_width=True)
    except ValueError as error:
        st.warning(str(error))

    with st.expander("Ver tabla completa de temas y frecuencia documental"):
        st.dataframe(
            temas_juego[
                [
                    "term",
                    "ngram_type",
                    "tfidf_score",
                    "document_frequency",
                    "document_pct",
                ]
            ],
            hide_index=True,
            use_container_width=True,
        )


# ----------------------------------------------------------
# PESTAÑA 4: RESEÑAS Y DESCARGAS
# ----------------------------------------------------------

with pestana_reviews:
    st.subheader("Explorador de reseñas")

    col_sentimiento, col_recomendacion, col_busqueda = st.columns([1, 1, 2])

    with col_sentimiento:
        filtro_sentimiento = st.selectbox(
            "Sentimiento VADER",
            options=["Todos", "positive", "neutral", "negative"],
        )

    with col_recomendacion:
        filtro_recomendacion = st.selectbox(
            "Recomendación de Steam",
            options=["Todas", "Recomendadas", "No recomendadas"],
        )

    with col_busqueda:
        filtro_texto = st.text_input(
            "Buscar dentro del texto",
            placeholder="Ejemplo: server, story, bugs...",
        )

    reviews_filtradas = filtrar_reviews(
        reviews_juego,
        sentimiento=filtro_sentimiento,
        recomendacion=filtro_recomendacion,
        consulta=filtro_texto,
    )

    st.caption(
        f"Se muestran {len(reviews_filtradas):,} de {len(reviews_juego):,} reseñas."
    )

    columnas_preferidas = [
        "created_at_utc",
        "sentiment_vader",
        "vader_compound",
        "voted_up",
        "vader_correct",
        "votes_up",
        "playtime_at_review_minutes",
        "text",
    ]
    columnas_tabla = [
        columna
        for columna in columnas_preferidas
        if columna in reviews_filtradas.columns
    ]

    st.dataframe(
        reviews_filtradas[columnas_tabla].head(200),
        hide_index=True,
        use_container_width=True,
        height=520,
    )

    col_descarga_reviews, col_descarga_resumen = st.columns(2)

    with col_descarga_reviews:
        st.download_button(
            "Descargar reseñas filtradas",
            data=dataframe_a_csv_bytes(reviews_filtradas),
            file_name=(
                f"reviews_{nombre_archivo_seguro(nombre_juego)}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    with col_descarga_resumen:
        resumen_descarga = {
            clave: valor
            for clave, valor in metrica.to_dict().items()
            if not (isinstance(valor, float) and pd.isna(valor))
        }

        st.download_button(
            "Descargar resumen de métricas",
            data=json.dumps(
                resumen_descarga,
                ensure_ascii=False,
                indent=2,
                default=str,
            ).encode("utf-8"),
            file_name=(
                f"metricas_{nombre_archivo_seguro(nombre_juego)}.json"
            ),
            mime="application/json",
            use_container_width=True,
        )

st.caption(
    "Los gráficos de Plotly pueden descargarse como PNG mediante el icono de cámara de cada gráfica."
)
