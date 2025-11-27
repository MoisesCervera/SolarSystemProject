import json
import os
from OpenGL.GL import *
from src.graphics.ui_renderer import UIRenderer


class PlanetInfoPanel:
    TAB_ENCYCLOPEDIA = 0
    TAB_STRUCTURE = 1

    def __init__(self, planet_name, x, y, width, height):
        self.planet_name = planet_name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.current_tab = self.TAB_ENCYCLOPEDIA
        self.data = self._load_data()

        # Scroll state
        self.scroll_y = 0.0
        self.max_scroll = 0.0

        # Tab dimensions
        self.tab_height = 50
        self.tab_width = width / 2

        # Drag state
        self.dragging_scrollbar = False
        self.dragging_content = False
        self.last_mouse_y = 0

    def update_dimensions(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.tab_width = width / 2

    def _load_data(self):
        # Try to load from assets/data
        filename = f"{self.planet_name}.json"

        # Posibles rutas base
        base_paths = [
            "assets/data",
            "../assets/data",
            os.path.join(os.path.dirname(os.path.dirname(
                os.path.dirname(__file__))), "assets", "data")
        ]

        for base in base_paths:
            path = os.path.join(base, filename)
            if not os.path.exists(path):
                # Try capitalized
                path = os.path.join(
                    base, f"{self.planet_name.capitalize()}.json")

            if os.path.exists(path):
                print(f"[PlanetInfoPanel] Loading data from: {path}")
                try:
                    with open(path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"[PlanetInfoPanel] Error loading JSON: {e}")
                    return {}

        print(
            f"[PlanetInfoPanel] Could not find data file for {self.planet_name}")
        return {}

    def handle_click(self, x, y):
        """
        Maneja clics del mouse. x, y son coordenadas de pantalla (origen abajo-izquierda).
        Retorna True si el clic fue consumido por el panel.
        """
        # Verificar si está dentro del panel
        if not (self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height):
            return False

        # Verificar tabs
        tab_y_start = self.y + self.height - self.tab_height
        if y >= tab_y_start:
            if x < self.x + self.tab_width:
                self.current_tab = self.TAB_ENCYCLOPEDIA
            else:
                self.current_tab = self.TAB_STRUCTURE
            # Reset scroll on tab change
            self.scroll_y = 0.0
            return True

        # Verificar Scrollbar
        # Area de scrollbar: lado derecho, ancho 20px (para facilitar clic)
        if x > self.x + self.width - 30:
            self.dragging_scrollbar = True
            self._update_scroll_from_mouse(y)
            return True

        # Click en contenido para arrastrar
        self.dragging_content = True
        self.last_mouse_y = y
        return True

    def handle_drag(self, x, y):
        if self.dragging_scrollbar:
            self._update_scroll_from_mouse(y)
            return True

        if self.dragging_content:
            dy = y - self.last_mouse_y
            # Scroll normal (dy positivo sube contenido -> baja vista)
            self.handle_scroll(dy)
            # Si arrastro hacia arriba (dy > 0), quiero que el contenido baje (ver lo de arriba) -> scroll_y disminuye?
            # handle_scroll: scroll_y += y_offset * speed
            # Si muevo mouse arriba, quiero ver lo de abajo -> scroll_y aumenta.
            # Espera, comportamiento touch: arrastro arriba -> contenido sube -> veo lo de abajo.
            # Si arrastro arriba (dy > 0), contenido sube.
            # scroll_y controla el offset positivo del inicio del contenido.
            # Si scroll_y aumenta, el contenido baja (start_y + scroll_y).
            # Entonces si arrastro hacia arriba, quiero que el contenido suba (scroll_y disminuye).

            # Ajustemos handle_scroll para que sea intuitivo
            # Actualmente: self.scroll_y += y_offset * scroll_speed
            # Si paso dy positivo, scroll_y aumenta.

            # Touch drag logic:
            # Move finger up (dy > 0) -> Content moves up -> Scroll Down (view lower content) -> scroll_y increases?
            # No.
            # Content Y = BaseY + ScrollY.
            # If ScrollY increases, Content Y increases -> Content moves DOWN.
            # So positive ScrollY means we are seeing the TOP of the content (shifted down).
            # Wait.
            # Let's look at draw:
            # content_start_y = self.y + body_height - 40 + self.scroll_y
            # If scroll_y is 0, content starts at top.
            # If scroll_y is positive, content starts HIGHER? No, Y increases upwards in OpenGL usually?
            # In this project, Y=0 is bottom.
            # self.y is bottom of panel.
            # self.y + height is top.
            # content_start_y = top - 40 + scroll_y.
            # If scroll_y increases, content_start_y increases (moves UP).
            # If content moves UP, we see the bottom of the content?
            # Yes.
            # So increasing scroll_y means scrolling DOWN (viewing lower parts).

            # Dragging UP (dy > 0):
            # Finger moves up. Content should move up.
            # So scroll_y should increase.

            # Let's try passing dy directly.
            # But handle_scroll multiplies by speed (20.0). Dragging should be 1:1 usually.

            self.scroll_y += dy

            # Clamp
            if self.scroll_y < 0:
                self.scroll_y = 0
            if self.scroll_y > self.max_scroll:
                self.scroll_y = self.max_scroll

            self.last_mouse_y = y
            return True

        return False

    def handle_release(self):
        self.dragging_scrollbar = False
        self.dragging_content = False

    def _update_scroll_from_mouse(self, y):
        if self.max_scroll <= 0:
            return

        body_height = self.height - self.tab_height
        bar_h = body_height - 40
        bar_y = self.y + 20

        # Calcular posición relativa en la barra (0 a 1)
        # y es coordenada de pantalla (abajo-arriba)
        # bar_y es el fondo de la barra
        # bar_y + bar_h es el tope de la barra

        # Clamp y
        y = max(bar_y, min(y, bar_y + bar_h))

        # Normalizar (0 en fondo, 1 en tope)
        normalized_pos = (y - bar_y) / bar_h

        # Invertir porque scroll_y=0 es tope (normalized=1)
        scroll_ratio = 1.0 - normalized_pos

        self.scroll_y = scroll_ratio * self.max_scroll

        # Clamp final
        if self.scroll_y < 0:
            self.scroll_y = 0
        if self.scroll_y > self.max_scroll:
            self.scroll_y = self.max_scroll

    def handle_scroll(self, y_offset):
        """
        Maneja el scroll del mouse.
        y_offset: positivo (arriba) o negativo (abajo).
        """
        scroll_speed = 20.0
        self.scroll_y += y_offset * scroll_speed

        # Clamp scroll
        # scroll_y debe ser negativo para subir el contenido (mostrar lo de abajo)
        # max_scroll es la altura total del contenido menos la altura visible
        # Pero como dibujamos de arriba hacia abajo, el contenido "sobrante" está en Y negativo.
        # Si scroll_y es positivo, bajamos el contenido (vemos lo de arriba).

        # Lógica simplificada:
        # scroll_y = 0 -> Tope del contenido
        # scroll_y > 0 -> Scroll hacia abajo (ver contenido inferior)

        if self.scroll_y < 0:
            self.scroll_y = 0
        if self.scroll_y > self.max_scroll:
            self.scroll_y = self.max_scroll

    def draw(self):
        # Dibujar fondo del panel principal (Sleek dark background)
        body_height = self.height - self.tab_height

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Fondo oscuro semitransparente (Alpha 0.8)
        glColor4f(0.0, 0.05, 0.1, 0.85)

        # Dibujar cuerpo con esquinas recortadas
        chamfer = 15.0
        x, y, w, h = self.x, self.y, self.width, body_height

        glBegin(GL_POLYGON)
        glVertex2f(x + chamfer, y)
        glVertex2f(x + w - chamfer, y)
        glVertex2f(x + w, y + chamfer)
        # Top corners are straight (connected to tabs)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glVertex2f(x, y + chamfer)
        glEnd()

        # Borde Cyan
        glLineWidth(2.0)
        glColor3f(0.0, 1.0, 1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x + chamfer, y)
        glVertex2f(x + w - chamfer, y)
        glVertex2f(x + w, y + chamfer)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glVertex2f(x, y + chamfer)
        glEnd()

        glDisable(GL_BLEND)

        # Dibujar Tabs
        self._draw_tabs()

        # --- SCISSOR TEST PARA CONTENIDO SCROLLABLE ---
        # glScissor usa coordenadas de ventana (0,0 abajo-izquierda)
        glEnable(GL_SCISSOR_TEST)
        glScissor(int(self.x), int(self.y + 10),
                  int(self.width), int(body_height - 20))

        # Dibujar contenido con offset de scroll
        # El contenido empieza en el tope del cuerpo y va bajando
        content_start_y = self.y + body_height - 40 + self.scroll_y
        content_x = self.x + 25

        # Guardar posición final para calcular max_scroll
        final_y = content_start_y

        if self.current_tab == self.TAB_ENCYCLOPEDIA:
            final_y = self._draw_encyclopedia(content_x, content_start_y)
        else:
            final_y = self._draw_structure(content_x, content_start_y)

        # Calcular altura total del contenido
        # content_height = start_y - final_y
        # visible_height = body_height
        # max_scroll = max(0, content_height - visible_height)

        content_height = content_start_y - final_y
        visible_height = body_height - 60
        self.max_scroll = max(0, content_height - visible_height)

        glDisable(GL_SCISSOR_TEST)

        # Scrollbar indicator (opcional)
        if self.max_scroll > 0:
            self._draw_scrollbar(body_height)

    def _draw_scrollbar(self, body_height):
        bar_x = self.x + self.width - 10
        bar_w = 4
        bar_h = body_height - 40
        bar_y = self.y + 20

        # Background track
        glColor4f(0.0, 0.2, 0.3, 0.5)
        glRectf(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h)

        # Thumb
        ratio = body_height / (body_height + self.max_scroll)
        thumb_h = max(20, bar_h * ratio)
        scroll_ratio = self.scroll_y / self.max_scroll if self.max_scroll > 0 else 0
        thumb_y = bar_y + bar_h - thumb_h - (scroll_ratio * (bar_h - thumb_h))

        glColor4f(0.0, 1.0, 1.0, 0.8)
        glRectf(bar_x, thumb_y, bar_x + bar_w, thumb_y + thumb_h)

    def _draw_tabs(self):
        tab_y = self.y + self.height - self.tab_height

        # Tab 1: Encyclopedia
        self._draw_tab_button(self.x, tab_y, "ENCYCLOPEDIA",
                              self.current_tab == self.TAB_ENCYCLOPEDIA)

        # Tab 2: Structure
        self._draw_tab_button(self.x + self.tab_width, tab_y,
                              "STRUCTURE", self.current_tab == self.TAB_STRUCTURE)

    def _draw_tab_button(self, x, y, text, is_active):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Color de fondo
        if is_active:
            glColor4f(0.0, 1.0, 1.0, 0.8)  # Cyan sólido brillante
            text_color = (0.0, 0.0, 0.0)  # Texto negro
        else:
            glColor4f(0.0, 0.0, 0.0, 0.0)  # Transparente (solo borde)
            text_color = (0.0, 1.0, 1.0)  # Texto Cyan

        # Dibujar rectángulo del tab
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + self.tab_width, y)
        glVertex2f(x + self.tab_width, y + self.tab_height)
        glVertex2f(x, y + self.tab_height)
        glEnd()

        # Borde
        glLineWidth(2.0)
        glColor3f(0.0, 1.0, 1.0)  # Cyan siempre

        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + self.tab_width, y)
        glVertex2f(x + self.tab_width, y + self.tab_height)
        glVertex2f(x, y + self.tab_height)
        glEnd()

        glDisable(GL_BLEND)

        # Texto centrado
        text_size = 18  # Bigger text
        char_width = 10
        text_width = len(text) * char_width
        text_x = x + (self.tab_width - text_width) / 2
        text_y = y + (self.tab_height - text_size) / 2

        UIRenderer.draw_text(text_x, text_y, text,
                             size=text_size, color=text_color)

    def _draw_encyclopedia(self, x, start_y):
        data = self.data.get("encyclopedia", {})
        if not data:
            UIRenderer.draw_text(
                x, start_y, "NO DATA AVAILABLE", size=24, color=(1.0, 0.0, 0.0))
            return start_y - 30

        y = start_y

        # 1. Quick Stats Table
        stats_table = data.get("encyclopedia_table", {})
        if not stats_table:
            stats_table = data.get("stats", {})

        description_text = ""

        for key, item in stats_table.items():
            if key == "planet_description":
                description_text = item.get("value", "")
                continue

            if isinstance(item, dict):
                label = item.get("name", key).upper()
                value = str(item.get("value", ""))
            else:
                label = key.upper()
                value = str(item)

            # Increased spacing and font size
            UIRenderer.draw_text(x, y, label, size=16, color=(
                0.0, 1.0, 1.0))  # Custom font for headers

            # Dynamic value position (Right aligned)
            # Estimate value width to align right
            # Helvetica char width approx 0.5 * size = 8
            val_width_est = len(value) * 8
            value_x = self.x + self.width - 40 - val_width_est

            # Ensure it doesn't overlap label too much (simple check)
            if value_x < x + 150:
                value_x = x + 150

            UIRenderer.draw_text(value_x, y, value, size=16, color=(
                0.9, 0.9, 0.9), font_name="Helvetica")  # Helvetica for values

            y -= 35  # More vertical padding

        y -= 30

        # 2. Description
        if not description_text:
            description_text = data.get("short_description", "")

        if description_text:
            UIRenderer.draw_text(x, y, "DESCRIPTION",
                                 size=20, color=(0.0, 1.0, 1.0))
            y -= 30
            y = self._draw_wrapped_text(
                x, y, description_text, self.width - 50, 16)
            y -= 40

        # 3. Detailed Sections
        for key, content in data.items():
            if key in ["encyclopedia_table", "stats", "short_description", "description"]:
                continue

            if isinstance(content, dict) and "title" in content and "text" in content:
                title = content["title"].upper()
                text = content["text"]

                UIRenderer.draw_text(x, y, title, size=20,
                                     color=(0.0, 1.0, 1.0))
                y -= 30
                y = self._draw_wrapped_text(x, y, text, self.width - 50, 16)
                y -= 40

        return y

    def _draw_structure(self, x, start_y):
        structure_data = self.data.get("structure", {})
        if not structure_data:
            UIRenderer.draw_text(
                x, start_y, "NO STRUCTURE DATA", size=24, color=(1.0, 0.0, 0.0))
            return start_y - 30

        y = start_y

        items = []
        if isinstance(structure_data, list):
            items = structure_data
        elif isinstance(structure_data, dict):
            items = structure_data.values()

        for layer in items:
            # Layer Name
            name = layer.get("title", layer.get("name", "Unknown Layer"))
            UIRenderer.draw_text(x, y, name.upper(),
                                 size=22, color=(0.0, 1.0, 1.0))
            y -= 30

            # Layer Description
            desc = layer.get("text", layer.get("description", ""))
            if desc:
                y = self._draw_wrapped_text(x, y, desc, self.width - 50, 16)

            y -= 50  # More space between layers

        return y

    def _draw_wrapped_text(self, x, y, text, max_width, size):
        """
        Dibuja texto con salto de línea simple. Retorna la nueva posición Y.
        """
        words = text.split(' ')
        line = ""
        line_height = size + 8  # More line height
        char_width_approx = size * 0.45  # Tighter estimate to use more width

        for word in words:
            test_line = line + word + " "
            test_width = len(test_line) * char_width_approx

            if test_width > max_width:
                UIRenderer.draw_text(x, y, line, size=size, color=(
                    0.9, 0.9, 0.9), font_name="Helvetica")
                y -= line_height
                line = word + " "
            else:
                line = test_line

        if line:
            UIRenderer.draw_text(x, y, line, size=size, color=(
                0.9, 0.9, 0.9), font_name="Helvetica")
            y -= line_height

        return y
