import json
import tempfile
import unittest
from pathlib import Path

from src.auth import (
    cargar_usuarios,
    guardar_usuarios,
    nombre_para_mostrar,
    registrar_usuario,
    usuario_existe,
    verificar_credenciales,
)


class TestRegistro(unittest.TestCase):
    """Pruebas del alta de usuarios (lógica pura, sin Streamlit)."""

    def test_registro_exitoso(self):
        usuarios = {}
        exito, _ = registrar_usuario("Ana", "1234", usuarios)

        self.assertTrue(exito)
        self.assertTrue(usuario_existe("ana", usuarios))
        self.assertEqual(usuarios["ana"]["display"], "Ana")
        self.assertEqual(usuarios["ana"]["password"], "1234")

    def test_nombre_vacio(self):
        usuarios = {}
        exito, _ = registrar_usuario("   ", "1234", usuarios)

        self.assertFalse(exito)
        self.assertEqual(usuarios, {})

    def test_password_vacia(self):
        usuarios = {}
        exito, _ = registrar_usuario("Ana", "", usuarios)

        self.assertFalse(exito)
        self.assertEqual(usuarios, {})

    def test_duplicado_mismo_case(self):
        usuarios = {}
        registrar_usuario("Ana", "1234", usuarios)
        exito, _ = registrar_usuario("Ana", "otra", usuarios)

        self.assertFalse(exito)
        self.assertEqual(len(usuarios), 1)

    def test_duplicado_distinto_case(self):
        usuarios = {}
        registrar_usuario("Ana", "1234", usuarios)
        # "ana" y "ANA" normalizan a la misma clave que "Ana".
        exito, _ = registrar_usuario("ANA", "otra", usuarios)

        self.assertFalse(exito)
        self.assertEqual(len(usuarios), 1)


class TestCredenciales(unittest.TestCase):
    """Pruebas de verificación de credenciales y nombre visible."""

    def setUp(self):
        self.usuarios = {}
        registrar_usuario("Ana", "1234", self.usuarios)

    def test_credenciales_correctas(self):
        self.assertTrue(
            verificar_credenciales("Ana", "1234", self.usuarios)
        )
        # El usuario se compara sin distinguir mayúsculas.
        self.assertTrue(
            verificar_credenciales("ana", "1234", self.usuarios)
        )

    def test_password_incorrecta(self):
        self.assertFalse(
            verificar_credenciales("Ana", "incorrecta", self.usuarios)
        )

    def test_usuario_inexistente(self):
        self.assertFalse(
            verificar_credenciales("Sandra", "1234", self.usuarios)
        )

    def test_nombre_para_mostrar(self):
        self.assertEqual(
            nombre_para_mostrar("ana", self.usuarios),
            "Ana",
        )

    def test_nombre_para_mostrar_desconocido(self):
        self.assertEqual(
            nombre_para_mostrar("  Sandra  ", self.usuarios),
            "Sandra",
        )


class TestPersistencia(unittest.TestCase):
    """Pruebas de lectura y escritura del archivo JSON."""

    def test_ida_y_vuelta(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "usuarios.json"

            usuarios = {}
            registrar_usuario("Ana", "1234", usuarios)
            guardar_usuarios(usuarios, ruta)

            self.assertTrue(ruta.exists())
            recargado = cargar_usuarios(ruta)
            self.assertEqual(recargado, usuarios)

    def test_crea_directorio_padre(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "auth" / "usuarios.json"

            guardar_usuarios({"ana": {"display": "Ana", "password": "1"}}, ruta)

            self.assertTrue(ruta.exists())

    def test_archivo_inexistente(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "no_existe.json"

            self.assertEqual(cargar_usuarios(ruta), {})

    def test_archivo_corrupto(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "corrupto.json"
            ruta.write_text("esto no es json", encoding="utf-8")

            self.assertEqual(cargar_usuarios(ruta), {})

    def test_codificacion_utf8(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "usuarios.json"

            usuarios = {}
            registrar_usuario("Begoña", "ñandú", usuarios)
            guardar_usuarios(usuarios, ruta)

            # El JSON conserva los acentos (ensure_ascii=False).
            contenido = ruta.read_text(encoding="utf-8")
            self.assertIn("Begoña", contenido)
            self.assertEqual(cargar_usuarios(ruta), usuarios)
            # Y sigue siendo JSON válido.
            json.loads(contenido)


if __name__ == "__main__":
    unittest.main()
