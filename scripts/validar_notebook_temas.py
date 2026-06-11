from __future__ import annotations

import sys
from pathlib import Path

import nbformat


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_NOTEBOOK = RAIZ_PROYECTO / "notebooks" / "03_temas.ipynb"


def main() -> int:
    """Comprueba que el notebook exista y no contenga errores de ejecución."""
    if not RUTA_NOTEBOOK.exists():
        print(f"[ERROR] No existe el notebook: {RUTA_NOTEBOOK}")
        return 1

    notebook = nbformat.read(RUTA_NOTEBOOK, as_version=4)

    errores = []
    celdas_codigo = 0
    celdas_ejecutadas = 0

    for indice, celda in enumerate(notebook.cells):
        if celda.cell_type != "code":
            continue

        celdas_codigo += 1

        if celda.execution_count is not None:
            celdas_ejecutadas += 1

        for salida in celda.get("outputs", []):
            if salida.get("output_type") == "error":
                errores.append(
                    {
                        "celda": indice,
                        "tipo": salida.get("ename", "Error"),
                        "mensaje": salida.get("evalue", ""),
                    }
                )

    print("=" * 68)
    print("VALIDACIÓN DEL NOTEBOOK 03_TEMAS")
    print("=" * 68)
    print(f"Celdas de código: {celdas_codigo}")
    print(f"Celdas ejecutadas: {celdas_ejecutadas}")
    print(f"Errores encontrados: {len(errores)}")

    if errores:
        print("\nDETALLE DE ERRORES")
        for error in errores:
            print(
                f"- Celda {error['celda']}: "
                f"{error['tipo']} — {error['mensaje']}"
            )
        return 1

    if celdas_ejecutadas != celdas_codigo:
        print(
            "[ERROR] El notebook no fue ejecutado completamente. "
            "Ejecuta todas las celdas antes de validarlo."
        )
        return 1

    print("RESULTADO: NOTEBOOK EJECUTADO SIN ERRORES.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
