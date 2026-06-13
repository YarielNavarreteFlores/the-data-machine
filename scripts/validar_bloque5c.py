from __future__ import annotations

import ast
import importlib
import importlib.metadata
import sys
import tomllib
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

if str(RAIZ) not in sys.path:
    sys.path.insert(
        0,
        str(RAIZ),
    )


RUTA_REQUIREMENTS = RAIZ / "requirements.txt"
RUTA_CONFIG = RAIZ / ".streamlit" / "config.toml"
RUTA_APP = RAIZ / "app.py"
RUTA_PRODUCCION = RAIZ / "data" / "production"

DEPENDENCIAS = {
    "beautifulsoup4": ("4.14.3", "bs4"),
    "nltk": ("3.9.4", "nltk"),
    "numpy": ("2.4.6", "numpy"),
    "pandas": ("3.0.3", "pandas"),
    "plotly": ("6.8.0", "plotly"),
    "requests": ("2.34.2", "requests"),
    "scikit-learn": ("1.9.0", "sklearn"),
    "streamlit": ("1.58.0", "streamlit"),
    "vaderSentiment": ("3.3.2", "vaderSentiment"),
    "wordcloud": ("1.9.6", "wordcloud"),
}

ARCHIVOS_PRODUCCION = (
    "catalogo_10_juegos.csv",
    "reviews_analizadas.csv",
    "metricas_sentimiento.json",
    "temas_tfidf.csv",
    "tags_steam.csv",
    "manifest.json",
)


def leer_requirements() -> dict[str, str]:
    """
    Lee el archivo usando UTF-8 estricto.
    """
    datos = RUTA_REQUIREMENTS.read_bytes()

    if (
        datos.startswith(b"\xff\xfe")
        or datos.startswith(b"\xfe\xff")
        or b"\x00" in datos
    ):
        raise ValueError(
            "requirements.txt continúa en UTF-16."
        )

    if datos.startswith(b"\xef\xbb\xbf"):
        raise ValueError(
            "requirements.txt contiene BOM UTF-8."
        )

    contenido = datos.decode("utf-8")
    resultado: dict[str, str] = {}

    for linea in contenido.splitlines():
        linea = linea.strip()

        if not linea or linea.startswith("#"):
            continue

        if "==" not in linea:
            raise ValueError(
                f"Dependencia sin versión fija: {linea}"
            )

        paquete, version = linea.split(
            "==",
            maxsplit=1,
        )

        paquete = paquete.strip()
        version = version.strip()

        if paquete in resultado:
            raise ValueError(
                f"Dependencia repetida: {paquete}"
            )

        resultado[paquete] = version

    return resultado


