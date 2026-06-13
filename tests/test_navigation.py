import unittest

from src.navigation import (
    cerrar_sesion,
    convertir_appid,
    establecer_juego,
    inicializar_sesion,
    limpiar_seleccion,
    normalizar_parametro_consulta,
)


class TestNavigation(unittest.TestCase):
    """Pruebas de la lógica de sesión y navegación."""

    def test_normalizar_parametro_consulta(self):
        self.assertEqual(
            normalizar_parametro_consulta(["570", "252490"]),
            "252490",
        )
        self.assertIsNone(normalizar_parametro_consulta([]))
        self.assertIsNone(normalizar_parametro_consulta("   "))

    def test_convertir_appid(self):
        self.assertEqual(convertir_appid("570"), 570)
        self.assertEqual(convertir_appid(["570"]), 570)
        self.assertIsNone(convertir_appid("Dota 2"))
        self.assertIsNone(convertir_appid("-1"))
        self.assertIsNone(convertir_appid(None))

    def test_inicializar_sesion_no_sobrescribe(self):
        estado = {
            "authenticated": True,
            "username": "Yariel",
        }

        inicializar_sesion(estado)

        self.assertTrue(estado["authenticated"])
        self.assertEqual(estado["username"], "Yariel")
        self.assertIn("selected_appid", estado)
        self.assertIn("selected_game", estado)

    def test_establecer_y_limpiar_juego(self):
        estado = {}

        establecer_juego(
            570,
            "Dota 2",
            estado,
        )

        self.assertEqual(estado["selected_appid"], 570)
        self.assertEqual(estado["selected_game"], "Dota 2")

        limpiar_seleccion(estado)

        self.assertIsNone(estado["selected_appid"])
        self.assertIsNone(estado["selected_game"])

    def test_cerrar_sesion(self):
        estado = {
            "authenticated": True,
            "username": "Yariel",
            "selected_appid": 570,
            "selected_game": "Dota 2",
        }

        cerrar_sesion(estado)

        self.assertFalse(estado["authenticated"])
        self.assertEqual(estado["username"], "")
        self.assertIsNone(estado["selected_appid"])
        self.assertIsNone(estado["selected_game"])


if __name__ == "__main__":
    unittest.main()
