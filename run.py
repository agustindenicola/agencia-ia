"""Inicia el panel de la agencia en http://127.0.0.1:8790"""
import logging
import os

from agencia.server import create_app


def cargar_env(ruta=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Lee claves de un archivo .env (CLAVE=valor por línea), sin pisar las que ya estén definidas."""
    if os.path.exists(ruta):
        for linea in open(ruta, encoding="utf-8"):
            clave, sep, valor = linea.strip().partition("=")
            if sep and not clave.startswith("#"):
                os.environ.setdefault(clave.strip(), valor.strip().strip('"'))


cargar_env()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    from waitress import serve

    puerto = int(os.environ.get("PORT", "8790"))
    print(f"Panel de la agencia: http://127.0.0.1:{puerto}")
    serve(create_app(), host=os.environ.get("HOST", "127.0.0.1"), port=puerto, threads=4)
