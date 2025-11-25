from OpenGL.GL import *
import os
try:
    from PIL import Image
except ImportError:
    Image = None
    print("[TextureLoader] Error: Pillow (PIL) not installed. Textures will not load.")


class TextureLoader:
    @staticmethod
    def load_texture(path):
        if Image is None:
            print("[TextureLoader] Cannot load texture because PIL is missing.")
            return None

        # Resolver ruta absoluta para evitar errores de CWD
        if not os.path.isabs(path):
            full_path = os.path.abspath(path)

            # Si no existe relativo al CWD, intentar relativo a la raíz del proyecto
            if not os.path.exists(full_path):
                # Estamos en src/graphics/texture_loader.py
                # Subir 2 niveles para salir de src/graphics -> src
                # Subir 1 nivel más para salir de src -> Root
                current_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(os.path.dirname(current_dir))

                possible_path = os.path.join(project_root, path)
                if os.path.exists(possible_path):
                    full_path = possible_path
        else:
            full_path = path

        if not os.path.exists(full_path):
            print(f"[TextureLoader] Error: File not found at {full_path}")
            return None

        try:
            img = Image.open(full_path)
            # Convertir a RGBA para asegurar consistencia
            img = img.convert("RGBA")

            # Voltear horizontalmente para corregir el efecto espejo (East/West)
            # No volteamos verticalmente (FLIP_TOP_BOTTOM) porque al rotar el planeta 90 grados
            # (para alinear polos), la orientación vertical se corrige "naturalmente" si
            # mapeamos los pixeles del Norte (Top) al Polo Sur (T=0) y luego rotamos el Polo Sur hacia Arriba?
            # Espera, si rotamos 90 en X: Z+ (Norte) -> -Y (Abajo). Z- (Sur) -> Y (Arriba).
            # Si no hacemos FLIP_TOP_BOTTOM:
            #   Image Top (Norte) -> Data Start -> T=0 -> Z- (Sur).
            #   Image Bottom (Sur) -> Data End -> T=1 -> Z+ (Norte).
            #   Resultado: Pixeles Norte en Z- (Sur). Pixeles Sur en Z+ (Norte).
            #   Al rotar 90 en X:
            #     Z- (Sur, con pixeles Norte) -> Y (Arriba).
            #     Z+ (Norte, con pixeles Sur) -> -Y (Abajo).
            #   Resultado Final: Pixeles Norte Arriba. Pixeles Sur Abajo. CORRECTO.

            # img = img.transpose(Image.FLIP_LEFT_RIGHT)
            # img = img.transpose(Image.FLIP_TOP_BOTTOM)

            img_data = img.tobytes("raw", "RGBA", 0, -1)
            width, height = img.size

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Configurar parámetros de textura
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Cargar datos
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                         0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

            print(
                f"[TextureLoader] Successfully loaded texture: {path} (ID: {texture_id})")
            return texture_id
        except Exception as e:
            print(f"[TextureLoader] Failed to load texture {path}: {e}")
            return None
