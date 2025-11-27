from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.renderer import Renderer
from src.graphics.ui_renderer import UIRenderer
from src.graphics.texture_loader import TextureLoader
from src.graphics.skybox import Skybox
from src.data.planet_layers import PLANET_LAYERS
from src.graphics.planet_info_panel import PlanetInfoPanel
from src.core.mission_manager import MissionManager, get_trophy_for_planet
from src.core.quiz_manager import QuizManager
from src.entities.trophies.trophy_base import TrophyRenderer
import math


class PlanetDetailState(BaseState):
    def __init__(self, planet_data):
        """
        :param planet_data: Objeto Planet o diccionario con 'name', 'radius', etc.
        """
        self.planet_obj = planet_data
        self.planet_name = getattr(planet_data, 'name', 'Unknown')
        self.planet_radius = getattr(planet_data, 'radius', 1.0)

        # Escalar un poco para que se vea bien en pantalla
        self.display_radius = 5.0

        self.layers = PLANET_LAYERS.get(self.planet_name, [])
        if not self.layers:
            # Fallback si no hay capas definidas
            self.layers = [
                {"name": "Surface", "color": (0.5, 0.5, 0.5), "width": 1.0}]

        self.open_factor = 0.0
        self.target_open_factor = 1.0
        self.animation_speed = 0.5

        self.texture_id = None
        self.quadric = None

        # Variables de rotación interactiva
        self.rot_x = 0.0
        self.rot_y = 0.0
        self.dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        # Skybox para el fondo
        self.skybox = Skybox(size=200.0)

        # Panel de Información
        self.info_panel = None

        # Quiz system
        self.mission_manager = MissionManager()
        self.quiz_manager = QuizManager()
        self.quiz_session = None
        self.is_mission_target = False
        self.quiz_active = False
        self.selected_answer = -1
        self.answer_feedback = None  # (is_correct, correct_index, explanation)
        self.feedback_question = None  # Store question data during feedback display
        self.feedback_timer = 0.0
        # Wait for feedback to finish before next question
        self.feedback_delay_active = False
        self.quiz_completed = False
        self.quiz_passed = False
        self.trophy_awarded = False
        self.show_trophy_animation = False
        self.trophy_animation_time = 0.0
        self.trophy_renderer = None
        self.trophy_rotation = 0.0

        # Cargar texturas para cada capa
        for layer in self.layers:
            if "texture" in layer:
                tex_path = f"assets/textures/planets/{layer['texture']}"
                layer['texture_id'] = TextureLoader.load_texture(tex_path)

    def enter(self):
        print(
            f"[PlanetDetailState] Entering detail view for {self.planet_name}")
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)
        gluQuadricTexture(self.quadric, GL_TRUE)

        # Reset animation
        self.open_factor = 0.0

        # Inicializar Panel
        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)
        panel_w = 350
        panel_h = h - 100
        panel_x = 20
        panel_y = 50
        self.info_panel = PlanetInfoPanel(
            self.planet_name, panel_x, panel_y, panel_w, panel_h)

        # Check if this is the current mission target
        self.is_mission_target = self.mission_manager.is_target_planet(
            self.planet_name)
        self.quiz_completed = self.mission_manager.is_mission_completed(
            self.planet_name)

        if self.is_mission_target and not self.quiz_completed:
            # Start quiz for mission target
            self.quiz_session = self.quiz_manager.start_quiz(self.planet_name)
            if self.quiz_session:
                self.quiz_active = True
                print(
                    f"[PlanetDetailState] Quiz started for {self.planet_name}")
            else:
                print(
                    f"[PlanetDetailState] No quiz questions for {self.planet_name}")

        # Reset quiz state
        self.selected_answer = -1
        self.answer_feedback = None
        self.feedback_question = None
        self.feedback_timer = 0.0
        self.feedback_delay_active = False
        self.quiz_passed = False
        self.trophy_awarded = False
        self.show_trophy_animation = False
        self.trophy_animation_time = 0.0
        self.trophy_renderer = TrophyRenderer()
        self.trophy_rotation = 0.0

    def exit(self):
        if self.quadric:
            gluDeleteQuadric(self.quadric)
            self.quadric = None

        # Clean up trophy renderer
        if self.trophy_renderer:
            self.trophy_renderer.cleanup()
            self.trophy_renderer = None

        # Limpiar luces extra para no afectar otros estados
        glDisable(GL_LIGHT1)

    def update(self, dt):
        # Animar apertura
        if self.open_factor < self.target_open_factor:
            self.open_factor += self.animation_speed * dt
            if self.open_factor > self.target_open_factor:
                self.open_factor = self.target_open_factor

        # Update answer feedback timer
        if self.answer_feedback:
            self.feedback_timer += dt
            if self.feedback_timer > 2.5:  # Show feedback for 2.5 seconds
                # Clear feedback display but don't advance yet
                self.answer_feedback = None
                self.feedback_question = None
                self.feedback_options = None
                self.feedback_selected = -1
                self.feedback_timer = 0.0
                self.feedback_delay_active = True  # Enter delay state

        # Handle delay before advancing to next question
        if self.feedback_delay_active:
            self.feedback_timer += dt
            if self.feedback_timer > 0.2:  # Wait 0.2s after clearing feedback
                self.feedback_delay_active = False
                self.feedback_timer = 0.0
                self.selected_answer = -1

                # Check if quiz is complete
                if self.quiz_session and self.quiz_session.is_completed():
                    self.quiz_completed = True
                    self.quiz_passed = self.quiz_session.passed()
                    self.quiz_active = False

                    if self.quiz_passed and not self.trophy_awarded:
                        # Complete the mission and award trophy
                        trophy_type = get_trophy_for_planet(self.planet_name)
                        game_complete = self.mission_manager.complete_current_mission(
                            trophy_type)
                        self.trophy_awarded = True
                        self.show_trophy_animation = True
                        self.trophy_animation_time = 0.0
                        print(
                            f"[PlanetDetailState] Trophy awarded: {trophy_type}")

                        if game_complete:
                            print(
                                "[PlanetDetailState] ALL MISSIONS COMPLETE! Triggering victory!")

        # Update trophy animation
        if self.show_trophy_animation:
            self.trophy_animation_time += dt
            if self.trophy_animation_time > 4.0:
                # Check if game is complete
                if self.mission_manager.is_game_complete():
                    # Transition to victory state
                    if hasattr(self, 'state_machine'):
                        from src.states.game_complete_state import GameCompleteState
                        self.state_machine.change(GameCompleteState())

    def handle_input(self, event, x, y):
        # Handle quiz answer selection (1-4 keys)
        if event[0] == 'KEY_DOWN':
            key = event[1]

            # Allow ESC key for pause menu even during quiz
            if key == b'\x1b':  # ESC key
                if hasattr(self, 'state_machine'):
                    from src.states.pause_state import PauseState
                    self.state_machine.push(PauseState())
                return

            # Quiz answer input - block during feedback or delay
            if self.quiz_active and self.quiz_session and not self.answer_feedback and not self.feedback_delay_active:
                question = self.quiz_session.get_current_question()
                if question:
                    answer_map = {b'1': 0, b'2': 1, b'3': 2, b'4': 3}
                    if key in answer_map:
                        answer_idx = answer_map[key]
                        num_options = len(question.get('options', []))
                        if answer_idx < num_options:
                            self.selected_answer = answer_idx
                            # Store the question, options, and selected answer BEFORE submitting
                            # (submit advances to next question)
                            self.feedback_question = question.copy()
                            self.feedback_options = question.get('options', [])[
                                :]
                            self.feedback_selected = answer_idx
                            is_correct, correct_idx, explanation = self.quiz_session.submit_answer(
                                answer_idx)
                            self.answer_feedback = (
                                is_correct, correct_idx, explanation)
                            self.feedback_timer = 0.0
                            return

            # Exit handling
            if key == b'\r' or key == b' ':  # Enter o Espacio
                # Don't allow exit during quiz unless completed
                if self.quiz_active and not self.quiz_completed:
                    return  # Block exit during active quiz

                # Pop this state to return to gameplay
                if hasattr(self, 'state_machine'):
                    self.state_machine.pop()

        # Manejo del mouse para rotación
        elif event[0] == 'MOUSE_BUTTON':
            button, state = event[1], event[2]

            # Convertir Y de arriba-abajo a abajo-arriba para UI
            h = glutGet(GLUT_WINDOW_HEIGHT)
            ui_y = h - y

            if button == GLUT_LEFT_BUTTON:
                if state == GLUT_DOWN:
                    # Verificar clic en panel primero
                    if self.info_panel and self.info_panel.handle_click(x, ui_y):
                        return  # Consumido por el panel

                    self.dragging = True
                    self.last_mouse_x = x
                    self.last_mouse_y = y
                elif state == GLUT_UP:
                    if self.info_panel:
                        self.info_panel.handle_release()
                    self.dragging = False

        elif event[0] == 'MOUSE_MOTION':
            # Convertir Y de arriba-abajo a abajo-arriba para UI
            h = glutGet(GLUT_WINDOW_HEIGHT)
            ui_y = h - y

            if self.info_panel and self.info_panel.handle_drag(x, ui_y):
                return

            if self.dragging:
                dx = x - self.last_mouse_x
                dy = y - self.last_mouse_y

                self.rot_y += dx * 0.5
                self.rot_x += dy * 0.5

                self.last_mouse_x = x
                self.last_mouse_y = y

    def draw(self):
        # Limpiar todo
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Update panel dimensions
        if self.info_panel:
            panel_w = 450  # Wider panel
            panel_h = h - 100
            panel_x = 20
            panel_y = 50
            self.info_panel.update_dimensions(
                panel_x, panel_y, panel_w, panel_h)

        Renderer.setup_3d(w, h)

        glLoadIdentity()
        # Cámara fija mirando al origen, ligeramente elevada y más lejos
        gluLookAt(0, 3, 20,  0, 0, 0,  0, 1, 0)

        # Dibujar Skybox (Fondo)
        glPushMatrix()
        try:
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            # Asegurar que el skybox sea visible
            glColor3f(1.0, 1.0, 1.0)
            self.skybox.draw()
            glEnable(GL_LIGHTING)
            glEnable(GL_DEPTH_TEST)
        finally:
            glPopMatrix()

        # Iluminación Profesional
        glEnable(GL_LIGHTING)

        # Luz Ambiental Global
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])

        # Luz Principal (Key Light) - Simulando el Sol desde arriba a la derecha
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [30.0, 30.0, 30.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.05, 0.05, 0.05, 1.0])
        # Ligeramente cálida e intensa
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.2, 1.15, 1.1, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [0.8, 0.8, 0.8, 1.0])

        # Luz de Relleno (Fill Light) - Desde el lado opuesto, azulada y tenue
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, [-30.0, -10.0, 10.0, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.15, 0.15, 0.25, 1.0])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])

        # Configuración de Material por defecto (puede ser sobrescrito por texturas)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.2, 0.2, 0.2, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 10.0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

        # Rotaciones del modelo
        glPushMatrix()
        try:
            # Rotación interactiva
            glRotatef(self.rot_x, 1, 0, 0)
            glRotatef(self.rot_y, 0, 1, 0)

            # Orientar el planeta para que los polos estén en Y (gluSphere usa Z)
            glRotatef(-90, 1, 0, 0)
            # Rotar 180 grados para que el corte quede frente a la cámara por defecto
            glRotatef(230, 0, 0, 1)

            # Renderizado Matryoshka
            current_radius = 0.0
            total_width = sum(l['width'] for l in self.layers)

            # Dibujar de adentro hacia afuera
            for i, layer in enumerate(self.layers):
                layer_width = layer['width']
                radius_increment = (
                    layer_width / total_width) * self.display_radius
                inner_radius = current_radius
                current_radius += radius_increment

                # Obtener ángulo de apertura de la capa (si existe en data, sino calcular)
                max_angle = layer.get(
                    'opening_angle', 180.0 * (i / max(1, len(self.layers)-1)))

                # Interpolar con la animación
                current_cut_angle = max_angle * self.open_factor

                self._draw_clipped_layer(
                    inner_radius, current_radius, layer, current_cut_angle)

            # Dibujar anillos si existen
            if hasattr(self.planet_obj, 'ring_list_id') and self.planet_obj.ring_list_id:
                glPushMatrix()
                try:
                    # Escalar los anillos para que coincidan con el radio de visualización
                    # Ratio = display_radius / original_radius
                    scale = self.display_radius / \
                        max(0.001, self.planet_radius)
                    glScalef(scale, scale, scale)

                    # Los anillos en RingedPlanet ya tienen rotación aplicada en la lista compilada?
                    # RingedPlanet._compile_ring_list aplica glRotatef(inclination, 1, 0, 0)
                    # Pero aquí hemos rotado el planeta -90 en X para alinear polos con Y.
                    # RingedPlanet asume que el planeta está en su orientación orbital normal.
                    # Si aplicamos la lista tal cual, se dibujará relativa al sistema de coordenadas actual.
                    # El sistema actual tiene:
                    # 1. Rotación interactiva (X, Y)
                    # 2. Rotación de alineación (-90 en X) -> Polos en Y.
                    # 3. Rotación de corte (240 en Z).

                    # Los anillos de RingedPlanet se compilan asumiendo que el planeta está "vertical" (Y up)?
                    # No, RingedPlanet usa gluSphere que por defecto es Z-up? No, gluSphere es Z-axis aligned.
                    # RingedPlanet no rota la esfera en su draw(), solo traslada.
                    # Así que la esfera de RingedPlanet tiene polos en Z.
                    # Los anillos se rotan 'inclination' sobre X.

                    # Aquí hemos rotado -90 en X. Esto lleva Z a Y. (Polos en Y).
                    # Si dibujamos los anillos aquí, estarán rotados 'inclination' sobre el eje X local.
                    # Si la inclinación es 90 (Urano), los anillos estarán en el plano YZ (verticales).
                    # Si la inclinación es 30 (Saturno), estarán inclinados.

                    # Sin embargo, RingedPlanet._compile_ring_list hace:
                    # glRotatef(inclination, 1, 0, 0)
                    # gluDisk (en plano XY por defecto)

                    # Espera, gluDisk dibuja en el plano Z=0 (XY plane).
                    # Si rotamos 30 en X, el plano se inclina.

                    # En PlanetDetailState, hemos hecho glRotatef(-90, 1, 0, 0).
                    # El eje Z original ahora apunta a Y.
                    # El eje Y original ahora apunta a -Z.
                    # El eje X original sigue en X.

                    # Si dibujamos los anillos (que son un disco en XY rotado en X),
                    # y estamos en un sistema donde Z->Y...
                    # Un disco en XY (Z=0) se dibujará en X(-Z) -> X(-Y)?

                    # Vamos a probar dibujándolos tal cual, pero necesitamos deshacer la rotación de corte
                    # si queremos que los anillos no giren con el corte (aunque tal vez sí deberían).
                    # Probablemente los anillos deban estar fijos respecto al planeta.

                    # Pero hay un detalle: RingedPlanet dibuja la esfera y luego los anillos.
                    # Aquí dibujamos capas.
                    # La escala es lo importante.

                    # Hay un problema potencial: RingedPlanet._compile_ring_list usa GL_CULL_FACE disable/enable.
                    # Eso está bien.

                    glCallList(self.planet_obj.ring_list_id)
                finally:
                    glPopMatrix()

            # --- ETIQUETAS HUD ---
            # Dibujar etiquetas para cada capa si el planeta está abierto
            if self.open_factor > 0.1:
                lbl_radius = 0.0
                total_w = sum(l['width'] for l in self.layers)

                for i, layer in enumerate(self.layers):
                    l_width = layer['width']
                    r_inc = (l_width / total_w) * self.display_radius
                    mid_r = lbl_radius + r_inc * 0.8
                    lbl_radius += r_inc

                    # Calcular ángulo de apertura (debe coincidir con el usado en el dibujo)
                    max_angle = layer.get(
                        'opening_angle', 180.0 * (i / max(1, len(self.layers)-1)))
                    current_angle = max_angle * self.open_factor

                    # Ajustes de posición:
                    # 1. Subir en Z (escalonado) para que no se solapen verticalmente
                    z_offset = i * 0.6
                    # 2. Compensar radio para mantenerse "dentro" visualmente al subir
                    r_adjusted = mid_r - (i * 0.15)

                    # Posición en la cara de apertura (rotada current_angle grados)
                    rad = math.radians(current_angle)
                    lx = r_adjusted * math.cos(rad)
                    ly = r_adjusted * math.sin(rad)
                    lz = 0.1 + z_offset

                    UIRenderer.draw_hud_label(
                        lx, ly, lz, layer['name'].upper())

        finally:
            glPopMatrix()  # Fin de rotaciones del modelo

        # Recuperar w y h para UI
        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # UI Overlay
        self._draw_ui(w, h)

    def _draw_ui(self, w, h):
        UIRenderer.setup_2d(w, h)
        try:
            # Dibujar Panel de Información
            if self.info_panel:
                self.info_panel.draw()

            # Draw quiz panel on the right side if this is mission target
            if self.is_mission_target:
                self._draw_quiz_panel(w, h)

            # Draw trophy animation
            if self.show_trophy_animation:
                self._draw_trophy_celebration(w, h)

            # Instrucción (Abajo a la derecha)
            if not self.quiz_active or self.quiz_completed:
                UIRenderer.draw_text(
                    w - 300, 20, "PRESS SPACE TO RETURN", size=18, color=(1.0, 0.5, 0.5))
            else:
                UIRenderer.draw_text(
                    w - 350, 20, "COMPLETE QUIZ TO CONTINUE", size=18, color=(1.0, 0.8, 0.0))
        finally:
            UIRenderer.restore_3d()

    def _draw_quiz_panel(self, w, h):
        """Draw the quiz panel on the right side of the screen."""
        # Panel dimensions
        panel_w = 420
        panel_h = h - 80
        panel_x = w - panel_w - 15
        panel_y = 40

        # Draw semi-transparent background with gradient effect
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Main panel background
        chamfer = 20
        glBegin(GL_POLYGON)
        glColor4f(0.02, 0.06, 0.12, 0.95)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glColor4f(0.01, 0.04, 0.08, 0.95)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glColor4f(0.02, 0.06, 0.12, 0.95)
        glVertex2f(panel_x, panel_y + chamfer)
        glEnd()

        # Inner glow/highlight at top
        glBegin(GL_QUADS)
        border_color = (0.0, 0.8, 1.0) if not self.quiz_completed else (
            (0.0, 1.0, 0.5) if self.quiz_passed else (1.0, 0.3, 0.3))
        glColor4f(border_color[0] * 0.3, border_color[1]
                  * 0.3, border_color[2] * 0.3, 0.4)
        glVertex2f(panel_x + chamfer, panel_y + panel_h - 60)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h - 60)
        glColor4f(border_color[0] * 0.1, border_color[1]
                  * 0.1, border_color[2] * 0.1, 0.0)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h - 100)
        glVertex2f(panel_x + chamfer, panel_y + panel_h - 100)
        glEnd()

        # Border with glow effect
        glLineWidth(3.0)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.8)
        glBegin(GL_LINE_LOOP)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glVertex2f(panel_x, panel_y + chamfer)
        glEnd()

        # Corner accents
        glLineWidth(2.0)
        glColor3f(*border_color)
        accent_size = 25
        # Top-left
        glBegin(GL_LINES)
        glVertex2f(panel_x, panel_y + panel_h - chamfer - accent_size)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer + accent_size, panel_y + panel_h)
        # Top-right
        glVertex2f(panel_x + panel_w - chamfer -
                   accent_size, panel_y + panel_h)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w, panel_y +
                   panel_h - chamfer - accent_size)
        # Bottom-left
        glVertex2f(panel_x, panel_y + chamfer + accent_size)
        glVertex2f(panel_x, panel_y + chamfer)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + chamfer + accent_size, panel_y)
        # Bottom-right
        glVertex2f(panel_x + panel_w - chamfer - accent_size, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glVertex2f(panel_x + panel_w, panel_y + chamfer + accent_size)
        glEnd()

        glDisable(GL_BLEND)

        # Header with icon indicator
        header = "MISSION QUIZ" if not self.quiz_completed else (
            "QUIZ PASSED" if self.quiz_passed else "QUIZ FAILED")
        header_color = (0.0, 1.0, 1.0) if not self.quiz_completed else (
            (0.0, 1.0, 0.5) if self.quiz_passed else (1.0, 0.3, 0.3))

        # Draw header icon (small decorative element)
        icon_x = panel_x + 20
        icon_y = panel_y + panel_h - 38
        glColor3f(*header_color)
        glBegin(GL_TRIANGLES)
        glVertex2f(icon_x, icon_y)
        glVertex2f(icon_x + 12, icon_y + 8)
        glVertex2f(icon_x, icon_y + 16)
        glEnd()

        UIRenderer.draw_text(panel_x + 40, panel_y + panel_h - 40, header,
                             size=24, color=header_color)

        # Decorative separator line with gradient
        glEnable(GL_BLEND)
        glBegin(GL_QUADS)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.0)
        glVertex2f(panel_x + 15, panel_y + panel_h - 55)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.8)
        glVertex2f(panel_x + panel_w / 2, panel_y + panel_h - 55)
        glVertex2f(panel_x + panel_w / 2, panel_y + panel_h - 53)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.0)
        glVertex2f(panel_x + 15, panel_y + panel_h - 53)
        glEnd()
        glBegin(GL_QUADS)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.8)
        glVertex2f(panel_x + panel_w / 2, panel_y + panel_h - 55)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.0)
        glVertex2f(panel_x + panel_w - 15, panel_y + panel_h - 55)
        glVertex2f(panel_x + panel_w - 15, panel_y + panel_h - 53)
        glColor4f(border_color[0], border_color[1], border_color[2], 0.8)
        glVertex2f(panel_x + panel_w / 2, panel_y + panel_h - 53)
        glEnd()
        glDisable(GL_BLEND)

        if self.quiz_completed:
            # Show final results
            self._draw_quiz_results(panel_x, panel_y, panel_w, panel_h)
        elif self.quiz_session:
            # Show current question
            self._draw_quiz_question(panel_x, panel_y, panel_w, panel_h)
        else:
            # No quiz available
            UIRenderer.draw_text(panel_x + 15, panel_y + panel_h - 80,
                                 "No quiz available", size=18, color=(0.7, 0.7, 0.7))

    def _draw_quiz_question(self, panel_x, panel_y, panel_w, panel_h):
        """Draw the current quiz question and options."""
        # Use feedback_question during feedback display, otherwise current question
        if self.answer_feedback and self.feedback_question:
            question = self.feedback_question
            # During feedback, show the question number that was answered
            q_num = self.quiz_session.get_question_number(
            ) - 1 if not self.quiz_session.is_completed() else self.quiz_session.get_question_number()
        else:
            question = self.quiz_session.get_current_question()
            q_num = self.quiz_session.get_question_number()

        if not question:
            return

        # Progress bar and stats
        q_total = self.quiz_session.get_total_questions()
        score = self.quiz_session.get_score()
        current_score = q_num - 1 if not self.answer_feedback else q_num

        # Progress bar background
        bar_x = panel_x + 20
        bar_y = panel_y + panel_h - 80
        bar_w = panel_w - 40
        bar_h = 8

        glEnable(GL_BLEND)
        glColor4f(0.1, 0.1, 0.15, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + bar_w, bar_y)
        glVertex2f(bar_x + bar_w, bar_y + bar_h)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()

        # Progress bar fill
        progress = q_num / q_total
        glColor4f(0.0, 0.8, 1.0, 0.9)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + bar_w * progress, bar_y)
        glVertex2f(bar_x + bar_w * progress, bar_y + bar_h)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()
        glDisable(GL_BLEND)

        # Question counter and score
        UIRenderer.draw_text(panel_x + 20, panel_y + panel_h - 100,
                             f"Question {q_num} of {q_total}", size=14, color=(0.6, 0.7, 0.8))
        score_text = f"Score: {score} of {current_score}"
        UIRenderer.draw_text(panel_x + panel_w - 130, panel_y + panel_h - 100,
                             score_text, size=14, color=(0.9, 0.8, 0.3))

        # Question text box
        question_text = question.get('question', 'No question')
        q_box_y = panel_y + panel_h - 200
        q_box_h = 80

        # Question background
        glEnable(GL_BLEND)
        glColor4f(0.05, 0.08, 0.12, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(panel_x + 15, q_box_y)
        glVertex2f(panel_x + panel_w - 15, q_box_y)
        glVertex2f(panel_x + panel_w - 15, q_box_y + q_box_h)
        glVertex2f(panel_x + 15, q_box_y + q_box_h)
        glEnd()

        # Question left accent bar
        glColor4f(0.0, 0.8, 1.0, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(panel_x + 15, q_box_y + 5)
        glVertex2f(panel_x + 19, q_box_y + 5)
        glVertex2f(panel_x + 19, q_box_y + q_box_h - 5)
        glVertex2f(panel_x + 15, q_box_y + q_box_h - 5)
        glEnd()
        glDisable(GL_BLEND)

        # Question text with word wrap
        y_pos = q_box_y + q_box_h - 25
        words = question_text.split()
        line = ""
        max_chars = 48
        for word in words:
            if len(line) + len(word) + 1 <= max_chars:
                line = line + " " + word if line else word
            else:
                UIRenderer.draw_text(panel_x + 28, y_pos, line,
                                     size=16, color=(1.0, 1.0, 1.0), font_name="helvetica")
                y_pos -= 24
                line = word
        if line:
            UIRenderer.draw_text(panel_x + 28, y_pos, line,
                                 size=16, color=(1.0, 1.0, 1.0), font_name="helvetica")

        # Options as cards
        options = question.get('options', [])
        opt_start_y = panel_y + panel_h - 250
        opt_height = 55
        opt_spacing = 8

        for i, option in enumerate(options):
            opt_y = opt_start_y - i * (opt_height + opt_spacing)

            # Use feedback_selected during feedback display
            current_selected = self.feedback_selected if self.answer_feedback else self.selected_answer

            # Determine option styling based on state
            if self.answer_feedback:
                is_correct, correct_idx, _ = self.answer_feedback
                if i == correct_idx:
                    border_color = (0.0, 1.0, 0.5)
                    bg_color = (0.0, 0.25, 0.1, 0.7)
                    text_color = (0.7, 1.0, 0.7)
                    num_color = (0.0, 1.0, 0.5)
                elif i == current_selected and not is_correct:
                    border_color = (1.0, 0.3, 0.3)
                    bg_color = (0.25, 0.05, 0.05, 0.7)
                    text_color = (1.0, 0.7, 0.7)
                    num_color = (1.0, 0.3, 0.3)
                else:
                    border_color = (0.3, 0.3, 0.35)
                    bg_color = (0.05, 0.05, 0.08, 0.5)
                    text_color = (0.5, 0.5, 0.5)
                    num_color = (0.4, 0.4, 0.4)
            elif i == current_selected:
                border_color = (1.0, 0.8, 0.0)
                bg_color = (0.2, 0.15, 0.0, 0.6)
                text_color = (1.0, 0.95, 0.8)
                num_color = (1.0, 0.8, 0.0)
            else:
                border_color = (0.2, 0.4, 0.5)
                bg_color = (0.03, 0.06, 0.08, 0.6)
                text_color = (0.85, 0.85, 0.85)
                num_color = (0.0, 0.7, 0.9)

            # Option card background
            glEnable(GL_BLEND)
            glColor4f(*bg_color)
            card_x = panel_x + 15
            card_w = panel_w - 30
            glBegin(GL_QUADS)
            glVertex2f(card_x, opt_y)
            glVertex2f(card_x + card_w, opt_y)
            glVertex2f(card_x + card_w, opt_y + opt_height)
            glVertex2f(card_x, opt_y + opt_height)
            glEnd()

            # Option card border
            glLineWidth(2.0)
            glColor3f(*border_color)
            glBegin(GL_LINE_LOOP)
            glVertex2f(card_x, opt_y)
            glVertex2f(card_x + card_w, opt_y)
            glVertex2f(card_x + card_w, opt_y + opt_height)
            glVertex2f(card_x, opt_y + opt_height)
            glEnd()

            # Number badge
            badge_size = 28
            badge_x = card_x + 12
            badge_y = opt_y + (opt_height - badge_size) / 2
            glColor4f(border_color[0] * 0.3, border_color[1]
                      * 0.3, border_color[2] * 0.3, 0.8)
            glBegin(GL_QUADS)
            glVertex2f(badge_x, badge_y)
            glVertex2f(badge_x + badge_size, badge_y)
            glVertex2f(badge_x + badge_size, badge_y + badge_size)
            glVertex2f(badge_x, badge_y + badge_size)
            glEnd()
            glDisable(GL_BLEND)

            # Number text
            UIRenderer.draw_text(badge_x + 8, badge_y + 5,
                                 str(i + 1), size=16, color=num_color)

            # Option text with word wrap - calculate lines first to center vertically
            opt_words = option.split()
            opt_lines = []
            opt_line = ""
            opt_max = 42
            for word in opt_words:
                if len(opt_line) + len(word) + 1 <= opt_max:
                    opt_line = opt_line + " " + word if opt_line else word
                else:
                    opt_lines.append(opt_line)
                    opt_line = word
            if opt_line:
                opt_lines.append(opt_line)

            # Calculate vertical centering
            line_height = 22
            total_text_height = len(opt_lines) * line_height
            opt_y_start = opt_y + \
                (opt_height + total_text_height) / 2 - line_height + 2

            # Draw centered lines
            for idx, line_text in enumerate(opt_lines):
                UIRenderer.draw_text(card_x + 50, opt_y_start - idx * line_height, line_text,
                                     size=14, color=text_color, font_name="helvetica")

        # Show feedback explanation
        if self.answer_feedback:
            _, _, explanation = self.answer_feedback
            if explanation:
                # Explanation box at bottom
                exp_box_y = panel_y + 50
                exp_box_h = 70

                glEnable(GL_BLEND)
                # Background
                glColor4f(0.08, 0.06, 0.02, 0.8)
                glBegin(GL_QUADS)
                glVertex2f(panel_x + 15, exp_box_y)
                glVertex2f(panel_x + panel_w - 15, exp_box_y)
                glVertex2f(panel_x + panel_w - 15, exp_box_y + exp_box_h)
                glVertex2f(panel_x + 15, exp_box_y + exp_box_h)
                glEnd()

                # Left accent bar (yellow for explanation)
                glColor4f(0.9, 0.8, 0.2, 0.9)
                glBegin(GL_QUADS)
                glVertex2f(panel_x + 15, exp_box_y + 5)
                glVertex2f(panel_x + 19, exp_box_y + 5)
                glVertex2f(panel_x + 19, exp_box_y + exp_box_h - 5)
                glVertex2f(panel_x + 15, exp_box_y + exp_box_h - 5)
                glEnd()
                glDisable(GL_BLEND)

                UIRenderer.draw_text(panel_x + 28, exp_box_y + exp_box_h - 20,
                                     "Explanation", size=12, color=(0.9, 0.8, 0.3))

                # Word wrap explanation
                exp_words = explanation.split()
                exp_line = ""
                exp_y = exp_box_y + exp_box_h - 38
                for word in exp_words:
                    if len(exp_line) + len(word) + 1 <= 42:
                        exp_line = exp_line + " " + word if exp_line else word
                    else:
                        UIRenderer.draw_text(panel_x + 28, exp_y, exp_line,
                                             size=12, color=(0.8, 0.8, 0.7), font_name="helvetica")
                        exp_y -= 16
                        exp_line = word
                if exp_line:
                    UIRenderer.draw_text(panel_x + 28, exp_y, exp_line,
                                         size=12, color=(0.8, 0.8, 0.7), font_name="helvetica")
        else:
            # Instruction hint at bottom
            glEnable(GL_BLEND)
            glColor4f(0.0, 0.1, 0.15, 0.6)
            glBegin(GL_QUADS)
            glVertex2f(panel_x + 15, panel_y + 50)
            glVertex2f(panel_x + panel_w - 15, panel_y + 50)
            glVertex2f(panel_x + panel_w - 15, panel_y + 80)
            glVertex2f(panel_x + 15, panel_y + 80)
            glEnd()
            glDisable(GL_BLEND)
            UIRenderer.draw_text(panel_x + panel_w / 2 - 80, panel_y + 58,
                                 "Press 1-4 to select", size=14, color=(0.5, 0.6, 0.7))

    def _draw_quiz_results(self, panel_x, panel_y, panel_w, panel_h):
        """Draw the quiz results after completion."""
        if not self.quiz_session:
            return

        results = self.quiz_session.get_results()

        # Center content area
        content_y = panel_y + panel_h / 2

        # Score circle/badge
        circle_x = panel_x + panel_w / 2
        circle_y = content_y + 80
        circle_r = 60

        glEnable(GL_BLEND)

        # Circle background
        if results['passed']:
            glColor4f(0.0, 0.3, 0.15, 0.8)
        else:
            glColor4f(0.3, 0.1, 0.1, 0.8)

        # Draw circle segments
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(circle_x, circle_y)
        import math
        for i in range(33):
            angle = math.radians(i * 11.25)
            glVertex2f(circle_x + circle_r * math.cos(angle),
                       circle_y + circle_r * math.sin(angle))
        glEnd()

        # Circle border
        if results['passed']:
            glColor4f(0.0, 1.0, 0.5, 0.9)
        else:
            glColor4f(1.0, 0.3, 0.3, 0.9)
        glLineWidth(4.0)
        glBegin(GL_LINE_LOOP)
        for i in range(32):
            angle = math.radians(i * 11.25)
            glVertex2f(circle_x + circle_r * math.cos(angle),
                       circle_y + circle_r * math.sin(angle))
        glEnd()
        glDisable(GL_BLEND)

        # Score number in circle
        score_text = f"{results['score']} of {results['total']}"
        UIRenderer.draw_text(circle_x - 35, circle_y + 5, score_text,
                             size=22, color=(1.0, 1.0, 1.0))

        # Percentage below
        pct_color = (0.0, 1.0, 0.5) if results['passed'] else (1.0, 0.5, 0.5)
        pct_text = f"{results['percentage']:.0f}%"
        UIRenderer.draw_text(circle_x - 25, circle_y - 30, pct_text,
                             size=18, color=pct_color)

        # Result message
        y_pos = content_y - 20

        if results['passed']:
            UIRenderer.draw_text(panel_x + panel_w / 2 - 100, y_pos,
                                 "MISSION COMPLETE", size=24, color=(0.0, 1.0, 0.5))
            y_pos -= 40

            # Trophy earned box
            glEnable(GL_BLEND)
            glColor4f(0.15, 0.12, 0.0, 0.7)
            box_x = panel_x + 30
            box_w = panel_w - 60
            glBegin(GL_QUADS)
            glVertex2f(box_x, y_pos - 25)
            glVertex2f(box_x + box_w, y_pos - 25)
            glVertex2f(box_x + box_w, y_pos + 35)
            glVertex2f(box_x, y_pos + 35)
            glEnd()
            glColor4f(1.0, 0.8, 0.2, 0.8)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(box_x, y_pos - 25)
            glVertex2f(box_x + box_w, y_pos - 25)
            glVertex2f(box_x + box_w, y_pos + 35)
            glVertex2f(box_x, y_pos + 35)
            glEnd()
            glDisable(GL_BLEND)

            trophy_type = get_trophy_for_planet(self.planet_name)
            trophy_name = trophy_type.replace('_', ' ').title()
            UIRenderer.draw_text(box_x + 15, y_pos + 8, "TROPHY EARNED",
                                 size=12, color=(0.8, 0.7, 0.4))
            UIRenderer.draw_text(box_x + 15, y_pos - 12, trophy_name,
                                 size=18, color=(1.0, 0.9, 0.5))
        else:
            UIRenderer.draw_text(panel_x + panel_w / 2 - 85, y_pos,
                                 "MISSION FAILED", size=24, color=(1.0, 0.3, 0.3))
            y_pos -= 35
            UIRenderer.draw_text(panel_x + panel_w / 2 - 75, y_pos,
                                 "60% required to pass", size=14, color=(0.7, 0.5, 0.5))
            y_pos -= 25
            UIRenderer.draw_text(panel_x + panel_w / 2 - 55, y_pos,
                                 "Try again later", size=14, color=(0.6, 0.6, 0.6))

        # Bottom hint
        glEnable(GL_BLEND)
        glColor4f(0.0, 0.1, 0.15, 0.6)
        glBegin(GL_QUADS)
        glVertex2f(panel_x + 15, panel_y + 50)
        glVertex2f(panel_x + panel_w - 15, panel_y + 50)
        glVertex2f(panel_x + panel_w - 15, panel_y + 80)
        glVertex2f(panel_x + 15, panel_y + 80)
        glEnd()
        glDisable(GL_BLEND)
        UIRenderer.draw_text(panel_x + panel_w / 2 - 80, panel_y + 58,
                             "Press SPACE to return", size=14, color=(0.5, 0.6, 0.7))

    def _draw_trophy_celebration(self, w, h):
        """Draw trophy celebration animation with actual 3D trophy."""
        if self.trophy_animation_time < 4.0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Animated background flash
            flash_alpha = max(0, 0.3 - self.trophy_animation_time * 0.1)
            glColor4f(1.0, 0.8, 0.0, flash_alpha)
            glBegin(GL_QUADS)
            glVertex2f(0, 0)
            glVertex2f(w, 0)
            glVertex2f(w, h)
            glVertex2f(0, h)
            glEnd()

            # Trophy text
            if self.trophy_animation_time > 0.5:
                alpha = min(1.0, (self.trophy_animation_time - 0.5) * 2)
                trophy_type = get_trophy_for_planet(self.planet_name)
                trophy_name = trophy_type.replace('_', ' ').title()

                # Main text - positioned above the trophy
                text1 = "TROPHY EARNED!"
                text1_width = len(text1) * 36 * 0.55
                UIRenderer.draw_text((w - text1_width) / 2, h / 2 + 160, text1,
                                     size=36, color=(1.0, 0.8, 0.0))

                text2 = trophy_name
                text2_width = len(text2) * 28 * 0.55
                UIRenderer.draw_text((w - text2_width) / 2, h / 2 + 110, text2,
                                     size=28, color=(1.0, 1.0, 1.0))

            glDisable(GL_BLEND)

            # Render the actual 3D trophy in the center of the screen
            if self.trophy_animation_time > 0.3 and self.trophy_renderer:
                self._render_3d_trophy_centered(w, h)

    def _render_3d_trophy_centered(self, w, h):
        """Render a 3D trophy model centered on screen."""
        # Clear depth buffer so trophy renders fresh with proper depth
        glClear(GL_DEPTH_BUFFER_BIT)

        # Save current matrices
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()

        # Set up a 3D perspective projection for the trophy
        aspect = w / h if h > 0 else 1.0
        gluPerspective(45.0, aspect, 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Position the camera to look at the trophy
        gluLookAt(0, 0, 3,   # Camera position
                  0, 0, 0,   # Look at point
                  0, 1, 0)   # Up vector

        # Enable lighting for 3D trophy
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Set up a nice light
        light_pos = [2.0, 3.0, 2.0, 1.0]
        light_ambient = [0.3, 0.3, 0.3, 1.0]
        light_diffuse = [1.0, 1.0, 1.0, 1.0]
        light_specular = [0.5, 0.5, 0.5, 1.0]

        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

        # Smooth animation - scale up trophy as it appears
        appear_scale = min(1.0, (self.trophy_animation_time - 0.3) * 2.0)

        # Spin the trophy
        rotation = self.trophy_animation_time * 60  # 60 degrees per second

        # Render the trophy with animation
        self.trophy_renderer.render_trophy(
            self.planet_name,
            x=0,
            y=-0.3,  # Slightly below center
            z=0,
            scale=appear_scale * 1.8,  # Make it bigger for visibility
            rotation=rotation
        )

        # Restore OpenGL state
        glDisable(GL_LIGHTING)
        glDisable(GL_LIGHT0)
        glDisable(GL_COLOR_MATERIAL)

        # Restore matrices
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    def _draw_clipped_layer(self, inner_radius, outer_radius, layer, cut_angle):
        """
        Dibuja una capa esférica recortada (Sphere minus Wedge).
        cut_angle: Ángulo de la cuña removida (0 a 180).
        """
        # Material / Color
        tex_id = layer.get('texture_id')
        if tex_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(*layer['color'])

        # Si el ángulo de corte es muy pequeño, dibujar esfera completa
        if cut_angle < 1.0:
            gluSphere(self.quadric, outer_radius, 64, 64)
            return

        # --- PASO 1: Hemisferio "Trasero" (180-360 grados) ---
        glPushMatrix()
        try:
            # Clip Plane: y < 0 => Normal (0, -1, 0)
            glClipPlane(GL_CLIP_PLANE0, [0.0, -1.0, 0.0, 0.0])
            glEnable(GL_CLIP_PLANE0)
            gluSphere(self.quadric, outer_radius, 64, 64)
            glDisable(GL_CLIP_PLANE0)
        finally:
            glPopMatrix()

        # --- PASO 2: Hemisferio "Delantero" Parcial (cut_angle..180) ---
        glPushMatrix()
        try:
            # Clip Plane 1: y > 0 => Normal (0, 1, 0)
            glClipPlane(GL_CLIP_PLANE0, [0.0, 1.0, 0.0, 0.0])
            glEnable(GL_CLIP_PLANE0)

            # Clip Plane 2: Angle > cut_angle
            rad = math.radians(cut_angle)
            nx = -math.sin(rad)
            ny = math.cos(rad)
            glClipPlane(GL_CLIP_PLANE1, [nx, ny, 0.0, 0.0])
            glEnable(GL_CLIP_PLANE1)

            gluSphere(self.quadric, outer_radius, 64, 64)

            glDisable(GL_CLIP_PLANE0)
            glDisable(GL_CLIP_PLANE1)
        finally:
            glPopMatrix()

        # --- PASO 3: Paredes del corte (Relleno sólido) ---
        # Usar la misma textura si existe
        tex_id = layer.get('texture_id')
        if tex_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(*layer['color'])

        # Desactivar Culling para asegurar que las paredes se vean desde cualquier ángulo
        glDisable(GL_CULL_FACE)

        # Pared 1: En ángulo 0 (Eje X positivo)
        glPushMatrix()
        try:
            glRotatef(90, 1, 0, 0)
            disk = gluNewQuadric()
            if tex_id:
                gluQuadricTexture(disk, GL_TRUE)
            try:
                gluPartialDisk(disk, inner_radius, outer_radius, 64, 1, 0, 180)
            finally:
                gluDeleteQuadric(disk)
        finally:
            glPopMatrix()

        # Pared 2: En ángulo cut_angle
        glPushMatrix()
        try:
            glRotatef(cut_angle, 0, 0, 1)  # Rotar alrededor del eje polar (Z)
            glRotatef(-90, 1, 0, 0)

            disk2 = gluNewQuadric()
            if tex_id:
                gluQuadricTexture(disk2, GL_TRUE)
            try:
                gluPartialDisk(disk2, inner_radius,
                               outer_radius, 64, 1, 0, 180)
            finally:
                gluDeleteQuadric(disk2)
        finally:
            glPopMatrix()

        if tex_id:
            glDisable(GL_TEXTURE_2D)

        # Restaurar Culling
        glEnable(GL_CULL_FACE)
