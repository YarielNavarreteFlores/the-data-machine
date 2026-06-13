from __future__ import annotations

from pathlib import Path


# ==========================================================
# RUTAS DE DATOS — DESARROLLO Y PRODUCCIÓN
# ==========================================================

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

# Fuentes locales completas. Permanecen fuera de Git.
RUTA_DATASET_DESARROLLO = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "dataset_limpio.csv"
)

RUTA_NLP_DESARROLLO = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "nlp"
)

# Paquete compacto que sí se incluye en el repositorio.
RUTA_PRODUCCION = (
    RAIZ_PROYECTO
    / "data"
    / "production"
)

RUTA_CATALOGO_PRODUCCION = (
    RUTA_PRODUCCION
    / "catalogo_10_juegos.csv"
)

RUTA_MANIFIESTO_PRODUCCION = (
    RUTA_PRODUCCION
    / "manifest.json"
)

NOMBRES_ARCHIVOS_NLP = (
    "reviews_analizadas.csv",
    "metricas_sentimiento.json",
    "temas_tfidf.csv",
    "tags_steam.csv",
)


def _directorio_nlp_completo(
    directorio: Path,
) -> bool:
    """
    Comprueba que un directorio contenga los cuatro
    resultados indispensables del pipeline NLP.
    """
    return all(
        (
            directorio
            / nombre_archivo
        ).exists()
        for nombre_archivo
        in NOMBRES_ARCHIVOS_NLP
    )


def resolver_ruta_metadata(
    ruta_produccion: Path = RUTA_CATALOGO_PRODUCCION,
    ruta_desarrollo: Path = RUTA_DATASET_DESARROLLO,
) -> Path:
    """
    Prioriza el catálogo compacto de producción.

    Si todavía no se ha generado, utiliza el dataset completo
    del entorno local. Cuando ninguno existe, retorna la ruta
    de producción para que el cargador muestre un error claro.
    """
    if ruta_produccion.exists():
        return ruta_produccion

    if ruta_desarrollo.exists():
        return ruta_desarrollo

    return ruta_produccion


def resolver_directorio_nlp(
    ruta_produccion: Path = RUTA_PRODUCCION,
    ruta_desarrollo: Path = RUTA_NLP_DESARROLLO,
) -> Path:
    """
    Prioriza los resultados NLP compactos incluidos en Git.

    En desarrollo se mantiene compatibilidad con
    data/processed/nlp/.
    """
    if _directorio_nlp_completo(
        ruta_produccion
    ):
        return ruta_produccion

    if _directorio_nlp_completo(
        ruta_desarrollo
    ):
        return ruta_desarrollo

    return ruta_produccion
