from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


# ==========================================================
# CONFIGURACIÓN DE RUTAS
# ==========================================================

# La raíz del proyecto se calcula desde la ubicación de este archivo.
# Esto evita utilizar rutas absolutas que solo funcionen en una PC.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

# Ruta del dataset limpio acordado por todo el equipo.
RUTA_DATASET = (
    RAIZ_PROYECTO
    / "data"
    / "processed"
    / "dataset_limpio.csv"
)

# Ruta del catálogo oficial de videojuegos.
RUTA_CATALOGO = (
    RAIZ_PROYECTO
    / "config"
    / "catalogo.json"
)


# ==========================================================
# HUELLA DIGITAL DEL DATASET
# ==========================================================

# SHA-256 calculado sobre el dataset_limpio.csv proporcionado.
# Si el archivo cambia aunque sea por un solo carácter,
# este valor dejará de coincidir.
SHA256_ESPERADO = (
    "b79786bad6eeed3ac23b2b51f0104d5f"
    "c57ed7cf34f4e1f0ef5e3f6c2e7e7ed5"
)


# ==========================================================
# COLUMNAS QUE NECESITARÁ EL PROYECTO
# ==========================================================

# Estas columnas serán utilizadas por el catálogo,
# el scraper, el módulo NLP y el dashboard.
COLUMNAS_REQUERIDAS = {
    "appid",
    "name",
    "reviews",
    "header_image",
    "genres",
    "tags",
    "positive",
    "negative",
    "pct_pos_total",
    "num_reviews_total",
    "metacritic_score",
    "price",
    "estimated_owners",
    "average_playtime_forever",
}


def calcular_sha256(
    ruta: Path,
    tamano_bloque: int = 1024 * 1024,
) -> str:
    """
    Calcula la huella SHA-256 de un archivo.

    El archivo se lee en bloques de 1 MB para evitar
    cargar los 69 MB completos en memoria.
    """
    hash_archivo = hashlib.sha256()

    with ruta.open("rb") as archivo:
        while bloque := archivo.read(tamano_bloque):
            hash_archivo.update(bloque)

    return hash_archivo.hexdigest()


def cargar_catalogo(ruta: Path) -> list[dict]:
    """
    Lee el archivo catalogo.json.

    Retorna únicamente los juegos que tengan activo=true.
    """
    with ruta.open("r", encoding="utf-8") as archivo:
        contenido = json.load(archivo)

    juegos = contenido.get("juegos", [])

    return [
        juego
        for juego in juegos
        if juego.get("activo", True)
    ]


def registrar_error(
    mensaje: str,
    errores: list[str],
) -> None:
    """
    Registra e imprime un error.

    Se guardan todos los errores para evitar que el
    programa se detenga en la primera inconsistencia.
    """
    errores.append(mensaje)
    print(f"[ERROR] {mensaje}")


