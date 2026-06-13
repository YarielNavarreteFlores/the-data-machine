from __future__ import annotations

import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ),
    )


from src.data_paths import (
    resolver_directorio_nlp,
    resolver_ruta_metadata,
)
from src.production import (
    RUTA_PRODUCCION,
    validar_datos_produccion,
)


def main() -> int:
    """
    Valida integridad y resolución de rutas de producción.
    """
    print("=" * 72)
    print("VALIDACIÓN DEL BLOQUE 5B — DATOS DE PRODUCCIÓN")
    print("=" * 72)

    errores = validar_datos_produccion(
        RUTA_PRODUCCION
    )

    for error in errores:
        print(
            f"[ERROR] {error}"
        )

    ruta_metadata = (
        resolver_ruta_metadata()
    )

    ruta_nlp = (
        resolver_directorio_nlp()
    )

    if (
        ruta_metadata
        != (
            RUTA_PRODUCCION
            / "catalogo_10_juegos.csv"
        )
    ):
        errores.append(
            "La aplicación no prioriza "
            "el catálogo de producción."
        )
    else:
        print(
            "[OK] Catálogo de producción "
            "seleccionado."
        )

    if ruta_nlp != RUTA_PRODUCCION:
        errores.append(
            "La aplicación no prioriza "
            "los resultados NLP de producción."
        )
    else:
        print(
            "[OK] Directorio NLP de "
            "producción seleccionado."
        )

    print("=" * 72)

    if errores:
        print(
            "RESULTADO: BLOQUE 5B "
            f"NO APROBADO "
            f"({len(errores)} errores)."
        )
        return 1

    print(
        "RESULTADO: DATOS DE PRODUCCIÓN "
        "APROBADOS."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
