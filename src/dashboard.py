from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from wordcloud import WordCloud


# ==========================================================
# RUTAS DEL PROYECTO
# ==========================================================

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_DATASET = RAIZ_PROYECTO / "data" / "processed" / "dataset_limpio.csv"
RUTA_NLP = RAIZ_PROYECTO / "data" / "processed" / "nlp"
RUTA_REVIEWS_ANALIZADAS = RUTA_NLP / "reviews_analizadas.csv"
RUTA_METRICAS = RUTA_NLP / "metricas_sentimiento.json"
RUTA_TEMAS = RUTA_NLP / "temas_tfidf.csv"
RUTA_TAGS = RUTA_NLP / "tags_steam.csv"

ARCHIVOS_NLP = (
    RUTA_REVIEWS_ANALIZADAS,
    RUTA_METRICAS,
    RUTA_TEMAS,
    RUTA_TAGS,
)


# ==========================================================
# COLUMNAS REQUERIDAS
# ==========================================================

COLUMNAS_REVIEWS = {
    "appid",
    "game_name",
    "review_hash",
    "text",
    "voted_up",
    "sentiment_vader",
    "vader_compound",
}

COLUMNAS_METRICAS = {
    "appid",
    "game_name",
    "reviews_total",
    "coverage_non_neutral",
    "accuracy_non_neutral",
    "balanced_accuracy_non_neutral",
    "majority_baseline_non_neutral",
    "confusion_matrix",
}

COLUMNAS_TEMAS = {
    "appid",
    "game_name",
    "term",
    "ngram_type",
    "tfidf_score",
    "document_frequency",
    "document_pct",
}

COLUMNAS_TAGS = {
    "appid",
    "game_name",
    "tag",
    "tag_votes",
    "score_normalized",
}

COLUMNAS_METADATA_DESEADAS = [
    "appid",
    "name",
    "header_image",
    "genres",
    "tags",
    "pct_pos_total",
    "positive",
    "negative",
    "num_reviews_total",
    "metacritic_score",
    "price",
    "estimated_owners",
    "average_playtime_forever",
    "release_date",
]


# ==========================================================
# VALIDACIONES GENERALES
# ==========================================================

def validar_archivos_nlp(
    rutas: Iterable[Path] = ARCHIVOS_NLP,
) -> list[Path]:
    """Devuelve la lista de archivos NLP que no existen."""
    return [ruta for ruta in rutas if not ruta.exists()]


def _validar_columnas(
    df: pd.DataFrame,
    requeridas: set[str],
    nombre: str,
) -> None:
    """Detiene la carga si un archivo carece de columnas esenciales."""
    faltantes = requeridas.difference(df.columns)

    if faltantes:
        raise ValueError(
            f"{nombre} no contiene las columnas: "
            + ", ".join(sorted(faltantes))
        )


