from __future__ import annotations

import py_compile
import sys
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN DE RUTAS
# ==========================================================

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

RUTA_PAGINA = RAIZ_PROYECTO / "pages" / "analisis.py"
RUTA_DASHBOARD = RAIZ_PROYECTO / "src" / "dashboard.py"
RUTA_ESTILOS = RAIZ_PROYECTO / "src" / "styles.py"


# Importación posterior a la configuración de sys.path.
from src.dashboard import (  # noqa: E402
    cargar_metadata_catalogo,
    cargar_resultados_nlp,
    construir_distribucion_sentimiento,
    construir_matriz_confusion,
    generar_nube_palabras,
    obtener_appids_disponibles,
    obtener_datos_juego,
)


# ==========================================================
# ELEMENTOS QUE DEBE CONTENER LA PÁGINA
# ==========================================================

FRAGMENTOS_REQUERIDOS = {
    "configuración de página": "st.set_page_config(",
    "caché de Streamlit": "@st.cache_data",
    "selector por appid": 'st.session_state["selected_appid"]',
    "compatibilidad por nombre": 'st.session_state["selected_game"]',
    "cuatro pestañas": "st.tabs(",
    "pestaña resumen": '"Resumen"',
    "pestaña sentimiento": '"Sentimiento"',
    "pestaña temas": '"Temas y nube"',
    "pestaña reseñas": '"Reseñas y descarga"',
    "gráficas Plotly": "st.plotly_chart(",
    "tabla interactiva": "st.dataframe(",
    "descarga de archivos": "st.download_button(",
    "nube de palabras": "crear_nube_cacheada(",
    "regreso al catálogo": 'st.switch_page("pages/homepage.py")',
}


def registrar_error(mensaje: str, errores: list[str]) -> None:
    """Guarda e imprime un error de validación."""
    errores.append(mensaje)
    print(f"[ERROR] {mensaje}")


def main() -> int:
    """Valida la estructura y las fuentes de datos de analisis.py."""
    errores: list[str] = []

    print("=" * 72)
    print("VALIDACIÓN DE LA PÁGINA DE ANÁLISIS — THE DATA MACHINE")
    print("=" * 72)

    # ------------------------------------------------------
    # 1. EXISTENCIA DE ARCHIVOS
    # ------------------------------------------------------

    for ruta in (RUTA_PAGINA, RUTA_DASHBOARD, RUTA_ESTILOS):
        if ruta.exists():
            print(f"[OK] Archivo localizado: {ruta.relative_to(RAIZ_PROYECTO)}")
        else:
            registrar_error(f"No existe el archivo: {ruta}", errores)

    if errores:
        return 1

    # ------------------------------------------------------
    # 2. SINTAXIS DE PYTHON
    # ------------------------------------------------------

    for ruta in (RUTA_PAGINA, RUTA_DASHBOARD):
        try:
            py_compile.compile(str(ruta), doraise=True)
            print(f"[OK] Sintaxis válida: {ruta.relative_to(RAIZ_PROYECTO)}")
        except py_compile.PyCompileError as error:
            registrar_error(f"Error de sintaxis en {ruta.name}: {error}", errores)

    # ------------------------------------------------------
    # 3. COMPONENTES OBLIGATORIOS DE LA INTERFAZ
    # ------------------------------------------------------

    contenido = RUTA_PAGINA.read_text(encoding="utf-8")

    for nombre, fragmento in FRAGMENTOS_REQUERIDOS.items():
        if fragmento in contenido:
            print(f"[OK] Componente presente: {nombre}")
        else:
            registrar_error(
                f"Falta el componente '{nombre}' ({fragmento}).",
                errores,
            )

    # ------------------------------------------------------
    # 4. CARGA REAL DE LOS RESULTADOS DEL PROYECTO
    # ------------------------------------------------------

    try:
        reviews, metricas, temas, tags = cargar_resultados_nlp()
        metadata = cargar_metadata_catalogo(metricas["appid"].tolist())
        appids = obtener_appids_disponibles(metadata, metricas, reviews)
    except (FileNotFoundError, KeyError, OSError, ValueError) as error:
        registrar_error(f"No se pudieron cargar los datos reales: {error}", errores)
        return 1

    if len(appids) != 10:
        registrar_error(
            f"Se esperaban 10 juegos y se encontraron {len(appids)}.",
            errores,
        )
    else:
        print("[OK] Juegos disponibles para el selector: 10")

    if len(reviews) != 5000:
        registrar_error(
            f"Se esperaban 5000 reseñas y se encontraron {len(reviews)}.",
            errores,
        )
    else:
        print("[OK] Reseñas disponibles para el dashboard: 5000")

    # ------------------------------------------------------
    # 5. VALIDACIÓN DE LAS CUATRO SECCIONES POR JUEGO
    # ------------------------------------------------------

    for appid in appids:
        try:
            datos = obtener_datos_juego(
                appid,
                metadata,
                reviews,
                metricas,
                temas,
                tags,
            )

            distribucion = construir_distribucion_sentimiento(datos["reviews"])
            matriz = construir_matriz_confusion(
                datos["metricas"]["confusion_matrix"]
            )

            if len(datos["reviews"]) != 500:
                raise ValueError("cantidad de reseñas distinta de 500")

            if len(datos["temas"]) != 15:
                raise ValueError("cantidad de temas distinta de 15")

            if len(datos["tags"]) != 15:
                raise ValueError("cantidad de tags distinta de 15")

            if int(distribucion["count"].sum()) != 1000:
                raise ValueError(
                    "la distribución combinada VADER/Steam no suma 1000"
                )

            if matriz.shape != (2, 2):
                raise ValueError("la matriz de confusión no es 2 x 2")

            print(
                f"[OK] {appid} | {datos['metadata']['name']} | "
                "resumen, sentimiento, temas y reseñas disponibles"
            )

        except (KeyError, TypeError, ValueError) as error:
            registrar_error(f"Fallo en appid {appid}: {error}", errores)

    # ------------------------------------------------------
    # 6. NUBE DE PALABRAS
    # ------------------------------------------------------

    if appids:
        datos_primero = obtener_datos_juego(
            appids[0],
            metadata,
            reviews,
            metricas,
            temas,
            tags,
        )

        try:
            imagen = generar_nube_palabras(datos_primero["reviews"]["text"])
            if imagen.size[0] <= 0 or imagen.size[1] <= 0:
                raise ValueError("la imagen generada tiene dimensiones inválidas")
            print(f"[OK] Nube de palabras generada: {imagen.size[0]} x {imagen.size[1]}")
        except (TypeError, ValueError) as error:
            registrar_error(f"No se pudo generar la nube: {error}", errores)

    # ------------------------------------------------------
    # RESULTADO FINAL
    # ------------------------------------------------------

    print("=" * 72)

    if errores:
        print(f"RESULTADO: PÁGINA NO APROBADA ({len(errores)} error(es)).")
        return 1

    print("RESULTADO: PÁGINA DE ANÁLISIS PREPARADA CORRECTAMENTE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
