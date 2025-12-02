from OpenGL.GL import *
from OpenGL.GLUT import *
from src.entities.base.renderable import Renderable
from src.core.input_manager import InputManager
from src.core.session import GameContext
# Import actual ship models
from src.entities.player.ships.shipM import ShipModel
from src.entities.player.ships.shipS import dibujar_nave as draw_ship_s
from src.entities.player.ships.shipZ import draw_nave as draw_ship_z
import math

# Singleton ship model instance (created once, reused)
_ufo_model_instance = None


def get_ufo_model():
    """Get or create the singleton UFO model instance."""
    global _ufo_model_instance
    if _ufo_model_instance is None:
        _ufo_model_instance = ShipModel()
    return _ufo_model_instance


class Ship(Renderable):
    def __init__(self, position=[0.0, 0.0, 0.0]):
        super().__init__()
        self.position = list(position)  # [x, y, z]
        self.velocity = [0.0, 0.0, 0.0]
        self.rotation_y = 0.0  # Yaw
        self.tilt_angle = 0.0  # Roll (banking)
        self.pitch_angle = 0.0  # Pitch (forward tilt)
        self.speed = 0.0

        self.input_manager = InputManager()

        # Use singleton UFO model (shared, already compiled)
        self.ufo_model = get_ufo_model()
        self.animation_time = 0.0

        # Get selected ship from session
        self.selected_ship = getattr(GameContext, 'selected_ship', 'shipM')

        # Default stats (Ship M / Balanced)
        self.max_speed = 20.0
        self.acceleration = 30.0
        self.friction = 0.98
        self.turn_speed = 120.0

        # Boost parameters
        self.boost_cooldown = 0.0
        self.boost_duration = 0.0
        self.is_boosting = False
        self.boost_duration_max = 1.8
        self.boost_cooldown_time = 3.5
        self.boost_accel_multiplier = 6.0

        # Apply ship-specific stats
        if self.selected_ship == 'shipS':  # Bug Crawler - Fast & Agile
            self.max_speed = 30.0
            self.acceleration = 50.0
            self.turn_speed = 160.0
            self.boost_duration_max = 1.2  # Shorter boost
            self.boost_cooldown_time = 2.0  # Faster cooldown
            self.boost_accel_multiplier = 8.0  # Explosive speed

        elif self.selected_ship == 'shipZ':  # Starfighter - Combat/Heavy
            self.max_speed = 25.0
            self.acceleration = 35.0
            self.turn_speed = 110.0  # Slightly heavier turning
            self.boost_duration_max = 3.0  # Long sustained boost
            self.boost_cooldown_time = 5.0
            self.boost_accel_multiplier = 4.0  # Less explosive, more sustained

        # Global speed multiplier to easily scale ship movement across the game
        # Increase this value to make the ship move much faster in gameplay
        # Global speed multiplier to easily scale ship movement across the game
        # Reduced to 1.5 to tone down the speed (half of previous 3.0 per user feedback)
        self.speed_multiplier = 1

        # Cache animation state dict to avoid per-frame allocation
        self._anim_state = {"hover_y": 0.0, "balanceo_pata_z": 0.0}

        # Don't compile display list - ship models handle their own optimization

    def _draw_geometry(self):
        """
        Dibuja la nave seleccionada.
        """
        # Get selected ship (refresh in case it changed)
        self.selected_ship = getattr(GameContext, 'selected_ship', 'shipM')

        if self.selected_ship == 'shipM':
            # Draw UFO model
            glPushMatrix()
            glScalef(0.3, 0.3, 0.3)  # Scale for gameplay
            glRotatef(180, 0, 1, 0)  # Face forward
            glRotatef(self.pitch_angle, 1, 0, 0)  # Apply Pitch (Nose Down)
            glRotatef(self.tilt_angle, 0, 0, 1)  # Apply tilt (Bank)
            self.ufo_model.draw()
            glPopMatrix()

        elif self.selected_ship == 'shipS':
            # Draw Bug Crawler
            glPushMatrix()
            glScalef(0.6, 0.6, 0.6)  # Scale for gameplay

            # Apply tilt (Bank) - Inverted because shipS has internal 180 flip
            glRotatef(-self.pitch_angle, 1, 0, 0)  # Apply Pitch (Nose Down)
            glRotatef(-self.tilt_angle, 0, 0, 1)

            # Reuse cached animation state dict
            self._anim_state["hover_y"] = math.sin(
                self.animation_time * 2) * 0.05
            self._anim_state["balanceo_pata_z"] = math.sin(
                self.animation_time * 4) * 3
            draw_ship_s(self._anim_state)
            glPopMatrix()

        elif self.selected_ship == 'shipZ':
            # Draw Starfighter
            glPushMatrix()
            glScalef(0.4, 0.4, 0.4)  # Scale for gameplay
            draw_ship_z()
            glPopMatrix()

        else:
            # Fallback: default cone ship
            if self.is_boosting:
                glColor3f(0.0, 1.0, 1.0)  # Cyan cuando hace boost
            else:
                glColor3f(0.0, 1.0, 0.5)

            glPushMatrix()
            glRotatef(180, 0, 1, 0)
            glutSolidCone(0.5, 1.5, 16, 16)
            glPopMatrix()

            glBegin(GL_TRIANGLES)
            glColor3f(0.0, 0.8, 0.4)
            glVertex3f(-0.5, 0, 0.5)
            glVertex3f(-1.5, 0, 1.0)
            glVertex3f(-0.5, 0, 1.5)
            glVertex3f(0.5, 0, 0.5)
            glVertex3f(1.5, 0, 1.0)
            glVertex3f(0.5, 0, 1.5)
            glEnd()

    def update(self, dt):
        # Update animation time for ship models
        self.animation_time += dt

        # Update UFO model animation
        self.ufo_model.update(dt)

        # Actualizar timers de boost
        if self.boost_cooldown > 0:
            self.boost_cooldown -= dt

        if self.boost_duration > 0:
            self.boost_duration -= dt
            if self.boost_duration <= 0:
                self.is_boosting = False

        # Activar Boost (Espacio)
        if self.input_manager.is_key_pressed(' ') and self.boost_cooldown <= 0:
            self.is_boosting = True
            self.boost_duration = self.boost_duration_max
            self.boost_cooldown = self.boost_cooldown_time
            print("BOOST ACTIVATED!")

        # 1. Rotación (A/D o Flechas Izq/Der)
        target_tilt = 0.0
        if self.input_manager.is_key_pressed('a') or self.input_manager.is_special_key_pressed(GLUT_KEY_LEFT):
            self.rotation_y += self.turn_speed * dt
            target_tilt = -15.0  # Bank left (Reversed)
        if self.input_manager.is_key_pressed('d') or self.input_manager.is_special_key_pressed(GLUT_KEY_RIGHT):
            self.rotation_y -= self.turn_speed * dt
            target_tilt = 15.0  # Bank right (Reversed)

        # Smoothly interpolate tilt
        # Faster return to 0 than entry
        tilt_speed = 5.0 * dt
        if target_tilt == 0.0:
            tilt_speed *= 1.5

        self.tilt_angle += (target_tilt - self.tilt_angle) * tilt_speed

        # 2. Aceleración (W/S o Flechas Arr/Abj)
        # Apply global speed multiplier so the ship moves faster if required
        current_accel = self.acceleration * \
            (self.boost_accel_multiplier if self.is_boosting else 1.0) * \
            self.speed_multiplier

        accel = 0.0
        target_pitch = 0.0
        if self.input_manager.is_key_pressed('w') or self.input_manager.is_special_key_pressed(GLUT_KEY_UP):
            accel = current_accel
            target_pitch = 10.0  # Lean forward
        elif self.input_manager.is_key_pressed('s') or self.input_manager.is_special_key_pressed(GLUT_KEY_DOWN):
            accel = -current_accel
            target_pitch = -10.0  # Lean backward

        # Smoothly interpolate pitch
        pitch_speed = 5.0 * dt
        self.pitch_angle += (target_pitch - self.pitch_angle) * pitch_speed

        # Calcular vector dirección (Hacia donde mira la nave)
        # En OpenGL -Z es "adelante".
        # rotation_y = 0 -> Mira a -Z
        # x = -sin(angle), z = -cos(angle)
        rad = math.radians(self.rotation_y)
        dir_x = -math.sin(rad)
        dir_z = -math.cos(rad)

        # Aplicar aceleración a la velocidad
        self.velocity[0] += dir_x * accel * dt
        self.velocity[2] += dir_z * accel * dt

        # 3. Friction (space-like inertia simulated)
        self.velocity[0] *= self.friction
        self.velocity[2] *= self.friction

        # 4. Update position
        self.position[0] += self.velocity[0] * dt
        self.position[2] += self.velocity[2] * dt

        # Cap the horizontal speed to a maximum to avoid runaway velocities
        hspeed = math.sqrt(
            self.velocity[0] * self.velocity[0] + self.velocity[2] * self.velocity[2])
        # Allow a slightly higher maximum speed while boosting (40% higher)
        max_speed_allowed = self.max_speed * self.speed_multiplier * (
            1.4 if self.is_boosting else 1.0)
        if hspeed > max_speed_allowed and hspeed > 0:
            # scale down velocities to cap
            scale = max_speed_allowed / hspeed
            self.velocity[0] *= scale
            self.velocity[2] *= scale

    def draw(self):
        # Desactivar culling para la nave
        glDisable(GL_CULL_FACE)

        glPushMatrix()

        # Trasladar a la posición actual
        glTranslatef(self.position[0], self.position[1], self.position[2])

        # Rotar según la dirección
        glRotatef(self.rotation_y, 0, 1, 0)

        # Dibujar geometría
        # Si estamos en boost, podríamos dibujar algo extra, pero cambiamos el color en _draw_geometry
        # Como usamos display list, el cambio de color en _draw_geometry NO se reflejará dinámicamente
        # a menos que recompiles la lista o no uses la lista para el color.
        # Renderable.draw_list() llama a glCallList.
        # Si queremos efectos dinámicos, mejor llamamos a _draw_geometry directamente o usamos glColor antes de callList
        # PERO el color está DENTRO de la lista.
        # Para que el color cambie, debemos sacar el glColor de la lista o no usar lista.
        # Por simplicidad, llamaremos a _draw_geometry directamente aquí si queremos cambio de color,
        # O simplemente aceptamos que el color no cambie.
        # El usuario pidió "opción de boost", no necesariamente visuales complejos, pero el color ayuda.
        # Vamos a llamar a _draw_geometry directamente para permitir el cambio de color dinámico.
        self._draw_geometry()

        glPopMatrix()

        # Reactivar culling
        glEnable(GL_CULL_FACE)
