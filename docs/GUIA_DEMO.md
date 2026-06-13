# Guía de demostración

## Objetivo

Realizar una demostración reproducible de 6 a 8 minutos sin depender de scraping ni procesamiento durante la exposición.

## Enlaces

- App: https://the-data-machine-01.streamlit.app/
- Repositorio: https://github.com/MelSurikun/the-data-machine

## Preparación previa

1. Abrir la app 10 minutos antes para evitar suspensión por inactividad.
2. Verificar conexión a internet.
3. Abrir una ventana normal y una ventana de incógnito.
4. Tener el repositorio abierto en otra pestaña.
5. Probar Dota 2, War Thunder y ELDEN RING.
6. Descargar un CSV y un JSON antes de la exposición.
7. Conservar capturas por si falla la red.

## Guion sugerido

### 1. Problema y alcance - 45 segundos

“Steam concentra millones de opiniones. The Data Machine combina métricas históricas con el análisis detallado de 5,000 reseñas recientes de 10 videojuegos. La meta es resumir sentimiento y temas sin leer manualmente cada reseña.”

### 2. Login y catálogo - 45 segundos

- Mostrar el login.
- Explicar que es demostrativo y maneja sesión.
- Entrar y mostrar los 10 juegos.
- Señalar metadata: precio, aprobación, Metacritic, géneros e imagen.

### 3. Dashboard de Dota 2 - 2 minutos

- Abrir Dota 2.
- Explicar las tres referencias: histórico, muestra y VADER.
- Mostrar accuracy 78.2 %, balanced accuracy 73.0 %, cobertura 56.8 % y baseline 71.8 %.
- Aclarar que neutrales no entran en la evaluación binaria.

### 4. Matriz de confusión y temas - 1.5 minutos

- Abrir Sentimiento y mostrar la matriz.
- Abrir Temas y nube.
- Distinguir TF-IDF de tags de Steam.

### 5. Cambio de juego - 1 minuto

- Cambiar a War Thunder.
- Mostrar que portada, métricas, gráfica y reseñas se actualizan.
- Comentar que War Thunder no llega a 75 % de accuracy, pero supera su baseline.

### 6. Filtros y descarga - 45 segundos

- Filtrar reseñas negativas o buscar `match`.
- Descargar CSV de reseñas y JSON de métricas.

### 7. Arquitectura y calidad - 45 segundos

- Mostrar el repositorio.
- Mencionar scraper, NLP, paquete de producción y Streamlit.
- Indicar 33 pruebas automatizadas y despliegue en Python 3.12.

### 8. Cierre - 30 segundos

“The Data Machine no afirma procesar millones de textos. Contextualiza millones de opiniones históricas y analiza 5,000 reseñas recientes. La arquitectura permite cambiar juegos, aumentar el corpus y migrar a almacenamiento escalable.”

## Preguntas previsibles

### ¿Por qué solo 10 juegos?

El alcance formal exige entre 8 y 10 juegos y al menos 500 reseñas por título. Se priorizó una versión reproducible y desplegable.

### ¿Por qué VADER?

Es interpretable, no necesita entrenamiento y está diseñado para texto informal en inglés. Se reconoce que tiene limitaciones con sarcasmo y jerga.

### ¿Por qué excluir neutrales de accuracy?

`voted_up` es binario. La neutralidad no tiene una clase equivalente en Steam, por lo que se reporta cobertura y se evalúan solo predicciones positivas o negativas.

### ¿Por qué el histórico no coincide con la muestra?

El histórico acumula años de reseñas; la muestra contiene 500 opiniones recientes. No representan el mismo periodo.

### ¿El login es seguro?

No. Es un prototipo de manejo de sesión. Una versión real requeriría usuarios persistentes, hash de contraseñas y control de roles.

### ¿Puede escalar?

Sí. Para volúmenes moderados basta parametrizar el pipeline. Para millones de textos se requiere Parquet, base de datos, ingestión incremental y procesamiento por lotes.

## Plan de contingencia

Si la nube falla:

```powershell
.\.venv-deploy\Scripts\Activate.ps1
python -m streamlit run app.py
```

Si no hay internet, usar capturas del Login, Homepage, Dota 2, Temas y Reseñas.
