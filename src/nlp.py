from __future__ import annotations

import argparse
import ast
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Iterable

import nltk
import numpy as np
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

try:
    from vaderSentiment.vaderSentiment import (
        SentimentIntensityAnalyzer as VaderStandalone,
    )
except ImportError:
    VaderStandalone = None


# ==========================================================
# RUTAS Y PARÁMETROS DEL PROYECTO
# ==========================================================

RAIZ = Path(__file__).resolve().parents[1]

# Reseñas individuales generadas durante el Bloque 1.
RUTA_REVIEWS = RAIZ / "data" / "reviews_extra.json"

# Dataset principal e inmutable del equipo.
RUTA_DATASET = (
    RAIZ
    / "data"
    / "processed"
    / "dataset_limpio.csv"
)

# Catálogo oficial de los 10 videojuegos.
RUTA_CATALOGO = (
    RAIZ
    / "config"
    / "catalogo.json"
)

# Carpeta para guardar los resultados procesados.
RUTA_SALIDA = (
    RAIZ
    / "data"
    / "processed"
    / "nlp"
)


# Umbrales estándar utilizados por VADER.
UMBRAL_POSITIVO = 0.05
UMBRAL_NEGATIVO = -0.05


# Palabras demasiado generales dentro del dominio.
#
# Se eliminan únicamente durante TF-IDF.
# No se eliminan para el análisis VADER.
STOPWORDS_DOMINIO = {
    "game",
    "games",
    "gaming",
    "play",
    "played",
    "playing",
    "player",
    "players",
    "steam",
    "review",
    "reviews",
    "hour",
    "hours",
    "time",
    "times",
    "really",
    "just",
    "like",
    "good",
    "great",
    "bad",
    "recommend",
    "recommended",
}

STOPWORDS_TFIDF = sorted(
    set(ENGLISH_STOP_WORDS)
    | STOPWORDS_DOMINIO
)


# ==========================================================
# CARGA Y VALIDACIÓN DE DATOS
# ==========================================================

def cargar_appids_catalogo(
    ruta: Path = RUTA_CATALOGO,
) -> list[int]:
    """
    Obtiene los appids activos del catálogo oficial.

    Esto evita escribir manualmente los videojuegos
    dentro del código NLP.
    """
    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        datos = json.load(archivo)

    appids = [
        int(juego["appid"])
        for juego in datos.get("juegos", [])
        if juego.get("activo", True)
    ]

    if not appids:
        raise ValueError(
            "El catálogo no contiene juegos activos."
        )

    return appids


def _convertir_bool(
    valor: Any,
) -> bool:
    """
    Normaliza las etiquetas positivas y negativas
    recuperadas por el scraper.
    """
    if isinstance(
        valor,
        (bool, np.bool_),
    ):
        return bool(valor)

    texto = str(valor).strip().lower()

    if texto in {
        "true",
        "1",
        "positive",
        "recommended",
    }:
        return True

    if texto in {
        "false",
        "0",
        "negative",
        "not recommended",
    }:
        return False

    raise ValueError(
        f"Valor booleano no reconocido: {valor!r}"
    )


