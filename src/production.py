from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.data_paths import (
    NOMBRES_ARCHIVOS_NLP,
    RAIZ_PROYECTO,
    RUTA_CATALOGO_PRODUCCION,
    RUTA_DATASET_DESARROLLO,
    RUTA_MANIFIESTO_PRODUCCION,
    RUTA_NLP_DESARROLLO,
    RUTA_PRODUCCION,
)


# ==========================================================
# CONFIGURACIÓN DEL PAQUETE DE PRODUCCIÓN
# ==========================================================

RUTA_CATALOGO_JSON = (
    RAIZ_PROYECTO
    / "config"
    / "catalogo.json"
)

COLUMNAS_METADATA_PRODUCCION = [
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
    "positive",
    "negative",
]

ARCHIVOS_PRODUCCION = (
    "catalogo_10_juegos.csv",
    *NOMBRES_ARCHIVOS_NLP,
)


# ==========================================================
# UTILIDADES
# ==========================================================

def calcular_sha256(
    ruta: Path,
    tamano_bloque: int = 1024 * 1024,
) -> str:
    """
    Calcula SHA-256 sin cargar el archivo completo en memoria.
    """
    huella = hashlib.sha256()

    with ruta.open("rb") as archivo:
        while bloque := archivo.read(
            tamano_bloque
        ):
            huella.update(bloque)

    return huella.hexdigest()


def obtener_appids_catalogo(
    ruta_catalogo: Path = RUTA_CATALOGO_JSON,
) -> list[int]:
    """
    Lee los appids activos en el orden oficial.
    """
    with ruta_catalogo.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        contenido = json.load(archivo)

    juegos = [
        juego
        for juego
        in contenido.get("juegos", [])
        if juego.get("activo", True)
    ]

    juegos = sorted(
        juegos,
        key=lambda juego: int(
            juego.get("orden", 0)
        ),
    )

    appids = [
        int(juego["appid"])
        for juego in juegos
    ]

    if not 8 <= len(appids) <= 10:
        raise ValueError(
            "El catálogo debe contener "
            "entre 8 y 10 juegos activos."
        )

    if len(appids) != len(set(appids)):
        raise ValueError(
            "El catálogo contiene appids repetidos."
        )

    return appids


def _leer_metricas(
    ruta: Path,
) -> list[dict[str, Any]]:
    """
    Lee y valida la estructura general del JSON de métricas.
    """
    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        contenido = json.load(archivo)

    if not isinstance(
        contenido,
        list,
    ):
        raise ValueError(
            "metricas_sentimiento.json debe "
            "contener una lista."
        )

    return contenido


def _escribir_csv_atomico(
    dataframe: pd.DataFrame,
    ruta: Path,
) -> None:
    """
    Escribe un CSV temporal y después reemplaza el definitivo.
    """
    temporal = ruta.with_suffix(
        ruta.suffix + ".tmp"
    )

    dataframe.to_csv(
        temporal,
        index=False,
        encoding="utf-8",
    )

    temporal.replace(ruta)


def _copiar_atomico(
    origen: Path,
    destino: Path,
) -> None:
    """
    Copia un archivo mediante una ruta temporal.
    """
    temporal = destino.with_suffix(
        destino.suffix + ".tmp"
    )

    shutil.copy2(
        origen,
        temporal,
    )

    temporal.replace(destino)


# ==========================================================
# CONSTRUCCIÓN DEL PAQUETE
# ==========================================================

