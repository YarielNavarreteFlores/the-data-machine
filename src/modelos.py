from __future__ import annotations

from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

# Se reutilizan las stopwords de dominio (inglés + términos genéricos del
# mundo de los videojuegos) ya definidas para el TF-IDF de nlp.py, de modo que
# el vocabulario del clasificador sea coherente con la extracción de temas.
from src.nlp import STOPWORDS_TFIDF


# ==========================================================
# CONSTANTES DE ENTRENAMIENTO
# ==========================================================

RANDOM_STATE = 42
TEST_SIZE = 0.2

# Máximo de puntos guardados para la gráfica de dispersión predicho vs. real.
MAX_PUNTOS_DISPERSION = 500

# Etiquetas legibles de cada modelo (orden en que se reportan).
ETIQUETA_LOGISTICA = "Regresión logística"
ETIQUETA_NAIVE_BAYES = "Naive Bayes"
ETIQUETA_VADER = "VADER (léxico)"
ETIQUETA_BASELINE = "Baseline mayoritario"

# Variables numéricas usadas para la regresión sobre weighted_vote_score.
FEATURES_REGRESION = [
    "votes_up",
    "votes_funny",
    "comment_count",
    "playtime_forever_minutes",
    "playtime_at_review_minutes",
    "author_num_reviews",
    "author_num_games_owned",
]

OBJETIVO_REGRESION = "weighted_vote_score"


# ==========================================================
# UTILIDADES
# ==========================================================

def _a_bool(valor: Any) -> Any:
    """Convierte un valor CSV a booleano conservando los nulos como pd.NA."""
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
# 1) CLASIFICACIÓN SUPERVISADA vs VADER
# ==========================================================

def calcular_metricas_clasificacion(
    y_true: Iterable[Any],
    y_pred: Iterable[Any],
) -> dict[str, Any]:
    """
    Calcula las mismas métricas binarias que usa VADER en nlp.py.

    La clase positiva es ``True`` (voted_up). La matriz de confusión usa las
    mismas llaves que ``evaluar_sentimiento`` para reutilizar las funciones de
    visualización del dashboard.
    """
    y_true = np.asarray(list(y_true), dtype=bool)
    y_pred = np.asarray(list(y_pred), dtype=bool)

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[False, True],
    ).ravel()

    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
        "balanced_accuracy": round(
            float(balanced_accuracy_score(y_true, y_pred)), 6
        ),
        "precision": round(
            float(precision_score(y_true, y_pred, pos_label=True, zero_division=0)),
            6,
        ),
        "recall": round(
            float(recall_score(y_true, y_pred, pos_label=True, zero_division=0)),
            6,
        ),
        "f1": round(
            float(f1_score(y_true, y_pred, pos_label=True, zero_division=0)),
            6,
        ),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def baseline_mayoritario(
    y_entrenamiento: Iterable[Any],
    y_evaluacion: Iterable[Any],
) -> dict[str, Any]:
    """
    Métricas de predecir siempre la clase mayoritaria del entrenamiento.

    Sirve como referencia mínima: cualquier modelo útil debe superarla.
    """
    y_entrenamiento = np.asarray(list(y_entrenamiento), dtype=bool)
    y_evaluacion = np.asarray(list(y_evaluacion), dtype=bool)

    clase_mayoritaria = bool(
        np.bincount(y_entrenamiento.astype(int), minlength=2).argmax()
    )

    y_pred = np.full(len(y_evaluacion), clase_mayoritaria, dtype=bool)

    return calcular_metricas_clasificacion(y_evaluacion, y_pred)