def main() -> int:
    errores: list[str] = []

    print("=" * 72)
    print("VALIDACIÓN DEL BLOQUE 5C — DEPENDENCIAS Y DESPLIEGUE")
    print("=" * 72)

    version_python = (
        f"{sys.version_info.major}."
        f"{sys.version_info.minor}."
        f"{sys.version_info.micro}"
    )

    print(
        f"[INFO] Python activo: {version_python}"
    )

    if sys.version_info[:2] != (3, 12):
        errores.append(
            "El entorno de despliegue debe usar Python 3.12."
        )
        print(
            "[ERROR] Debes ejecutar esta validación "
            "desde el entorno Python 3.12."
        )
    else:
        print(
            "[OK] Versión de Python compatible con "
            "Streamlit Community Cloud: 3.12."
        )

    for ruta in (
        RUTA_REQUIREMENTS,
        RUTA_CONFIG,
        RUTA_APP,
        RUTA_PRODUCCION,
    ):
        if not ruta.exists():
            errores.append(
                f"No existe {ruta.relative_to(RAIZ)}."
            )
            print(
                f"[ERROR] Archivo o directorio ausente: "
                f"{ruta.relative_to(RAIZ)}"
            )
        else:
            print(
                f"[OK] Localizado: "
                f"{ruta.relative_to(RAIZ)}"
            )

    if errores:
        print("=" * 72)
        print(
            f"RESULTADO: BLOQUE 5C NO APROBADO "
            f"({len(errores)} errores)."
        )
        return 1

    try:
        requirements = leer_requirements()
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
    ) as error:
        errores.append(str(error))
        print(
            f"[ERROR] requirements.txt inválido: {error}"
        )
        requirements = {}

    esperado = {
        paquete: datos[0]
        for paquete, datos
        in DEPENDENCIAS.items()
    }

    if requirements != esperado:
        errores.append(
            "Las dependencias no coinciden con "
            "la lista aprobada."
        )
        print(
            "[ERROR] requirements.txt no contiene "
            "la lista exacta aprobada."
        )
    else:
        print(
            "[OK] requirements.txt está en UTF-8, "
            "sin BOM y con versiones fijas."
        )

    for paquete, (
        version_esperada,
        modulo,
    ) in DEPENDENCIAS.items():
        try:
            importlib.import_module(modulo)

            version_instalada = (
                importlib.metadata.version(
                    paquete
                )
            )

            if version_instalada != version_esperada:
                raise RuntimeError(
                    f"versión instalada "
                    f"{version_instalada}; "
                    f"esperada {version_esperada}"
                )

            print(
                f"[OK] {paquete}=={version_instalada}"
            )

        except (
            ImportError,
            importlib.metadata.PackageNotFoundError,
            RuntimeError,
        ) as error:
            errores.append(
                f"{paquete}: {error}"
            )
            print(
                f"[ERROR] {paquete}: {error}"
            )

    try:
        with RUTA_CONFIG.open("rb") as archivo:
            config = tomllib.load(archivo)

        cliente = config.get("client", {})

        if (
            cliente.get("showErrorDetails")
            != "none"
        ):
            raise ValueError(
                "showErrorDetails debe ser 'none'."
            )

        if (
            cliente.get("toolbarMode")
            != "minimal"
        ):
            raise ValueError(
                "toolbarMode debe ser 'minimal'."
            )

        if cliente.get(
            "showSidebarNavigation",
            True,
        ):
            raise ValueError(
                "showSidebarNavigation debe ser false."
            )

        print(
            "[OK] config.toml está preparado "
            "para producción."
        )

    except (
        OSError,
        tomllib.TOMLDecodeError,
        ValueError,
    ) as error:
        errores.append(str(error))
        print(
            f"[ERROR] config.toml inválido: {error}"
        )

    try:
        ast.parse(
            RUTA_APP.read_text(
                encoding="utf-8",
            ),
            filename=str(RUTA_APP),
        )

        print(
            "[OK] Sintaxis válida: app.py"
        )

    except (
        OSError,
        UnicodeDecodeError,
        SyntaxError,
    ) as error:
        errores.append(str(error))
        print(
            f"[ERROR] app.py inválido: {error}"
        )

    for nombre in ARCHIVOS_PRODUCCION:
        ruta = RUTA_PRODUCCION / nombre

        if not ruta.exists():
            errores.append(
                f"Falta {nombre}."
            )
            print(
                f"[ERROR] Falta dato de producción: "
                f"{nombre}"
            )
            continue

        tamano = ruta.stat().st_size

        if tamano <= 0:
            errores.append(
                f"{nombre} está vacío."
            )
            print(
                f"[ERROR] {nombre} está vacío."
            )
            continue

        if tamano >= 100 * 1024 * 1024:
            errores.append(
                f"{nombre} supera 100 MiB."
            )
            print(
                f"[ERROR] {nombre} supera 100 MiB."
            )
            continue

        print(
            f"[OK] {nombre} | bytes={tamano}"
        )

    print("=" * 72)

    if errores:
        print(
            f"RESULTADO: BLOQUE 5C NO APROBADO "
            f"({len(errores)} errores)."
        )

        for error in errores:
            print(
                f"- {error}"
            )

        return 1

    print(
        "RESULTADO: ENTORNO DE DESPLIEGUE "
        "APROBADO."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
