import unittest

import numpy as np
import pandas as pd

from src.modelos import (
    ETIQUETA_BASELINE,
    ETIQUETA_LOGISTICA,
    ETIQUETA_NAIVE_BAYES,
    baseline_mayoritario,
    calcular_metricas_clasificacion,
    calcular_metricas_regresion,
    entrenar_clasificadores,
    entrenar_regresion,
    preparar_datos_clasificacion,
    preparar_datos_regresion,
)


class TestMetricasClasificacion(unittest.TestCase):
    """Pruebas de las métricas binarias (lógica pura, sin entrenamiento)."""

    def test_calcular_metricas(self):
        y_true = [True, True, False, False]
        y_pred = [True, False, False, True]

        metricas = calcular_metricas_clasificacion(y_true, y_pred)

        self.assertAlmostEqual(metricas["accuracy"], 0.5)
        self.assertAlmostEqual(metricas["precision"], 0.5)
        self.assertAlmostEqual(metricas["recall"], 0.5)
        self.assertEqual(
            metricas["confusion_matrix"],
            {
                "true_negative": 1,
                "false_positive": 1,
                "false_negative": 1,
                "true_positive": 1,
            },
        )

    def test_baseline_mayoritario(self):
        # El entrenamiento es mayoritariamente positivo -> predice siempre True.
        y_train = [True, True, True, False]
        y_eval = [True, True, False]

        metricas = baseline_mayoritario(y_train, y_eval)

        self.assertAlmostEqual(metricas["accuracy"], 2 / 3, places=5)
        # Al predecir siempre True no hay verdaderos negativos.
        self.assertEqual(metricas["confusion_matrix"]["true_negative"], 0)
        self.assertEqual(metricas["confusion_matrix"]["true_positive"], 2)


class TestMetricasRegresion(unittest.TestCase):
    """Pruebas de R², MAE y RMSE."""

    def test_prediccion_perfecta(self):
        metricas = calcular_metricas_regresion([1, 2, 3, 4], [1, 2, 3, 4])

        self.assertAlmostEqual(metricas["r2"], 1.0)
        self.assertAlmostEqual(metricas["mae"], 0.0)
        self.assertAlmostEqual(metricas["rmse"], 0.0)

    def test_con_error(self):
        metricas = calcular_metricas_regresion([1, 2, 3, 4], [1, 2, 3, 5])

        self.assertAlmostEqual(metricas["mae"], 0.25)
        self.assertAlmostEqual(metricas["rmse"], 0.5)
        self.assertLess(metricas["r2"], 1.0)


class TestPreparacion(unittest.TestCase):
    """Pruebas del filtrado y armado de los datos de entrada."""

    def test_preparar_clasificacion_filtra(self):
        df = pd.DataFrame(
            {
                "text": ["buen juego", "", "sin recomendacion"],
                "voted_up": [True, False, None],
            }
        )

        datos = preparar_datos_clasificacion(df)

        # Se descartan la fila con texto vacío y la de voted_up nulo.
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos.loc[0, "text"], "buen juego")
        self.assertTrue(bool(datos.loc[0, "voted_up"]))

    def test_preparar_regresion_descarta_nulos(self):
        df = pd.DataFrame(
            {
                "votes_up": [1, 2, np.nan, 4, 5],
                "weighted_vote_score": [0.5, 0.6, 0.7, np.nan, 0.9],
                "author_num_reviews": [3, 4, 5, 6, 7],
            }
        )

        x, y = preparar_datos_regresion(df)

        # Quedan solo las filas sin nulos en features ni objetivo.
        self.assertEqual(len(x), 3)
        self.assertEqual(len(y), 3)
        self.assertIn("votes_up", x.columns)


class TestEntrenamiento(unittest.TestCase):
    """Pruebas de entrenamiento sobre datos sintéticos pequeños."""

    def test_entrenar_clasificadores(self):
        # Corpus separable: positivas con "amazing love", negativas con
        # "terrible broken bug". Cada término se repite por encima de min_df.
        positivas = ["amazing love wonderful experience"] * 10
        negativas = ["terrible broken bug crash"] * 10

        df = pd.DataFrame(
            {
                "text": positivas + negativas,
                "voted_up": [True] * 10 + [False] * 10,
                "vader_prediction_binary": [True] * 10 + [False] * 10,
            }
        )

        datos = preparar_datos_clasificacion(df)
        resultado = entrenar_clasificadores(
            datos,
            test_size=0.4,
            random_state=42,
        )

        self.assertEqual(resultado["n_total"], 20)
        self.assertGreaterEqual(resultado["n_test"], 1)

        for etiqueta in (ETIQUETA_LOGISTICA, ETIQUETA_NAIVE_BAYES, ETIQUETA_BASELINE):
            self.assertIn(etiqueta, resultado["modelos"])
            metricas = resultado["modelos"][etiqueta]
            self.assertGreaterEqual(metricas["accuracy"], 0.0)
            self.assertLessEqual(metricas["accuracy"], 1.0)
            self.assertIn("confusion_matrix", metricas)

        # Con datos perfectamente separables el supervisado debe acertar.
        self.assertEqual(
            resultado["modelos"][ETIQUETA_LOGISTICA]["accuracy"],
            1.0,
        )

    def test_entrenar_regresion(self):
        generador = np.random.default_rng(0)
        votes = generador.integers(0, 50, size=40).astype(float)
        autor = generador.integers(1, 20, size=40).astype(float)

        df = pd.DataFrame(
            {
                "votes_up": votes,
                "author_num_reviews": autor,
                # Relación lineal limpia con el objetivo.
                "weighted_vote_score": 0.5 + 0.01 * votes + 0.002 * autor,
            }
        )

        x, y = preparar_datos_regresion(df)
        resultado = entrenar_regresion(x, y, test_size=0.25, random_state=42)

        self.assertIn("r2", resultado)
        self.assertGreater(resultado["r2"], 0.9)
        self.assertGreaterEqual(resultado["n_test"], 1)
        self.assertTrue(len(resultado["puntos"]) > 0)
        self.assertEqual(set(resultado["coeficientes"]), set(x.columns))


if __name__ == "__main__":
    unittest.main()
