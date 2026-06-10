import unittest

from src.scraper import (
    combinar_reviews,
    limpiar_texto_html,
    normalizar_review_api,
    parsear_reviews_html,
)


class TestScraper(unittest.TestCase):
    """
    Pruebas unitarias del módulo src.scraper.

    Estas pruebas no realizan solicitudes a Internet.
    Utilizan datos simulados para verificar la lógica.
    """

    def test_limpiar_texto_html(self):
        """
        Comprueba que BeautifulSoup elimine etiquetas HTML
        y normalice espacios.
        """
        texto = limpiar_texto_html(
            "<b>Great</b>\n\n game &amp; fun"
        )

        self.assertEqual(
            texto,
            "Great game & fun",
        )

    def test_normalizar_review_api(self):
        """
        Comprueba que una respuesta simulada de Steam
        se convierta al esquema del proyecto.
        """
        review_original = {
            "recommendationid": "12345",
            "language": "english",
            "review": "<p>Very good game!</p>",
            "timestamp_created": 1700000000,
            "timestamp_updated": 1700000010,
            "voted_up": True,
            "votes_up": 10,
            "votes_funny": 2,
            "weighted_vote_score": "0.8",
            "comment_count": 1,
            "steam_purchase": True,
            "received_for_free": False,
            "written_during_early_access": False,
            "author": {
                # Este campo no debe guardarse.
                "steamid": "identificador_privado",
                "num_games_owned": 100,
                "num_reviews": 5,
                "playtime_forever": 200,
                "playtime_at_review": 150,
            },
        }

        resultado = normalizar_review_api(
            review_original,
            appid=570,
            nombre_juego="Dota 2",
            scraped_at_utc=(
                "2026-01-01T00:00:00+00:00"
            ),
        )

        self.assertIsNotNone(
            resultado
        )

        self.assertEqual(
            resultado["text"],
            "Very good game!",
        )

        self.assertTrue(
            resultado["voted_up"]
        )

        self.assertEqual(
            resultado["sentiment_steam"],
            "positive",
        )

        # Se verifica que no se conserve el steamid.
        self.assertNotIn(
            "steamid",
            resultado,
        )

    def test_parsear_reviews_html(self):
        """
        Comprueba el respaldo basado en BeautifulSoup
        con una tarjeta HTML simulada.
        """
        html = """
        <div class="apphub_Card">
            <div class="title">
                Recommended
            </div>

            <div class="apphub_CardTextContent">
                <div class="date_posted">
                    Posted: 1 June
                </div>

                Excellent <b>game</b>.
            </div>
        </div>
        """

        resultado = parsear_reviews_html(
            html,
            appid=570,
            nombre_juego="Dota 2",
            max_reviews=10,
        )

        self.assertEqual(
            len(resultado),
            1,
        )

        self.assertTrue(
            resultado[0]["voted_up"]
        )

        self.assertEqual(
            resultado[0]["source"],
            "steamcommunity_html_fallback",
        )

        # La fecha HTML no debe quedar dentro del texto.
        self.assertNotIn(
            "Posted:",
            resultado[0]["text"],
        )

    def test_combinar_reviews(self):
        """
        Comprueba que actualizar Dota 2 no elimine
        las reseñas existentes de Rust.
        """
        review_dota_anterior = {
            "appid": 570,
            "review_hash": "dota-anterior",
        }

        review_rust_anterior = {
            "appid": 252490,
            "review_hash": "rust-anterior",
        }

        review_dota_nueva = {
            "appid": 570,
            "review_hash": "dota-nueva",
        }

        resultado = combinar_reviews(
            existentes=[
                review_dota_anterior,
                review_rust_anterior,
            ],
            nuevas=[
                review_dota_nueva,
                # Duplicado intencional.
                review_dota_nueva,
            ],
            appids_actualizados={570},
        )

        hashes = {
            review["review_hash"]
            for review in resultado
        }

        self.assertEqual(
            hashes,
            {
                "rust-anterior",
                "dota-nueva",
            },
        )


if __name__ == "__main__":
    unittest.main()