def cargar_reviews(
    ruta: Path = RUTA_REVIEWS,
) -> pd.DataFrame:
    """
    Carga reviews_extra.json.

    También comprueba que existan todos los campos
    indispensables para NLP y elimina duplicados.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe {ruta}. "
            "Ejecuta primero: python -m src.scraper"
        )

    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        registros = json.load(archivo)

    df = pd.DataFrame(registros)

    columnas_requeridas = {
        "appid",
        "game_name",
        "review_id",
        "review_hash",
        "text",
        "language",
        "voted_up",
    }

    faltantes = columnas_requeridas.difference(
        df.columns
    )

    if faltantes:
        raise ValueError(
            "Faltan campos en reviews_extra.json: "
            + ", ".join(sorted(faltantes))
        )

    # Normalización de tipos.
    df["appid"] = pd.to_numeric(
        df["appid"],
        errors="raise",
    ).astype("int64")

    df["text"] = (
        df["text"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["voted_up"] = (
        df["voted_up"]
        .map(_convertir_bool)
        .astype("boolean")
    )

    # Eliminar textos vacíos y reseñas duplicadas.
    df = df[df["text"].ne("")]

    df = df.drop_duplicates(
        subset="review_hash",
        keep="last",
    )

    if df.empty:
        raise ValueError(
            "No quedaron reseñas válidas."
        )

    return df.reset_index(drop=True)


def cargar_metadata(
    appids: Iterable[int],
    ruta: Path = RUTA_DATASET,
) -> pd.DataFrame:
    """
    Lee solamente las columnas del dataset necesarias
    para el análisis NLP.

    No modifica dataset_limpio.csv.
    """
    objetivos = {
        int(appid)
        for appid in appids
    }

    df = pd.read_csv(
        ruta,
        usecols=[
            "appid",
            "name",
            "tags",
            "pct_pos_total",
        ],
    )

    df["appid"] = pd.to_numeric(
        df["appid"],
        errors="coerce",
    )

    df = df[
        df["appid"].isin(objetivos)
    ].copy()

    df["appid"] = df["appid"].astype(
        "int64"
    )

    df = df.drop_duplicates(
        subset="appid",
        keep="first",
    )

    encontrados = set(
        df["appid"].tolist()
    )

    faltantes = objetivos.difference(
        encontrados
    )

    if faltantes:
        raise ValueError(
            "Appids ausentes en "
            "dataset_limpio.csv: "
            + ", ".join(
                map(
                    str,
                    sorted(faltantes),
                )
            )
        )

    return df.reset_index(drop=True)


# ==========================================================
# VADER: SENTIMIENTO Y EVALUACIÓN
# ==========================================================

def crear_analizador_vader() -> Any:
    """
    Crea el analizador de sentimiento.

    Se utiliza NLTK VADER como implementación principal.

    Si falta vader_lexicon:
    1. Se intenta descargar automáticamente.
    2. Si la descarga falla, se utiliza vaderSentiment
       como respaldo, siempre que esté instalado.
    """
    try:
        return SentimentIntensityAnalyzer()

    except LookupError as error_nltk:
        logging.info(
            "Descargando vader_lexicon de NLTK..."
        )

        descargado = nltk.download(
            "vader_lexicon",
            quiet=True,
        )

        if descargado:
            try:
                return SentimentIntensityAnalyzer()
            except LookupError:
                pass

        if VaderStandalone is not None:
            logging.warning(
                "Se utilizará vaderSentiment "
                "como respaldo."
            )

            return VaderStandalone()

        raise RuntimeError(
            "No fue posible iniciar VADER. "
            "Ejecuta: "
            "python -m nltk.downloader "
            "vader_lexicon"
        ) from error_nltk


def clasificar_compound(
    compound: float,
) -> str:
    """
    Clasifica el compound de VADER.

    Retorna:
        positive: compound >= 0.05
        negative: compound <= -0.05
        neutral: cualquier valor intermedio
    """
    if compound >= UMBRAL_POSITIVO:
        return "positive"

    if compound <= UMBRAL_NEGATIVO:
        return "negative"

    return "neutral"


def _prediccion_binaria(
    compound: float,
) -> bool | None:
    """
    Convierte el resultado de VADER a una etiqueta binaria.

    Las reseñas neutrales no se fuerzan artificialmente
    como positivas o negativas. Se dejan como None.
    """
    if compound >= UMBRAL_POSITIVO:
        return True

    if compound <= UMBRAL_NEGATIVO:
        return False

    return None


def analizar_sentimientos(
    reviews: pd.DataFrame,
    analizador: Any | None = None,
) -> pd.DataFrame:
    """
    Aplica VADER al texto original de cada reseña.

    No se eliminan mayúsculas, puntuación o intensificadores,
    porque esos elementos son considerados por VADER.
    """
    analizador = (
        analizador
        or crear_analizador_vader()
    )

    salida = reviews.copy()

    puntuaciones = [
        analizador.polarity_scores(texto)
        for texto in (
            salida["text"]
            .fillna("")
            .astype(str)
        )
    ]

    salida["vader_negative"] = [
        float(puntuacion["neg"])
        for puntuacion in puntuaciones
    ]

    salida["vader_neutral"] = [
        float(puntuacion["neu"])
        for puntuacion in puntuaciones
    ]

    salida["vader_positive"] = [
        float(puntuacion["pos"])
        for puntuacion in puntuaciones
    ]

    salida["vader_compound"] = [
        float(puntuacion["compound"])
        for puntuacion in puntuaciones
    ]

    salida["sentiment_vader"] = (
        salida["vader_compound"]
        .map(clasificar_compound)
    )

    salida["vader_prediction_binary"] = (
        salida["vader_compound"]
        .map(_prediccion_binaria)
        .astype("boolean")
    )

    salida["vader_evaluable"] = (
        salida["vader_prediction_binary"]
        .notna()
    )

    # Esta columna indica si VADER coincide con la
    # recomendación original recuperada desde Steam.
    salida["vader_correct"] = (
        salida["vader_prediction_binary"]
        == salida["voted_up"]
    ).astype("boolean")

    return salida


def evaluar_sentimiento(
    df: pd.DataFrame,
    pct_pos_total_dataset: float | None = None,
) -> dict[str, Any]:
    """
    Calcula las métricas de evaluación.

    La evaluación binaria se realiza solo sobre reseñas
    clasificadas como positivas o negativas por VADER.

    Las neutrales se reportan mediante:
        coverage_non_neutral

    Esto evita convertirlas arbitrariamente en negativas.
    """
    total = len(df)

    if total == 0:
        raise ValueError(
            "No hay reseñas para evaluar."
        )

    steam_positivas = int(
        df["voted_up"].sum()
    )

    conteos_vader = (
        df["sentiment_vader"]
        .value_counts()
    )

    vader_positivas = int(
        conteos_vader.get(
            "positive",
            0,
        )
    )

    vader_neutrales = int(
        conteos_vader.get(
            "neutral",
            0,
        )
    )

    vader_negativas = int(
        conteos_vader.get(
            "negative",
            0,
        )
    )

    evaluables = df[
        df["vader_prediction_binary"].notna()
    ].copy()

    metricas: dict[str, Any] = {
        "reviews_total": total,

        "steam_positive": steam_positivas,
        "steam_negative": (
            total - steam_positivas
        ),
        "steam_positive_pct_sample": round(
            100 * steam_positivas / total,
            4,
        ),

        "vader_positive": vader_positivas,
        "vader_neutral": vader_neutrales,
        "vader_negative": vader_negativas,

        "vader_positive_pct_all": round(
            100 * vader_positivas / total,
            4,
        ),
        "vader_neutral_pct_all": round(
            100 * vader_neutrales / total,
            4,
        ),
        "vader_negative_pct_all": round(
            100 * vader_negativas / total,
            4,
        ),

        "evaluable_reviews": len(evaluables),
        "coverage_non_neutral": round(
            len(evaluables) / total,
            6,
        ),

        "accuracy_non_neutral": None,
        "balanced_accuracy_non_neutral": None,
        "precision_positive_non_neutral": None,
        "recall_positive_non_neutral": None,
        "f1_positive_non_neutral": None,
        "majority_baseline_non_neutral": None,

        "confusion_matrix": {
            "true_negative": 0,
            "false_positive": 0,
            "false_negative": 0,
            "true_positive": 0,
        },
    }

    # Comparación agregada contra el porcentaje histórico
    # contenido en dataset_limpio.csv.
    if (
        pct_pos_total_dataset is not None
        and not pd.isna(
            pct_pos_total_dataset
        )
    ):
        pct_dataset = float(
            pct_pos_total_dataset
        )

        metricas[
            "steam_positive_pct_dataset"
        ] = round(
            pct_dataset,
            4,
        )

        metricas[
            "absolute_error_vader_vs_dataset_pct"
        ] = round(
            abs(
                metricas[
                    "vader_positive_pct_all"
                ]
                - pct_dataset
            ),
            4,
        )

        metricas[
            "absolute_error_sample_vs_dataset_pct"
        ] = round(
            abs(
                metricas[
                    "steam_positive_pct_sample"
                ]
                - pct_dataset
            ),
            4,
        )

    # Si todas las reseñas resultaron neutrales,
    # no es posible calcular métricas binarias.
    if evaluables.empty:
        return metricas

    y_true = (
        evaluables["voted_up"]
        .astype(bool)
        .to_numpy()
    )

    y_pred = (
        evaluables[
            "vader_prediction_binary"
        ]
        .astype(bool)
        .to_numpy()
    )

    matriz = confusion_matrix(
        y_true,
        y_pred,
        labels=[
            False,
            True,
        ],
    )

    tn, fp, fn, tp = matriz.ravel()

    conteos_clase = np.bincount(
        y_true.astype(int),
        minlength=2,
    )

    baseline = (
        conteos_clase.max()
        / len(y_true)
    )

    metricas.update(
        {
            "accuracy_non_neutral": round(
                float(
                    accuracy_score(
                        y_true,
                        y_pred,
                    )
                ),
                6,
            ),

            "balanced_accuracy_non_neutral": round(
                float(
                    balanced_accuracy_score(
                        y_true,
                        y_pred,
                    )
                ),
                6,
            ),

            "precision_positive_non_neutral": round(
                float(
                    precision_score(
                        y_true,
                        y_pred,
                        zero_division=0,
                    )
                ),
                6,
            ),

            "recall_positive_non_neutral": round(
                float(
                    recall_score(
                        y_true,
                        y_pred,
                        zero_division=0,
                    )
                ),
                6,
            ),

            "f1_positive_non_neutral": round(
                float(
                    f1_score(
                        y_true,
                        y_pred,
                        zero_division=0,
                    )
                ),
                6,
            ),

            "majority_baseline_non_neutral": round(
                float(baseline),
                6,
            ),

            "confusion_matrix": {
                "true_negative": int(tn),
                "false_positive": int(fp),
                "false_negative": int(fn),
                "true_positive": int(tp),
            },
        }
    )

    return metricas


# ==========================================================
# TF-IDF Y TAGS
# ==========================================================

def extraer_temas_tfidf(
    textos: Iterable[str],
    top_n: int = 15,
    min_df: int | None = None,
) -> pd.DataFrame:
    """
    Extrae unigramas y bigramas relevantes.

    Cada reseña representa un documento independiente.
    """
    documentos: list[str] = []

    for texto in textos:
        # Eliminar URLs para evitar que aparezcan como temas.
        limpio = re.sub(
            r"https?://\S+|www\.\S+",
            " ",
            str(texto),
        )

        limpio = re.sub(
            r"\s+",
            " ",
            limpio,
        ).strip()

        if limpio:
            documentos.append(limpio)

    if len(documentos) < 2:
        raise ValueError(
            "TF-IDF requiere al menos dos reseñas."
        )

    # Ajustar min_df según el tamaño del corpus.
    if min_df is None:
        if len(documentos) >= 200:
            min_df = 3
        elif len(documentos) >= 20:
            min_df = 2
        else:
            min_df = 1

    vectorizador = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words=STOPWORDS_TFIDF,

        # Unigramas y bigramas.
        ngram_range=(1, 2),

        min_df=min_df,

        # Eliminar términos presentes en casi
        # todas las reseñas.
        max_df=(
            0.90
            if len(documentos) >= 10
            else 1.0
        ),

        max_features=10_000,
        sublinear_tf=True,

        # Palabras de al menos tres caracteres.
        token_pattern=(
            r"(?u)\b"
            r"[a-zA-Z]"
            r"[a-zA-Z']{2,}"
            r"\b"
        ),
    )

    matriz = vectorizador.fit_transform(
        documentos
    )

    terminos = (
        vectorizador
        .get_feature_names_out()
    )

    # Promedio de TF-IDF por término.
    puntuaciones_medias = np.asarray(
        matriz.mean(axis=0)
    ).ravel()

    # Número de documentos donde aparece el término.
    frecuencias = np.asarray(
        (matriz > 0).sum(axis=0)
    ).ravel()

    indices_ordenados = np.argsort(
        puntuaciones_medias
    )[::-1][:top_n]

    puntuacion_maxima = (
        float(
            puntuaciones_medias[
                indices_ordenados[0]
            ]
        )
        if len(indices_ordenados)
        else 0.0
    )

    filas = []

    for indice in indices_ordenados:
        termino = str(
            terminos[indice]
        )

        puntuacion = float(
            puntuaciones_medias[indice]
        )

        frecuencia = int(
            frecuencias[indice]
        )

        filas.append(
            {
                "term": termino,

                "ngram_type": (
                    "bigram"
                    if " " in termino
                    else "unigram"
                ),

                "tfidf_score": round(
                    puntuacion,
                    8,
                ),

                "score_normalized": round(
                    puntuacion
                    / puntuacion_maxima,
                    6,
                )
                if puntuacion_maxima
                else 0.0,

                "document_frequency": frecuencia,

                "document_pct": round(
                    100
                    * frecuencia
                    / len(documentos),
                    4,
                ),
            }
        )

    return pd.DataFrame(filas)


def parsear_tags(
    valor: Any,
    top_n: int = 15,
) -> pd.DataFrame:
    """
    Convierte la columna tags del dataset a una tabla.

    Se utiliza ast.literal_eval en lugar de eval
    para interpretar el diccionario de forma segura.
    """
    if valor is None or (
        not isinstance(
            valor,
            (
                dict,
                list,
                tuple,
            ),
        )
        and pd.isna(valor)
    ):
        return pd.DataFrame(
            columns=[
                "tag",
                "tag_votes",
                "score_normalized",
            ]
        )

    contenido = valor

    if isinstance(
        valor,
        str,
    ):
        try:
            contenido = ast.literal_eval(
                valor.strip()
            )

        except (
            ValueError,
            SyntaxError,
        ):
            contenido = [
                elemento.strip()
                for elemento in valor.split(",")
                if elemento.strip()
            ]

    if isinstance(
        contenido,
        dict,
    ):
        elementos = [
            (
                str(tag),
                float(votos),
            )
            for tag, votos
            in contenido.items()
        ]

    elif isinstance(
        contenido,
        (
            list,
            tuple,
        ),
    ):
        elementos = [
            (
                str(tag),
                float(
                    len(contenido)
                    - posicion
                ),
            )
            for posicion, tag
            in enumerate(contenido)
        ]

    else:
        elementos = []

    elementos = sorted(
        elementos,
        key=lambda elemento: elemento[1],
        reverse=True,
    )[:top_n]

    valor_maximo = (
        elementos[0][1]
        if elementos
        else 0.0
    )

    filas = []

    for tag, votos in elementos:
        filas.append(
            {
                "tag": tag,

                "tag_votes": (
                    int(votos)
                    if votos.is_integer()
                    else votos
                ),

                "score_normalized": round(
                    votos / valor_maximo,
                    6,
                )
                if valor_maximo
                else 0.0,
            }
        )

    return pd.DataFrame(filas)


# ==========================================================
# PIPELINE Y SALIDAS PARA STREAMLIT
# ==========================================================

def procesar_nlp(
    reviews: pd.DataFrame,
    metadata: pd.DataFrame,
    top_temas: int = 15,
    analizador: Any | None = None,
) -> tuple[
    pd.DataFrame,
    list[dict[str, Any]],
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Procesa sentimiento, métricas, temas y tags
    para todos los juegos solicitados.
    """
    analizador = (
        analizador
        or crear_analizador_vader()
    )

    reviews_analizadas = analizar_sentimientos(
        reviews,
        analizador,
    )

    metadata_por_appid = metadata.set_index(
        "appid",
        drop=False,
    )

    nombre_motor = (
        f"{analizador.__class__.__module__}."
        f"{analizador.__class__.__name__}"
    )

    metricas: list[
        dict[str, Any]
    ] = []

    temas_lista: list[
        pd.DataFrame
    ] = []

    tags_lista: list[
        pd.DataFrame
    ] = []

    for appid, grupo in (
        reviews_analizadas
        .groupby(
            "appid",
            sort=True,
        )
    ):
        fila_metadata = (
            metadata_por_appid
            .loc[appid]
        )

        nombre_juego = str(
            fila_metadata["name"]
        )

        logging.info(
            "Procesando %s (%s)...",
            nombre_juego,
            appid,
        )

        # -----------------------------
        # Métricas de sentimiento
        # -----------------------------

        resumen = evaluar_sentimiento(
            grupo,
            fila_metadata.get(
                "pct_pos_total"
            ),
        )

        resumen.update(
            {
                "appid": int(appid),
                "game_name": nombre_juego,
                "vader_engine": nombre_motor,
            }
        )

        metricas.append(resumen)

        # -----------------------------
        # Temas obtenidos con TF-IDF
        # -----------------------------

        temas = extraer_temas_tfidf(
            grupo["text"],
            top_n=top_temas,
        )

        temas.insert(
            0,
            "game_name",
            nombre_juego,
        )

        temas.insert(
            0,
            "appid",
            int(appid),
        )

        temas_lista.append(temas)

        # -----------------------------
        # Tags oficiales del dataset
        # -----------------------------

        tags = parsear_tags(
            fila_metadata.get("tags"),
            top_n=top_temas,
        )

        tags.insert(
            0,
            "game_name",
            nombre_juego,
        )

        tags.insert(
            0,
            "appid",
            int(appid),
        )

        tags_lista.append(tags)

    return (
        reviews_analizadas,
        metricas,
        pd.concat(
            temas_lista,
            ignore_index=True,
        ),
        pd.concat(
            tags_lista,
            ignore_index=True,
        ),
    )


