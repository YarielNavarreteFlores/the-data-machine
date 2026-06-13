# Resultados y limitaciones

## 1. Alcance de evaluación

Se evaluaron 5,000 reseñas recientes: 500 por cada uno de los 10 videojuegos. La referencia individual es `voted_up` de Steam. Las reseñas clasificadas como neutrales por VADER se excluyen de la evaluación binaria y se reportan mediante la métrica de cobertura.

## 2. Resultados por videojuego

| Videojuego | Accuracy | Balanced accuracy | Cobertura | Baseline mayoritario | Cumple 75 % | Supera baseline |
|---|---:|---:|---:|---:|:---:|:---:|
| Dota 2 | 78.2 % | 73.0 % | 56.8 % | 71.8 % | Sí | Sí |
| War Thunder | 69.4 % | 70.4 % | 77.0 % | 56.9 % | No | Sí |
| Rust | 70.8 % | 71.8 % | 76.6 % | 74.9 % | No | No |
| The Witcher 3: Wild Hunt | 93.4 % | 80.4 % | 72.8 % | 97.5 % | Sí | No |
| Hollow Knight | 83.2 % | 66.9 % | 74.8 % | 97.9 % | Sí | No |
| Stardew Valley | 93.7 % | 75.7 % | 82.0 % | 98.3 % | Sí | No |
| Phasmophobia | 70.8 % | 66.9 % | 81.4 % | 67.3 % | No | Sí |
| Among Us | 86.7 % | 82.2 % | 70.6 % | 92.6 % | Sí | No |
| Apex Legends | 81.7 % | 79.3 % | 74.4 % | 69.1 % | Sí | Sí |
| ELDEN RING | 76.8 % | 59.1 % | 74.2 % | 93.0 % | Sí | No |

## 3. Resumen global

- Accuracy promedio: **80.4 %**.
- Balanced accuracy promedio: **72.6 %**.
- Cobertura no neutral promedio: **74.1 %**.
- Juegos con accuracy igual o superior a 75 %: **7 de 10**.
- Juegos que superan el baseline mayoritario: **4 de 10**.

## 4. Interpretación

El objetivo de 75 % de accuracy se cumple en la mayoría de los títulos. Sin embargo, la accuracy debe interpretarse junto con el baseline.

En títulos con una proporción muy alta de recomendaciones positivas, un clasificador que siempre predice la clase mayoritaria puede lograr una accuracy superior a VADER. Por ejemplo, The Witcher 3, Hollow Knight y Stardew Valley presentan baselines cercanos a 98 %. En esos casos VADER ofrece mayor diversidad de predicción, pero no supera el baseline en accuracy.

War Thunder y Apex Legends muestran un caso distinto: VADER supera claramente el baseline y conserva una balanced accuracy razonable, lo que indica mayor utilidad para distinguir ambas clases.

## 5. Diferencia entre métricas históricas y muestra reciente

El dashboard compara:

- aprobación histórica agregada del dataset;
- aprobación de las 500 reseñas recientes;
- proporción positiva asignada por VADER.

Estas cifras no son equivalentes. La primera resume toda la historia disponible del juego; la segunda representa una ventana reciente; la tercera depende de un clasificador léxico que además puede asignar neutralidad.

Por ello, el “error respecto al histórico” no debe interpretarse como accuracy individual. Es una diferencia descriptiva entre poblaciones y metodologías distintas.

## 6. Temas

TF-IDF entrega 15 términos por juego, incluyendo unigramas y bigramas. Estos resultados se contrastan con 15 tags comunitarios de Steam. La separación es importante:

- TF-IDF se calcula sobre el corpus reciente;
- los tags provienen de la comunidad y describen características globales del juego.

La nube de palabras ayuda a explorar vocabulario frecuente, pero no sustituye una evaluación temática formal.

## 7. Limitaciones

### Datos

- 500 reseñas recientes por juego no representan toda la historia.
- La adquisición prioriza disponibilidad y recencia, no un muestreo aleatorio estratificado.
- El corpus puede contener spam, texto corto, emojis, otros idiomas y contenido fuera de contexto.

### Modelo

- VADER fue diseñado para inglés y texto informal.
- Puede fallar con sarcasmo, negaciones complejas, jerga de videojuegos y reseñas mixtas.
- Excluir neutrales incrementa claridad binaria, pero reduce la cobertura.
- TF-IDF identifica relevancia léxica, no necesariamente temas semánticos completos.

### Aplicación

- El login es demostrativo.
- El despliegue utiliza resultados precalculados y no realiza scraping en tiempo real.
- La versión de Community Cloud tiene recursos limitados.

## 8. Trabajo futuro

1. Muestreo por periodos y tipo de recomendación.
2. Detección de idioma y análisis multilingüe.
3. Modelos supervisados o Transformers.
4. Calibración de umbrales por dominio.
5. Análisis temporal y detección de cambios después de actualizaciones.
6. Datos en Parquet/base de datos para escalar.
7. Procesamiento incremental y selección dinámica de juegos.
8. Autenticación real y perfiles persistentes.
