import tempfile
import unittest
from pathlib import Path

from src.data_paths import (
    resolver_directorio_nlp,
    resolver_ruta_metadata,
)
from src.production import (
    calcular_sha256,
)


class TestProduction(unittest.TestCase):
    """
    Pruebas de resolución de rutas e integridad básica.
    """

    def test_calcular_sha256(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = (
                Path(temporal)
                / "archivo.txt"
            )

            ruta.write_text(
                "the-data-machine",
                encoding="utf-8",
            )

            hash_1 = calcular_sha256(
                ruta
            )

            hash_2 = calcular_sha256(
                ruta
            )

            self.assertEqual(
                hash_1,
                hash_2,
            )

            self.assertEqual(
                len(hash_1),
                64,
            )

    def test_metadata_prioriza_produccion(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)

            produccion = (
                raiz
                / "catalogo.csv"
            )

            desarrollo = (
                raiz
                / "dataset.csv"
            )

            produccion.write_text(
                "appid,name\n570,Dota 2\n",
                encoding="utf-8",
            )

            desarrollo.write_text(
                "appid,name\n252490,Rust\n",
                encoding="utf-8",
            )

            resultado = resolver_ruta_metadata(
                ruta_produccion=produccion,
                ruta_desarrollo=desarrollo,
            )

            self.assertEqual(
                resultado,
                produccion,
            )

    def test_metadata_usa_desarrollo_como_respaldo(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)

            produccion = (
                raiz
                / "inexistente.csv"
            )

            desarrollo = (
                raiz
                / "dataset.csv"
            )

            desarrollo.write_text(
                "appid,name\n570,Dota 2\n",
                encoding="utf-8",
            )

            resultado = resolver_ruta_metadata(
                ruta_produccion=produccion,
                ruta_desarrollo=desarrollo,
            )

            self.assertEqual(
                resultado,
                desarrollo,
            )

    def test_nlp_prioriza_directorio_completo(self):
        nombres = (
            "reviews_analizadas.csv",
            "metricas_sentimiento.json",
            "temas_tfidf.csv",
            "tags_steam.csv",
        )

        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)

            produccion = raiz / "production"
            desarrollo = raiz / "development"

            produccion.mkdir()
            desarrollo.mkdir()

            for nombre in nombres:
                (
                    produccion
                    / nombre
                ).write_text(
                    "contenido",
                    encoding="utf-8",
                )

                (
                    desarrollo
                    / nombre
                ).write_text(
                    "contenido",
                    encoding="utf-8",
                )

            resultado = resolver_directorio_nlp(
                ruta_produccion=produccion,
                ruta_desarrollo=desarrollo,
            )

            self.assertEqual(
                resultado,
                produccion,
            )


if __name__ == "__main__":
    unittest.main()
