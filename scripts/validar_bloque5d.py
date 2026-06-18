from __future__ import annotations

import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]

ARCHIVOS = {
    "readme": RAIZ / "README.md",
    "arquitectura": RAIZ / "docs" / "ARQUITECTURA.md",
    "resultados": RAIZ / "docs" / "RESULTADOS_Y_LIMITACIONES.md",
    "demo": RAIZ / "docs" / "GUIA_DEMO.md",
    "checklist": RAIZ / "docs" / "RELEASE_CHECKLIST.md",
    "informe_docx": RAIZ / "docs" / "Informe_Final_The_Data_Machine.docx",
    "informe_pdf": RAIZ / "docs" / "Informe_Final_The_Data_Machine.pdf",
    "app": RAIZ / "app.py",
    "manifest": RAIZ / "data" / "production" / "manifest.json",
}

URL_APP = "https://the-data-machine-01.streamlit.app/"

MARCADORES_README = (
    "5,000 reseñas",
    "10 videojuegos",
    "8,854,428",
    "56 pruebas",
    URL_APP,
    "data/production",
    "Python 3.12",
    "docs/ARQUITECTURA.md",
    "docs/RESULTADOS_Y_LIMITACIONES.md",
)

TEXTOS_OBSOLETOS = (
    "STATUS-EN%20DESARROLLO",
    "Disponible próximamente",
    "pages/1_Login.py",
    "pages/2_Homepage.py",
    "pages/3_Analisis.py",
    "src/data_loader.py",
    "games_march2025_cleaned.csv",
    "+21 millones de reseñas",
)


def main() -> int:
    errores: list[str] = []

    print("=" * 72)
    print("VALIDACIÓN DEL BLOQUE 5D - DOCUMENTACIÓN Y LIBERACIÓN")
    print("=" * 72)

    for nombre, ruta in ARCHIVOS.items():
        if not ruta.exists():
            errores.append(f"No existe {ruta.relative_to(RAIZ)}")
            print(f"[ERROR] Falta: {ruta.relative_to(RAIZ)}")
        elif ruta.stat().st_size == 0:
            errores.append(f"Está vacío {ruta.relative_to(RAIZ)}")
            print(f"[ERROR] Vacío: {ruta.relative_to(RAIZ)}")
        else:
            print(f"[OK] Localizado: {ruta.relative_to(RAIZ)}")

    if errores:
        print("=" * 72)
        print(f"RESULTADO: BLOQUE 5D NO APROBADO ({len(errores)} errores).")
        return 1

    readme = ARCHIVOS["readme"].read_text(encoding="utf-8")

    for marcador in MARCADORES_README:
        if marcador not in readme:
            errores.append(f"README no contiene: {marcador}")
            print(f"[ERROR] Falta en README: {marcador}")
        else:
            print(f"[OK] Marcador README: {marcador}")

    for texto in TEXTOS_OBSOLETOS:
        if texto in readme:
            errores.append(f"README conserva texto obsoleto: {texto}")
            print(f"[ERROR] Texto obsoleto: {texto}")

    contenidos = {
        nombre: ruta.read_text(encoding="utf-8")
        for nombre, ruta in ARCHIVOS.items()
        if ruta.suffix == ".md"
    }

    comprobaciones = {
        "arquitectura": ("src/scraper.py", "src/nlp.py", "src/production.py", "Streamlit Community Cloud"),
        "resultados": ("Accuracy promedio", "Baseline", "Limitaciones", "80.4 %"),
        "demo": ("Guion sugerido", "Dota 2", "War Thunder", "Plan de contingencia"),
        "checklist": ("56 pruebas", "Pull request", "Teams", "v1.0.0"),
    }

    for documento, marcadores in comprobaciones.items():
        contenido = contenidos[documento]
        for marcador in marcadores:
            if marcador not in contenido:
                errores.append(f"{documento} no contiene: {marcador}")
                print(f"[ERROR] Falta en {documento}: {marcador}")
        print(f"[OK] Contenido mínimo: {ARCHIVOS[documento].relative_to(RAIZ)}")

    print("=" * 72)

    if errores:
        print(f"RESULTADO: BLOQUE 5D NO APROBADO ({len(errores)} errores).")
        for error in errores:
            print(f"- {error}")
        return 1

    print("RESULTADO: DOCUMENTACIÓN FINAL PREPARADA CORRECTAMENTE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
