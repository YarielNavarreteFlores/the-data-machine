from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]
PUERTO = 8765
URL_SALUD = (
    f"http://127.0.0.1:{PUERTO}"
    "/_stcore/health"
)


def esperar_servidor(
    proceso: subprocess.Popen[str],
    segundos: int = 45,
) -> bool:
    """
    Espera a que Streamlit responda en su endpoint de salud.
    """
    limite = time.time() + segundos

    while time.time() < limite:
        if proceso.poll() is not None:
            return False

        try:
            with urllib.request.urlopen(
                URL_SALUD,
                timeout=2,
            ) as respuesta:
                contenido = (
                    respuesta.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                    .strip()
                    .lower()
                )

                if (
                    respuesta.status == 200
                    and contenido == "ok"
                ):
                    return True

        except (
            urllib.error.URLError,
            TimeoutError,
        ):
            pass

        time.sleep(1)

    return False


def detener_proceso(
    proceso: subprocess.Popen[str],
) -> None:
    """
    Detiene Streamlit y sus procesos descendientes.

    En Windows se utiliza taskkill /T para evitar que un proceso
    secundario conserve abierto el archivo temporal del log.
    """
    if proceso.poll() is not None:
        return

    if os.name == "nt":
        subprocess.run(
            [
                "taskkill",
                "/PID",
                str(proceso.pid),
                "/T",
                "/F",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        try:
            proceso.wait(
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            proceso.kill()
            proceso.wait(
                timeout=5,
            )

        return

    proceso.terminate()

    try:
        proceso.wait(
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        proceso.kill()
        proceso.wait(
            timeout=5,
        )


def eliminar_log_temporal(
    ruta_log: Path,
    intentos: int = 12,
    pausa: float = 0.25,
) -> None:
    """
    Elimina el log temporal con reintentos.

    Windows puede conservar el archivo bloqueado unos instantes
    después de cerrar Streamlit. La limpieza no debe convertir
    una prueba aprobada en un fallo.
    """
    for intento in range(1, intentos + 1):
        try:
            ruta_log.unlink(
                missing_ok=True,
            )
            return

        except PermissionError:
            if intento == intentos:
                print(
                    "[ADVERTENCIA] No se pudo eliminar "
                    f"el log temporal: {ruta_log}"
                )
                return

            time.sleep(
                pausa,
            )


def mostrar_ultimas_lineas(
    ruta_log: Path,
    cantidad: int = 40,
) -> None:
    """
    Muestra el final del log cuando Streamlit no arranca.
    """
    if not ruta_log.exists():
        return

    lineas = ruta_log.read_text(
        encoding="utf-8",
        errors="replace",
    ).splitlines()

    print("\nÚLTIMAS LÍNEAS DEL LOG")
    print("-" * 72)

    for linea in lineas[-cantidad:]:
        print(linea)


def main() -> int:
    """
    Inicia Streamlit en modo headless, comprueba salud y lo detiene.
    """
    comando = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.headless=true",
        f"--server.port={PUERTO}",
        "--browser.gatherUsageStats=false",
    ]

    print("=" * 72)
    print("PRUEBA DE ARRANQUE STREAMLIT — THE DATA MACHINE")
    print("=" * 72)
    print(
        "[INFO] Ejecutando: "
        + " ".join(comando)
    )

    # mkstemp crea una ruta única. El descriptor se cierra antes
    # de entregar el archivo al proceso de Streamlit.
    descriptor, nombre_log = tempfile.mkstemp(
        suffix=".log",
    )
    os.close(
        descriptor,
    )

    ruta_log = Path(
        nombre_log
    )

    proceso: subprocess.Popen[str] | None = None
    aprobado = False

    try:
        with ruta_log.open(
            "w",
            encoding="utf-8",
        ) as salida_log:
            proceso = subprocess.Popen(
                comando,
                cwd=RAIZ,
                stdout=salida_log,
                stderr=subprocess.STDOUT,
                text=True,
            )

        aprobado = esperar_servidor(
            proceso,
        )

    finally:
        if proceso is not None:
            detener_proceso(
                proceso,
            )

    if aprobado:
        print(
            f"[OK] Streamlit respondió en "
            f"{URL_SALUD}"
        )
        print(
            "RESULTADO: ARRANQUE HEADLESS "
            "APROBADO."
        )
        codigo_salida = 0

    else:
        print(
            "[ERROR] Streamlit no respondió "
            "correctamente."
        )
        mostrar_ultimas_lineas(
            ruta_log,
        )
        codigo_salida = 1

    eliminar_log_temporal(
        ruta_log,
    )

    return codigo_salida


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
