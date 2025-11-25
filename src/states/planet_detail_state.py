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

        # Panel de Información (se inicializa en enter() para tener dimensiones de ventana correctas si fuera necesario,
        # pero aquí podemos poner None)
        self.info_panel = None

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

    def exit(self):
        if self.quadric:
            gluDeleteQuadric(self.quadric)
            self.quadric = None

        # Limpiar luces extra para no afectar otros estados
        glDisable(GL_LIGHT1)

    def update(self, dt):
        # Animar apertura
        if self.open_factor < self.target_open_factor:
            self.open_factor += self.animation_speed * dt
            if self.open_factor > self.target_open_factor:
                self.open_factor = self.target_open_factor

        # Input para salir
        # Nota: Usamos glut directamente o InputManager si estuviera disponible globalmente
        # Como no tenemos acceso fácil al InputManager global aquí sin pasarlo,
        # asumimos que WindowManager llama a handle_input o usamos un check directo si es posible.
        # Pero BaseState no tiene handle_input por defecto en la definición que vi,
        # aunque WindowManager lo llama.
        pass

    def handle_input(self, event, x, y):
        # Detectar Enter o Espacio para salir
        if event[0] == 'KEY_DOWN':
            key = event[1]
            if key == b'\r' or key == b' ':  # Enter o Espacio
                from src.states.gameplay_state import GameplayState
                if hasattr(self, 'state_machine'):
                    self.state_machine.change(GameplayState())

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

            # Instrucción (Abajo a la derecha)
            UIRenderer.draw_text(
                w - 300, 20, "PRESS SPACE TO RETURN", size=18, color=(1.0, 0.5, 0.5))
        finally:
            UIRenderer.restore_3d()

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
