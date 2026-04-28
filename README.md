<div align="center">

```
████████╗██╗  ██╗███████╗    ██████╗  █████╗ ████████╗ █████╗ 
╚══██╔══╝██║  ██║██╔════╝    ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
   ██║   ███████║█████╗      ██║  ██║███████║   ██║   ███████║
   ██║   ██╔══██║██╔══╝      ██║  ██║██╔══██║   ██║   ██╔══██║
   ██║   ██║  ██║███████╗    ██████╔╝██║  ██║   ██║   ██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
███╗   ███╗ █████╗  ██████╗██╗  ██╗██╗███╗   ██╗███████╗
████╗ ████║██╔══██╗██╔════╝██║  ██║██║████╗  ██║██╔════╝
██╔████╔██║███████║██║     ███████║██║██╔██╗ ██║█████╗  
██║╚██╔╝██║██╔══██║██║     ██╔══██║██║██║╚██╗██║██╔══╝  
██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║██║██║ ╚████║███████╗
╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝
```

### 🎮 Análisis de reseñas de videojuegos con NLP · La máquina de datos

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![scikit--learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![NLTK](https://img.shields.io/badge/NLTK-VADER-154360?style=for-the-badge&logoColor=white)

![Status](https://img.shields.io/badge/STATUS-EN%20DESARROLLO-yellow?style=for-the-badge)
![Semestre](https://img.shields.io/badge/SEMESTRE-IV-purple?style=for-the-badge)
![IPN](https://img.shields.io/badge/IPN-ESCOM%20%2F%20-8B0000?style=for-the-badge)

</div>

---

## ⚔️ ¿Qué es The Data Machine?

> *"Millones de reseñas. Cero tiempo para leerlas. Una máquina para entenderlas todas."*

**The Data Machine** es una aplicación web de análisis de reseñas de videojuegos. A partir de un dataset real de Steam con millones de opiniones, la app clasifica el sentimiento de la comunidad, detecta los temas más recurrentes y lo presenta todo en un dashboard interactivo — sin que el usuario tenga que leer ni una sola reseña.

El usuario inicia sesión, elige su juego del catálogo y obtiene en segundos:

- 📊 **¿La comunidad lo ama o lo odia?** — gráfica de sentimiento positivo / negativo / neutral
- ☁️ **¿De qué habla la gente?** — nube de palabras con los términos más frecuentes
- 🏷️ **¿Qué temas se repiten?** — bugs, historia, precio, multijugador... lo que más menciona la gente
- ⬇️ **¿Quieres los datos?** — descarga el análisis completo en CSV o la gráfica en PNG

---

## 🗺️ Mapa del Proyecto

```
📁 the-data-machine/
├── 🚀 app.py                        ← Punto de entrada de Streamlit
├── 📋 requirements.txt              ← Dependencias del proyecto
├── 📖 README.md                     ← Este archivo
│
├── 📁 data/
│   ├── raw/                         ← Dataset original de Kaggle (sin tocar)
│   └── processed/                   ← Dataset limpio listo para análisis
│
├── 📁 notebooks/
│   ├── 01_eda.ipynb                 ← Exploración inicial del dataset
│   ├── 02_sentimiento.ipynb         ← Prototipo análisis de sentimiento
│   └── 03_temas.ipynb               ← Prototipo extracción de temas TF-IDF
│
├── 📁 src/
│   ├── auth.py                      ← Login y manejo de sesión
│   ├── data_loader.py               ← Carga y filtrado del dataset
│   └── nlp.py                       ← Sentimiento (VADER) + temas (TF-IDF)
│
└── 📁 pages/
    ├── 1_Login.py                   ← Pantalla de inicio de sesión
    ├── 2_Homepage.py                ← Catálogo de videojuegos
    └── 3_Analisis.py                ← Dashboard de análisis
```

---

## 🎮 Pantallas de la App

| Pantalla | Descripción |
|----------|-------------|
| 🔐 **Login** | Autenticación de usuario con manejo de sesión |
| 🏠 **Homepage** | Catálogo visual de juegos con rating general de sentimiento |
| 📊 **Dashboard** | Análisis completo: sentimiento, nube de palabras, temas y descarga |

---

## 🛠️ Stack Tecnológico

<div align="center">

| Capa | Tecnología | Uso |
|------|-----------|-----|
| 🖥️ App Web | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white) | Framework de la app web completa |
| 📦 Datos | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white) ![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy&logoColor=white) | Carga, limpieza y manipulación del dataset |
| 🧠 NLP | ![NLTK](https://img.shields.io/badge/NLTK-VADER-154360?style=flat) | Análisis de sentimiento por reseña |
| 🔍 Temas | ![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white) | Extracción de temas con TF-IDF |
| 📊 Gráficas | ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white) | Gráficas interactivas en el dashboard |
| ☁️ Nube | ![WordCloud](https://img.shields.io/badge/WordCloud-8E44AD?style=flat) | Nube de palabras por videojuego |
| 🔄 Versiones | ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white) | Control de versiones y colaboración |
| ☁️ Deploy | ![Streamlit Cloud](https://img.shields.io/badge/Streamlit_Cloud-FF4B4B?style=flat&logo=streamlit&logoColor=white) | Hosting gratuito de la app |

</div>

---

## 📡 Dataset

El proyecto utiliza el dataset **Steam Reviews 2021** disponible públicamente en Kaggle:

- 🔗 **Fuente:** [kaggle.com/datasets/najzeko/steam-reviews-2021](https://www.kaggle.com/datasets/najzeko/steam-reviews-2021)
- 📊 **Contenido:** +21 millones de reseñas reales de usuarios de Steam
- 🌐 **Idioma principal:** Inglés
- 💰 **Costo:** Gratuito con cuenta de Kaggle

**Columnas principales utilizadas:**

| Columna | Descripción |
|---------|-------------|
| `app_name` | Nombre del videojuego |
| `review` | Texto completo de la reseña (input del NLP) |
| `voted_up` | Si el usuario recomendó el juego (True/False) |
| `timestamp_created` | Fecha de la reseña |
| `language` | Idioma de la reseña |

---

## 🚀 Cómo Ejecutar el Proyecto

**1. Clonar el repositorio**
```bash
git clone https://github.com/MelSurikun/the-data-machine.git
cd the-data-machine
```

**2. Crear y activar entorno virtual**
```bash
# Crear entorno
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Mac/Linux
source venv/bin/activate
```

**3. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**4. Descargar dataset**

Descarga el dataset de Kaggle y colócalo en `data/raw/steam_reviews.csv`

**5. Ejecutar la app**
```bash
streamlit run app.py
```

La app abre automáticamente en `http://localhost:8501` 🎮

---

## 🌐 Demo en Vivo

> 🚧 Disponible próximamente en Streamlit Community Cloud

---

## 👾 Equipo

<div align="center">

| Avatar | Nombre | Rol en el Proyecto |
|--------|--------|--------------------|
| 👩‍💻 | **Melanie** | Arquitecta del Proyecto · Ingesta de Datos · Homepage · Integración |
| 👩‍🔬 | **Melina** | Login & Auth · Análisis de Sentimiento (NLP) · Export |
| 🧙‍♀️ | **Yariel** | Preprocesamiento · Extracción de Temas · Dashboard Visual |

</div>

---

## 📅 Cronograma

```
Sem 1  [28 Abr – 4 May]   ████░░░░░░░░   🔍 Investigación & Setup GitHub
Sem 2  [5 May – 11 May]   ████████░░░░   📦 Ingesta & EDA del dataset
Sem 3  [12 May – 18 May]  ████████████   🧠 Módulo NLP (sentimiento + temas)
Sem 4  [19 May – 25 May]  ░░░░░░░░░░░░   🖥️ Desarrollo de la App Web
Sem 5  [26 May – 1 Jun]   ░░░░░░░░░░░░   🔗 Integración & Deploy
Sem 6  [2 Jun – 6 Jun]    ░░░░░░░░░░░░   🎓 Documentación & Entrega Final
```

---

## 📚 Contexto Académico

```
🏫 Instituto Politécnico Nacional
🏢 ESCOM
📖 Licenciatura en Ciencia de Datos
📘 Unidad de Aprendizaje: Desarrollo de Aplicaciones para Análisis de Datos
📅 Semestre IV · 2026
```

---

<div align="center">

*Hecho con 🎮 y mucho café por el equipo La Máquina de Datos*

</div>