def _normalizar_appid(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    """Convierte appid a entero y rechaza valores inválidos."""
    salida = df.copy()
    salida["appid"] = pd.to_numeric(
        salida["appid"],
        errors="raise",
    ).astype("int64")

    if salida.empty:
        raise ValueError(f"{nombre} no contiene registros.")

    return salida


def _convertir_bool_nullable(valor: Any) -> Any:
    """Convierte valores CSV a booleanos de pandas conservando nulos."""
    if pd.isna(valor):
        return pd.NA

    if isinstance(valor, bool):
        return valor

    texto = str(valor).strip().lower()

    if texto in {"true", "1", "yes", "positive", "recommended"}:
        return True

    if texto in {"false", "0", "no", "negative", "not recommended"}:
        return False

    return pd.NA


# ==========================================================
# CARGA DE RESULTADOS NLP Y METADATA
# ==========================================================

def cargar_resultados_nlp(
    ruta_reviews: Path = RUTA_REVIEWS_ANALIZADAS,
    ruta_metricas: Path = RUTA_METRICAS,
    ruta_temas: Path = RUTA_TEMAS,
    ruta_tags: Path = RUTA_TAGS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Carga y valida los cuatro archivos generados por ``src.nlp``."""
    faltantes = validar_archivos_nlp(
        (
            ruta_reviews,
            ruta_metricas,
            ruta_temas,
            ruta_tags,
        )
    )

    if faltantes:
        raise FileNotFoundError(
            "Faltan resultados NLP: "
            + ", ".join(str(ruta) for ruta in faltantes)
        )

    reviews = pd.read_csv(ruta_reviews, low_memory=False)
    temas = pd.read_csv(ruta_temas)
    tags = pd.read_csv(ruta_tags)

    with ruta_metricas.open("r", encoding="utf-8") as archivo:
        contenido_metricas = json.load(archivo)

    if not isinstance(contenido_metricas, list):
        raise ValueError(
            "metricas_sentimiento.json debe contener una lista JSON."
        )

    metricas = pd.DataFrame(contenido_metricas)

    _validar_columnas(reviews, COLUMNAS_REVIEWS, "reviews_analizadas.csv")
    _validar_columnas(metricas, COLUMNAS_METRICAS, "metricas_sentimiento.json")
    _validar_columnas(temas, COLUMNAS_TEMAS, "temas_tfidf.csv")
    _validar_columnas(tags, COLUMNAS_TAGS, "tags_steam.csv")

    reviews = _normalizar_appid(reviews, "reviews_analizadas.csv")
    metricas = _normalizar_appid(metricas, "metricas_sentimiento.json")
    temas = _normalizar_appid(temas, "temas_tfidf.csv")
    tags = _normalizar_appid(tags, "tags_steam.csv")

    if metricas["appid"].duplicated().any():
        raise ValueError("Existe más de una fila de métricas para un appid.")

    reviews["text"] = reviews["text"].fillna("").astype(str)
    reviews["sentiment_vader"] = (
        reviews["sentiment_vader"].fillna("unknown").astype(str).str.lower()
    )
    reviews["voted_up"] = reviews["voted_up"].map(
        _convertir_bool_nullable
    ).astype("boolean")

    if "vader_correct" in reviews.columns:
        reviews["vader_correct"] = reviews["vader_correct"].map(
            _convertir_bool_nullable
        ).astype("boolean")

    return reviews, metricas, temas, tags


def cargar_metadata_catalogo(
    appids: Iterable[int] | None = None,
    ruta_dataset: Path = RUTA_DATASET,
) -> pd.DataFrame:
    """Carga únicamente la metadata necesaria del dataset principal."""
    if not ruta_dataset.exists():
        raise FileNotFoundError(f"No existe el dataset: {ruta_dataset}")

    encabezados = pd.read_csv(ruta_dataset, nrows=0).columns.tolist()
    columnas = [
        columna
        for columna in COLUMNAS_METADATA_DESEADAS
        if columna in encabezados
    ]

    if "appid" not in columnas or "name" not in columnas:
        raise ValueError("El dataset no contiene appid y name.")

    metadata = pd.read_csv(
        ruta_dataset,
        usecols=columnas,
        low_memory=False,
    )
    metadata = _normalizar_appid(metadata, "dataset_limpio.csv")
    metadata = metadata.drop_duplicates("appid", keep="first")

    if appids is not None:
        objetivos = {int(appid) for appid in appids}
        metadata = metadata[metadata["appid"].isin(objetivos)].copy()

        faltantes = objetivos.difference(metadata["appid"].tolist())
        if faltantes:
            raise ValueError(
                "No se encontró metadata para los appids: "
                + ", ".join(map(str, sorted(faltantes)))
            )

    return metadata.reset_index(drop=True)


def obtener_appids_disponibles(
    metadata: pd.DataFrame,
    metricas: pd.DataFrame,
    reviews: pd.DataFrame,
) -> list[int]:
    """Obtiene la intersección de juegos presentes en todas las fuentes."""
    disponibles = (
        set(metadata["appid"])
        & set(metricas["appid"])
        & set(reviews["appid"])
    )
    return sorted(int(appid) for appid in disponibles)


def obtener_datos_juego(
    appid: int,
    metadata: pd.DataFrame,
    reviews: pd.DataFrame,
    metricas: pd.DataFrame,
    temas: pd.DataFrame,
    tags: pd.DataFrame,
) -> dict[str, Any]:
    """Agrupa todos los datos del videojuego seleccionado."""
    appid = int(appid)

    metadata_juego = metadata[metadata["appid"] == appid]
    metricas_juego = metricas[metricas["appid"] == appid]
    reviews_juego = reviews[reviews["appid"] == appid].copy()
    temas_juego = temas[temas["appid"] == appid].copy()
    tags_juego = tags[tags["appid"] == appid].copy()

    if metadata_juego.empty:
        raise KeyError(f"No existe metadata para appid {appid}.")

    if metricas_juego.empty:
        raise KeyError(f"No existen métricas para appid {appid}.")

    if reviews_juego.empty:
        raise KeyError(f"No existen reseñas para appid {appid}.")

    return {
        "metadata": metadata_juego.iloc[0],
        "metricas": metricas_juego.iloc[0],
        "reviews": reviews_juego.reset_index(drop=True),
        "temas": temas_juego.sort_values(
            "tfidf_score",
            ascending=False,
        ).reset_index(drop=True),
        "tags": tags_juego.sort_values(
            "tag_votes",
            ascending=False,
        ).reset_index(drop=True),
    }


# ==========================================================
# TRANSFORMACIONES PARA VISUALIZACIÓN
# ==========================================================

def construir_distribucion_sentimiento(
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    """Construye una tabla comparable entre VADER y Steam."""
    total = len(reviews)
    if total == 0:
        return pd.DataFrame(
            columns=["source", "sentiment", "count", "percentage"]
        )

    orden = ("positive", "neutral", "negative")
    conteo_vader = reviews["sentiment_vader"].value_counts()

    positivas_steam = int(reviews["voted_up"].fillna(False).sum())
    negativas_steam = int(reviews["voted_up"].notna().sum()) - positivas_steam

    conteo_steam = {
        "positive": positivas_steam,
        "neutral": 0,
        "negative": negativas_steam,
    }

    filas: list[dict[str, Any]] = []

    for fuente, conteos in (
        ("VADER", conteo_vader),
        ("Steam", conteo_steam),
    ):
        for sentimiento in orden:
            cantidad = int(conteos.get(sentimiento, 0))
            filas.append(
                {
                    "source": fuente,
                    "sentiment": sentimiento,
                    "count": cantidad,
                    "percentage": round(100 * cantidad / total, 4),
                }
            )

    return pd.DataFrame(filas)


def _normalizar_matriz(valor: Any) -> dict[str, int]:
    """Convierte la matriz almacenada como dict o texto a un diccionario."""
    if isinstance(valor, dict):
        matriz = valor
    elif isinstance(valor, str):
        texto = valor.strip()
        try:
            matriz = json.loads(texto)
        except json.JSONDecodeError:
            matriz = ast.literal_eval(texto)
    else:
        raise ValueError("La matriz de confusión tiene un formato inválido.")

    claves = {
        "true_negative",
        "false_positive",
        "false_negative",
        "true_positive",
    }

    faltantes = claves.difference(matriz)
    if faltantes:
        raise ValueError(
            "Faltan valores en la matriz de confusión: "
            + ", ".join(sorted(faltantes))
        )

    return {clave: int(matriz[clave]) for clave in claves}


def construir_matriz_confusion(valor: Any) -> pd.DataFrame:
    """Construye una matriz 2 x 2 lista para Plotly o Streamlit."""
    matriz = _normalizar_matriz(valor)

    return pd.DataFrame(
        [
            [matriz["true_negative"], matriz["false_positive"]],
            [matriz["false_negative"], matriz["true_positive"]],
        ],
        index=["Steam negativa", "Steam positiva"],
        columns=["VADER negativa", "VADER positiva"],
    )


def filtrar_reviews(
    reviews: pd.DataFrame,
    sentimiento: str = "Todos",
    recomendacion: str = "Todas",
    consulta: str = "",
) -> pd.DataFrame:
    """Aplica los filtros interactivos de la pestaña de reseñas."""
    salida = reviews.copy()

    if sentimiento != "Todos":
        salida = salida[
            salida["sentiment_vader"].str.lower()
            == sentimiento.lower()
        ]

    if recomendacion == "Recomendadas":
        salida = salida[salida["voted_up"] == True]  # noqa: E712
    elif recomendacion == "No recomendadas":
        salida = salida[salida["voted_up"] == False]  # noqa: E712

    consulta = consulta.strip()
    if consulta:
        salida = salida[
            salida["text"].str.contains(
                consulta,
                case=False,
                regex=False,
                na=False,
            )
        ]

    return salida.reset_index(drop=True)


def generar_nube_palabras(
    textos: Iterable[str],
    ancho: int = 1200,
    alto: int = 600,
) -> Any:
    """Genera una imagen WordCloud a partir de reseñas individuales."""
    corpus = " ".join(
        str(texto).strip()
        for texto in textos
        if str(texto).strip()
    )

    if not corpus:
        raise ValueError("No existe texto para generar la nube de palabras.")

    stopwords_dominio = {
        "game",
        "games",
        "play",
        "played",
        "playing",
        "steam",
        "really",
        "just",
        "like",
        "good",
        "great",
    }

    nube = WordCloud(
        width=ancho,
        height=alto,
        background_color="#0b0e1a",
        colormap="plasma",
        stopwords=stopwords_dominio,
        collocations=True,
        max_words=120,
        random_state=42,
    )

    return nube.generate(corpus).to_image()


# ==========================================================
# FORMATO Y DESCARGAS
# ==========================================================

def parsear_lista_texto(valor: Any) -> list[str]:
    """Convierte listas serializadas o texto separado por comas."""
    if valor is None or (not isinstance(valor, (list, tuple)) and pd.isna(valor)):
        return []

    if isinstance(valor, (list, tuple)):
        return [str(item).strip() for item in valor if str(item).strip()]

    texto = str(valor).strip()
    if not texto:
        return []

    try:
        contenido = ast.literal_eval(texto)
        if isinstance(contenido, (list, tuple)):
            return [
                str(item).strip()
                for item in contenido
                if str(item).strip()
            ]
    except (ValueError, SyntaxError):
        pass

    return [
        parte.strip().strip("[]'\"")
        for parte in texto.split(",")
        if parte.strip().strip("[]'\"")
    ]


def formatear_numero(valor: Any, decimales: int = 0) -> str:
    """Da formato legible a valores numéricos y conserva datos ausentes."""
    if valor is None or pd.isna(valor):
        return "No disponible"

    numero = float(valor)
    if decimales == 0:
        return f"{numero:,.0f}"
    return f"{numero:,.{decimales}f}"


def formatear_porcentaje(valor: Any, decimales: int = 1) -> str:
    """Muestra porcentajes o un texto neutral cuando faltan."""
    if valor is None or pd.isna(valor):
        return "No disponible"
    return f"{float(valor):.{decimales}f}%"


def formatear_proporcion(valor: Any, decimales: int = 1) -> str:
    """Convierte una proporción de 0 a 1 en porcentaje."""
    if valor is None or pd.isna(valor):
        return "No disponible"
    return f"{100 * float(valor):.{decimales}f}%"


def formatear_precio(valor: Any) -> str:
    """Presenta el precio del dataset sin inventar conversión de moneda."""
    if valor is None or pd.isna(valor):
        return "No disponible"

    precio = float(valor)
    if precio == 0:
        return "Gratis"
    return f"US${precio:,.2f}"


def formatear_minutos(valor: Any) -> str:
    """Convierte minutos de juego a una expresión en horas."""
    if valor is None or pd.isna(valor):
        return "No disponible"

    minutos = float(valor)
    return f"{minutos / 60:,.1f} h"


def dataframe_a_csv_bytes(df: pd.DataFrame) -> bytes:
    """Genera CSV con BOM para abrir correctamente en Excel."""
    return df.to_csv(index=False).encode("utf-8-sig")


def nombre_archivo_seguro(nombre: str) -> str:
    """Crea un nombre de archivo portable a partir del nombre del juego."""
    limpio = re.sub(r"[^a-zA-Z0-9_-]+", "_", nombre.strip())
    return limpio.strip("_").lower() or "juego"
