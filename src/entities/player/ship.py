from OpenGL.GL import *
from OpenGL.GLUT import *
from src.entities.base.renderable import Renderable
from src.core.input_manager import InputManager
import math


class Ship(Renderable):
    def __init__(self, position=[0.0, 0.0, 0.0]):
        super().__init__()
        self.position = list(position)  # [x, y, z]
        self.velocity = [0.0, 0.0, 0.0]
        self.rotation_y = 0.0  # Yaw
        self.speed = 0.0
        self.max_speed = 20.0
        self.acceleration = 30.0
        self.friction = 0.95
        self.turn_speed = 120.0

        # Boost parameters
        self.boost_cooldown = 0.0
        self.boost_duration = 0.0
        self.is_boosting = False

        self.input_manager = InputManager()
        self.compile_display_list()

    def _draw_geometry(self):
        """
        Dibuja la nave (Cono apuntando hacia -Z).
        """
        # Color de la nave (Verde Sci-Fi)
        if self.is_boosting:
            glColor3f(0.0, 1.0, 1.0)  # Cyan cuando hace boost
        else:
            glColor3f(0.0, 1.0, 0.5)

        glPushMatrix()
        # Rotar el cono para que apunte hacia -Z (por defecto apunta a +Z)
        glRotatef(180, 0, 1, 0)
        # glutSolidCone(base, height, slices, stacks)
        glutSolidCone(0.5, 1.5, 16, 16)
        glPopMatrix()

        # Alas decorativas (Triángulos simples)
        glBegin(GL_TRIANGLES)
        glColor3f(0.0, 0.8, 0.4)
        # Ala izquierda
        glVertex3f(-0.5, 0, 0.5)
        glVertex3f(-1.5, 0, 1.0)
        glVertex3f(-0.5, 0, 1.5)
        # Ala derecha
        glVertex3f(0.5, 0, 0.5)
        glVertex3f(1.5, 0, 1.0)
        glVertex3f(0.5, 0, 1.5)
        glEnd()

    def update(self, dt):
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
            self.boost_duration = 1.0  # Dura 1 segundo
            self.boost_cooldown = 5.0  # 5 segundos de espera
            print("BOOST ACTIVATED!")

        # 1. Rotación (A/D o Flechas Izq/Der)
        if self.input_manager.is_key_pressed('a') or self.input_manager.is_special_key_pressed(GLUT_KEY_LEFT):
            self.rotation_y += self.turn_speed * dt
        if self.input_manager.is_key_pressed('d') or self.input_manager.is_special_key_pressed(GLUT_KEY_RIGHT):
            self.rotation_y -= self.turn_speed * dt

        # 2. Aceleración (W/S o Flechas Arr/Abj)
        current_accel = self.acceleration * (3.0 if self.is_boosting else 1.0)

        accel = 0.0
        if self.input_manager.is_key_pressed('w') or self.input_manager.is_special_key_pressed(GLUT_KEY_UP):
            accel = current_accel
        elif self.input_manager.is_key_pressed('s') or self.input_manager.is_special_key_pressed(GLUT_KEY_DOWN):
            accel = -current_accel

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

        # 3. Fricción (Inercia espacial simulada)
        self.velocity[0] *= self.friction
        self.velocity[2] *= self.friction

        # 4. Actualizar posición
        self.position[0] += self.velocity[0] * dt
        self.position[2] += self.velocity[2] * dt

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
