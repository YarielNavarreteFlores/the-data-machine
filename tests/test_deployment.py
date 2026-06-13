from __future__ import annotations

import importlib
import importlib.metadata
import tomllib
import unittest
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

RUTA_REQUIREMENTS = RAIZ / "requirements.txt"
RUTA_CONFIG = RAIZ / ".streamlit" / "config.toml"
RUTA_APP = RAIZ / "app.py"
RUTA_PRODUCCION = RAIZ / "data" / "production"

DEPENDENCIAS_ESPERADAS = {
    "beautifulsoup4": "4.14.3",
    "nltk": "3.9.4",
    "numpy": "2.4.6",
    "pandas": "3.0.3",
    "plotly": "6.8.0",
    "requests": "2.34.2",
    "scikit-learn": "1.9.0",
    "streamlit": "1.58.0",
    "vaderSentiment": "3.3.2",
    "wordcloud": "1.9.6",
}

MODULOS_IMPORTABLES = (
    "bs4",
    "nltk",
    "numpy",
    "pandas",
    "plotly",
    "requests",
    "sklearn",
    "streamlit",
    "vaderSentiment",
    "wordcloud",
)

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
    Lee requirements.txt como UTF-8 y devuelve paquete -> versión.
    """
    contenido = RUTA_REQUIREMENTS.read_text(
        encoding="utf-8",
    )

    dependencias: dict[str, str] = {}

    for linea in contenido.splitlines():
        linea = linea.strip()

        if not linea or linea.startswith("#"):
            continue

        if "==" not in linea:
            raise AssertionError(
                f"Dependencia sin versión fija: {linea}"
            )

        paquete, version = linea.split(
            "==",
            maxsplit=1,
        )

        dependencias[paquete.strip()] = version.strip()

    return dependencias


class TestDeployment(unittest.TestCase):
    """Pruebas de preparación para Streamlit Community Cloud."""

    def test_requirements_es_utf8_sin_bom(self):
        datos = RUTA_REQUIREMENTS.read_bytes()

        self.assertFalse(
            datos.startswith(b"\xff\xfe"),
            "requirements.txt continúa en UTF-16 LE.",
        )

        self.assertFalse(
            datos.startswith(b"\xfe\xff"),
            "requirements.txt continúa en UTF-16 BE.",
        )

        self.assertFalse(
            datos.startswith(b"\xef\xbb\xbf"),
            "requirements.txt no debe incluir BOM UTF-8.",
        )

        self.assertNotIn(
            b"\x00",
            datos,
            "requirements.txt contiene bytes nulos.",
        )

        datos.decode("utf-8")

    def test_dependencias_fijas_y_completas(self):
        self.assertEqual(
            leer_requirements(),
            DEPENDENCIAS_ESPERADAS,
        )

    def test_dependencias_instaladas_e_importables(self):
        for modulo in MODULOS_IMPORTABLES:
            with self.subTest(modulo=modulo):
                importlib.import_module(modulo)

        for paquete, version in DEPENDENCIAS_ESPERADAS.items():
            with self.subTest(paquete=paquete):
                self.assertEqual(
                    importlib.metadata.version(paquete),
                    version,
                )

    def test_configuracion_de_produccion(self):
        with RUTA_CONFIG.open("rb") as archivo:
            config = tomllib.load(archivo)

        cliente = config.get("client", {})
        servidor = config.get("server", {})
        navegador = config.get("browser", {})

        self.assertFalse(
            cliente.get("showSidebarNavigation"),
        )

        self.assertEqual(
            cliente.get("toolbarMode"),
            "minimal",
        )

        self.assertEqual(
            cliente.get("showErrorDetails"),
            "none",
        )

        self.assertFalse(
            cliente.get("showErrorLinks"),
        )

        self.assertTrue(
            servidor.get("headless"),
        )

        self.assertFalse(
            navegador.get("gatherUsageStats"),
        )

    def test_entrypoint_y_datos_de_produccion(self):
        self.assertTrue(
            RUTA_APP.exists(),
            "No existe app.py en la raíz.",
        )

        self.assertTrue(
            RUTA_PRODUCCION.is_dir(),
            "No existe data/production/.",
        )

        for nombre in ARCHIVOS_PRODUCCION:
            ruta = RUTA_PRODUCCION / nombre

            with self.subTest(archivo=nombre):
                self.assertTrue(
                    ruta.exists(),
                    f"Falta {nombre}.",
                )

                self.assertGreater(
                    ruta.stat().st_size,
                    0,
                    f"{nombre} está vacío.",
                )

                self.assertLess(
                    ruta.stat().st_size,
                    100 * 1024 * 1024,
                    f"{nombre} supera 100 MiB.",
                )


if __name__ == "__main__":
    unittest.main()
