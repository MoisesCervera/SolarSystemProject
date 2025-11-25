from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image, ImageDraw, ImageFont
import os


class UIRenderer:
    """
    Clase estática para dibujar la interfaz 2D.
    """
    _font_cache = {}
    _texture_cache = {}
    FONT_PATH = "assets/fonts/Exo Space DEMO.ttf"

    @classmethod
    def get_font(cls, size, font_name=None):
        key = (font_name, size)
        if key not in cls._font_cache:
            try:
                if font_name and font_name.lower() == "helvetica":
                    # Try loading Helvetica or Arial
                    try:
                        cls._font_cache[key] = ImageFont.truetype(
                            "Helvetica", size)
                    except IOError:
                        try:
                            cls._font_cache[key] = ImageFont.truetype(
                                "Arial", size)
                        except IOError:
                            cls._font_cache[key] = ImageFont.load_default()
                else:
                    cls._font_cache[key] = ImageFont.truetype(
                        cls.FONT_PATH, size)
            except IOError:
                print(
                    f"Warning: Could not load font {cls.FONT_PATH}. Using default.")
                cls._font_cache[key] = ImageFont.load_default()
        return cls._font_cache[key]

    @classmethod
    def get_text_texture(cls, text, size, font_name=None):
        key = (text, size, font_name)
        if key in cls._texture_cache:
            return cls._texture_cache[key]

        font = cls.get_font(size, font_name)
        # Obtener tamaño del texto
        try:
            left, top, right, bottom = font.getbbox(text)
            width = right - left
            height = bottom - top
            # Ajuste de padding
            width += 6
            height += 6
        except AttributeError:
            width, height = font.getsize(text)

        if width <= 0 or height <= 0:
            return None, 0, 0

        # Crear imagen RGBA
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Dibujar texto en blanco (se teñirá con glColor)
        draw.text((3, 0), text, font=font, fill=(255, 255, 255, 255))

        # No volteamos la imagen. Enviamos los bytes tal cual (Top-Down).
        # image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # Generar textura
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        img_data = image.tobytes("raw", "RGBA", 0, -1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

        cls._texture_cache[key] = (texture_id, width, height)
        return texture_id, width, height

    @staticmethod
    def setup_2d(width, height):
        """Configura glMatrixMode(GL_PROJECTION) y gluOrtho2D."""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Desactivar lighting y depth test para UI
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)

    @staticmethod
    def restore_3d():
        """Restaura el estado 3D previo."""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        # Restaurar modo ModelView para no romper el flujo externo
        glMatrixMode(GL_MODELVIEW)

    @staticmethod
    def draw_scifi_panel(x, y, w, h):
        """
        Dibuja un cuadro semitransparente (Alpha 0.7) con esquinas recortadas (chamfered).
        Dibuja un borde (GL_LINE_LOOP) color Cian o Verde Neón alrededor.
        """
        # Fondo semitransparente
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(0.0, 0.1, 0.2, 0.7)  # Azul oscuro transparente

        chamfer = 10.0

        glBegin(GL_POLYGON)
        glVertex2f(x + chamfer, y)
        glVertex2f(x + w - chamfer, y)
        glVertex2f(x + w, y + chamfer)
        glVertex2f(x + w, y + h - chamfer)
        glVertex2f(x + w - chamfer, y + h)
        glVertex2f(x + chamfer, y + h)
        glVertex2f(x, y + h - chamfer)
        glVertex2f(x, y + chamfer)
        glEnd()

        # Borde Cian
        glLineWidth(2.0)
        glColor3f(0.0, 1.0, 1.0)

        glBegin(GL_LINE_LOOP)
        glVertex2f(x + chamfer, y)
        glVertex2f(x + w - chamfer, y)
        glVertex2f(x + w, y + chamfer)
        glVertex2f(x + w, y + h - chamfer)
        glVertex2f(x + w - chamfer, y + h)
        glVertex2f(x + chamfer, y + h)
        glVertex2f(x, y + h - chamfer)
        glVertex2f(x, y + chamfer)
        glEnd()

        glDisable(GL_BLEND)

    @staticmethod
    def draw_text(x, y, text, size=20, color=(1.0, 1.0, 1.0), font_name=None):
        """
        Renderiza texto usando una textura generada con PIL y TrueType Font.
        """
        # Reemplazar caracteres no soportados por la fuente
        text = text.replace("[", "<").replace("]", ">")

        texture_id, width, height = UIRenderer.get_text_texture(
            text, size, font_name)
        if not texture_id:
            return

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        glColor3f(*color)

        glBegin(GL_QUADS)
        # Coordenadas de textura estándar (0,0 abajo-izq)
        glTexCoord2f(0, 0)
        glVertex2f(x, y)
        glTexCoord2f(1, 0)
        glVertex2f(x + width, y)
        glTexCoord2f(1, 1)
        glVertex2f(x + width, y + height)
        glTexCoord2f(0, 1)
        glVertex2f(x, y + height)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

    @staticmethod
    def draw_hud_label(x, y, z, title, subtitle=None):
        """
        Dibuja una etiqueta flotante estilo HUD en la posición 3D indicada.
        """
        # 1. Obtener matrices actuales
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)

        # 2. Proyectar de 3D a 2D
        try:
            win_x, win_y, win_z = gluProject(
                x, y, z, modelview, projection, viewport)
        except Exception:
            return

        # Si está detrás de la cámara, no dibujar
        if win_z > 1.0:
            return

        # 3. Configurar 2D
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        UIRenderer.setup_2d(viewport[2], viewport[3])

        try:
            title_size = 16
            subtitle_size = 12
            padding = 10

            # Calcular tamaños
            _, t_w, t_h = UIRenderer.get_text_texture(title, title_size)
            s_w, s_h = 0, 0
            if subtitle:
                _, s_w, s_h = UIRenderer.get_text_texture(
                    subtitle, subtitle_size)

            box_w = max(t_w, s_w) + padding * 2
            box_h = t_h + (s_h + 4 if subtitle else 0) + padding * 2

            # Posición del panel (arriba del punto)
            panel_x = win_x - box_w / 2
            panel_y = win_y + 40

            # Dibujar panel
            UIRenderer.draw_scifi_panel(panel_x, panel_y, box_w, box_h)

            # Dibujar textos
            title_x = panel_x + (box_w - t_w) / 2
            title_y = panel_y + box_h - padding - t_h
            UIRenderer.draw_text(title_x, title_y, title,
                                 size=title_size, color=(0.0, 1.0, 1.0))

            if subtitle:
                sub_x = panel_x + (box_w - s_w) / 2
                sub_y = title_y - s_h - 4
                UIRenderer.draw_text(sub_x, sub_y, subtitle,
                                     size=subtitle_size, color=(0.8, 0.8, 0.8))

            # Línea conectora
            glDisable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glColor4f(0.0, 1.0, 1.0, 0.5)
            glLineWidth(1.0)
            glBegin(GL_LINES)
            glVertex2f(win_x, win_y)
            glVertex2f(win_x, panel_y)
            glEnd()

        finally:
            UIRenderer.restore_3d()
            glPopAttrib()
