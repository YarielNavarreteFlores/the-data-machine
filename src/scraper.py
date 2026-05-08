import requests
from bs4 import BeautifulSoup
import json
import time
import os

def hacer_scraping_reviews(app_id, max_reviews=50):
    """
    Obtiene las reseñas más recientes de un juego en Steam usando BeautifulSoup.
    """
    # Endpoint de la comunidad de Steam para reseñas recientes
    url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter=mostrecent&p=1"
    
    # Headers para simular un navegador real y evitar bloqueos (Error 403)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        respuesta = requests.get(url, headers=headers)
        respuesta.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Steam para el App ID {app_id}: {e}")
        return []

    soup = BeautifulSoup(respuesta.content, 'html.parser')
    reviews_extraidas = []

    # Localizar las tarjetas de reseñas (clase HTML específica de Steam)
    tarjetas = soup.find_all('div', class_='apphub_Card', limit=max_reviews)

    for tarjeta in tarjetas:
        texto_limpio = ""
        # 1. Extraer el texto de la reseña
        contenido_div = tarjeta.find('div', class_='apphub_CardTextContent')
        if contenido_div:
            texto_bruto = contenido_div.get_text(separator=' ', strip=True)
            # Limpiar la marca de fecha que Steam pone al inicio ("Posted: May 5")
            if "Posted:" in texto_bruto:
                texto_limpio = texto_bruto.split("Posted:", 1)[-1].strip()
            else:
                texto_limpio = texto_bruto

        # 2. Extraer el sentimiento general (Recommended / Not Recommended)
        sentimiento_div = tarjeta.find('div', class_='title')
        sentimiento = sentimiento_div.text.strip() if sentimiento_div else "Unknown"

        if texto_limpio:
            reviews_extraidas.append({
                "app_id": app_id,
                "review": texto_limpio,
                "sentimiento_steam": sentimiento
            })

    return reviews_extraidas

def main():
    print("Iniciando Web Scraping de Steam (BeautifulSoup)...")
    
    # Los 8-10 juegos seleccionados por el equipo en la Semana 1
    # TODO: Actualizar esta lista con los App IDs oficiales de su selección
    app_ids_catalogo = ['730', '570', '271590'] # Ejemplos: CS:GO, Dota 2, GTA V
    
    todas_las_reviews = []

    for app_id in app_ids_catalogo:
        print(f"Obteniendo reviews recientes para App ID {app_id}...")
        reviews_juego = hacer_scraping_reviews(app_id, max_reviews=30)
        todas_las_reviews.extend(reviews_juego)
        
        # Pausa de 2 segundos entre peticiones para ser amigables con el servidor y no ser baneados
        time.sleep(2)

    # Reemplazar la ruta relativa por la absoluta
    DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
    ruta_salida = os.path.join(DIRECTORIO_ACTUAL, '..', 'data', 'reviews_extra.json')

    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)
    
    # Guardar los datos en formato JSON
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        json.dump(todas_las_reviews, f, ensure_ascii=False, indent=4)

    print(f"Scraping finalizado con éxito.")
    print(f"Se han guardado {len(todas_las_reviews)} reviews en: {ruta_salida}")

if __name__ == "__main__":
    main()