def preparar_datos_produccion(
    ruta_dataset: Path = RUTA_DATASET_DESARROLLO,
    ruta_nlp: Path = RUTA_NLP_DESARROLLO,
    ruta_salida: Path = RUTA_PRODUCCION,
    ruta_catalogo: Path = RUTA_CATALOGO_JSON,
) -> dict[str, Any]:
    """
    Genera un paquete compacto y reproducible para despliegue.

    El dataset_limpio.csv original permanece intacto y fuera de Git.
    Solo se extraen las 10 filas necesarias para la aplicación.
    """
    if not ruta_dataset.exists():
        raise FileNotFoundError(
            f"No existe el dataset fuente: "
            f"{ruta_dataset}"
        )

    faltantes_nlp = [
        ruta_nlp / nombre
        for nombre in NOMBRES_ARCHIVOS_NLP
        if not (
            ruta_nlp
            / nombre
        ).exists()
    ]

    if faltantes_nlp:
        raise FileNotFoundError(
            "Faltan resultados NLP: "
            + ", ".join(
                str(ruta)
                for ruta
                in faltantes_nlp
            )
        )

    appids = obtener_appids_catalogo(
        ruta_catalogo
    )

    # ------------------------------------------------------
    # Extraer metadata de los 10 juegos
    # ------------------------------------------------------

    encabezados = pd.read_csv(
        ruta_dataset,
        nrows=0,
    ).columns.tolist()

    faltantes_columnas = sorted(
        set(
            COLUMNAS_METADATA_PRODUCCION
        ).difference(encabezados)
    )

    if faltantes_columnas:
        raise ValueError(
            "El dataset no contiene columnas "
            "de producción: "
            + ", ".join(
                faltantes_columnas
            )
        )

    metadata = pd.read_csv(
        ruta_dataset,
        usecols=(
            COLUMNAS_METADATA_PRODUCCION
        ),
        low_memory=False,
    )

    metadata["appid"] = pd.to_numeric(
        metadata["appid"],
        errors="raise",
    ).astype("int64")

    metadata = metadata[
        metadata["appid"].isin(
            appids
        )
    ].copy()

    metadata = metadata.drop_duplicates(
        subset="appid",
        keep="first",
    )

    orden = {
        appid: posicion
        for posicion, appid
        in enumerate(appids)
    }

    metadata["__orden"] = (
        metadata["appid"]
        .map(orden)
    )

    metadata = (
        metadata
        .sort_values("__orden")
        .drop(columns="__orden")
        .reset_index(drop=True)
    )

    if metadata["appid"].tolist() != appids:
        raise ValueError(
            "La metadata no coincide exactamente "
            "con catalogo.json."
        )

    # ------------------------------------------------------
    # Validar los resultados NLP
    # ------------------------------------------------------

    reviews = pd.read_csv(
        ruta_nlp
        / "reviews_analizadas.csv",
        low_memory=False,
    )

    temas = pd.read_csv(
        ruta_nlp
        / "temas_tfidf.csv",
    )

    tags = pd.read_csv(
        ruta_nlp
        / "tags_steam.csv",
    )

    metricas = _leer_metricas(
        ruta_nlp
        / "metricas_sentimiento.json"
    )

    metricas_df = pd.DataFrame(
        metricas
    )

    for nombre, dataframe in {
        "reviews": reviews,
        "temas": temas,
        "tags": tags,
        "metricas": metricas_df,
    }.items():
        if "appid" not in dataframe.columns:
            raise ValueError(
                f"{nombre} no contiene appid."
            )

        dataframe["appid"] = pd.to_numeric(
            dataframe["appid"],
            errors="raise",
        ).astype("int64")

        appids_archivo = set(
            dataframe["appid"].tolist()
        )

        if appids_archivo != set(appids):
            raise ValueError(
                f"{nombre} no contiene exactamente "
                "los appids del catálogo."
            )

    if len(reviews) != 5000:
        raise ValueError(
            "Se esperaban 5000 reseñas "
            f"y se encontraron {len(reviews)}."
        )

    conteo_reviews = (
        reviews.groupby("appid")
        .size()
    )

    if not (
        conteo_reviews == 500
    ).all():
        raise ValueError(
            "Cada juego debe contener "
            "exactamente 500 reseñas."
        )

    if reviews["review_hash"].duplicated().any():
        raise ValueError(
            "Existen review_hash duplicados."
        )

    if len(metricas_df) != len(appids):
        raise ValueError(
            "Debe existir una fila de métricas "
            "por videojuego."
        )

    # ------------------------------------------------------
    # Escribir el paquete compacto
    # ------------------------------------------------------

    ruta_salida.mkdir(
        parents=True,
        exist_ok=True,
    )

    _escribir_csv_atomico(
        metadata,
        ruta_salida
        / "catalogo_10_juegos.csv",
    )

    for nombre in NOMBRES_ARCHIVOS_NLP:
        _copiar_atomico(
            ruta_nlp / nombre,
            ruta_salida / nombre,
        )

    # ------------------------------------------------------
    # Crear manifiesto de integridad
    # ------------------------------------------------------

    archivos: dict[
        str,
        dict[str, Any],
    ] = {}

    for nombre in ARCHIVOS_PRODUCCION:
        ruta = ruta_salida / nombre

        archivos[nombre] = {
            "bytes": ruta.stat().st_size,
            "sha256": calcular_sha256(
                ruta
            ),
        }

    archivos[
        "catalogo_10_juegos.csv"
    ]["rows"] = len(metadata)

    archivos[
        "reviews_analizadas.csv"
    ]["rows"] = len(reviews)

    archivos[
        "metricas_sentimiento.json"
    ]["rows"] = len(metricas_df)

    archivos[
        "temas_tfidf.csv"
    ]["rows"] = len(temas)

    archivos[
        "tags_steam.csv"
    ]["rows"] = len(tags)

    manifiesto: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "catalog_appids": appids,
        "source_dataset": {
            "filename": ruta_dataset.name,
            "bytes": (
                ruta_dataset
                .stat()
                .st_size
            ),
            "sha256": calcular_sha256(
                ruta_dataset
            ),
        },
        "files": archivos,
        "total_production_bytes": sum(
            datos["bytes"]
            for datos
            in archivos.values()
        ),
    }

    ruta_manifiesto = (
        ruta_salida
        / "manifest.json"
    )

    temporal = ruta_manifiesto.with_suffix(
        ".json.tmp"
    )

    with temporal.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            manifiesto,
            archivo,
            ensure_ascii=False,
            indent=2,
        )

    temporal.replace(
        ruta_manifiesto
    )

    return manifiesto


