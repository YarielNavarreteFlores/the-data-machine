import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.dashboard import (
    cargar_resultados_nlp,
    construir_distribucion_sentimiento,
    construir_matriz_confusion,
    dataframe_a_csv_bytes,
    filtrar_reviews,
    formatear_minutos,
    nombre_archivo_seguro,
    parsear_lista_texto,
)


class TestDashboard(unittest.TestCase):
    """Pruebas de la lógica del dashboard sin iniciar Streamlit."""

    def setUp(self):
        self.reviews = pd.DataFrame(
            {
                "appid": [570, 570, 570],
                "game_name": ["Dota 2"] * 3,
                "review_hash": ["a", "b", "c"],
                "text": [
                    "Excellent combat",
                    "Server problems",
                    "Neutral experience",
                ],
                "voted_up": pd.Series([True, False, True], dtype="boolean"),
                "sentiment_vader": ["positive", "negative", "neutral"],
                "vader_compound": [0.8, -0.7, 0.0],
            }
        )

    def test_construir_distribucion_sentimiento(self):
        distribucion = construir_distribucion_sentimiento(self.reviews)

        self.assertEqual(len(distribucion), 6)
        self.assertEqual(
            distribucion[distribucion["source"] == "VADER"]["count"].sum(),
            3,
        )
        self.assertEqual(
            distribucion[distribucion["source"] == "Steam"]["count"].sum(),
            3,
        )

    def test_construir_matriz_confusion(self):
        matriz = construir_matriz_confusion(
            {
                "true_negative": 10,
                "false_positive": 2,
                "false_negative": 3,
                "true_positive": 20,
            }
        )

        self.assertEqual(matriz.shape, (2, 2))
        self.assertEqual(int(matriz.values.sum()), 35)
        self.assertEqual(matriz.iloc[1, 1], 20)

    def test_filtrar_reviews(self):
        filtradas = filtrar_reviews(
            self.reviews,
            sentimiento="positive",
            recomendacion="Recomendadas",
            consulta="combat",
        )

        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas.iloc[0]["review_hash"], "a")

    def test_utilidades_de_formato(self):
        self.assertEqual(formatear_minutos(120), "2.0 h")
        self.assertEqual(
            parsear_lista_texto("['Action', 'RPG']"),
            ["Action", "RPG"],
        )
        self.assertEqual(
            nombre_archivo_seguro("The Witcher 3: Wild Hunt"),
            "the_witcher_3_wild_hunt",
        )
        self.assertTrue(dataframe_a_csv_bytes(self.reviews).startswith(b"\xef\xbb\xbf"))

    def test_cargar_resultados_nlp_temporales(self):
        """Comprueba la carga completa usando archivos temporales."""
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio)
            ruta_reviews = base / "reviews.csv"
            ruta_metricas = base / "metricas.json"
            ruta_temas = base / "temas.csv"
            ruta_tags = base / "tags.csv"

            self.reviews.to_csv(ruta_reviews, index=False)

            ruta_metricas.write_text(
                """
                [
                  {
                    "appid": 570,
                    "game_name": "Dota 2",
                    "reviews_total": 3,
                    "coverage_non_neutral": 0.666667,
                    "accuracy_non_neutral": 1.0,
                    "balanced_accuracy_non_neutral": 1.0,
                    "majority_baseline_non_neutral": 0.5,
                    "confusion_matrix": {
                      "true_negative": 1,
                      "false_positive": 0,
                      "false_negative": 0,
                      "true_positive": 1
                    }
                  }
                ]
                """,
                encoding="utf-8",
            )

            pd.DataFrame(
                {
                    "appid": [570],
                    "game_name": ["Dota 2"],
                    "term": ["combat"],
                    "ngram_type": ["unigram"],
                    "tfidf_score": [0.2],
                    "document_frequency": [2],
                    "document_pct": [66.67],
                }
            ).to_csv(ruta_temas, index=False)

            pd.DataFrame(
                {
                    "appid": [570],
                    "game_name": ["Dota 2"],
                    "tag": ["MOBA"],
                    "tag_votes": [100],
                    "score_normalized": [1.0],
                }
            ).to_csv(ruta_tags, index=False)

            reviews, metricas, temas, tags = cargar_resultados_nlp(
                ruta_reviews,
                ruta_metricas,
                ruta_temas,
                ruta_tags,
            )

            self.assertEqual(len(reviews), 3)
            self.assertEqual(len(metricas), 1)
            self.assertEqual(len(temas), 1)
            self.assertEqual(len(tags), 1)


if __name__ == "__main__":
    unittest.main()
