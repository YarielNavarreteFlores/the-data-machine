import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
import os

# Descargar stopwords (solo la primera vez)
nltk.download('stopwords', quiet=True)

# Stopwords en inglés
stop_words = set(stopwords.words('english'))

def limpiar_texto(texto):
    """Limpia el texto crudo de las reviews para el análisis NLP."""
    
    if pd.isna(texto):
        return ""

    # Convertir a minúsculas
    texto = str(texto).lower()

    # Eliminar caracteres especiales, puntuación y números
    texto = re.sub(r'[^a-z\s]', '', texto)

    # Eliminar espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()

    # Eliminar stopwords
    palabras = texto.split()
    palabras_limpias = [
        palabra for palabra in palabras
        if palabra not in stop_words
    ]

    return " ".join(palabras_limpias)


def main():
    print("Iniciando preprocesamiento de La Máquina de Datos...")

    # Carpeta donde está este script
    DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

    # Archivo de entrada:
    # data/raw/games_march2025_cleaned.csv
    ruta_entrada = os.path.join(
        DIRECTORIO_ACTUAL,
        '..',
        'raw',
        'games_march2025_cleaned.csv'
    )

    # Archivo de salida:
    # data/processed/dataset_limpio.csv
    ruta_salida = os.path.join(
        DIRECTORIO_ACTUAL,
        'dataset_limpio.csv'
    )

    # Normalizar rutas
    ruta_entrada = os.path.abspath(ruta_entrada)
    ruta_salida = os.path.abspath(ruta_salida)

    print(f"Archivo de entrada: {ruta_entrada}")
    print(f"Archivo de salida: {ruta_salida}")

    # Verificar que existe el CSV
    if not os.path.exists(ruta_entrada):
        print(f"Error: No se encontró el dataset en:\n{ruta_entrada}")
        return

    # Cargar dataset
    df = pd.read_csv(ruta_entrada)

    print(f"Dataset cargado correctamente.")
    print(f"Filas originales: {df.shape[0]}")
    print(f"Columnas disponibles: {list(df.columns)}")

    # Nombre de la columna que contiene las reviews
    columna_texto = 'reviews'

    if columna_texto not in df.columns:
        print(
            f"Error: No existe la columna '{columna_texto}'.\n"
            f"Columnas encontradas: {list(df.columns)}"
        )
        return

    # Eliminar nulos
    df = df.dropna(subset=[columna_texto])

    print(f"Filas después de eliminar nulos: {df.shape[0]}")

    # Limpiar texto
    print("Procesando reviews...")

    df['reviews_limpias'] = df[columna_texto].apply(limpiar_texto)

    # Eliminar reviews vacías
    df = df[df['reviews_limpias'] != ""]

    print(f"Filas después de limpieza: {df.shape[0]}")

    # Guardar dataset limpio
    df.to_csv(ruta_salida, index=False)

    print("\n✅ Proceso finalizado correctamente")
    print(f"Dataset guardado en:\n{ruta_salida}")


if __name__ == "__main__":
    main()