# ==========================================================
# VALIDACIÓN DEL PAQUETE EXISTENTE
# ==========================================================

def validar_datos_produccion(
    ruta_produccion: Path = RUTA_PRODUCCION,
) -> list[str]:
    """
    Verifica existencia, tamaño, hash y conteos del paquete.

    Retorna una lista vacía cuando el paquete es válido.
    """
    errores: list[str] = []

    ruta_manifiesto = (
        ruta_produccion
        / "manifest.json"
    )

    if not ruta_manifiesto.exists():
        return [
            "No existe data/production/manifest.json."
        ]

    try:
        with ruta_manifiesto.open(
            "r",
            encoding="utf-8",
        ) as archivo:
            manifiesto = json.load(
                archivo
            )

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        return [
            f"No se pudo leer manifest.json: "
            f"{error}"
        ]

    archivos = manifiesto.get(
        "files",
        {},
    )

    for nombre in ARCHIVOS_PRODUCCION:
        ruta = ruta_produccion / nombre
        esperado = archivos.get(nombre)

        if not ruta.exists():
            errores.append(
                f"Falta {nombre}."
            )
            continue

        if not isinstance(
            esperado,
            dict,
        ):
            errores.append(
                f"manifest.json no describe "
                f"{nombre}."
            )
            continue

        bytes_actuales = (
            ruta.stat().st_size
        )

        if (
            bytes_actuales
            != esperado.get("bytes")
        ):
            errores.append(
                f"Tamaño incorrecto en "
                f"{nombre}."
            )

        hash_actual = calcular_sha256(
            ruta
        )

        if (
            hash_actual
            != esperado.get("sha256")
        ):
            errores.append(
                f"SHA-256 incorrecto en "
                f"{nombre}."
            )

    # Verificación estructural adicional.
    if not errores:
        metadata = pd.read_csv(
            ruta_produccion
            / "catalogo_10_juegos.csv"
        )

        reviews = pd.read_csv(
            ruta_produccion
            / "reviews_analizadas.csv",
            low_memory=False,
        )

        temas = pd.read_csv(
            ruta_produccion
            / "temas_tfidf.csv"
        )

        tags = pd.read_csv(
            ruta_produccion
            / "tags_steam.csv"
        )

        metricas = _leer_metricas(
            ruta_produccion
            / "metricas_sentimiento.json"
        )

        if len(metadata) != 10:
            errores.append(
                "El catálogo de producción "
                "no contiene 10 filas."
            )

        if len(reviews) != 5000:
            errores.append(
                "El paquete no contiene "
                "5000 reseñas."
            )

        if len(metricas) != 10:
            errores.append(
                "El paquete no contiene "
                "10 métricas."
            )

        if len(temas) != 150:
            errores.append(
                "El paquete no contiene "
                "150 temas."
            )

        if len(tags) != 150:
            errores.append(
                "El paquete no contiene "
                "150 tags."
            )

        if (
            "review_hash"
            not in reviews.columns
            or reviews[
                "review_hash"
            ].duplicated().any()
        ):
            errores.append(
                "Las reseñas tienen hashes "
                "ausentes o duplicados."
            )

    return errores
