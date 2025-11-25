import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.camera import Camera
from src.graphics.renderer import Renderer
from src.entities.celestial.planet import Planet
from src.entities.celestial.ringed_planet import RingedPlanet
from src.entities.celestial.asteroid_belt import AsteroidBelt
from src.entities.player.ship import Ship
from src.graphics.skybox import Skybox
from src.graphics.texture_loader import TextureLoader
from src.utils.math_helper import check_collision
from src.graphics.ui_renderer import UIRenderer
from src.core.session import GameContext
from src.states.planet_detail_state import PlanetDetailState


class GameplayState(BaseState):
    """
    Estado principal del juego donde ocurre la simulación del sistema solar.
    """

    def __init__(self):
        self.camera = Camera()
        self.skybox = None  # Se inicializa en enter() para cargar texturas
        self.entities = []
        self.ship = None
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.is_dragging = False
        self.sun = None
        self.planet_in_range = None

        # Transición
        self.is_transitioning = False
        self.transition_target = None

    def enter(self):
        print("[GameplayState] Entrando a la simulación")

        # Cargar texturas
        bg_texture = TextureLoader.load_texture(
            "assets/textures/background/stars.jpg")
        self.skybox = Skybox(size=500.0, texture_id=bg_texture)

        # Inicializar entidades
        self._init_entities()

        # Inicializar Nave (Cerca de la Tierra, aprox radio 13)
        self.ship = Ship(position=[15.0, 0.0, 0.0])

        # Configurar cámara inicial (Orbital)
        self.camera.mode = Camera.MODE_ORBIT

    def _init_entities(self):
        self.entities = []

        # Factor de velocidad global para que sea jugable
        SPEED_FACTOR = 10.0
        # Factor de rotación (spin)
        ROTATION_FACTOR = 20.0

        # Sol: (0,0,0), Radio 4.0 (Más grande), Amarillo.
        self.sun = Planet(radius=4.0, orbit_radius=0.0,
                          orbit_speed=0.0, color=(1.0, 1.0, 0.0),
                          texture_path="assets/textures/planets/sun/sun_photosphere.jpg", name="Sun",
                          axial_tilt=7.25, rotation_speed=0.04 * ROTATION_FACTOR)
        self.entities.append(self.sun)

        # Planetas con escala artística (más grandes) y velocidades relativas científicas
        # Periodos orbitales aprox (Tierra = 1):
        # Mercurio: 0.24, Venus: 0.61, Tierra: 1, Marte: 1.88, Júpiter: 11.86, Saturno: 29.4, Urano: 84, Neptuno: 164
        # Velocidad ~ 1 / Periodo

        # Mercurio: Rápido, pequeño pero visible. Tilt ~0.
        self.entities.append(Planet(radius=0.8, orbit_radius=12.0,
                             orbit_speed=4.14 * SPEED_FACTOR, color=(0.7, 0.7, 0.7),
                             texture_path="assets/textures/planets/mercury/mercury_crust.jpg", name="Mercury",
                             axial_tilt=0.03, rotation_speed=(1.0/58.6) * ROTATION_FACTOR))

        # Venus: Brillante. Tilt 177 (Retrograde).
        self.entities.append(Planet(radius=1.1, orbit_radius=18.0,
                             orbit_speed=1.62 * SPEED_FACTOR, color=(1.0, 0.9, 0.6),
                             texture_path="assets/textures/planets/venus/venus_crust.jpg", name="Venus",
                             axial_tilt=177.3, rotation_speed=(1.0/243.0) * ROTATION_FACTOR))

        # Tierra: Azul. Tilt 23.4.
        self.entities.append(Planet(radius=1.1, orbit_radius=26.0,
                             orbit_speed=1.0 * SPEED_FACTOR, color=(0.2, 0.4, 1.0),
                             texture_path="assets/textures/planets/earth/earth_crust.jpg", name="Earth",
                             axial_tilt=23.4, rotation_speed=1.0 * ROTATION_FACTOR))

        # Marte: Rojo. Tilt 25.2.
        self.entities.append(Planet(radius=0.9, orbit_radius=34.0,
                             orbit_speed=0.53 * SPEED_FACTOR, color=(1.0, 0.3, 0.2),
                             texture_path="assets/textures/planets/mars/2k_mars.jpg", name="Mars",
                             axial_tilt=25.2, rotation_speed=0.97 * ROTATION_FACTOR))

        # --- CINTURÓN DE ASTEROIDES ---
        # Entre Marte (34) y Júpiter (80)
        self.entities.append(AsteroidBelt(
            num_asteroids=8000, min_radius=45.0, max_radius=55.0))

        # Júpiter: Gigante. Tilt 3.1. Spin rápido (0.41 dias).
        self.entities.append(Planet(radius=2.8, orbit_radius=80.0,
                             orbit_speed=0.08 * SPEED_FACTOR, color=(0.8, 0.6, 0.4),
                             texture_path="assets/textures/planets/jupiter/jupiter_atmosphere.jpg", name="Jupiter",
                             axial_tilt=3.1, rotation_speed=(1.0/0.41) * ROTATION_FACTOR))

        # Saturno (RingedPlanet): Anillos grandes. Tilt 26.7. Spin 0.45 dias.
        saturn = RingedPlanet(radius=2.4, orbit_radius=110.0, orbit_speed=0.03 * SPEED_FACTOR, color=(0.9, 0.8, 0.6),
                              ring_inner=2.8, ring_outer=4.5, ring_color=(0.8, 0.7, 0.5),
                              texture_path="assets/textures/planets/saturn/saturn_atmosphere.jpg", name="Saturn",
                              axial_tilt=26.7, rotation_speed=(1.0/0.45) * ROTATION_FACTOR)
        self.entities.append(saturn)

        # Urano: Cian. Tilt 97.8. Spin 0.72 dias (Retrograde but tilt handles it).
        uranus = RingedPlanet(radius=1.8, orbit_radius=140.0, orbit_speed=0.01 * SPEED_FACTOR, color=(0.4, 0.9, 0.9),
                              ring_inner=2.2, ring_outer=3.0, ring_color=(0.3, 0.6, 0.6),
                              texture_path="assets/textures/planets/uranus/uranus_atmosphere.jpg", name="Uranus",
                              axial_tilt=97.8, rotation_speed=(1.0/0.72) * ROTATION_FACTOR)
        self.entities.append(uranus)

        # Neptuno: Azul profundo. Tilt 28.3. Spin 0.67 dias.
        self.entities.append(Planet(radius=1.8, orbit_radius=170.0,
                             orbit_speed=0.006 * SPEED_FACTOR, color=(0.1, 0.1, 0.7),
                             texture_path="assets/textures/planets/neptune/neptune_atmosphere.jpg", name="Neptune",
                             axial_tilt=28.3, rotation_speed=(1.0/0.67) * ROTATION_FACTOR))

    def update(self, dt):
        # 0. Transición a Detalle
        if self.is_transitioning and self.transition_target:
            # Interpolar cámara hacia el planeta
            target_pos = self.transition_target.position

            # Mover cámara suavemente
            # Lerp simple: pos += (target - pos) * speed * dt
            lerp_speed = 2.0

            # Queremos acercarnos, pero no meternos dentro.
            # Vamos hacia una posición offset del planeta?
            # O simplemente movemos la cámara hacia el centro y cortamos cuando estemos cerca.
            # El usuario dijo: "Interpola ... hacia el centro ... Si distancia < radius * 3.0 -> CAMBIO"

            dx = target_pos[0] - self.camera.position[0]
            dy = target_pos[1] - self.camera.position[1]
            dz = target_pos[2] - self.camera.position[2]

            dist_sq = dx*dx + dy*dy + dz*dz
            dist = math.sqrt(dist_sq)

            if dist < self.transition_target.radius * 3.0:
                # LLEGAMOS
                print(
                    f"[Gameplay] Transición completada. Cambiando a detalle de {self.transition_target.name}")
                # Necesitamos inyectar la state machine al nuevo estado si queremos que pueda volver
                detail_state = PlanetDetailState(self.transition_target)
                # Hack: Inyectar manualmente si no se hace en el framework
                # Pero BaseState no tiene referencia.
                # Asumimos que el framework (WindowManager) maneja la pila.
                # Al hacer change(), el nuevo estado entra.
                # Pero el nuevo estado necesita llamar a change() para volver.
                # WindowManager llama a update() del estado actual.
                # Si el estado actual quiere cambiar, necesita acceso a la máquina.
                # Vamos a pasarle la referencia 'self.state_machine' si existe.
                # GameplayState debería tener 'self.state_machine' asignado por WindowManager?
                # Revisando WindowManager...
                # WindowManager tiene self.state_machine = StateMachine()
                # Y llama a self.state_machine.update().
                # StateMachine llama a state.update().
                # NO PARECE que se inyecte la referencia de la máquina al estado.
                # ERROR DE DISEÑO en el framework actual.
                # SOLUCIÓN RÁPIDA: Asignar la referencia aquí si la tenemos.
                # Pero GameplayState tampoco la tiene a menos que se la hayamos dado.
                # Vamos a asumir que la tenemos o la asignamos en el main.
                # Si no, fallará.
                # Voy a agregar un parche en WindowManager para inyectar la máquina al estado.

                # Por ahora, intentamos cambiar.
                if hasattr(self, 'state_machine'):
                    detail_state.state_machine = self.state_machine
                    self.state_machine.change(detail_state)
                else:
                    print(
                        "ERROR CRÍTICO: GameplayState no tiene referencia a state_machine")
            else:
                # Moverse
                self.camera.position[0] += dx * lerp_speed * dt
                self.camera.position[1] += dy * lerp_speed * dt
                self.camera.position[2] += dz * lerp_speed * dt

                # Mirar al planeta
                self.camera.target = list(target_pos)

            return  # Skip resto del update durante transición

        # 0. Input Global (Cambio de Cámara)
        # Verificamos input de cámara independientemente del modo
        if self.ship:
            if self.ship.input_manager.is_key_pressed('c'):
                if not hasattr(self, '_c_pressed') or not self._c_pressed:
                    self._c_pressed = True
                    if self.camera.mode == Camera.MODE_ORBIT:
                        print("[Camera] Cambiando a Modo Nave (Follow)")
                        self.camera.mode = Camera.MODE_FOLLOW
                        self.camera.follow_target = self.ship
                    else:
                        print("[Camera] Cambiando a Modo Orbital")
                        self.camera.mode = Camera.MODE_ORBIT
                        # Centrar en el sol (origen)
                        self.camera.target = [0.0, 0.0, 0.0]
            else:
                self._c_pressed = False

        # 1. Actualizar Nave (Solo en modo FOLLOW)
        if self.ship and self.camera.mode == Camera.MODE_FOLLOW:
            self.ship.update(dt)

            # Lógica de interacción (Tecla E)
            if self.ship.input_manager.is_key_pressed('e'):
                if not hasattr(self, '_e_pressed') or not self._e_pressed:
                    self._e_pressed = True
                    if self.planet_in_range:
                        print(
                            f"[Gameplay] Interactuando con {getattr(self.planet_in_range, 'name', 'Unknown')}")
                        GameContext().target_planet = self.planet_in_range

                        # Iniciar transición
                        self.is_transitioning = True
                        self.transition_target = self.planet_in_range
                        print("Iniciando secuencia de aproximación...")
            else:
                self._e_pressed = False

        # 2. Actualizar cámara (Debe ser DESPUÉS de la nave para evitar jitter)
        self.camera.update(dt)

        # 3. Actualizar todas las entidades (Planetas)
        for entity in self.entities:
            entity.update(dt)

        # 4. Verificar colisiones/proximidad con planetas (Solo en modo FOLLOW)
        self.planet_in_range = None
        if self.ship and self.camera.mode == Camera.MODE_FOLLOW:
            # Radio de la nave (visual es pequeña, pero usamos 1.0 para física)
            ship_radius = 1.0
            # Margen para UI (Hitbox de interacción)
            interaction_margin = 3.0

            for entity in self.entities:
                if isinstance(entity, Planet):  # Planet y RingedPlanet
                    # Calcular distancia real
                    dx = self.ship.position[0] - entity.position[0]
                    dy = self.ship.position[1] - entity.position[1]
                    dz = self.ship.position[2] - entity.position[2]
                    dist_sq = dx*dx + dy*dy + dz*dz
                    dist = math.sqrt(dist_sq)

                    # --- 1. Colisión Física (Solid Body) ---
                    min_dist = entity.radius + ship_radius
                    if dist < min_dist:
                        # Resolver colisión: Empujar nave fuera
                        if dist == 0:
                            dist = 0.001  # Evitar div/0

                        # Vector normal desde planeta a nave
                        nx = dx / dist
                        ny = dy / dist
                        nz = dz / dist

                        # Reposicionar nave en la superficie del radio de colisión
                        self.ship.position[0] = entity.position[0] + \
                            nx * min_dist
                        self.ship.position[1] = entity.position[1] + \
                            ny * min_dist
                        self.ship.position[2] = entity.position[2] + \
                            nz * min_dist

                        # Opcional: Anular velocidad hacia el planeta (simple bounce stop)
                        # self.ship.velocity = [0,0,0]

                    # --- 2. Interacción (UI) ---
                    # Distancia de interacción
                    interaction_threshold = min_dist + interaction_margin
                    if dist < interaction_threshold:
                        self.planet_in_range = entity
                        # No hacemos break para permitir que la física se resuelva con otros si hubiera overlap (raro)
                        # pero para UI nos quedamos con el último encontrado (o el más cercano si ordenáramos)

    def draw(self):
        # 1. Configurar entorno 3D
        # Obtenemos el tamaño de la ventana actual (podríamos pasarlo o guardarlo en session/window_manager)
        # Por simplicidad, asumimos que Renderer.setup_3d maneja el viewport si se llama en reshape,
        # pero aquí aseguramos las luces y matrices.
        # Nota: WindowManager llama a reshape, que configura viewport y proyección.
        # Renderer.setup_3d configura luces y estados.
        # Para ser seguros, llamamos a setup_3d con un tamaño dummy o recuperamos el tamaño real si es crítico,
        # pero WindowManager._reshape_callback ya hace gluPerspective.
        # Sin embargo, Renderer.setup_3d hace más cosas (luces).
        # Vamos a asumir que WindowManager maneja el viewport y proyección en reshape,
        # y aquí solo configuramos ModelView y estados.

        # Hack: Recuperamos el viewport actual para setup_3d si fuera necesario,
        # pero Renderer.setup_3d pide width/height.
        # Mejor solo configuramos lo necesario para el frame.
        # Como Renderer.setup_3d resetea la proyección, necesitamos el aspect ratio correcto.
        # Por ahora, confiaremos en que WindowManager mantiene la proyección correcta y solo aplicamos la cámara.
        # PERO, el usuario pidió explícitamente: "Llama a Renderer.setup_3d()".
        # Así que necesitamos el width/height.
        # Una forma es obtenerlo de glutGet(GLUT_WINDOW_WIDTH).

        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)
        Renderer.setup_3d(w, h)

        # 2. Aplicar Cámara
        self.camera.apply()

        # --- CONFIGURACIÓN DE ILUMINACIÓN ---
        # Posicionar la luz en el origen (0,0,0) DONDE ESTÁ EL SOL.
        # Al hacerlo después de camera.apply(), la posición es en coordenadas del mundo.
        # w=1.0 significa luz posicional (punto), no direccional
        light_pos = [0.0, 0.0, 0.0, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)

        # Configurar atenuación para que la luz llegue lejos pero sea intensa cerca
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.01)
        glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.0001)

        # 3. Dibujar Skybox (Fondo)
        if self.skybox:
            self.skybox.draw()

        # 4. Dibujar Entidades

        # DIBUJAR EL SOL (SIN ILUMINACIÓN)
        # El sol es la fuente de luz, no debe recibir sombra.
        # Desactivamos lighting para que se vea con su color puro brillante.
        glDisable(GL_LIGHTING)
        if self.sun:
            self.sun.draw()
        glEnable(GL_LIGHTING)

        # Dibujar el resto de entidades (saltando el sol que ya dibujamos)
        for entity in self.entities:
            if entity != self.sun:
                entity.draw()

        # Dibujar la Nave (Solo si estamos en modo FOLLOW/Nave)
        if self.ship and self.camera.mode == Camera.MODE_FOLLOW:
            self.ship.draw()

        # 5. UI Overlay
        if self.planet_in_range:
            w = glutGet(GLUT_WINDOW_WIDTH)
            h = glutGet(GLUT_WINDOW_HEIGHT)

            UIRenderer.setup_2d(w, h)

            # Panel inferior
            panel_w = 400
            panel_h = 100
            panel_x = (w - panel_w) / 2
            panel_y = 50

            UIRenderer.draw_scifi_panel(panel_x, panel_y, panel_w, panel_h)

            # Texto
            planet_name = getattr(self.planet_in_range,
                                  'name', 'Unknown Planet')
            text = f"ORBITING {planet_name.upper()}"
            text2 = "Press E to Scan"

            # Centrar texto (aprox)
            # Title (Cyan, Size 24)
            UIRenderer.draw_text(panel_x + 20, panel_y +
                                 60, text, size=24, color=(0.0, 1.0, 1.0))
            # Instruction (White, Size 18)
            UIRenderer.draw_text(panel_x + 20, panel_y +
                                 30, text2, size=18, color=(1.0, 1.0, 1.0))

            UIRenderer.restore_3d()

    def handle_input(self, event, x, y):
        event_type = event[0]

        if event_type == 'MOUSE_BUTTON':
            button, state = event[1], event[2]

            # Scroll para Zoom (Botones 3 y 4 en GLUT suelen ser scroll)
            if button == 3 and state == GLUT_DOWN:  # Scroll Up
                self.camera.zoom(2.0)
            elif button == 4 and state == GLUT_DOWN:  # Scroll Down
                self.camera.zoom(-2.0)

            # Click izquierdo para rotar
            if button == GLUT_LEFT_BUTTON:
                if state == GLUT_DOWN:
                    self.is_dragging = True
                    self.last_mouse_x = x
                    self.last_mouse_y = y
                elif state == GLUT_UP:
                    self.is_dragging = False

        elif event_type == 'MOUSE_MOTION':
            if self.is_dragging:
                dx = x - self.last_mouse_x
                dy = y - self.last_mouse_y

                self.last_mouse_x = x
                self.last_mouse_y = y

                # Ajustar sensibilidad
                sensitivity = 0.5
                self.camera.rotate(dx * sensitivity, dy * sensitivity)

        # Detectar tecla 'C' para cambiar cámara (usando el InputManager global sería mejor,
        # pero aquí recibimos eventos crudos de GLUT si no usamos el manager en handle_input)
        # Sin embargo, WindowManager ya delega eventos de teclado a InputManager.
        # Para eventos de "una sola vez" como cambiar cámara, es mejor revisar el InputManager en update
        # o usar un callback específico.
        # Dado que handle_input recibe eventos de mouse, vamos a agregar lógica de teclado en update
        # para el cambio de cámara usando InputManager, es más limpio.
