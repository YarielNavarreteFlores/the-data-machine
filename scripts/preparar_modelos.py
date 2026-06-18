from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ),
    )


import pandas as pd

from src.data_paths import RUTA_PRODUCCION
from src.modelos import (
    entrenar_clasificacion,
    entrenar_regresion_completa,
)


# La fuente es el paquete de producción ya analizado por VADER.
RUTA_REVIEWS = RUTA_PRODUCCION / "reviews_analizadas.csv"

RUTA_CLASIFICACION = RUTA_PRODUCCION / "modelos_clasificacion.json"
RUTA_REGRESION = RUTA_PRODUCCION / "modelos_regresion.json"


def _guardar_json(
    contenido: dict[str, Any],
    ruta: Path,
) -> None:
    """Escribe un JSON UTF-8 mediante una ruta temporal (escritura atómica)."""
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")

    with temporal.open("w", encoding="utf-8") as archivo:
        json.dump(
            contenido,
            archivo,
            ensure_ascii=False,
            indent=2,
        )

    temporal.replace(ruta)


def main() -> int:
    """
    Entrena los modelos de aprendizaje y guarda sus métricas como JSON.

    No reentrena nada en la app: pages/analisis.py solo lee estos archivos.
    """
    if not RUTA_REVIEWS.exists():
        print(f"[ERROR] No existe la fuente: {RUTA_REVIEWS}")
        return 1

    reviews = pd.read_csv(
        RUTA_REVIEWS,
        low_memory=False,
    )

    try:
        clasificacion = entrenar_clasificacion(reviews)
        regresion = entrenar_regresion_completa(reviews)
    except (ValueError, KeyError) as error:
        print(f"[ERROR] No se pudieron entrenar los modelos: {error}")
        return 1

    _guardar_json(clasificacion, RUTA_CLASIFICACION)
    _guardar_json(regresion, RUTA_REGRESION)

    print("=" * 72)
    print("MODELOS DE APRENDIZAJE — THE DATA MACHINE")
    print("=" * 72)

    print(
        "[OK] Clasificación supervisada vs VADER "
        f"(n_test={clasificacion['n_test']}):"
    )
    for nombre, metricas in clasificacion["modelos"].items():
        print(
            f"     - {nombre:22s} "
            f"accuracy={metricas['accuracy']:.3f} | "
            f"balanced={metricas['balanced_accuracy']:.3f} | "
            f"f1={metricas['f1']:.3f}"
        )

    print(
        "[OK] Regresión weighted_vote_score "
        f"(n_test={regresion['n_test']}): "
        f"R2={regresion['r2']:.3f} | "
        f"MAE={regresion['mae']:.4f} | "
        f"RMSE={regresion['rmse']:.4f}"
    )

    print("=" * 72)
    print(f"[OK] {RUTA_CLASIFICACION.name} y {RUTA_REGRESION.name} guardados.")
    print("RESULTADO: MODELOS GENERADOS CORRECTAMENTE.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
