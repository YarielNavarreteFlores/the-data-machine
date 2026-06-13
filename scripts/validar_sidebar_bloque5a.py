from __future__ import annotations

import ast
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ),
    )


RUTA_STYLES = (
    RAIZ
    / "src"
    / "styles.py"
)

RUTA_CONFIG = (
    RAIZ
    / ".streamlit"
    / "config.toml"
)

RUTA_MENU = (
    RAIZ
    / "src"
    / "menu_usuario.py"
)


def main() -> int:
    errores: list[str] = []

    print("=" * 72)
    print("VALIDACIÓN DE LA BARRA LATERAL — BLOQUE 5A")
    print("=" * 72)

    for ruta in (
        RUTA_STYLES,
        RUTA_CONFIG,
        RUTA_MENU,
    ):
        if not ruta.exists():
            errores.append(
                f"No existe: {ruta}"
            )
            print(
                f"[ERROR] Archivo ausente: "
                f"{ruta.relative_to(RAIZ)}"
            )
        else:
            print(
                f"[OK] Archivo localizado: "
                f"{ruta.relative_to(RAIZ)}"
            )

    if errores:
        return 1

    styles = RUTA_STYLES.read_text(
        encoding="utf-8"
    )

    # Validar sintaxis Python.
    ast.parse(
        styles,
        filename=str(RUTA_STYLES),
    )

    print(
        "[OK] Sintaxis válida: src/styles.py"
    )

    # Esta regla ocultaba también el botón de la barra lateral.
    regla_prohibida = (
        "#MainMenu, footer, header "
        "{ visibility: hidden; }"
    )

    if regla_prohibida in styles:
        errores.append(
            "styles.py todavía oculta todo el header."
        )

        print(
            "[ERROR] styles.py todavía oculta "
            "todo el header."
        )
    else:
        print(
            "[OK] styles.py no oculta "
            "todo el header."
        )

    requeridos = [
        'header[data-testid="stHeader"]',
        'stSidebarCollapsedControl',
        'visibility: visible !important',
    ]

    for marcador in requeridos:
        if marcador not in styles:
            errores.append(
                f"Falta marcador CSS: {marcador}"
            )

            print(
                f"[ERROR] Falta marcador CSS: "
                f"{marcador}"
            )
        else:
            print(
                f"[OK] Marcador CSS presente: "
                f"{marcador}"
            )

    config = RUTA_CONFIG.read_text(
        encoding="utf-8"
    )

    if (
        "showSidebarNavigation = false"
        not in config
    ):
        errores.append(
            "config.toml no oculta la "
            "navegación técnica."
        )

        print(
            "[ERROR] Falta "
            "showSidebarNavigation = false."
        )
    else:
        print(
            "[OK] Navegación técnica "
            "automática oculta."
        )

    menu = RUTA_MENU.read_text(
        encoding="utf-8"
    )

    if "with st.sidebar:" not in menu:
        errores.append(
            "menu_usuario.py no crea contenido "
            "en la barra lateral."
        )

        print(
            "[ERROR] menu_usuario.py no usa "
            "st.sidebar."
        )
    else:
        print(
            "[OK] Menú personalizado "
            "renderizado en st.sidebar."
        )

    print("=" * 72)

    if errores:
        print(
            "RESULTADO: BARRA LATERAL "
            f"NO APROBADA ({len(errores)} errores)."
        )

        for error in errores:
            print(
                f"- {error}"
            )

        return 1

    print(
        "RESULTADO: CONFIGURACIÓN DE "
        "BARRA LATERAL APROBADA."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
