from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


ARCHIVOS = {
    "app": RAIZ / "app.py",
    "homepage": RAIZ / "pages" / "homepage.py",
    "analisis": RAIZ / "pages" / "analisis.py",
    "navigation": RAIZ / "src" / "navigation.py",
    "catalogo": RAIZ / "config" / "catalogo.json",
}


MARCADORES = {
    "app": [
        "inicializar_sesion",
        "consumir_appid_query",
        'st.switch_page("pages/login.py")',
        'st.switch_page("pages/homepage.py")',
        'st.switch_page("pages/analisis.py")',
    ],
    "homepage": [
        "data-appid",
        "def abrir_analisis",
        "def renderizar_categoria",
        "st.button",
        "establecer_juego",
        'st.switch_page("pages/analisis.py")',
    ],
    "analisis": [
        "requerir_autenticacion",
        "consumir_appid_query",
        "establecer_juego",
        'st.switch_page("pages/homepage.py")',
    ],
    "navigation": [
        "def inicializar_sesion",
        "def convertir_appid",
        "def establecer_juego",
        "def requerir_autenticacion",
        "def consumir_appid_query",
    ],
}


def normalizar_codigo(texto: str) -> str:
    """
    Elimina espacios, saltos de línea y diferencias de comillas.

    Permite validar llamadas que estén distribuidas en varias líneas,
    como st.switch_page(...).
    """
    sin_espacios = re.sub(
        r"\s+",
        "",
        texto,
    )

    return sin_espacios.replace(
        "'",
        '"',
    )


def validar_sintaxis(ruta: Path) -> None:
    """Comprueba la sintaxis sin ejecutar Streamlit."""
    ast.parse(
        ruta.read_text(encoding="utf-8"),
        filename=str(ruta),
    )


def main() -> int:
    errores: list[str] = []

    print("=" * 72)
    print("VALIDACIÓN DE INTEGRACIÓN 4C — THE DATA MACHINE")
    print("=" * 72)

    for nombre, ruta in ARCHIVOS.items():
        if not ruta.exists():
            errores.append(f"No existe: {ruta}")
            print(f"[ERROR] Archivo ausente: {ruta}")
            continue

        print(f"[OK] Archivo localizado: {ruta.relative_to(RAIZ)}")

        if ruta.suffix == ".py":
            try:
                validar_sintaxis(ruta)
                print(f"[OK] Sintaxis válida: {ruta.relative_to(RAIZ)}")
            except SyntaxError as error:
                errores.append(str(error))
                print(f"[ERROR] Sintaxis inválida: {error}")

    for nombre, marcadores in MARCADORES.items():
        ruta = ARCHIVOS[nombre]

        if not ruta.exists():
            continue

        contenido = ruta.read_text(
            encoding="utf-8"
        )

        contenido_normalizado = normalizar_codigo(
            contenido
        )

        for marcador in marcadores:
            marcador_normalizado = normalizar_codigo(
                marcador
            )

            if (
                marcador_normalizado
                not in contenido_normalizado
            ):
                errores.append(
                    f"{ruta.relative_to(RAIZ)} "
                    f"no contiene {marcador!r}"
                )

                print(
                    f"[ERROR] Falta marcador en "
                    f"{ruta.relative_to(RAIZ)}: "
                    f"{marcador}"
                )

    catalogo = json.loads(
        ARCHIVOS["catalogo"].read_text(encoding="utf-8")
    )

    appids = [
        int(juego["appid"])
        for juego in catalogo.get("juegos", [])
        if juego.get("activo", True)
    ]

    if len(appids) != 10:
        errores.append(
            f"Se esperaban 10 appids activos y se encontraron {len(appids)}."
        )
    else:
        print("[OK] Catálogo oficial: 10 appids activos.")

    if len(appids) != len(set(appids)):
        errores.append("Existen appids repetidos en el catálogo.")
    else:
        print("[OK] Los appids del catálogo son únicos.")

    # La Homepage no debe navegar con href hacia ?appid=,
    # porque una recarga completa puede iniciar otra sesión.
    contenido_homepage = ARCHIVOS["homepage"].read_text(
        encoding="utf-8"
    )

    if re.search(
        r'href\\s*=\\s*["\\\']\\?appid=',
        contenido_homepage,
    ):
        errores.append(
            "homepage.py conserva enlaces href para navegar por appid."
        )
        print(
            "[ERROR] homepage.py conserva enlaces HTML que "
            "pueden perder la sesión."
        )
    else:
        print(
            "[OK] Homepage navega sin enlaces HTML que "
            "reinicien la sesión."
        )

    # El bypass temporal no debe permanecer en app.py.
    contenido_app = ARCHIVOS["app"].read_text(encoding="utf-8")

    if 'st.session_state["authenticated"] = True' in contenido_app:
        errores.append("app.py conserva el bypass de autenticación.")
        print("[ERROR] app.py conserva autenticación automática.")
    else:
        print("[OK] app.py no contiene autenticación automática.")

    print("=" * 72)

    if errores:
        print(f"RESULTADO: INTEGRACIÓN 4C NO APROBADA ({len(errores)} errores).")
        for error in errores:
            print(f"- {error}")
        return 1

    print("RESULTADO: INTEGRACIÓN 4C PREPARADA CORRECTAMENTE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
