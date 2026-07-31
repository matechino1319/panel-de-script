import os
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image


SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".tiff",
}

SESSION = None


def quitar_fondo(ruta_entrada, ruta_salida):
    from rembg import remove, new_session

    global SESSION
    if SESSION is None:
        print("Cargando motor de recorte...")
        SESSION = new_session("u2netp")
        print("Motor cargado correctamente.")

    with open(ruta_entrada, "rb") as archivo:
        contenido = archivo.read()

    resultado = remove(contenido, session=SESSION)
    imagen = Image.open(BytesIO(resultado)).convert("RGBA")
    imagen.save(ruta_salida, "PNG")


def main():
    file_path = os.environ.get("SCRIPT_INPUT_FILE", "").strip()
    output_dir = os.environ.get("SCRIPT_OUTPUT_DIR", "").strip()

    if not file_path:
        print("Error: no se recibio SCRIPT_INPUT_FILE.")
        return 1

    ruta_entrada = Path(file_path)
    extension = ruta_entrada.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        print(f"Error: formato no soportado '{extension}'. Formatos validos: {', '.join(SUPPORTED_EXTENSIONS)}")
        return 1

    if not output_dir:
        output_dir = str(ruta_entrada.parent)

    nombre_salida = f"{ruta_entrada.stem}_sin_fondo.png"
    ruta_salida = Path(output_dir) / nombre_salida

    print(f"Procesando imagen: {ruta_entrada}")
    quitar_fondo(str(ruta_entrada), str(ruta_salida))
    print(f"Imagen generada: {ruta_salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
