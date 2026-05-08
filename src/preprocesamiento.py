import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
import os

# Descargar las stopwords de NLTK (esto solo se hace la primera vez, luego se almacenan localmente)
nltk.download('stopwords', quiet=True)
# Asumimos que la mayoría de reviews están en inglés (cambiar a 'spanish' si es necesario) y que queremos eliminar estas palabras comunes que no aportan valor analítico.
stop_words = set(stopwords.words('english'))

def limpiar_texto(texto):
    """Limpia el texto crudo de las reviews para el análisis NLP."""
    if pd.isna(texto):
        return ""
    
    # 1. Convertir a minúsculas 
    texto = str(texto).lower()
    # 2. Eliminar caracteres especiales, signos de puntuación y números (dejar solo letras) 
    texto = re.sub(r'[^a-z\s]', '', texto)
    # 3. Eliminar espacios en blanco extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # 4. Eliminar Stopwords (palabras vacías sin valor de sentimiento/tema)
    palabras = texto.split()
    palabras_limpias = [palabra for palabra in palabras if palabra not in stop_words]
    
    return " ".join(palabras_limpias)

def main():
    print("Iniciando preprocesamiento de La Máquina de Datos...")
    
    # Detecta automáticamente la ruta absoluta de donde está guardado este script (la carpeta src/)
    DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
    
    # Construye la ruta exacta subiendo un nivel ('..') y entrando a la carpeta 'data'
    ruta_entrada = os.path.join(DIRECTORIO_ACTUAL, '..', 'data', 'games_march2025_cleaned.csv')
    ruta_salida = os.path.join(DIRECTORIO_ACTUAL, '..', 'data', 'dataset_limpio.csv')
    # Rutas relativas asumiendo la estructura: src/preprocesamiento.py y data/ 
    
    # Validar si el archivo existe
    if not os.path.exists(ruta_entrada):
        print(f"Error: No se encontró el dataset en {ruta_entrada}")
        print("Asegúrate de que el CSV esté en la carpeta 'data/'.")
        return

    # 1. Cargar el dataset original
    df = pd.read_csv(ruta_entrada)
    print(f"Dataset cargado. Filas originales: {df.shape[0]}")

    # 2. Filtrar por los 8-10 juegos seleccionados (Ajustar los App IDs o nombres)
    # Reemplaza esta lista con los IDs o nombres de los juegos que definieron en la Semana 1
    juegos_seleccionados = [730, 570, 271590] # Ejemplos: CS:GO, Dota 2, GTA V
    # df = df[df['app_id'].isin(juegos_seleccionados)] 
    
    # 3. Manejo de nulos en las reviews
    # Ajusta 'reviews' al nombre exacto de la columna de texto en tu CSV
    columna_texto = 'reviews' 
    if columna_texto in df.columns:
        # Eliminar filas donde la review esté vacía
        df = df.dropna(subset=[columna_texto])
        print(f"Valores nulos eliminados. Filas restantes: {df.shape[0]}")
        
        # 4. Transformación: Texto crudo -> Texto limpio
        print("Limpiando el texto de las reviews con NLTK y Regex (esto puede tardar unos segundos)...")
        df['reviews_limpias'] = df[columna_texto].apply(limpiar_texto)
        
        # Eliminar filas que hayan quedado vacías tras la limpieza (ej. reviews que solo eran números)
        df = df[df['reviews_limpias'] != ""]
    else:
        print(f"Advertencia: No se encontró la columna '{columna_texto}'. Revisa el nombre exacto.")

    # 5. Exportar el dataset limpio
    # Asegurar que el directorio data exista
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    df.to_csv(ruta_salida, index=False)
    print(f"¡Éxito! Dataset limpio guardado en: {ruta_salida}")

if __name__ == "__main__":
    main()