from __future__ import annotations

import sys
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN DE LA RUTA DEL PROYECTO
# ==========================================================

# Obtiene la carpeta raíz de The Data Machine.
#
# __file__ apunta a:
# the-data-machine/scripts/validar_dashboard.py
#
# parents[1] apunta a:
# the-data-machine/
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

# Cuando un archivo dentro de scripts/ se ejecuta directamente,
# Python agrega scripts/ a sus rutas de búsqueda, pero no siempre
# agrega la raíz del proyecto. Por eso se incorpora manualmente.
#
# Esto permite importar:
# from src.dashboard import ...
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ_PROYECTO),
    )


from src.dashboard import (
    cargar_metadata_catalogo,
    cargar_resultados_nlp,
    construir_distribucion_sentimiento,
    construir_matriz_confusion,
    obtener_appids_disponibles,
    obtener_datos_juego,
)

def main() -> int:
    """Valida que el dashboard pueda construirse para los 10 juegos."""
    print("=" * 68)
    print("VALIDACIÓN DEL DASHBOARD — THE DATA MACHINE")
    print("=" * 68)

    try:
        reviews, metricas, temas, tags = cargar_resultados_nlp()
        metadata = cargar_metadata_catalogo(metricas["appid"].tolist())
        appids = obtener_appids_disponibles(metadata, metricas, reviews)

        errores: list[str] = []

        if len(appids) != 10:
            errores.append(
                f"Se esperaban 10 juegos disponibles y se encontraron {len(appids)}."
            )

        total_reviews = 0

        for appid in appids:
            datos = obtener_datos_juego(
                appid,
                metadata,
                reviews,
                metricas,
                temas,
                tags,
            )

            nombre = datos["metadata"]["name"]
            reviews_juego = datos["reviews"]
            metricas_juego = datos["metricas"]
            temas_juego = datos["temas"]
            tags_juego = datos["tags"]

            total_reviews += len(reviews_juego)

            distribucion = construir_distribucion_sentimiento(reviews_juego)
            matriz = construir_matriz_confusion(
                metricas_juego["confusion_matrix"]
            )

            if len(reviews_juego) != 500:
                errores.append(
                    f"{nombre}: se esperaban 500 reseñas y hay {len(reviews_juego)}."
                )

            if len(temas_juego) != 15:
                errores.append(
                    f"{nombre}: se esperaban 15 temas y hay {len(temas_juego)}."
                )

            if len(tags_juego) != 15:
                errores.append(
                    f"{nombre}: se esperaban 15 tags y hay {len(tags_juego)}."
                )

            total_vader = int(
                distribucion[distribucion["source"] == "VADER"]["count"].sum()
            )
            total_steam = int(
                distribucion[distribucion["source"] == "Steam"]["count"].sum()
            )

            if total_vader != len(reviews_juego):
                errores.append(f"{nombre}: el conteo VADER no coincide.")

            if total_steam != len(reviews_juego):
                errores.append(f"{nombre}: el conteo Steam no coincide.")

            evaluables = int(metricas_juego["evaluable_reviews"])
            if int(matriz.values.sum()) != evaluables:
                errores.append(
                    f"{nombre}: la matriz no suma {evaluables} reseñas evaluables."
                )

            print(
                f"[OK] {appid} | {nombre} | "
                f"reviews={len(reviews_juego)} | "
                f"temas={len(temas_juego)} | tags={len(tags_juego)}"
            )

        print("-" * 68)
        print(f"Juegos disponibles: {len(appids)}")
        print(f"Reseñas disponibles: {total_reviews}")

        if errores:
            print("\nERRORES")
            for error in errores:
                print(f"- {error}")
            print("\nRESULTADO: DASHBOARD NO APROBADO.")
            return 1

        print("RESULTADO: DATOS DEL DASHBOARD APROBADOS.")
        return 0

    except Exception as error:
        print(f"[ERROR] {error}")
        print("RESULTADO: DASHBOARD NO APROBADO.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