def preparar_datos_clasificacion(reviews: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra las reseñas con texto y recomendación válidos para clasificar.

    Conserva ``vader_prediction_binary`` cuando existe, para comparar el modelo
    supervisado contra VADER sobre el mismo conjunto de prueba.
    """
    df = reviews.copy()

    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df["voted_up"] = df["voted_up"].map(_a_bool).astype("boolean")

    if "vader_prediction_binary" in df.columns:
        df["vader_prediction_binary"] = (
            df["vader_prediction_binary"].map(_a_bool).astype("boolean")
        )

    df = df[(df["text"] != "") & (df["voted_up"].notna())]

    return df.reset_index(drop=True)


def _vectorizador_clasificacion() -> TfidfVectorizer:
    """TF-IDF coherente con nlp.py (unigramas + bigramas, stopwords de dominio)."""
    return TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        stop_words=STOPWORDS_TFIDF,
        ngram_range=(1, 2),
        min_df=5,
        max_df=0.90,
        max_features=10_000,
        sublinear_tf=True,
    )


def entrenar_clasificadores(
    datos: pd.DataFrame,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
) -> dict[str, Any]:
    """
    Entrena LogisticRegression y MultinomialNB sobre el TF-IDF del texto.

    Evalúa ambos modelos, VADER y el baseline mayoritario sobre el MISMO
    conjunto de prueba (división estratificada) y devuelve un diccionario
    serializable a JSON. Reporta el resultado real aunque el modelo no gane.
    """
    if len(datos) < 4:
        raise ValueError("Se requieren al menos cuatro reseñas para clasificar.")

    textos = datos["text"].tolist()
    y = datos["voted_up"].astype(bool).to_numpy()

    indices = np.arange(len(datos))
    idx_train, idx_test = train_test_split(
        indices,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    textos_train = [textos[i] for i in idx_train]
    textos_test = [textos[i] for i in idx_test]
    y_train = y[idx_train]
    y_test = y[idx_test]

    vectorizador = _vectorizador_clasificacion()
    x_train = vectorizador.fit_transform(textos_train)
    x_test = vectorizador.transform(textos_test)

    modelos: dict[str, Any] = {}

    logistica = LogisticRegression(max_iter=1000, random_state=random_state)
    logistica.fit(x_train, y_train)
    modelos[ETIQUETA_LOGISTICA] = calcular_metricas_clasificacion(
        y_test, logistica.predict(x_test)
    )

    naive_bayes = MultinomialNB()
    naive_bayes.fit(x_train, y_train)
    modelos[ETIQUETA_NAIVE_BAYES] = calcular_metricas_clasificacion(
        y_test, naive_bayes.predict(x_test)
    )

    # VADER se evalúa sobre el mismo test, solo en las reseñas no neutrales.
    if "vader_prediction_binary" in datos.columns:
        vader_test = datos["vader_prediction_binary"].to_numpy()[idx_test]
        evaluable = pd.notna(vader_test)

        if evaluable.sum() > 0:
            metricas_vader = calcular_metricas_clasificacion(
                y_test[evaluable],
                np.array([bool(v) for v in vader_test[evaluable]]),
            )
            metricas_vader["cobertura"] = round(
                float(evaluable.sum() / len(evaluable)), 6
            )
            modelos[ETIQUETA_VADER] = metricas_vader

    modelos[ETIQUETA_BASELINE] = baseline_mayoritario(y_train, y_test)

    return {
        "objetivo": "voted_up",
        "n_total": int(len(datos)),
        "n_train": int(len(idx_train)),
        "n_test": int(len(idx_test)),
        "test_size": float(test_size),
        "random_state": int(random_state),
        "distribucion_clases": {
            "positivas": int(y.sum()),
            "negativas": int((~y).sum()),
        },
        "modelos": modelos,
    }


# ==========================================================
# 2) REGRESIÓN SOBRE weighted_vote_score
# ==========================================================

def calcular_metricas_regresion(
    y_true: Iterable[float],
    y_pred: Iterable[float],
) -> dict[str, float]:
    """Devuelve R², MAE y RMSE de una predicción de regresión."""
    y_true = np.asarray(list(y_true), dtype=float)
    y_pred = np.asarray(list(y_pred), dtype=float)

    # squared=False fue retirado en sklearn reciente; se usa np.sqrt.
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))

    return {
        "r2": round(float(r2_score(y_true, y_pred)), 6),
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 6),
        "rmse": round(rmse, 6),
    }


def preparar_datos_regresion(
    reviews: pd.DataFrame,
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Selecciona las features numéricas disponibles y el objetivo de regresión.

    Descarta filas con valores ausentes en las features o en el objetivo.
    """
    if OBJETIVO_REGRESION not in reviews.columns:
        raise ValueError(
            f"Falta la columna objetivo '{OBJETIVO_REGRESION}'."
        )

    columnas = [c for c in FEATURES_REGRESION if c in reviews.columns]

    if not columnas:
        raise ValueError("No hay features numéricas disponibles para la regresión.")

    x = reviews[columnas].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(reviews[OBJETIVO_REGRESION], errors="coerce")

    valido = x.notna().all(axis=1) & y.notna()

    x = x[valido].reset_index(drop=True)
    y = y[valido].to_numpy(dtype=float)

    if x.empty:
        raise ValueError("No quedaron filas válidas para la regresión.")

    return x, y


def entrenar_regresion(
    x: pd.DataFrame,
    y: np.ndarray,
    test_size: float = TEST_SIZE,
    random_state: int = RANDOM_STATE,
    max_puntos: int = MAX_PUNTOS_DISPERSION,
) -> dict[str, Any]:
    """
    Entrena LinearRegression y reporta R², MAE y RMSE en test.

    Devuelve además una muestra de pares (real, predicho) para la gráfica de
    dispersión y los coeficientes por feature.
    """
    if len(x) < 4:
        raise ValueError("Se requieren al menos cuatro filas para la regresión.")

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
    )

    modelo = LinearRegression()
    modelo.fit(x_train, y_train)
    y_pred = modelo.predict(x_test)

    metricas = calcular_metricas_regresion(y_test, y_pred)

    # Muestra acotada de puntos para no inflar el JSON.
    n_test = len(y_test)
    if n_test > max_puntos:
        generador = np.random.default_rng(random_state)
        seleccion = generador.choice(n_test, size=max_puntos, replace=False)
    else:
        seleccion = np.arange(n_test)

    puntos = [
        {
            "real": round(float(y_test[i]), 6),
            "predicho": round(float(y_pred[i]), 6),
        }
        for i in seleccion
    ]

    coeficientes = {
        columna: round(float(coef), 6)
        for columna, coef in zip(x.columns, modelo.coef_)
    }

    return {
        "objetivo": OBJETIVO_REGRESION,
        "r2": metricas["r2"],
        "mae": metricas["mae"],
        "rmse": metricas["rmse"],
        "n_train": int(len(x_train)),
        "n_test": int(n_test),
        "intercepto": round(float(modelo.intercept_), 6),
        "features": list(x.columns),
        "coeficientes": coeficientes,
        "puntos": puntos,
    }


# ==========================================================
# ORQUESTACIÓN (la usa el script de precómputo)
# ==========================================================

def entrenar_clasificacion(reviews: pd.DataFrame) -> dict[str, Any]:
    """Prepara los datos y entrena los clasificadores en un solo paso."""
    datos = preparar_datos_clasificacion(reviews)
    return entrenar_clasificadores(datos)


def entrenar_regresion_completa(reviews: pd.DataFrame) -> dict[str, Any]:
    """Prepara los datos y entrena la regresión en un solo paso."""
    x, y = preparar_datos_regresion(reviews)
    return entrenar_regresion(x, y)
