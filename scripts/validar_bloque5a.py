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


ARCHIVOS = {
    "config": (
        RAIZ
        / ".streamlit"
        / "config.toml"
    ),
    "menu": (
        RAIZ
        / "src"
        / "menu_usuario.py"
    ),
    "homepage": (
        RAIZ
        / "pages"
        / "homepage.py"
    ),
    "analisis": (
        RAIZ
        / "pages"
        / "analisis.py"
    ),
}


def validar_sintaxis(
    ruta: Path,
) -> None:
    """
    Comprueba la sintaxis Python sin ejecutar Streamlit.
    """
    ast.parse(
        ruta.read_text(
            encoding="utf-8",
        ),
        filename=str(ruta),
    )


def main() -> int:
    errores: list[str] = []

    print("=" * 72)
    print("VALIDACIÓN DEL BLOQUE 5A — EXPERIENCIA Y CIERRE DE SESIÓN")
    print("=" * 72)

    for nombre, ruta in ARCHIVOS.items():
        if not ruta.exists():
            errores.append(
                f"No existe: {ruta}"
            )
            print(
                f"[ERROR] Archivo ausente: "
                f"{ruta.relative_to(RAIZ)}"
            )
            continue

        print(
            f"[OK] Archivo localizado: "
            f"{ruta.relative_to(RAIZ)}"
        )

        if ruta.suffix == ".py":
            try:
                validar_sintaxis(ruta)

                print(
                    f"[OK] Sintaxis válida: "
                    f"{ruta.relative_to(RAIZ)}"
                )

            except SyntaxError as error:
                errores.append(
                    str(error)
                )

                print(
                    f"[ERROR] Sintaxis inválida: "
                    f"{error}"
                )

    if not errores:
        config = ARCHIVOS[
            "config"
        ].read_text(
            encoding="utf-8"
        )

        requeridos_config = [
            "showSidebarNavigation = false",
            'toolbarMode = "minimal"',
            "headless = true",
            "gatherUsageStats = false",
        ]

        for marcador in requeridos_config:
            if marcador not in config:
                errores.append(
                    f"config.toml no contiene: "
                    f"{marcador}"
                )

                print(
                    f"[ERROR] Falta configuración: "
                    f"{marcador}"
                )

        menu = ARCHIVOS[
            "menu"
        ].read_text(
            encoding="utf-8"
        )

        requeridos_menu = [
            "def renderizar_menu_usuario",
            "st.sidebar",
            "st.page_link",
            "Cerrar sesión",
            "cerrar_sesion",
            'st.switch_page(',
            '"pages/login.py"',
        ]

        for marcador in requeridos_menu:
            if marcador not in menu:
                errores.append(
                    f"menu_usuario.py no contiene: "
                    f"{marcador}"
                )

                print(
                    f"[ERROR] Falta marcador en menú: "
                    f"{marcador}"
                )

        for pagina in (
            "homepage",
            "analisis",
        ):
            contenido = ARCHIVOS[
                pagina
            ].read_text(
                encoding="utf-8"
            )

            if (
                "renderizar_menu_usuario"
                not in contenido
            ):
                errores.append(
                    f"{pagina}.py no usa "
                    "renderizar_menu_usuario."
                )

                print(
                    f"[ERROR] {pagina}.py no "
                    "renderiza el menú lateral."
                )

            else:
                print(
                    f"[OK] {pagina}.py integra "
                    "el menú lateral."
                )

        homepage = ARCHIVOS[
            "homepage"
        ].read_text(
            encoding="utf-8"
        )

        if "Millones de reseñas." in homepage:
            errores.append(
                "La Homepage conserva el texto "
                "'Millones de reseñas.'."
            )

            print(
                "[ERROR] La cifra principal de "
                "la Homepage sigue siendo imprecisa."
            )

        else:
            print(
                "[OK] La Homepage ya no afirma "
                "'Millones de reseñas.'."
            )

    print("=" * 72)

    if errores:
        print(
            "RESULTADO: BLOQUE 5A NO APROBADO "
            f"({len(errores)} errores)."
        )

        for error in errores:
            print(
                f"- {error}"
            )

        return 1

    print(
        "RESULTADO: BLOQUE 5A "
        "PREPARADO CORRECTAMENTE."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
