from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ==========================================================
# RUTAS DEL PROYECTO
# ==========================================================

# Se calcula la raíz del proyecto desde la ubicación
# de este archivo. Así se evitan rutas absolutas.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

# Catálogo oficial creado durante el Bloque 0.
RUTA_CATALOGO = RAIZ_PROYECTO / "config" / "catalogo.json"

# Archivo donde se almacenarán las reseñas individuales.
RUTA_SALIDA = RAIZ_PROYECTO / "data" / "reviews_extra.json"

# Archivo local para registrar el desarrollo del scraping.
RUTA_LOG = RAIZ_PROYECTO / "data" / "logs" / "scraper.log"


# ==========================================================
# ENDPOINTS DE STEAM
# ==========================================================

# Endpoint documentado por Steam para obtener reseñas
# individuales en formato JSON.
URL_REVIEWS_API = (
    "https://store.steampowered.com/appreviews/{appid}"
)

# Página HTML utilizada como respaldo si falla el endpoint JSON.
URL_REVIEWS_HTML = (
    "https://steamcommunity.com/app/{appid}/reviews/"
    "?browsefilter=mostrecent&p=1"
)

# Steam permite solicitar hasta 100 reseñas por página.
REVIEWS_POR_PAGINA = 100


# ==========================================================
# CAMPOS OBLIGATORIOS DEL JSON FINAL
# ==========================================================

CAMPOS_REQUERIDOS = {
    "appid",
    "game_name",
    "review_id",
    "review_hash",
    "text",
    "language",
    "voted_up",
    "sentiment_steam",
    "source",
    "scraped_at_utc",
}


# ==========================================================
# CONFIGURACIÓN DE MENSAJES Y LOGS
# ==========================================================

def configurar_logging() -> None:
    """
    Configura los mensajes mostrados en la terminal y crea
    un archivo de registro dentro de data/logs/.
    """
    RUTA_LOG.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                RUTA_LOG,
                encoding="utf-8",
            ),
        ],
        force=True,
    )


# ==========================================================
# CARGA DEL CATÁLOGO
# ==========================================================

def cargar_catalogo(
    ruta: Path = RUTA_CATALOGO,
) -> list[dict[str, Any]]:
    """
    Lee config/catalogo.json y devuelve únicamente
    los juegos que tengan activo=true.
    """
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el catálogo: {ruta}"
        )

    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        contenido = json.load(archivo)

    juegos = contenido.get("juegos", [])

    juegos_activos = [
        juego
        for juego in juegos
        if juego.get("activo", True)
    ]

    if not juegos_activos:
        raise ValueError(
            "El catálogo no contiene juegos activos."
        )

    return sorted(
        juegos_activos,
        key=lambda juego: int(
            juego.get("orden", 0)
        ),
    )


# ==========================================================
# LIMPIEZA Y NORMALIZACIÓN
# ==========================================================

def limpiar_texto_html(
    texto: str | None,
) -> str:
    """
    Convierte posibles etiquetas HTML a texto plano.

    BeautifulSoup retira etiquetas y entidades HTML.
    Después se eliminan saltos y espacios repetidos.

    Esta limpieza es ligera porque VADER necesita conservar
    signos, palabras completas y estructura emocional.
    """
    if not texto:
        return ""

    soup = BeautifulSoup(
        str(texto),
        "html.parser",
    )

    texto_plano = soup.get_text(
        separator=" ",
        strip=True,
    )

    return " ".join(
        texto_plano.split()
    )


def timestamp_a_iso(
    valor: Any,
) -> str | None:
    """
    Convierte una fecha Unix a formato ISO 8601 en UTC.
    """
    try:
        timestamp = int(valor)
    except (TypeError, ValueError):
        return None

    if timestamp <= 0:
        return None

    return datetime.fromtimestamp(
        timestamp,
        tz=timezone.utc,
    ).isoformat()


def calcular_hash_review(
    appid: int,
    review_id: str,
    texto: str,
) -> str:
    """
    Genera una huella SHA-256 para cada reseña.

    Esta huella permite eliminar registros duplicados,
    aunque aparezcan en dos solicitudes diferentes.
    """
    contenido = (
        f"{appid}|{review_id}|{texto}"
    ).encode("utf-8")

    return hashlib.sha256(
        contenido
    ).hexdigest()


