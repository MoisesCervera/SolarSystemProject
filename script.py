import numpy as np
from PIL import Image
import py360convert


def convert_flat_to_equi(img_path, output_path):
    # 1. Cargar imagen
    try:
        pil_img = Image.open(img_path)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{img_path}'")
        return

    # 2. Redimensionar a cuadrado (importante para las caras del cubo)
    w, h = pil_img.size
    if h != w:
        print(f"Redimensionando de {w}x{h} a cuadrado...")
        min_side = min(h, w)
        pil_img = pil_img.resize((min_side, min_side), Image.LANCZOS)

    # Convertir a numpy array y asegurar RGB (quitar alfa si existe)
    image = np.array(pil_img)
    if image.shape[2] == 4:
        image = image[:, :, :3]

    # 3. Crear el Cubo (repetir la misma textura en las 6 caras)
    # IMPORTANTE: Esto debe ser una LISTA de Python de arrays, NO un array gigante.
    cube_faces = [image, image, image, image, image, image]

    print("Convirtiendo...")

    # 4. Convertir
    out_img = py360convert.c2e(
        cube_faces,
        h=1024,
        w=2048,
        mode='bilinear',
        cube_format='list'
    )

    # 5. Guardar
    Image.fromarray(out_img.astype(np.uint8)).save(output_path)
    print(f"¡Listo! Guardado en: {output_path}")


# Ejecutar
if __name__ == "__main__":
    # Asegúrate de que 'tu_textura.jpg' exista en la carpeta
    convert_flat_to_equi('tu_textura.jpg', 'textura_equirectangular.jpg')