import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.camera import Camera
from src.graphics.renderer import Renderer
import random
from src.entities.celestial.planet import Planet
from src.entities.celestial.ringed_planet import RingedPlanet
from src.entities.celestial.asteroid_belt import AsteroidBelt
from src.entities.player.ship import Ship
from src.graphics.skybox import Skybox
from src.core.resource_loader import ResourceManager
from src.utils.math_helper import check_collision
from src.graphics.ui_renderer import UIRenderer
from src.core.session import GameContext
from src.core.mission_manager import MissionManager, get_trophy_for_planet
from src.states.planet_detail_state import PlanetDetailState
from src.core.audio_manager import get_audio_manager


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

        # Boundary system
        self.BOUNDARY_WARNING = 200.0  # Start warning at this distance
        self.BOUNDARY_DANGER = 250.0   # Danger zone - asteroid incoming
        self.BOUNDARY_DEATH = 280.0    # Ship destroyed at this distance
        self.warning_level = 0  # 0=safe, 1=warning, 2=danger, 3=death
        self.warning_pulse = 0.0

        # Death sequence
        self.is_dead = False
        self.death_animation_time = 0.0
        self.death_asteroid = None  # Asteroid position for death animation
        self.explosion_particles = []
        self.show_restart_menu = False
        self.asteroid_impact_pending = False  # Asteroid is flying toward ship
        self.impact_position = None  # Where the impact will happen
        self.camera_pullback_active = False  # Camera pulling back for cinematic view
        self.camera_original_offset_dist = 10.0
        self.camera_target_offset_dist = 25.0

        # Screen shake
        self.screen_shake = 0.0
        
        # Alarm sound channel (to stop when impact is imminent)
        self.alarm_sound_channel = None

        # Speed lines effect for boost - OPTIMIZED
        self.speed_lines = []
        self.speed_line_scroll = 0.0
        self.boost_fade = 0.0  # 0.0 = invisible, 1.0 = fully visible

        # Pre-generate fixed pool of speed lines
        random.seed(42)  # Consistent look
        for _ in range(80):  # Reduced count slightly for performance
            angle = random.uniform(0, 2 * math.pi)
            self.speed_lines.append({
                'angle': angle,
                'cos_angle': math.cos(angle),  # Pre-calculate trig
                'sin_angle': math.sin(angle),
                'offset': random.uniform(0, 1.0),  # Initial phase
                'speed_mult': random.uniform(1.0, 2.0),  # Variation in speed
                'length_mult': random.uniform(0.8, 1.8),  # Longer lines
                'thickness': random.uniform(1.5, 3.0),
                'color_shift': random.uniform(-0.1, 0.1)
            })
        random.seed()  # Reset seed

    def enter(self):
        print("[GameplayState] Entrando a la simulación")

        # Initialize mission system if not orbital-only mode
        self.mission_manager = MissionManager()
        orbital_only = getattr(GameContext, 'orbital_only', False)

        if not orbital_only and not self.mission_manager.game_started:
            self.mission_manager.start_new_game()
            print(
                f"[GameplayState] Mission started! First target: {self.mission_manager.get_current_target()}")

        # Cargar texturas
        bg_texture = ResourceManager.load_texture("background/stars.jpg")
        self.skybox = Skybox(size=500.0, texture_id=bg_texture)

        # Inicializar entidades
        self._init_entities()

        # Check if this is orbital-only mode (no ship)
        orbital_only = getattr(GameContext, 'orbital_only', False)

        if orbital_only:
            # Orbital view mode - no ship, use orbital camera
            self.ship = None
            self.camera.mode = Camera.MODE_ORBIT
            # Reset the flag
            GameContext.orbital_only = False

            # Play orbital view music
            self.audio = get_audio_manager()
            self.audio.play_music('ORBIT')
        else:
            # Normal gameplay mode - with ship
            # Random spawn location within safe bounds
            spawn_pos = self._get_random_spawn_position()
            self.ship = Ship(position=spawn_pos)
            # Use follow camera for gameplay (not orbital)
            self.camera.mode = Camera.MODE_FOLLOW
            self.camera.follow_target = self.ship
            print("[Camera] Cambiando a Modo Nave (Follow)")

            # Start ship-specific gameplay music
            self.audio = get_audio_manager()
            from src.core.audio_manager import get_gameplay_music_state
            music_state = get_gameplay_music_state()
            self.audio.play_music(music_state)

            # Start thruster rumble audio (looping)
            self.audio.play_sfx_looping(
                'thruster', volume_scale=0.0)  # Start silent
            self._thruster_channel = None  # Will be set when we have velocity

    def exit(self):
        """Called when leaving gameplay state - cleanup audio."""
        print("[GameplayState] Saliendo de la simulación")
        # Stop looping sounds when leaving gameplay
        if hasattr(self, 'audio'):
            self.audio.stop_sfx_looping('thruster', fade_ms=200)

    def _get_random_spawn_position(self):
        """Generate a random spawn position within safe bounds."""
        # Spawn at random angle around the solar system
        angle = random.uniform(0, 2 * math.pi)
        # Random distance: not too close to sun (>20), not in warning zone (<150)
        distance = random.uniform(30.0, 150.0)
        
        x = distance * math.cos(angle)
        z = distance * math.sin(angle)
        y = 0.0
        
        print(f"[GameplayState] Ship spawning at random position: ({x:.1f}, {y:.1f}, {z:.1f})")
        return [x, y, z]

    def _init_entities(self):
        self.entities = []

        # Factor de velocidad global para que sea jugable
        SPEED_FACTOR = 10.0
        # Factor de rotación (spin)
        ROTATION_FACTOR = 20.0

        # Sol: (0,0,0), Radio 4.0 (Más grande), Amarillo.
        self.sun = Planet(radius=4.0, orbit_radius=0.0,
                          orbit_speed=0.0, color=(1.0, 1.0, 0.0),
                          texture_path="planets/sun/sun_photosphere.jpg", name="Sun",
                          axial_tilt=7.25, rotation_speed=0.04 * ROTATION_FACTOR)
        self.entities.append(self.sun)

        # Planetas con escala artística (más grandes) y velocidades relativas científicas
        # Periodos orbitales aprox (Tierra = 1):
        # Mercurio: 0.24, Venus: 0.61, Tierra: 1, Marte: 1.88, Júpiter: 11.86, Saturno: 29.4, Urano: 84, Neptuno: 164
        # Velocidad ~ 1 / Periodo

        # Mercurio: Rápido, pequeño pero visible. Tilt ~0.
        self.entities.append(Planet(radius=0.8, orbit_radius=12.0,
                             orbit_speed=4.14 * SPEED_FACTOR, color=(0.7, 0.7, 0.7),
                             texture_path="planets/mercury/mercury_crust.jpg", name="Mercury",
                             axial_tilt=0.03, rotation_speed=(1.0/58.6) * ROTATION_FACTOR))

        # Venus: Brillante. Tilt 177 (Retrograde).
        self.entities.append(Planet(radius=1.1, orbit_radius=18.0,
                             orbit_speed=1.62 * SPEED_FACTOR, color=(1.0, 0.9, 0.6),
                             texture_path="planets/venus/venus_crust.jpg", name="Venus",
                             axial_tilt=177.3, rotation_speed=(1.0/243.0) * ROTATION_FACTOR))

        # Tierra: Azul. Tilt 23.4.
        self.entities.append(Planet(radius=1.1, orbit_radius=26.0,
                             orbit_speed=1.0 * SPEED_FACTOR, color=(0.2, 0.4, 1.0),
                             texture_path="planets/earth/earth_crust.jpg", name="Earth",
                             axial_tilt=23.4, rotation_speed=1.0 * ROTATION_FACTOR))

        # Marte: Rojo. Tilt 25.2.
        self.entities.append(Planet(radius=0.9, orbit_radius=34.0,
                             orbit_speed=0.53 * SPEED_FACTOR, color=(1.0, 0.3, 0.2),
                             texture_path="planets/mars/2k_mars.jpg", name="Mars",
                             axial_tilt=25.2, rotation_speed=0.97 * ROTATION_FACTOR))

        # --- CINTURÓN DE ASTEROIDES ---
        # Entre Marte (34) y Júpiter (80)
        self.entities.append(AsteroidBelt(
            num_asteroids=8000, min_radius=45.0, max_radius=55.0))

        # Júpiter: Gigante. Tilt 3.1. Spin rápido (0.41 dias).
        self.entities.append(Planet(radius=2.8, orbit_radius=80.0,
                             orbit_speed=0.08 * SPEED_FACTOR, color=(0.8, 0.6, 0.4),
                             texture_path="planets/jupiter/jupiter_atmosphere.jpg", name="Jupiter",
                             axial_tilt=3.1, rotation_speed=(1.0/0.41) * ROTATION_FACTOR))

        # Saturno (RingedPlanet): Anillos grandes. Tilt 26.7. Spin 0.45 dias.
        saturn = RingedPlanet(radius=2.4, orbit_radius=110.0, orbit_speed=0.03 * SPEED_FACTOR, color=(0.9, 0.8, 0.6),
                              ring_inner=2.8, ring_outer=4.5, ring_color=(0.8, 0.7, 0.5),
                              texture_path="planets/saturn/saturn_atmosphere.jpg", name="Saturn",
                              axial_tilt=26.7, rotation_speed=(1.0/0.45) * ROTATION_FACTOR)
        self.entities.append(saturn)

        # Urano: Cian. Tilt 97.8. Spin 0.72 dias (Retrograde but tilt handles it).
        uranus = RingedPlanet(radius=1.8, orbit_radius=140.0, orbit_speed=0.01 * SPEED_FACTOR, color=(0.4, 0.9, 0.9),
                              ring_inner=2.2, ring_outer=3.0, ring_color=(0.3, 0.6, 0.6),
                              texture_path="planets/uranus/uranus_atmosphere.jpg", name="Uranus",
                              axial_tilt=97.8, rotation_speed=(1.0/0.72) * ROTATION_FACTOR)
        self.entities.append(uranus)

        # Neptuno: Azul profundo. Tilt 28.3. Spin 0.67 dias.
        self.entities.append(Planet(radius=1.8, orbit_radius=170.0,
                             orbit_speed=0.006 * SPEED_FACTOR, color=(0.1, 0.1, 0.7),
                             texture_path="planets/neptune/neptune_atmosphere.jpg", name="Neptune",
                             axial_tilt=28.3, rotation_speed=(1.0/0.67) * ROTATION_FACTOR))

    def _check_boundary(self):
        """Check if ship is too far from the solar system center."""
        if not self.ship or self.asteroid_impact_pending:
            return

        # Calculate distance from origin (sun)
        x, y, z = self.ship.position
        dist = math.sqrt(x*x + y*y + z*z)

        # Track previous warning level for alarm trigger
        prev_warning_level = self.warning_level

        # Update warning level
        if dist < self.BOUNDARY_WARNING:
            self.warning_level = 0  # Safe
            self.death_asteroid = None  # Clear asteroid if player returned to safety
        elif dist < self.BOUNDARY_DANGER:
            self.warning_level = 1  # Warning
            self.death_asteroid = None  # Clear asteroid if player moved back from danger
            # Play alarm when first entering warning zone
            if prev_warning_level == 0:
                self.alarm_sound_channel = self.audio.play_sfx('alarm', volume_scale=0.6)
        elif dist < self.BOUNDARY_DEATH:
            self.warning_level = 2  # Danger - asteroid approaching
            # Play alarm when entering danger zone
            if prev_warning_level < 2:
                self.alarm_sound_channel = self.audio.play_sfx('alarm', volume_scale=0.8)
            # Spawn incoming asteroid if not already
            if self.death_asteroid is None:
                self._spawn_death_asteroid()
        else:
            # Past the death boundary - launch the killing asteroid!
            self.warning_level = 3
            self._launch_impact_asteroid()

    def _spawn_death_asteroid(self):
        """Spawn an asteroid visible in the distance as a warning."""
        import random
        if not self.ship:
            return

        # Asteroid spawns far away, visible as a threat
        ship_pos = self.ship.position
        dist_from_origin = math.sqrt(
            ship_pos[0]**2 + ship_pos[1]**2 + ship_pos[2]**2)

        # Direction from origin to ship (normalized)
        if dist_from_origin > 0:
            dir_x = ship_pos[0] / dist_from_origin
            dir_y = ship_pos[1] / dist_from_origin
            dir_z = ship_pos[2] / dist_from_origin
        else:
            dir_x, dir_y, dir_z = 1, 0, 0

        # Asteroid visible in the distance, slightly off to the side
        asteroid_dist = self.BOUNDARY_DEATH + 30
        offset_angle = random.uniform(-0.3, 0.3)
        self.death_asteroid = {
            'position': [
                dir_x * asteroid_dist + random.uniform(-10, 10),
                dir_y * asteroid_dist + random.uniform(-5, 5),
                dir_z * asteroid_dist + random.uniform(-10, 10)
            ],
            'velocity': [0, 0, 0],  # Stationary warning asteroid
            'rotation': random.uniform(0, 360),
            'size': random.uniform(2.0, 3.0)
        }
        print("[WARNING] Asteroid field ahead!")

    def _launch_impact_asteroid(self):
        """Launch an asteroid that will hit the ship - visible approach."""
        import random
        if not self.ship or self.asteroid_impact_pending:
            return

        # Stop alarm sound - impact is imminent
        if self.alarm_sound_channel and self.alarm_sound_channel.get_busy():
            self.alarm_sound_channel.fadeout(200)
            self.alarm_sound_channel = None

        self.asteroid_impact_pending = True
        self.impact_position = list(
            self.ship.position)  # Remember where ship is

        ship_pos = self.ship.position

        # Get the direction the ship is facing
        ship_facing_rad = math.radians(self.ship.rotation_y)
        forward_x = -math.sin(ship_facing_rad)
        forward_z = -math.cos(ship_facing_rad)

        # Asteroid comes from IN FRONT and ABOVE the player at an angle
        # So the player can actually SEE it coming
        start_distance = 50  # Start far enough to see it approach
        start_height = 30    # Above but not directly overhead

        self.death_asteroid = {
            'position': [
                ship_pos[0] + forward_x *
                start_distance + random.uniform(-5, 5),
                ship_pos[1] + start_height,
                ship_pos[2] + forward_z *
                start_distance + random.uniform(-5, 5)
            ],
            'target': list(ship_pos),
            'rotation': [random.uniform(0, 360), random.uniform(0, 360), random.uniform(0, 360)],
            'rotation_speed': [random.uniform(100, 200), random.uniform(80, 150), random.uniform(60, 120)],
            'size': 3.5,
            'speed': 45.0,  # Slower so player can see it coming
            'visible': True  # This asteroid should be visible immediately
        }

        # Pull camera back to show the incoming asteroid
        self._start_camera_pullback()

        print("[IMPACT] Asteroid incoming from ahead!")

    def _start_camera_pullback(self):
        """Pull the camera back to show the incoming asteroid."""
        self.camera_pullback_active = True
        self.camera_original_offset_dist = 10.0  # Default from camera.py
        self.camera_target_offset_dist = 25.0    # Pull back to this distance

    def _trigger_death(self):
        """Trigger the death sequence - called when asteroid hits ship."""
        if self.is_dead:
            return

        print("[DEATH] Ship destroyed by asteroid impact!")
        self.is_dead = True
        self.screen_shake = 2.0
        self.death_animation_time = 0.0
        self.show_restart_menu = False

        # Stop all looping ship sounds and play destroyed sound
        if hasattr(self, 'audio'):
            self.audio.stop_sfx_looping('thruster', fade_ms=100)
            self.audio.play_sfx('ship_destroyed')

        # Create explosion particles at ship/impact position
        import random
        impact_pos = self.impact_position if self.impact_position else (
            self.ship.position if self.ship else [0, 0, 0])
        self.explosion_particles = []

        # More particles for a bigger explosion
        for _ in range(80):
            speed = random.uniform(5, 25)
            angle1 = random.uniform(0, math.pi * 2)
            angle2 = random.uniform(-math.pi/2, math.pi/2)
            self.explosion_particles.append({
                'position': list(impact_pos),
                'velocity': [
                    math.cos(angle1) * math.cos(angle2) * speed,
                    math.sin(angle2) * speed,
                    math.sin(angle1) * math.cos(angle2) * speed
                ],
                'life': random.uniform(1.5, 3.0),
                'size': random.uniform(0.3, 1.2),
                'color': random.choice([
                    (1.0, 0.5, 0.0),  # Orange
                    (1.0, 0.8, 0.0),  # Yellow
                    (1.0, 0.2, 0.0),  # Red
                    (1.0, 0.3, 0.1),  # Deep orange
                    (0.6, 0.6, 0.6),  # Gray debris
                    (0.4, 0.4, 0.4),  # Dark debris
                ])
            })

        # Add some larger debris chunks
        for _ in range(15):
            speed = random.uniform(8, 18)
            angle1 = random.uniform(0, math.pi * 2)
            angle2 = random.uniform(-math.pi/3, math.pi/3)
            self.explosion_particles.append({
                'position': list(impact_pos),
                'velocity': [
                    math.cos(angle1) * math.cos(angle2) * speed,
                    math.sin(angle2) * speed + random.uniform(2, 5),
                    math.sin(angle1) * math.cos(angle2) * speed
                ],
                'life': random.uniform(2.0, 4.0),
                'size': random.uniform(0.8, 1.5),
                'color': (0.3, 0.3, 0.35),  # Metal debris
            })

    def _update_death_sequence(self, dt):
        """Update death animation and show restart menu."""
        self.death_animation_time += dt

        # Update asteroid flying toward ship (before death)
        if self.death_asteroid and self.asteroid_impact_pending and not self.is_dead:
            ast = self.death_asteroid

            # Move asteroid toward the ship's position (falling from above)
            target = self.ship.position if self.ship else ast.get('target', [
                                                                  0, 0, 0])

            dx = target[0] - ast['position'][0]
            dy = target[1] - ast['position'][1]
            dz = target[2] - ast['position'][2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)

            if dist > 0:
                # Move toward target - mostly downward since it's above
                speed = ast.get('speed', 150.0)
                ast['position'][0] += (dx / dist) * speed * dt
                ast['position'][1] += (dy / dist) * speed * dt
                ast['position'][2] += (dz / dist) * speed * dt

            # Tumbling rotation on all axes
            rot = ast.get('rotation', [0, 0, 0])
            rot_speed = ast.get('rotation_speed', [150, 100, 80])
            if isinstance(rot, list):
                rot[0] += rot_speed[0] * dt
                rot[1] += rot_speed[1] * dt
                rot[2] += rot_speed[2] * dt
            else:
                ast['rotation'] += 300 * dt

            # Check if asteroid hit the ship
            if dist < 3.0:  # Impact distance
                self._trigger_death()

        # Keep asteroid visible and tumbling after death (continues past impact point)
        if self.death_asteroid and self.is_dead:
            ast = self.death_asteroid

            # Continue tumbling rotation
            rot = ast.get('rotation', [0, 0, 0])
            rot_speed = ast.get('rotation_speed', [150, 100, 80])
            if isinstance(rot, list):
                # Slow down slightly after impact
                rot[0] += rot_speed[0] * dt * 0.5
                rot[1] += rot_speed[1] * dt * 0.5
                rot[2] += rot_speed[2] * dt * 0.5

            # Continue moving in its original trajectory (past the impact point)
            if 'post_impact_velocity' not in ast:
                # Calculate velocity based on original approach direction
                target = ast.get('target', [0, 0, 0])
                pos = ast['position']
                # Direction it was traveling
                dx = target[0] - pos[0]
                dy = target[1] - pos[1]
                dz = target[2] - pos[2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1
                # Continue in same direction at reduced speed
                ast['post_impact_velocity'] = [
                    dx/dist * 30, dy/dist * 30 - 10, dz/dist * 30]

            ast['position'][0] += ast['post_impact_velocity'][0] * dt
            ast['position'][1] += ast['post_impact_velocity'][1] * dt
            ast['position'][2] += ast['post_impact_velocity'][2] * dt

        # Update explosion particles
        for p in self.explosion_particles:
            p['position'][0] += p['velocity'][0] * dt
            p['position'][1] += p['velocity'][1] * dt
            p['position'][2] += p['velocity'][2] * dt
            p['velocity'][1] -= 2.0 * dt  # Slight gravity
            p['life'] -= dt

        # Remove dead particles
        self.explosion_particles = [
            p for p in self.explosion_particles if p['life'] > 0]

        # Show restart menu after animation
        if self.death_animation_time > 2.0:
            self.show_restart_menu = True

        # Handle camera pullback for cinematic effect
        if self.camera_pullback_active and self.camera.mode == Camera.MODE_FOLLOW:
            # Gradually increase the camera offset distance
            current_offset = getattr(
                self.camera, 'custom_offset_dist', self.camera_original_offset_dist)
            if current_offset < self.camera_target_offset_dist:
                new_offset = current_offset + 15.0 * dt  # Smooth pullback
                self.camera.custom_offset_dist = min(
                    new_offset, self.camera_target_offset_dist)

        # Keep updating camera and entities for visual effect
        self._update_camera_with_custom_offset(dt)
        for entity in self.entities:
            entity.update(dt)

    def _update_camera_with_custom_offset(self, dt):
        """Update camera with custom offset distance for cinematic pullback."""
        if self.camera.mode == Camera.MODE_FOLLOW and self.camera.follow_target:
            target_x = self.camera.follow_target.position[0]
            target_y = self.camera.follow_target.position[1]
            target_z = self.camera.follow_target.position[2]

            # Use custom offset distance if set, otherwise default
            offset_dist = getattr(self.camera, 'custom_offset_dist', 10.0)
            # Raise camera as it pulls back
            offset_height = 5.0 + (offset_dist - 10.0) * 0.3

            rad = math.radians(self.camera.follow_target.rotation_y)
            desired_x = target_x - (-math.sin(rad) * offset_dist)
            desired_z = target_z - (-math.cos(rad) * offset_dist)
            desired_y = target_y + offset_height

            lerp_factor = self.camera.follow_smoothness * dt
            self.camera.position[0] += (desired_x -
                                        self.camera.position[0]) * lerp_factor
            self.camera.position[1] += (desired_y -
                                        self.camera.position[1]) * lerp_factor
            self.camera.position[2] += (desired_z -
                                        self.camera.position[2]) * lerp_factor

            self.camera.target = [target_x, target_y, target_z]
        else:
            self.camera.update(dt)

    def _restart_game(self):
        """Restart the game from ship select with transition."""
        if hasattr(self, 'state_machine'):
            from src.states.ship_select_state import ShipSelectState
            self.state_machine.change(
                ShipSelectState(), use_transition=True, duration=0.6)

    def _return_to_menu(self):
        """Return to main menu with transition."""
        if hasattr(self, 'state_machine'):
            from src.states.welcome_state import WelcomeState
            # Clear all states without transition, then change with transition
            while len(self.state_machine.states) > 1:
                self.state_machine.pop_immediate()
            self.state_machine.change(
                WelcomeState(), use_transition=True, duration=0.6)

    def update(self, dt):
        # Decay screen shake
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - dt * 3.0)

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
                    # Reset transition flags BEFORE pushing so we don't re-trigger on return
                    self.is_transitioning = False
                    self.transition_target = None
                    self.state_machine.push(
                        detail_state, use_transition=True, duration=0.5)
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
        # 'c' key toggle removed per user request

        # Update warning pulse for UI effects
        self.warning_pulse += dt * 5.0

        # Handle death sequence (asteroid incoming or already dead)
        if self.is_dead or self.asteroid_impact_pending:
            self._update_death_sequence(dt)
            if self.is_dead:
                return
            # If asteroid is incoming but not dead yet, continue updating but don't allow ship control

        # 1. Actualizar Nave (Solo en modo FOLLOW)
        if self.ship and self.camera.mode == Camera.MODE_FOLLOW and not self.asteroid_impact_pending:
            self.ship.update(dt)

            # Update thruster rumble volume based on ship speed
            self._update_thruster_audio()

            # Update speed lines effect based on boost state
            self._update_speed_lines(dt)

            # Camera follow smoothing should be tighter during boost to keep
            # the ship centered even at higher velocities - reduce perceived lag
            # by increasing the camera interpolation factor while boosting.
            if self.ship.is_boosting:
                self.camera.follow_smoothness = 6.0
            else:
                # Restore to a comfortable value (default 5.0) when not boosting
                self.camera.follow_smoothness = 3.0

            # Check boundary distance
            self._check_boundary()

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
        # Use custom offset if camera pullback is active
        if self.camera_pullback_active:
            self._update_camera_with_custom_offset(dt)
        else:
            self.camera.update(dt)

        # 3. Actualizar todas las entidades (Planetas)
        for entity in self.entities:
            entity.update(dt)

        # 4. Verificar colisiones/proximidad con planetas (Solo en modo FOLLOW)
        # Track previous planet to detect when entering a new planet's range
        prev_planet_in_range = self.planet_in_range
        current_planet_in_range = None
        
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
                        current_planet_in_range = entity
                        # No hacemos break para permitir que la física se resuelva con otros si hubiera overlap (raro)
                        # pero para UI nos quedamos con el último encontrado (o el más cercante si ordenáramos)

        # Play scan sound only when entering a new planet's range (not already in range of this planet)
        if current_planet_in_range and current_planet_in_range != prev_planet_in_range:
            self.audio.play_sfx('scan_planet', volume_scale=0.25)
        
        self.planet_in_range = current_planet_in_range

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

        # Apply screen shake
        if self.screen_shake > 0:
            shake_x = (random.random() - 0.5) * self.screen_shake
            shake_y = (random.random() - 0.5) * self.screen_shake
            glTranslatef(shake_x, shake_y, 0)

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

        # Dibujar la Nave (Solo si estamos en modo FOLLOW/Nave y no está muerta)
        if self.ship and self.camera.mode == Camera.MODE_FOLLOW and not self.is_dead:
            self.ship.draw()

        # Draw death asteroid ONLY when impact is pending or after death (not warning asteroid)
        if self.death_asteroid and (self.asteroid_impact_pending or self.is_dead):
            # Only draw if marked as visible (impact asteroid) or after death
            if self.death_asteroid.get('visible', False) or self.is_dead:
                self._draw_death_asteroid()

        # Draw explosion particles
        if self.explosion_particles:
            self._draw_explosion()

        # 5. UI Overlay
        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Draw boundary warnings
        if (self.warning_level > 0 or self.asteroid_impact_pending) and not self.is_dead:
            self._draw_boundary_warning(w, h)

        # Draw death/restart screen
        if self.is_dead and self.show_restart_menu:
            self._draw_restart_menu(w, h)

        if self.planet_in_range and not self.is_dead:
            w = glutGet(GLUT_WINDOW_WIDTH)
            h = glutGet(GLUT_WINDOW_HEIGHT)

            UIRenderer.setup_2d(w, h)

            # Panel inferior
            panel_w = 450
            panel_h = 120
            panel_x = (w - panel_w) / 2
            panel_y = 50

            # Custom Sci-Fi Panel Drawing
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Background
            glColor4f(0.0, 0.05, 0.1, 0.9)
            chamfer = 20
            glBegin(GL_POLYGON)
            glVertex2f(panel_x + chamfer, panel_y)
            glVertex2f(panel_x + panel_w - chamfer, panel_y)
            glVertex2f(panel_x + panel_w, panel_y + chamfer)
            glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
            glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
            glVertex2f(panel_x + chamfer, panel_y + panel_h)
            glVertex2f(panel_x, panel_y + panel_h - chamfer)
            glVertex2f(panel_x, panel_y + chamfer)
            glEnd()

            # Glowing Border
            pulse = 0.6 + 0.4 * math.sin(self.warning_pulse)
            glLineWidth(2.0)
            glColor4f(0.0, 0.8 * pulse, 1.0 * pulse, 0.8)
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

            glDisable(GL_BLEND)

            # Texto
            planet_name = getattr(self.planet_in_range,
                                  'name', 'Unknown Planet')
            text = f"ORBITING {planet_name.upper()}"

            # Check if this is the mission target
            is_target = self.mission_manager.is_target_planet(planet_name)
            text2 = "PRESS E TO SCAN"
            if is_target:
                text2 = "PRESS E TO SCAN [MISSION TARGET]"

            # Centrar texto
            # Title (Cyan, Size 28)
            _, t1_w, t1_h = UIRenderer.get_text_texture(
                text, 28, font_name="radiospace")
            UIRenderer.draw_text(panel_x + (panel_w - t1_w)/2, panel_y + 70, text,
                                 size=28, color=(0.0, 1.0, 1.0), font_name="radiospace")

            # Instruction (White/Yellow, Size 20)
            color2 = (1.0, 0.8, 0.0) if is_target else (0.8, 0.9, 1.0)
            _, t2_w, t2_h = UIRenderer.get_text_texture(
                text2, 20, font_name="radiospace")
            UIRenderer.draw_text(panel_x + (panel_w - t2_w)/2, panel_y + 35, text2,
                                 size=20, color=color2, font_name="radiospace")

            UIRenderer.restore_3d()

        # Draw mission panel (top-right)
        if self.ship and not self.is_dead and self.mission_manager.game_started:
            self._draw_mission_panel(w, h)

        # Draw speed lines effect when boosting
        if self.ship and self.ship.is_boosting and not self.is_dead:
            self._draw_speed_lines(w, h)

    def _draw_boundary_warning(self, w, h):
        """Draw warning UI when approaching boundary."""
        UIRenderer.setup_2d(w, h)

        pulse = 0.5 + 0.5 * math.sin(self.warning_pulse)

        if self.asteroid_impact_pending:
            # Critical - impact imminent!
            color = (1.0, 0.0, 0.0)
            text1 = "*** IMPACT IMMINENT ***"
            text2 = "COLLISION UNAVOIDABLE"
            text3 = ""
            border_width = 12.0
            border_alpha = 0.7
        elif self.warning_level == 1:
            # Yellow warning
            color = (1.0, 0.8 * pulse, 0.0)
            text1 = "! WARNING !"
            text2 = "APPROACHING SOLAR SYSTEM BOUNDARY"
            text3 = "TURN BACK NOW"
            border_width = 4.0
            border_alpha = pulse * 0.3
        else:
            # Red danger
            color = (1.0, 0.2 * pulse, 0.0)
            text1 = "!!! DANGER !!!"
            text2 = "ASTEROID FIELD DETECTED"
            text3 = "TURN BACK IMMEDIATELY"
            border_width = 8.0
            border_alpha = pulse * 0.5

        # Draw flashing border
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(color[0], color[1], color[2], border_alpha)
        glLineWidth(border_width)
        glBegin(GL_LINE_LOOP)
        glVertex2f(10, 10)
        glVertex2f(w - 10, 10)
        glVertex2f(w - 10, h - 10)
        glVertex2f(10, h - 10)
        glEnd()

        glDisable(GL_BLEND)

        # Draw warning text at top
        text1_size = 40
        _, t1_w, _ = UIRenderer.get_text_texture(
            text1, text1_size, font_name="radiospace")
        UIRenderer.draw_text((w - t1_w) / 2, h - 80,
                             text1, size=text1_size, color=color, font_name="radiospace")

        text2_size = 24
        _, t2_w, _ = UIRenderer.get_text_texture(
            text2, text2_size, font_name="radiospace")
        UIRenderer.draw_text((w - t2_w) / 2, h - 120,
                             text2, size=text2_size, color=color, font_name="radiospace")

        text3_size = 20
        _, t3_w, _ = UIRenderer.get_text_texture(
            text3, text3_size, font_name="radiospace")
        UIRenderer.draw_text((w - t3_w) / 2, h - 155,
                             text3, size=text3_size, color=(1.0, 1.0, 1.0), font_name="radiospace")

        # Draw distance indicator
        if self.ship:
            dist = math.sqrt(sum(p**2 for p in self.ship.position))
            dist_text = f"DISTANCE FROM SUN: {dist:.0f} UNITS"
            dist_size = 16
            _, d_w, _ = UIRenderer.get_text_texture(
                dist_text, dist_size, font_name="radiospace")
            UIRenderer.draw_text((w - d_w) / 2, h - 185,
                                 dist_text, size=dist_size, color=(0.7, 0.7, 0.7), font_name="radiospace")

        UIRenderer.restore_3d()

    def _draw_death_asteroid(self):
        """Draw the incoming death asteroid - irregular rocky shape."""
        if not self.death_asteroid:
            return

        ast = self.death_asteroid
        glPushMatrix()
        glTranslatef(ast['position'][0], ast['position']
                     [1], ast['position'][2])

        # Apply tumbling rotation on multiple axes
        rot = ast.get('rotation', [0, 0, 0])
        if isinstance(rot, list):
            glRotatef(rot[0], 1, 0, 0)
            glRotatef(rot[1], 0, 1, 0)
            glRotatef(rot[2], 0, 0, 1)
        else:
            glRotatef(rot, 0.3, 1.0, 0.2)

        glDisable(GL_LIGHTING)

        # Main asteroid body - dark gray (space rock color)
        glColor3f(0.35, 0.35, 0.38)
        glutSolidSphere(ast['size'], 16, 16)

        # Add irregular bumps to make it look more like a real asteroid
        glColor3f(0.4, 0.4, 0.42)
        bump_positions = [
            (0.7, 0.3, 0.2), (-0.5, 0.6, 0.3), (0.2, -0.7, 0.4),
            (-0.3, 0.2, 0.7), (0.5, -0.3, -0.5), (-0.6, -0.4, 0.2)
        ]
        for bx, by, bz in bump_positions:
            glPushMatrix()
            glTranslatef(bx * ast['size'], by * ast['size'], bz * ast['size'])
            glutSolidSphere(ast['size'] * 0.4, 8, 8)
            glPopMatrix()

        # Add darker craters/indentations
        glColor3f(0.2, 0.2, 0.22)
        crater_positions = [
            (0.8, 0, 0), (-0.8, 0.1, 0), (0, 0.8, 0.1),
            (0.4, 0.4, 0.6), (-0.3, -0.5, 0.5)
        ]
        for cx, cy, cz in crater_positions:
            glPushMatrix()
            glTranslatef(cx * ast['size'], cy * ast['size'], cz * ast['size'])
            glutSolidSphere(ast['size'] * 0.25, 6, 6)
            glPopMatrix()

        # Add some lighter mineral spots
        glColor3f(0.5, 0.5, 0.52)
        for i in range(3):
            glPushMatrix()
            angle = i * 120
            glRotatef(angle, 1, 1, 0)
            glTranslatef(ast['size'] * 0.85, 0, 0)
            glutSolidSphere(ast['size'] * 0.15, 4, 4)
            glPopMatrix()

        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_explosion(self):
        """Draw explosion particles."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        for p in self.explosion_particles:
            alpha = min(1.0, p['life'])
            glColor4f(p['color'][0], p['color'][1], p['color'][2], alpha)

            glPushMatrix()
            glTranslatef(p['position'][0], p['position'][1], p['position'][2])
            glutSolidSphere(p['size'] * alpha, 6, 6)
            glPopMatrix()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_restart_menu(self, w, h):
        """Draw the restart/game over menu."""
        UIRenderer.setup_2d(w, h)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Dark overlay
        glColor4f(0.0, 0.0, 0.0, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(w, 0)
        glVertex2f(w, h)
        glVertex2f(0, h)
        glEnd()

        # Central panel
        panel_w = 500
        panel_h = 320
        panel_x = (w - panel_w) / 2
        panel_y = (h - panel_h) / 2

        glColor4f(0.1, 0.0, 0.0, 0.9)
        chamfer = 20
        glBegin(GL_POLYGON)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glVertex2f(panel_x, panel_y + chamfer)
        glEnd()

        # Red border
        pulse = 0.5 + 0.3 * math.sin(self.warning_pulse)
        glLineWidth(3.0)
        glColor3f(0.8 * pulse, 0.1, 0.1)
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

        glDisable(GL_BLEND)

        # Title
        title = "SHIP DESTROYED"
        title_size = 48
        _, t_w, _ = UIRenderer.get_text_texture(
            title, title_size, font_name="radiospace")
        UIRenderer.draw_text((w - t_w) / 2, panel_y + panel_h - 80, title,
                             size=title_size, color=(1.0, 0.2, 0.2), font_name="radiospace")

        # Subtitle
        sub = "ASTEROID COLLISION DETECTED"
        sub_size = 20
        _, s_w, _ = UIRenderer.get_text_texture(
            sub, sub_size, font_name="radiospace")
        UIRenderer.draw_text((w - s_w) / 2, panel_y + panel_h - 120, sub,
                             size=sub_size, color=(0.7, 0.7, 0.7), font_name="radiospace")

        # Options
        opt1 = "R - RESTART"
        opt1_size = 26
        _, o1_w, _ = UIRenderer.get_text_texture(
            opt1, opt1_size, font_name="radiospace")
        UIRenderer.draw_text((w - o1_w) / 2, panel_y + 120, opt1,
                             size=opt1_size, color=(0.0, 1.0, 1.0), font_name="radiospace")

        opt2 = "M - MAIN MENU"
        opt2_size = 26
        _, o2_w, _ = UIRenderer.get_text_texture(
            opt2, opt2_size, font_name="radiospace")
        UIRenderer.draw_text((w - o2_w) / 2, panel_y + 70, opt2,
                             size=opt2_size, color=(1.0, 0.8, 0.0), font_name="radiospace")

        UIRenderer.restore_3d()

    def _draw_mission_panel(self, w, h):
        """Draw the mission panel in the top-right corner."""
        UIRenderer.setup_2d(w, h)

        # Panel dimensions
        panel_w = 320
        panel_h = 180
        panel_x = w - panel_w - 30
        panel_y = h - panel_h - 30

        # Draw semi-transparent background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Darker, more tech-like background
        glColor4f(0.0, 0.02, 0.05, 0.9)
        chamfer = 20
        glBegin(GL_POLYGON)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glVertex2f(panel_x, panel_y + chamfer)
        glEnd()

        # Glowing Border
        pulse = 0.8 + 0.2 * math.sin(self.warning_pulse * 0.5)
        glLineWidth(2.0)
        glColor4f(0.0, 0.6 * pulse, 0.8 * pulse, 0.8)
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

        # Tech details (corner brackets)
        glLineWidth(2.0)
        glColor4f(0.0, 1.0, 1.0, 0.6)
        bracket_len = 15
        # Top Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(panel_x + panel_w - bracket_len, panel_y + panel_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - bracket_len)
        glEnd()
        # Bottom Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(panel_x + bracket_len, panel_y)
        glVertex2f(panel_x, panel_y)
        glVertex2f(panel_x, panel_y + bracket_len)
        glEnd()

        glDisable(GL_BLEND)

        # Header
        header = "MISSION CONTROL"
        UIRenderer.draw_text(panel_x + 20, panel_y + panel_h - 35, header,
                             size=20, color=(0.0, 1.0, 1.0), font_name="radiospace")

        # Separator line
        glColor3f(0.0, 0.4, 0.6)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(panel_x + 15, panel_y + panel_h - 45)
        glVertex2f(panel_x + panel_w - 15, panel_y + panel_h - 45)
        glEnd()

        # Current target
        target = self.mission_manager.get_current_target()
        mission_num = self.mission_manager.get_current_mission_number()
        total_missions = self.mission_manager.get_total_missions()

        if target:
            target_label = f"TARGET: {target.upper()}"
            UIRenderer.draw_text(panel_x + 20, panel_y + panel_h - 75, target_label,
                                 size=18, color=(1.0, 0.8, 0.0), font_name="radiospace")

            # Progress
            progress = f"MISSION {mission_num} / {total_missions}"
            UIRenderer.draw_text(panel_x + 20, panel_y + panel_h - 100, progress,
                                 size=16, color=(0.7, 0.8, 0.9), font_name="radiospace")

            # Progress bar
            bar_x = panel_x + 20
            bar_y = panel_y + panel_h - 130
            bar_w = panel_w - 40
            bar_h = 10

            # Bar background
            glColor4f(0.1, 0.2, 0.3, 0.5)
            glBegin(GL_QUADS)
            glVertex2f(bar_x, bar_y)
            glVertex2f(bar_x + bar_w, bar_y)
            glVertex2f(bar_x + bar_w, bar_y + bar_h)
            glVertex2f(bar_x, bar_y + bar_h)
            glEnd()

            # Progress fill
            progress_pct = self.mission_manager.get_progress_percentage() / 100.0
            fill_w = bar_w * progress_pct

            # Animated fill
            glColor4f(0.0, 0.9, 0.5, 0.8)
            glBegin(GL_QUADS)
            glVertex2f(bar_x, bar_y)
            glVertex2f(bar_x + fill_w, bar_y)
            glVertex2f(bar_x + fill_w, bar_y + bar_h)
            glVertex2f(bar_x, bar_y + bar_h)
            glEnd()

            # Trophies collected
            trophies_count = self.mission_manager.get_completed_count()
            trophies_text = f"DATA COLLECTED: {trophies_count}"
            UIRenderer.draw_text(panel_x + 20, panel_y + 20, trophies_text,
                                 size=14, color=(0.0, 0.8, 0.8), font_name="radiospace")
        else:
            # All missions complete!
            complete_text = "ALL MISSIONS COMPLETE"
            UIRenderer.draw_text(panel_x + 20, panel_y + panel_h - 80, complete_text,
                                 size=18, color=(0.0, 1.0, 0.5), font_name="radiospace")

            sub_text = "RETURN TO BASE"
            UIRenderer.draw_text(panel_x + 20, panel_y + panel_h - 110, sub_text,
                                 size=16, color=(0.0, 0.8, 0.8), font_name="radiospace")

        UIRenderer.restore_3d()

    def _update_thruster_audio(self):
        """Update thruster rumble volume based on ship speed."""
        if not self.ship or not hasattr(self, 'audio'):
            return

        # Calculate speed magnitude from velocity
        vx, vy, vz = self.ship.velocity
        speed = math.sqrt(vx*vx + vy*vy + vz*vz)

        # Normalize speed to 0-1 range (max_speed is the reference)
        max_speed = self.ship.max_speed * self.ship.speed_multiplier
        if self.ship.is_boosting:
            # During boost, max speed is higher
            max_speed *= self.ship.boost_accel_multiplier * 0.5

        # Calculate volume: min 0.15 (idle hum) to max 1.0 (full throttle)
        # Increased base and max for more prominent rumble
        speed_ratio = min(1.0, speed / max_speed) if max_speed > 0 else 0.0

        # Use exponential curve for more natural feel (quiet at low speeds, loud at high)
        volume = 0.15 + (speed_ratio ** 1.2) * 0.85

        # Boost gives extra rumble
        if self.ship.is_boosting:
            volume = min(1.0, volume * 1.4)

        # Update the looping sound volume
        if 'thruster' in self.audio._looping_sounds:
            info = self.audio._looping_sounds['thruster']
            sound = info.get('sound')
            if sound:
                effective_vol = self.audio._get_effective_sfx_volume() * volume
                sound.set_volume(effective_vol)
                info['volume_scale'] = volume  # Update stored scale

    def _update_speed_lines(self, dt):
        """Update speed lines scroll and fade state."""
        if not self.ship:
            return

        # Smoothly fade in/out based on boost state
        target_fade = 1.0 if self.ship.is_boosting else 0.0
        fade_speed = 4.0  # Fast transition

        if self.boost_fade < target_fade:
            self.boost_fade = min(
                target_fade, self.boost_fade + fade_speed * dt)
        elif self.boost_fade > target_fade:
            self.boost_fade = max(
                target_fade, self.boost_fade - fade_speed * dt)

        # Always scroll, but faster when boosting
        scroll_speed = 1.5 if self.ship.is_boosting else 0.5
        self.speed_line_scroll += scroll_speed * dt

    def _draw_speed_lines(self, w, h):
        """Draw optimized radial speed lines."""
        if self.boost_fade <= 0.01:
            return

        UIRenderer.setup_2d(w, h)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending
        glDisable(GL_TEXTURE_2D)

        center_x = w / 2
        center_y = h / 2
        max_radius = math.sqrt(w*w + h*h) * 0.6  # Cover corners

        # Batch drawing for performance
        glBegin(GL_LINES)

        for line in self.speed_lines:
            # Calculate progress (0 to 1) moving outward
            progress = (line['offset'] + self.speed_line_scroll *
                        line['speed_mult']) % 1.0

            # Don't draw if too close to center (looks weird)
            if progress < 0.4:
                continue

            # Calculate position using pre-calculated trig
            r = progress * max_radius
            x = center_x + line['cos_angle'] * r
            y = center_y + line['sin_angle'] * r

            # Calculate trail (behind the point, towards center)
            # Significantly increased length multiplier to avoid "dots" look
            trail_len = 150.0 * line['length_mult'] * progress

            tail_x = x - line['cos_angle'] * trail_len
            tail_y = y - line['sin_angle'] * trail_len

            # Alpha fades at edges and based on boost_fade
            alpha = self.boost_fade * \
                min(progress * 4.0, (1.0 - progress) * 4.0, 1.0)

            # Color
            r_val = 1.0
            g_val = 1.0
            b_val = 1.0

            # Note: glLineWidth cannot be changed inside glBegin/glEnd
            # We use a fixed width or simulate thickness with alpha/color
            # For performance, we use default width inside the batch

            glColor4f(r_val, g_val, b_val, 0.0)  # Tail (transparent)
            glVertex2f(tail_x, tail_y)
            glColor4f(r_val, g_val, b_val, alpha)  # Head (bright)
            glVertex2f(x, y)

        glEnd()

        glDisable(GL_BLEND)
        UIRenderer.restore_3d()

    def handle_input(self, event, x, y):
        event_type = event[0]

        # Handle restart menu input when dead
        if self.is_dead and self.show_restart_menu:
            if event_type == 'KEY_DOWN':
                key = event[1]
                if key == b'r' or key == b'R':
                    self._restart_game()
                    return
                elif key == b'm' or key == b'M':
                    self._return_to_menu()
                    return
            return  # Don't process other input when dead

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

        if event_type == 'KEY_DOWN':
            key = event[1]
            # Debug key to force game complete state
            if key == b'g':
                print("[DEBUG] Forcing Game Complete State")
                if hasattr(self, 'state_machine'):
                    from src.states.game_complete_state import GameCompleteState
                    self.state_machine.change(
                        GameCompleteState(), use_transition=True, duration=0.8)
