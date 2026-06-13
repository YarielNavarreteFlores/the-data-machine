from __future__ import annotations

import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ),
    )


from src.production import (
    preparar_datos_produccion,
)


def main() -> int:
    """
    Genera data/production/ desde las fuentes locales validadas.
    """
    try:
        manifiesto = (
            preparar_datos_produccion()
        )

    except (
        FileNotFoundError,
        OSError,
        ValueError,
    ) as error:
        print(
            f"[ERROR] No se pudo generar "
            f"el paquete: {error}"
        )
        return 1

    tamano_mb = (
        manifiesto[
            "total_production_bytes"
        ]
        / (1024 * 1024)
    )

    print("=" * 72)
    print("PAQUETE DE PRODUCCIÓN — THE DATA MACHINE")
    print("=" * 72)
    print(
        "[OK] Juegos incluidos: "
        f"{len(manifiesto['catalog_appids'])}"
    )
    print(
        "[OK] Tamaño total: "
        f"{tamano_mb:.2f} MB"
    )

    for nombre, datos in (
        manifiesto["files"].items()
    ):
        filas = datos.get(
            "rows",
            "—",
        )

        print(
            f"[OK] {nombre} | "
            f"rows={filas} | "
            f"bytes={datos['bytes']}"
        )

    print("=" * 72)
    print(
        "RESULTADO: PAQUETE DE PRODUCCIÓN "
        "GENERADO CORRECTAMENTE."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