def guardar_resultados(
    reviews: pd.DataFrame,
    metricas: list[dict[str, Any]],
    temas: pd.DataFrame,
    tags: pd.DataFrame,
) -> None:
    """
    Genera los archivos que utilizará
    pages/analisis.py.
    """
    RUTA_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    reviews.to_csv(
        RUTA_SALIDA
        / "reviews_analizadas.csv",
        index=False,
        encoding="utf-8",
    )

    temas.to_csv(
        RUTA_SALIDA
        / "temas_tfidf.csv",
        index=False,
        encoding="utf-8",
    )

    tags.to_csv(
        RUTA_SALIDA
        / "tags_steam.csv",
        index=False,
        encoding="utf-8",
    )

    with (
        RUTA_SALIDA
        / "metricas_sentimiento.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            metricas,
            archivo,
            ensure_ascii=False,
            indent=2,
        )


def main() -> int:
    """
    Permite ejecutar todo el pipeline con:

        python -m src.nlp
    """
    parser = argparse.ArgumentParser(
        description=(
            "Pipeline NLP de "
            "The Data Machine"
        )
    )

    parser.add_argument(
        "--appid",
        type=int,
        nargs="+",
        help=(
            "Procesa únicamente los appids "
            "indicados."
        ),
    )

    parser.add_argument(
        "--top-temas",
        type=int,
        default=15,
        help=(
            "Número de términos y tags "
            "por videojuego."
        ),
    )

    parser.add_argument(
        "--preparar-vader",
        action="store_true",
        help=(
            "Verifica o descarga el léxico "
            "de VADER."
        ),
    )

    argumentos = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(
                sys.stdout
            )
        ],
        force=True,
    )

    try:
        if argumentos.top_temas <= 0:
            raise ValueError(
                "--top-temas debe ser "
                "mayor que cero."
            )

        analizador = crear_analizador_vader()

        if argumentos.preparar_vader:
            print(
                "RESULTADO: "
                "VADER ESTÁ DISPONIBLE."
            )
            return 0

        appids_catalogo = cargar_appids_catalogo()

        appids_objetivo = (
            argumentos.appid
            or appids_catalogo
        )

        appids_no_permitidos = (
            set(appids_objetivo)
            .difference(
                appids_catalogo
            )
        )

        if appids_no_permitidos:
            raise ValueError(
                "Appids no activos en "
                "el catálogo: "
                + ", ".join(
                    map(
                        str,
                        sorted(
                            appids_no_permitidos
                        ),
                    )
                )
            )

        reviews = cargar_reviews()

        reviews = reviews[
            reviews["appid"].isin(
                appids_objetivo
            )
        ].copy()

        if reviews.empty:
            raise ValueError(
                "No hay reseñas para "
                "los appids solicitados."
            )

        metadata = cargar_metadata(
            appids_objetivo
        )

        resultados = procesar_nlp(
            reviews=reviews,
            metadata=metadata,
            top_temas=(
                argumentos.top_temas
            ),
            analizador=analizador,
        )

        guardar_resultados(
            *resultados
        )

        print("\nRESUMEN")

        for fila in resultados[1]:
            print(
                f"{fila['appid']} | "
                f"{fila['game_name']} | "
                f"reviews="
                f"{fila['reviews_total']} | "
                f"cobertura="
                f"{fila['coverage_non_neutral']:.4f} | "
                f"accuracy="
                f"{fila['accuracy_non_neutral']} | "
                f"balanced="
                f"{fila['balanced_accuracy_non_neutral']} | "
                f"baseline="
                f"{fila['majority_baseline_non_neutral']}"
            )

        print(
            "\nArchivos generados en: "
            f"{RUTA_SALIDA}"
        )

        print(
            "RESULTADO: PIPELINE NLP "
            "COMPLETADO CORRECTAMENTE."
        )

        return 0

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        logging.error(
            "No se pudo completar "
            "el pipeline NLP: %s",
            error,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())