def main() -> int:
    """
    Ejecuta las verificaciones correspondientes al Bloque 0.

    Retorna:
        0: todas las validaciones fueron correctas.
        1: se encontró al menos un error.
    """
    errores: list[str] = []

    print("=" * 68)
    print("VERIFICACIÓN DE LA BASE DEL PROYECTO — THE DATA MACHINE")
    print("=" * 68)

    # ======================================================
    # 1. VERIFICAR QUE LOS ARCHIVOS EXISTAN
    # ======================================================

    if not RUTA_DATASET.exists():
        registrar_error(
            f"No se encontró el dataset en: {RUTA_DATASET}",
            errores,
        )

    if not RUTA_CATALOGO.exists():
        registrar_error(
            f"No se encontró el catálogo en: {RUTA_CATALOGO}",
            errores,
        )

    # No es posible continuar si faltan los archivos base.
    if errores:
        return 1

    # ======================================================
    # 2. VERIFICAR QUE EL DATASET NO FUE MODIFICADO
    # ======================================================

    tamano_mb = (
        RUTA_DATASET.stat().st_size
        / (1024 * 1024)
    )

    sha256_actual = calcular_sha256(RUTA_DATASET)

    print(f"[OK] Dataset localizado: {RUTA_DATASET}")
    print(f"[OK] Tamaño del dataset: {tamano_mb:.2f} MB")
    print(f"[INFO] SHA-256 obtenido: {sha256_actual}")

    if sha256_actual != SHA256_ESPERADO:
        registrar_error(
            "El SHA-256 no coincide. El dataset fue "
            "modificado o no es el archivo acordado.",
            errores,
        )
    else:
        print(
            "[OK] El dataset coincide exactamente con "
            "dataset_limpio.csv."
        )

    # ======================================================
    # 3. VERIFICAR LAS COLUMNAS DEL DATASET
    # ======================================================

    # Solo se leen los encabezados del CSV.
    # No es necesario cargar todas las filas en este punto.
    encabezados = pd.read_csv(
        RUTA_DATASET,
        nrows=0,
    ).columns.tolist()

    columnas_faltantes = sorted(
        COLUMNAS_REQUERIDAS.difference(encabezados)
    )

    if columnas_faltantes:
        registrar_error(
            "Faltan columnas requeridas: "
            + ", ".join(columnas_faltantes),
            errores,
        )
    else:
        print(
            f"[OK] Estructura válida: "
            f"{len(encabezados)} columnas detectadas."
        )

    # ======================================================
    # 4. VERIFICAR EL CATÁLOGO
    # ======================================================

    juegos = cargar_catalogo(RUTA_CATALOGO)

    appids_catalogo = [
        int(juego["appid"])
        for juego in juegos
    ]

    # El alcance del proyecto establece de 8 a 10 juegos.
    if not 8 <= len(juegos) <= 10:
        registrar_error(
            "El catálogo debe tener entre 8 y 10 juegos "
            f"activos; actualmente tiene {len(juegos)}.",
            errores,
        )
    else:
        print(
            f"[OK] Catálogo válido: "
            f"{len(juegos)} juegos activos."
        )

    # Cada appid debe aparecer solo una vez.
    if len(appids_catalogo) != len(set(appids_catalogo)):
        registrar_error(
            "Existen appids repetidos en catalogo.json.",
            errores,
        )

    # ======================================================
    # 5. BUSCAR LOS JUEGOS DEL CATÁLOGO EN EL DATASET
    # ======================================================

    # Solo se cargan las columnas necesarias para esta prueba.
    columnas_revision = [
        "appid",
        "name",
        "pct_pos_total",
        "num_reviews_total",
        "header_image",
        "tags",
    ]

    df = pd.read_csv(
        RUTA_DATASET,
        usecols=columnas_revision,
    )

    df_catalogo = df[
        df["appid"].isin(appids_catalogo)
    ].copy()

    appids_encontrados = set(
        df_catalogo["appid"]
        .astype(int)
        .tolist()
    )

    appids_faltantes = sorted(
        set(appids_catalogo)
        .difference(appids_encontrados)
    )

    if appids_faltantes:
        registrar_error(
            "Los siguientes appids no existen en el dataset: "
            + ", ".join(map(str, appids_faltantes)),
            errores,
        )
    else:
        print(
            "[OK] Todos los appids del catálogo "
            "existen en el dataset."
        )

    # ======================================================
    # 6. VERIFICAR CAMPOS INDISPENSABLES
    # ======================================================

    campos_vacios = df_catalogo[
        df_catalogo[
            [
                "name",
                "header_image",
                "tags",
            ]
        ]
        .isna()
        .any(axis=1)
    ]

    if not campos_vacios.empty:
        registrar_error(
            "Hay juegos del catálogo con nombre, "
            "imagen o tags vacíos.",
            errores,
        )
    else:
        print(
            "[OK] Todos los juegos tienen "
            "nombre, imagen y tags."
        )

    # ======================================================
    # 7. MOSTRAR EL CATÁLOGO EN EL ORDEN DEFINIDO
    # ======================================================

    orden = {
        int(juego["appid"]): int(juego["orden"])
        for juego in juegos
    }

    df_catalogo["orden"] = (
        df_catalogo["appid"].map(orden)
    )

    df_catalogo = df_catalogo.sort_values("orden")

    print("\nCATÁLOGO VALIDADO")

    print(
        df_catalogo[
            [
                "orden",
                "appid",
                "name",
                "pct_pos_total",
                "num_reviews_total",
            ]
        ].to_string(index=False)
    )

    # ======================================================
    # 8. RESULTADO FINAL
    # ======================================================

    print("\n" + "=" * 68)

    if errores:
        print(
            "RESULTADO: BLOQUE 0 NO APROBADO "
            f"({len(errores)} error(es))."
        )
        return 1

    print("RESULTADO: BLOQUE 0 APROBADO.")
    return 0


if __name__ == "__main__":
    # sys.exit permite que GitHub Actions o las pruebas
    # detecten si el programa terminó correctamente.
    sys.exit(main())