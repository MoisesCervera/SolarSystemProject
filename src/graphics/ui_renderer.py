from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from PIL import Image, ImageDraw, ImageFont
import os
from src.core.resource_loader import ResourceManager


class UIRenderer:
    """
    Clase estática para dibujar la interfaz 2D.
    """
    _font_cache = {}
    _texture_cache = {}

    # Primary custom font used across the UI
    FONT_PATH = ResourceManager.get_font_path("Exo Space DEMO.ttf")
    # New alternate custom font used for answers and labels (SF Pro)
    FONT_SFPRO_PATH = ResourceManager.get_font_path("SF-Pro.ttf")
    # New sci-fi fonts
    FONT_SPACE_ARMOR_PATH = ResourceManager.get_font_path("space_armor.otf")
    FONT_RADIOSPACE_PATH = ResourceManager.get_font_path("radiospace.ttf")

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
                    # Support an alternate custom font via font_name alias
                    if font_name:
                        fn = font_name.lower()
                        # Map alias to SF-Pro first
                        if fn in ("sfpro", "sf-pro", "sf pro"):
                            try:
                                cls._font_cache[key] = ImageFont.truetype(
                                    cls.FONT_SFPRO_PATH, size)
                            except IOError:
                                cls._font_cache[key] = ImageFont.truetype(
                                    cls.FONT_PATH, size)
                        # Map alias to Space Armor
                        elif fn in ("space_armor", "space armor", "spacearmor"):
                            try:
                                cls._font_cache[key] = ImageFont.truetype(
                                    cls.FONT_SPACE_ARMOR_PATH, size)
                            except IOError:
                                cls._font_cache[key] = ImageFont.truetype(
                                    cls.FONT_PATH, size)
                        # Map alias to Radiospace
                        elif fn in ("radiospace", "radio space"):
                            try:
                                cls._font_cache[key] = ImageFont.truetype(
                                    cls.FONT_RADIOSPACE_PATH, size)
                            except IOError:
                                cls._font_cache[key] = ImageFont.truetype(
                                    cls.FONT_PATH, size)
                        else:
                            cls._font_cache[key] = ImageFont.truetype(
                                cls.FONT_PATH, size)
                    else:
                        cls._font_cache[key] = ImageFont.truetype(
                            cls.FONT_PATH, size)
            except IOError:
                print(
                    f"Warning: Could not load font {cls.FONT_PATH}. Using default.")
                cls._font_cache[key] = ImageFont.load_default()
        return cls._font_cache[key]

    @classmethod
    def get_text_texture(cls, text, size, font_name=None, bold=False, stroke_width=0, bold_strength=1, scale=1):
        key = (text, size, font_name, bool(bold), int(
            stroke_width), int(bold_strength), int(scale))
        if key in cls._texture_cache:
            return cls._texture_cache[key]

        font = cls.get_font(size, font_name)
        if scale != 1:
            # Create a scaled font instance for measurements and drawing
            scaled_font = cls.get_font(int(size * scale), font_name)
        else:
            scaled_font = font
        # Obtener tamaño del texto
        top_offset = 0
        left_offset = 0
        try:
            left, top, right, bottom = scaled_font.getbbox(text)
            width = right - left
            height = bottom - top
            top_offset = -top  # Account for ascender offset
            left_offset = -left
            # Ajuste de padding
            # Expand texture to account for stroke/bold offsets
            stroke_pad = max(0, stroke_width)
            if bold and stroke_pad == 0:
                # Default bold padding if no explicit stroke given
                stroke_pad = 1
            width += 8 + stroke_pad * 2
            height += 8 + stroke_pad * 2
        except AttributeError:
            width, height = font.getsize(text)
            width += 8
            height += 8

        if width <= 0 or height <= 0:
            return None, 0, 0

        # Crear imagen RGBA (render at scale for HiDPI crispness)
        image = Image.new("RGBA", (int(width), int(height)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Dibujar texto en blanco (se teñirá con glColor)
        # Use top_offset to properly position text and avoid cutoff
        # scale drawing positions if scale != 1
        x_pos = int(4 + left_offset + stroke_pad)
        y_pos = int(4 + top_offset + stroke_pad)
        # scale font drawing size
        # If font size needs rescaling, load a scaled font instead
        if scale != 1:
            # Create a scaled font instance for crispness
            try:
                scaled_font_size = int(size * scale)
                font = ImageFont.truetype(font.path, scaled_font_size) if hasattr(
                    font, 'path') else font
            except Exception:
                # Some PIL fonts might not expose .path; fallback to original font
                pass
        fill = (255, 255, 255, 255)

        # Try to use stroke_width drawing if provided, else emulate bold by drawing offsets
        if stroke_width > 0:
            # Pillow supports stroke_width and stroke_fill in newer versions; try it
            try:
                draw.text((x_pos, y_pos), text, font=scaled_font,
                          fill=fill, stroke_width=int(stroke_width * scale), stroke_fill=fill)
            except TypeError:
                # Fallback: draw multiple strokes around the text to mimic thickness
                s = int(max(1, stroke_width * scale))
                for dx in range(-s, s + 1):
                    for dy in range(-s, s + 1):
                        draw.text((x_pos + dx, y_pos + dy), text,
                                  font=scaled_font, fill=fill)
        elif bold:
            # Emulate bold by drawing multiple slightly offset duplicates
            # bold_strength controls the offset magnitude and thus thickness
            bs = max(1, int(bold_strength))
            # Scale the offset by scale to keep visual weight consistent on HiDPI
            sbs = max(1, int(bs * scale))
            offsets = [(0, 0), (-sbs, 0), (sbs, 0), (0, -sbs), (0, sbs)]
            for dx, dy in offsets:
                draw.text((x_pos + dx, y_pos + dy), text,
                          font=scaled_font, fill=fill)
        else:
            draw.text((x_pos, y_pos), text, font=font, fill=fill)

        # No volteamos la imagen. Enviamos los bytes tal cual (Top-Down).
        # image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # Generar textura
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        img_data = image.tobytes("raw", "RGBA", 0, -1)
        tex_w, tex_h = image.size
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, tex_w, tex_h,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        # Generate mipmaps for better downscaled quality
        try:
            glGenerateMipmap(GL_TEXTURE_2D)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                            GL_LINEAR_MIPMAP_LINEAR)
        except Exception:
            # GLenum not supported? ignore
            pass

        # Store rendered texture size as displayed width (tex_w / scale)
        disp_w = int(round(tex_w / scale))
        disp_h = int(round(tex_h / scale))
        cls._texture_cache[key] = (texture_id, disp_w, disp_h)
        return texture_id, disp_w, disp_h

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
    def draw_text(x, y, text, size=20, color=(1.0, 1.0, 1.0), font_name=None, bold=False, stroke_width=0, bold_strength=1, scale=1):
        """
        Renderiza texto usando una textura generada con PIL y TrueType Font.
        """
        # Reemplazar caracteres no soportados por la fuente
        text = text.replace("[", "<").replace("]", ">")

        texture_id, width, height = UIRenderer.get_text_texture(
            text, size, font_name, bold=bold, stroke_width=stroke_width, bold_strength=bold_strength, scale=scale)
        if not texture_id:
            return

        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        if len(color) == 4:
            glColor4f(*color)
        else:
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
