import unittest

import pandas as pd

from src.nlp import (
    analizar_sentimientos,
    clasificar_compound,
    evaluar_sentimiento,
    extraer_temas_tfidf,
    parsear_tags,
)


class AnalizadorFalso:
    """
    Imita el comportamiento de VADER.

    Permite probar la lógica del proyecto sin
    utilizar Internet ni descargar vader_lexicon.
    """

    def polarity_scores(
        self,
        texto,
    ):
        texto = texto.lower()

        if "excellent" in texto:
            return {
                "neg": 0.0,
                "neu": 0.2,
                "pos": 0.8,
                "compound": 0.8,
            }

        if "awful" in texto:
            return {
                "neg": 0.8,
                "neu": 0.2,
                "pos": 0.0,
                "compound": -0.8,
            }

        return {
            "neg": 0.2,
            "neu": 0.6,
            "pos": 0.2,
            "compound": 0.0,
        }


class TestNLP(unittest.TestCase):
    """
    Pruebas unitarias del módulo NLP.

    No realizan solicitudes a Internet.
    """

    def test_clasificar_compound(self):
        """
        Comprueba los límites exactos de VADER.
        """
        self.assertEqual(
            clasificar_compound(0.05),
            "positive",
        )

        self.assertEqual(
            clasificar_compound(-0.05),
            "negative",
        )

        self.assertEqual(
            clasificar_compound(0.0),
            "neutral",
        )

    def test_analizar_sentimientos(self):
        """
        Comprueba que se creen las tres clases
        y que el neutral quede fuera del binario.
        """
        df = pd.DataFrame(
            {
                "text": [
                    "Excellent combat",
                    "Awful servers",
                    "Mixed experience",
                ],

                "voted_up": pd.Series(
                    [
                        True,
                        False,
                        True,
                    ],
                    dtype="boolean",
                ),
            }
        )

        resultado = analizar_sentimientos(
            df,
            AnalizadorFalso(),
        )

        self.assertEqual(
            resultado[
                "sentiment_vader"
            ].tolist(),
            [
                "positive",
                "negative",
                "neutral",
            ],
        )

        self.assertEqual(
            resultado[
                "vader_evaluable"
            ].tolist(),
            [
                True,
                True,
                False,
            ],
        )

        self.assertTrue(
            pd.isna(
                resultado.loc[
                    2,
                    "vader_prediction_binary",
                ]
            )
        )

    def test_evaluar_sentimiento(self):
        """
        Comprueba cobertura, accuracy
        y matriz de confusión.
        """
        df = pd.DataFrame(
            {
                "voted_up": pd.Series(
                    [
                        True,
                        True,
                        False,
                        False,
                    ],
                    dtype="boolean",
                ),

                "sentiment_vader": [
                    "positive",
                    "neutral",
                    "negative",
                    "positive",
                ],

                "vader_prediction_binary":
                    pd.Series(
                        [
                            True,
                            pd.NA,
                            False,
                            True,
                        ],
                        dtype="boolean",
                    ),
            }
        )

        metricas = evaluar_sentimiento(
            df,
            pct_pos_total_dataset=60,
        )

        self.assertEqual(
            metricas["reviews_total"],
            4,
        )

        self.assertEqual(
            metricas["evaluable_reviews"],
            3,
        )

        self.assertAlmostEqual(
            metricas[
                "coverage_non_neutral"
            ],
            0.75,
        )

        self.assertAlmostEqual(
            metricas[
                "accuracy_non_neutral"
            ],
            2 / 3,
            places=5,
        )

        self.assertEqual(
            metricas[
                "confusion_matrix"
            ],
            {
                "true_negative": 1,
                "false_positive": 1,
                "false_negative": 0,
                "true_positive": 1,
            },
        )

    def test_parsear_tags(self):
        """
        Comprueba que la columna tags
        se convierta en una tabla ordenada.
        """
        tags = parsear_tags(
            "{'Action': 100, 'RPG': 50}",
            top_n=2,
        )

        self.assertEqual(
            tags["tag"].tolist(),
            [
                "Action",
                "RPG",
            ],
        )

        self.assertEqual(
            tags[
                "score_normalized"
            ].tolist(),
            [
                1.0,
                0.5,
            ],
        )

    def test_extraer_temas_tfidf(self):
        """
        Comprueba que TF-IDF genere temas
        y pueda incluir unigramas y bigramas.
        """
        textos = [
            (
                "Combat system and sword "
                "mechanics are responsive"
            ),
            (
                "The combat system has "
                "excellent boss mechanics"
            ),
            (
                "Server lag damages "
                "online combat"
            ),
            (
                "Online server lag "
                "is frequent"
            ),
        ]

        temas = extraer_temas_tfidf(
            textos,
            top_n=10,
            min_df=1,
        )

        self.assertFalse(
            temas.empty
        )

        todos_los_terminos = " ".join(
            temas["term"].tolist()
        )

        self.assertIn(
            "combat",
            todos_los_terminos,
        )

        self.assertTrue(
            temas[
                "ngram_type"
            ].isin(
                [
                    "unigram",
                    "bigram",
                ]
            ).all()
        )


if __name__ == "__main__":
    unittest.main()