# ==========================================================
# SESIÓN HTTP CON REINTENTOS
# ==========================================================

def crear_sesion_http() -> requests.Session:
    """
    Crea una sesión de requests con reintentos automáticos.

    Se reintentan errores de conexión, límites temporales
    y errores internos del servidor.
    """
    estrategia = Retry(
        total=4,
        connect=4,
        read=4,
        status=4,
        backoff_factor=1.0,
        status_forcelist=(
            429,
            500,
            502,
            503,
            504,
        ),
        allowed_methods=frozenset(
            {"GET"}
        ),
        respect_retry_after_header=True,
        raise_on_status=False,
    )

    adaptador = HTTPAdapter(
        max_retries=estrategia
    )

    sesion = requests.Session()

    sesion.mount(
        "https://",
        adaptador,
    )

    sesion.mount(
        "http://",
        adaptador,
    )

    sesion.headers.update(
        {
            "User-Agent": (
                "TheDataMachine/1.0 "
                "(proyecto academico ESCOM-IPN)"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
        }
    )

    return sesion


# ==========================================================
# NORMALIZACIÓN DE RESEÑAS DEL ENDPOINT JSON
# ==========================================================

def normalizar_review_api(
    review: dict[str, Any],
    appid: int,
    nombre_juego: str,
    scraped_at_utc: str,
) -> dict[str, Any] | None:
    """
    Convierte una reseña devuelta por Steam al esquema
    estándar utilizado por The Data Machine.
    """
    texto = limpiar_texto_html(
        review.get("review")
    )

    # No se guardan reseñas sin texto.
    if not texto:
        return None

    review_id = str(
        review.get("recommendationid")
        or ""
    ).strip()

    # Si Steam no entrega un identificador, se genera uno
    # con base en el contenido de la reseña.
    if not review_id:
        hash_texto = hashlib.sha256(
            texto.encode("utf-8")
        ).hexdigest()

        review_id = (
            f"sin-id-{hash_texto[:20]}"
        )

    autor = (
        review.get("author")
        or {}
    )

    voted_up = bool(
        review.get("voted_up", False)
    )

    return {
        # Identificación del videojuego.
        "appid": int(appid),
        "game_name": nombre_juego,

        # Identificación anónima de la reseña.
        "review_id": review_id,
        "review_hash": calcular_hash_review(
            appid,
            review_id,
            texto,
        ),

        # Información principal para NLP.
        "text": texto,
        "language": str(
            review.get("language")
            or "unknown"
        ),
        "voted_up": voted_up,
        "sentiment_steam": (
            "positive"
            if voted_up
            else "negative"
        ),

        # Fechas originales de Steam.
        "timestamp_created": review.get(
            "timestamp_created"
        ),
        "created_at_utc": timestamp_a_iso(
            review.get("timestamp_created")
        ),
        "timestamp_updated": review.get(
            "timestamp_updated"
        ),
        "updated_at_utc": timestamp_a_iso(
            review.get("timestamp_updated")
        ),

        # Métricas de utilidad de la reseña.
        "votes_up": int(
            review.get("votes_up")
            or 0
        ),
        "votes_funny": int(
            review.get("votes_funny")
            or 0
        ),
        "weighted_vote_score": float(
            review.get(
                "weighted_vote_score"
            )
            or 0.0
        ),
        "comment_count": int(
            review.get("comment_count")
            or 0
        ),

        # Características de compra.
        "steam_purchase": bool(
            review.get(
                "steam_purchase",
                False,
            )
        ),
        "received_for_free": bool(
            review.get(
                "received_for_free",
                False,
            )
        ),
        "written_during_early_access": bool(
            review.get(
                "written_during_early_access",
                False,
            )
        ),

        # Tiempo de juego en minutos.
        "playtime_at_review_minutes": (
            autor.get("playtime_at_review")
        ),
        "playtime_forever_minutes": (
            autor.get("playtime_forever")
        ),

        # Datos agregados del autor.
        # No se guarda su steamid.
        "author_num_games_owned": (
            autor.get("num_games_owned")
        ),
        "author_num_reviews": (
            autor.get("num_reviews")
        ),

        # Trazabilidad del registro.
        "source": "steam_reviews_api",
        "source_url": (
            URL_REVIEWS_API.format(
                appid=appid
            )
        ),
        "scraped_at_utc": scraped_at_utc,
    }


# ==========================================================
# SOLICITUD DE UNA PÁGINA DEL ENDPOINT JSON
# ==========================================================

def solicitar_pagina_api(
    sesion: requests.Session,
    appid: int,
    cursor: str,
    timeout: tuple[int, int] = (10, 30),
) -> dict[str, Any]:
    """
    Solicita una página de reseñas recientes.

    El cursor indica qué bloque de reseñas debe
    devolver Steam.
    """
    parametros = {
        "json": 1,
        "filter": "recent",
        "language": "english",
        "review_type": "all",
        "purchase_type": "all",
        "num_per_page": REVIEWS_POR_PAGINA,
        "filter_offtopic_activity": 1,
        "cursor": cursor,
    }

    respuesta = sesion.get(
        URL_REVIEWS_API.format(
            appid=appid
        ),
        params=parametros,
        timeout=timeout,
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if datos.get("success") != 1:
        raise RuntimeError(
            "Steam devolvió una respuesta "
            f"inválida para appid {appid}."
        )

    return datos


# ==========================================================
# PAGINACIÓN DEL ENDPOINT JSON
# ==========================================================

def obtener_reviews_api(
    sesion: requests.Session,
    appid: int,
    nombre_juego: str,
    max_reviews: int,
    pausa: float,
) -> list[dict[str, Any]]:
    """
    Descarga varias páginas hasta alcanzar max_reviews.

    Los duplicados se eliminan durante la descarga
    mediante review_hash.
    """
    resultados: list[dict[str, Any]] = []

    hashes_vistos: set[str] = set()
    cursores_vistos: set[str] = set()

    cursor = "*"

    scraped_at_utc = datetime.now(
        timezone.utc
    ).isoformat()

    while len(resultados) < max_reviews:

        # Evita un ciclo infinito si Steam repite cursor.
        if cursor in cursores_vistos:
            logging.warning(
                "Steam repitió el cursor para %s.",
                appid,
            )
            break

        cursores_vistos.add(cursor)

        datos = solicitar_pagina_api(
            sesion,
            appid,
            cursor,
        )

        reviews_pagina = (
            datos.get("reviews")
            or []
        )

        # Una página vacía indica que ya no hay
        # más reseñas disponibles.
        if not reviews_pagina:
            break

        for review in reviews_pagina:
            normalizada = normalizar_review_api(
                review,
                appid,
                nombre_juego,
                scraped_at_utc,
            )

            if normalizada is None:
                continue

            review_hash = normalizada[
                "review_hash"
            ]

            if review_hash in hashes_vistos:
                continue

            hashes_vistos.add(review_hash)
            resultados.append(normalizada)

            if len(resultados) >= max_reviews:
                break

        nuevo_cursor = str(
            datos.get("cursor")
            or ""
        ).strip()

        if (
            not nuevo_cursor
            or nuevo_cursor == cursor
        ):
            break

        cursor = nuevo_cursor

        logging.info(
            "%s (%s): %s/%s reseñas.",
            nombre_juego,
            appid,
            len(resultados),
            max_reviews,
        )

        if (
            len(resultados) < max_reviews
            and pausa > 0
        ):
            time.sleep(pausa)

    return resultados


# ==========================================================
# RESPALDO HTML CON BEAUTIFULSOUP
# ==========================================================

def normalizar_review_html(
    tarjeta: Any,
    appid: int,
    nombre_juego: str,
    scraped_at_utc: str,
) -> dict[str, Any] | None:
    """
    Normaliza una tarjeta obtenida desde la página HTML
    de Steam Community.
    """
    contenido = tarjeta.find(
        "div",
        class_="apphub_CardTextContent",
    )

    if contenido is None:
        return None

    # La fecha viene dentro del contenedor del texto.
    # Se elimina para que no forme parte de la reseña.
    fecha = contenido.find(
        "div",
        class_="date_posted",
    )

    if fecha is not None:
        fecha.extract()

    texto = limpiar_texto_html(
        str(contenido)
    )

    if not texto:
        return None

    titulo = tarjeta.find(
        "div",
        class_="title",
    )

    if titulo is None:
        return None

    etiqueta = limpiar_texto_html(
        str(titulo)
    ).lower()

    if etiqueta not in {
        "recommended",
        "not recommended",
    }:
        return None

    voted_up = (
        etiqueta == "recommended"
    )

    review_hash = calcular_hash_review(
        appid,
        "html",
        texto,
    )

    return {
        "appid": int(appid),
        "game_name": nombre_juego,
        "review_id": (
            f"html-{review_hash[:20]}"
        ),
        "review_hash": review_hash,
        "text": texto,
        "language": "english",
        "voted_up": voted_up,
        "sentiment_steam": (
            "positive"
            if voted_up
            else "negative"
        ),
        "timestamp_created": None,
        "created_at_utc": None,
        "timestamp_updated": None,
        "updated_at_utc": None,
        "votes_up": 0,
        "votes_funny": 0,
        "weighted_vote_score": 0.0,
        "comment_count": 0,
        "steam_purchase": None,
        "received_for_free": None,
        "written_during_early_access": None,
        "playtime_at_review_minutes": None,
        "playtime_forever_minutes": None,
        "author_num_games_owned": None,
        "author_num_reviews": None,
        "source": (
            "steamcommunity_html_fallback"
        ),
        "source_url": (
            URL_REVIEWS_HTML.format(
                appid=appid
            )
        ),
        "scraped_at_utc": scraped_at_utc,
    }


def parsear_reviews_html(
    html: str,
    appid: int,
    nombre_juego: str,
    max_reviews: int,
) -> list[dict[str, Any]]:
    """
    Extrae reseñas desde un documento HTML.

    Esta función también puede probarse sin Internet
    utilizando un HTML almacenado en memoria.
    """
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    tarjetas = soup.find_all(
        "div",
        class_="apphub_Card",
        limit=max_reviews,
    )

    scraped_at_utc = datetime.now(
        timezone.utc
    ).isoformat()

    resultados: list[dict[str, Any]] = []
    hashes_vistos: set[str] = set()

    for tarjeta in tarjetas:
        review = normalizar_review_html(
            tarjeta,
            appid,
            nombre_juego,
            scraped_at_utc,
        )

        if review is None:
            continue

        review_hash = review[
            "review_hash"
        ]

        if review_hash in hashes_vistos:
            continue

        hashes_vistos.add(review_hash)
        resultados.append(review)

    return resultados


def obtener_reviews_html(
    sesion: requests.Session,
    appid: int,
    nombre_juego: str,
    max_reviews: int,
) -> list[dict[str, Any]]:
    """
    Descarga y procesa la página HTML de respaldo.

    Este mecanismo puede devolver menos reseñas que el
    endpoint JSON; solo se utiliza cuando el principal falla.
    """
    respuesta = sesion.get(
        URL_REVIEWS_HTML.format(
            appid=appid
        ),
        timeout=(10, 30),
    )

    respuesta.raise_for_status()

    return parsear_reviews_html(
        respuesta.text,
        appid,
        nombre_juego,
        max_reviews,
    )


# ==========================================================
# LECTURA Y ESCRITURA DEL JSON
# ==========================================================

def cargar_reviews_existentes(
    ruta: Path = RUTA_SALIDA,
) -> list[dict[str, Any]]:
    """
    Lee el JSON existente.

    Esto permite actualizar un juego sin borrar
    las reseñas de los demás.
    """
    if not ruta.exists():
        return []

    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        contenido = json.load(archivo)

    if not isinstance(contenido, list):
        raise ValueError(
            "reviews_extra.json debe contener "
            "una lista JSON."
        )

    return contenido


def deduplicar_reviews(
    reviews: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Elimina reseñas repetidas usando review_hash.
    """
    unicas: dict[
        str,
        dict[str, Any],
    ] = {}

    for review in reviews:
        review_hash = str(
            review.get("review_hash")
            or ""
        ).strip()

        if not review_hash:
            continue

        unicas[review_hash] = review

    return list(
        unicas.values()
    )


def combinar_reviews(
    existentes: list[dict[str, Any]],
    nuevas: list[dict[str, Any]],
    appids_actualizados: set[int],
) -> list[dict[str, Any]]:
    """
    Reemplaza solamente las reseñas correspondientes
    a los appids procesados correctamente.

    Los demás juegos permanecen intactos.
    """
    conservadas = [
        review
        for review in existentes
        if int(
            review.get("appid", -1)
        )
        not in appids_actualizados
    ]

    return deduplicar_reviews(
        [
            *conservadas,
            *nuevas,
        ]
    )


def guardar_json_atomico(
    reviews: list[dict[str, Any]],
    ruta: Path = RUTA_SALIDA,
) -> None:
    """
    Guarda primero en un archivo temporal.

    Solo cuando la escritura termina correctamente,
    el archivo temporal reemplaza al JSON definitivo.
    """
    ruta.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_temporal = ruta.with_suffix(
        ruta.suffix + ".tmp"
    )

    with ruta_temporal.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            reviews,
            archivo,
            ensure_ascii=False,
            indent=2,
        )

    ruta_temporal.replace(ruta)


# ==========================================================
# VALIDACIÓN DEL JSON
# ==========================================================

def validar_reviews(
    reviews: list[dict[str, Any]],
) -> list[str]:
    """
    Revisa estructura, textos vacíos y duplicados.

    Retorna una lista de errores.
    Una lista vacía significa que el archivo es válido.
    """
    errores: list[str] = []
    hashes: set[str] = set()

    for indice, review in enumerate(
        reviews
    ):
        if not isinstance(review, dict):
            errores.append(
                f"Registro {indice}: "
                "no es un objeto JSON."
            )
            continue

        faltantes = (
            CAMPOS_REQUERIDOS
            .difference(review)
        )

        if faltantes:
            errores.append(
                f"Registro {indice}: "
                f"faltan {sorted(faltantes)}."
            )

        texto = str(
            review.get("text")
            or ""
        ).strip()

        if not texto:
            errores.append(
                f"Registro {indice}: "
                "texto vacío."
            )

        review_hash = str(
            review.get("review_hash")
            or ""
        ).strip()

        if review_hash in hashes:
            errores.append(
                f"Registro {indice}: "
                "review_hash duplicado."
            )
        elif review_hash:
            hashes.add(review_hash)

    return errores


def imprimir_resumen(
    reviews: list[dict[str, Any]],
) -> None:
    """
    Muestra un resumen por videojuego.
    """
    resumen: dict[
        int,
        dict[str, Any],
    ] = {}

    for review in reviews:
        appid = int(
            review["appid"]
        )

        fila = resumen.setdefault(
            appid,
            {
                "nombre": review.get(
                    "game_name",
                    "",
                ),
                "total": 0,
                "positivas": 0,
                "negativas": 0,
            },
        )

        fila["total"] += 1

        if review.get("voted_up") is True:
            fila["positivas"] += 1
        else:
            fila["negativas"] += 1

    print("\nRESUMEN DEL ARCHIVO")
    print("-" * 90)

    print(
        f"{'appid':>10}  "
        f"{'juego':35}  "
        f"{'total':>8}  "
        f"{'positivas':>10}  "
        f"{'negativas':>10}"
    )

    print("-" * 90)

    for appid in sorted(resumen):
        fila = resumen[appid]

        print(
            f"{appid:>10}  "
            f"{str(fila['nombre'])[:35]:35}  "
            f"{fila['total']:>8}  "
            f"{fila['positivas']:>10}  "
            f"{fila['negativas']:>10}"
        )

    print("-" * 90)

    print(
        f"Total general: "
        f"{len(reviews)} reseñas"
    )


# ==========================================================
# SELECCIÓN DE JUEGOS
# ==========================================================

def seleccionar_juegos(
    catalogo: list[dict[str, Any]],
    appids_solicitados: list[int] | None,
) -> list[dict[str, Any]]:
    """
    Selecciona todo el catálogo o únicamente
    los appids indicados en la terminal.
    """
    if not appids_solicitados:
        return catalogo

    solicitados = set(
        appids_solicitados
    )

    seleccionados = [
        juego
        for juego in catalogo
        if int(juego["appid"])
        in solicitados
    ]

    encontrados = {
        int(juego["appid"])
        for juego in seleccionados
    }

    faltantes = (
        solicitados
        .difference(encontrados)
    )

    if faltantes:
        raise ValueError(
            "Los siguientes appids no están "
            "activos en catalogo.json: "
            + ", ".join(
                map(
                    str,
                    sorted(faltantes),
                )
            )
        )

    return seleccionados


# ==========================================================
# EJECUCIÓN DEL SCRAPING
# ==========================================================

def ejecutar_scraping(
    juegos: list[dict[str, Any]],
    limite_por_juego: int,
    pausa: float,
) -> tuple[
    list[dict[str, Any]],
    set[int],
]:
    """
    Procesa cada videojuego.

    Primero utiliza el endpoint JSON.
    Si falla, intenta la página HTML con BeautifulSoup.
    """
    sesion = crear_sesion_http()

    nuevas_reviews: list[
        dict[str, Any]
    ] = []

    appids_exitosos: set[int] = set()

    try:
        for posicion, juego in enumerate(
            juegos,
            start=1,
        ):
            appid = int(
                juego["appid"]
            )

            nombre = str(
                juego.get("nombre")
                or appid
            )

            logging.info(
                "[%s/%s] Procesando %s (%s).",
                posicion,
                len(juegos),
                nombre,
                appid,
            )

            try:
                reviews_juego = (
                    obtener_reviews_api(
                        sesion,
                        appid,
                        nombre,
                        limite_por_juego,
                        pausa,
                    )
                )

            except (
                requests.RequestException,
                ValueError,
                RuntimeError,
            ) as error_api:

                logging.warning(
                    "Falló el endpoint JSON "
                    "para %s: %s",
                    appid,
                    error_api,
                )

                logging.warning(
                    "Se intentará el respaldo "
                    "HTML con BeautifulSoup."
                )

                try:
                    reviews_juego = (
                        obtener_reviews_html(
                            sesion,
                            appid,
                            nombre,
                            min(
                                limite_por_juego,
                                50,
                            ),
                        )
                    )

                except (
                    requests.RequestException,
                    ValueError,
                ) as error_html:

                    logging.error(
                        "También falló el HTML "
                        "para %s: %s",
                        appid,
                        error_html,
                    )

                    continue

            if not reviews_juego:
                logging.error(
                    "No se obtuvieron reseñas "
                    "para %s (%s).",
                    nombre,
                    appid,
                )
                continue

            nuevas_reviews.extend(
                reviews_juego
            )

            appids_exitosos.add(
                appid
            )

            logging.info(
                "%s (%s): %s reseñas válidas.",
                nombre,
                appid,
                len(reviews_juego),
            )

            if (
                posicion < len(juegos)
                and pausa > 0
            ):
                time.sleep(pausa)

    finally:
        sesion.close()

    return (
        nuevas_reviews,
        appids_exitosos,
    )


# ==========================================================
# ARGUMENTOS DE TERMINAL
# ==========================================================

def construir_parser() -> argparse.ArgumentParser:
    """
    Define las opciones disponibles para ejecutar
    el scraper desde la terminal.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Descarga y normaliza reseñas "
            "recientes para The Data Machine."
        )
    )

    parser.add_argument(
        "--limite",
        type=int,
        default=500,
        help=(
            "Cantidad máxima de reseñas "
            "por juego. Predeterminado: 500."
        ),
    )

    parser.add_argument(
        "--pausa",
        type=float,
        default=1.0,
        help=(
            "Segundos entre solicitudes. "
            "Predeterminado: 1.0."
        ),
    )

    parser.add_argument(
        "--appid",
        type=int,
        nargs="+",
        help=(
            "Procesa solamente los appids "
            "indicados."
        ),
    )

    parser.add_argument(
        "--reiniciar",
        action="store_true",
        help=(
            "Ignora el JSON anterior y "
            "genera uno nuevo."
        ),
    )

    parser.add_argument(
        "--validar",
        action="store_true",
        help=(
            "Valida reviews_extra.json "
            "sin conectarse a Steam."
        ),
    )

    return parser


# ==========================================================
# FUNCIÓN PRINCIPAL
# ==========================================================

def main() -> int:
    """
    Punto de entrada del módulo.

    Retorna:
        0 cuando la ejecución fue correcta.
        1 cuando se encontró un error.
    """
    configurar_logging()

    argumentos = (
        construir_parser()
        .parse_args()
    )

    if argumentos.limite <= 0:
        logging.error(
            "--limite debe ser mayor que cero."
        )
        return 1

    if argumentos.pausa < 0:
        logging.error(
            "--pausa no puede ser negativa."
        )
        return 1

    try:
        existentes = (
            cargar_reviews_existentes()
        )

    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as error:

        logging.error(
            "No se pudo leer el JSON "
            "existente: %s",
            error,
        )

        return 1

    # ------------------------------------------------------
    # MODO DE VALIDACIÓN
    # ------------------------------------------------------

    if argumentos.validar:

        if not RUTA_SALIDA.exists():
            logging.error(
                "No existe el archivo: %s",
                RUTA_SALIDA,
            )
            return 1

        errores = validar_reviews(
            existentes
        )

        imprimir_resumen(
            existentes
        )

        if errores:
            print(
                "\nERRORES ENCONTRADOS"
            )

            for error in errores[:20]:
                print(
                    f"- {error}"
                )

            if len(errores) > 20:
                print(
                    "- ... y "
                    f"{len(errores) - 20} "
                    "errores adicionales."
                )

            return 1

        print(
            "\nRESULTADO: "
            "ARCHIVO DE RESEÑAS VÁLIDO."
        )

        return 0

    # ------------------------------------------------------
    # CARGA Y SELECCIÓN DEL CATÁLOGO
    # ------------------------------------------------------

    try:
        catalogo = cargar_catalogo()

        juegos = seleccionar_juegos(
            catalogo,
            argumentos.appid,
        )

    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:

        logging.error(
            "No se pudo preparar "
            "el catálogo: %s",
            error,
        )

        return 1

    # ------------------------------------------------------
    # EJECUCIÓN DE LAS SOLICITUDES
    # ------------------------------------------------------

    nuevas, appids_exitosos = (
        ejecutar_scraping(
            juegos=juegos,
            limite_por_juego=(
                argumentos.limite
            ),
            pausa=argumentos.pausa,
        )
    )

    if not nuevas:
        logging.error(
            "La ejecución terminó sin reseñas. "
            "El archivo anterior no será modificado."
        )
        return 1

    # Si se indicó --reiniciar, se comienza con
    # una lista vacía. En caso contrario, se fusionan.
    base = (
        []
        if argumentos.reiniciar
        else existentes
    )

    resultado = combinar_reviews(
        base,
        nuevas,
        appids_exitosos,
    )

    errores = validar_reviews(
        resultado
    )

    if errores:
        logging.error(
            "El resultado tiene %s errores. "
            "No se guardará.",
            len(errores),
        )

        for error in errores[:20]:
            logging.error(
                error
            )

        return 1

    # ------------------------------------------------------
    # GUARDADO FINAL
    # ------------------------------------------------------

    try:
        guardar_json_atomico(
            resultado
        )

    except OSError as error:
        logging.error(
            "No se pudo guardar el archivo: %s",
            error,
        )
        return 1

    imprimir_resumen(
        resultado
    )

    print(
        f"\nArchivo generado: "
        f"{RUTA_SALIDA}"
    )

    print(
        "RESULTADO: SCRAPING "
        "COMPLETADO CORRECTAMENTE."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())