import unittest

from src.menu_usuario import (
    hay_juego_seleccionado,
    obtener_nombre_juego,
    obtener_nombre_usuario,
)


class TestMenuUsuario(unittest.TestCase):
    """
    Pruebas de la lógica pura del menú lateral.

    No levantan un servidor Streamlit.
    """

    def test_obtener_nombre_usuario(self):
        estado = {
            "authenticated": True,
            "username": " Yariel ",
        }

        self.assertEqual(
            obtener_nombre_usuario(estado),
            "Yariel",
        )

    def test_usuario_vacio(self):
        estado = {
            "authenticated": True,
            "username": "   ",
        }

        self.assertEqual(
            obtener_nombre_usuario(estado),
            "usuario",
        )

    def test_hay_juego_seleccionado(self):
        self.assertTrue(
            hay_juego_seleccionado(
                {
                    "selected_appid": 570,
                }
            )
        )

        self.assertFalse(
            hay_juego_seleccionado(
                {
                    "selected_appid": None,
                }
            )
        )

        self.assertFalse(
            hay_juego_seleccionado(
                {
                    "selected_appid": "invalido",
                }
            )
        )

    def test_obtener_nombre_juego(self):
        self.assertEqual(
            obtener_nombre_juego(
                {
                    "selected_game": "Dota 2",
                }
            ),
            "Dota 2",
        )

        self.assertEqual(
            obtener_nombre_juego(
                {
                    "selected_game": "",
                }
            ),
            "Juego seleccionado",
        )


if __name__ == "__main__":
    unittest.main()
