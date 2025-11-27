from OpenGL.GL import *
from OpenGL.GLU import *
from src.entities.base.renderable import Renderable
from src.graphics.texture_loader import TextureLoader
from src.graphics.ui_renderer import UIRenderer
import math
import random


class Planet(Renderable):
    def __init__(self, radius, orbit_radius, orbit_speed, color=(1.0, 1.0, 1.0), texture_path=None, name="Unknown Planet", axial_tilt=0.0, rotation_speed=1.0):
        super().__init__()
        self.name = name
        self.radius = radius
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.color = color
        self.texture_path = texture_path
        self.texture_id = None

        # Propiedades físicas
        self.axial_tilt = axial_tilt
        # Grados por segundo (o unidad de tiempo)
        self.rotation_speed = rotation_speed
        self.rotation_angle = 0.0

        if self.texture_path:
            self.texture_id = TextureLoader.load_texture(self.texture_path)

        # Inicio aleatorio de la órbita para caos visual
        self.orbit_angle = random.uniform(0.0, 360.0)
        self.orbit_list_id = None

        # Posición actual en el mundo (se actualiza en update)
        self.position = [0.0, 0.0, 0.0]

        # IMPORTANTE: Generar la Display List inmediatamente
        self.compile_display_list()
        self._compile_orbit_list()

    def _compile_orbit_list(self):
        """Compila la visualización de la órbita (círculo)."""
        if self.orbit_radius <= 0:
            return

        self.orbit_list_id = glGenLists(1)
        glNewList(self.orbit_list_id, GL_COMPILE)

        glDisable(GL_LIGHTING)  # Las líneas no necesitan iluminación
        glLineWidth(1.0)
        glColor3f(0.3, 0.3, 0.3)  # Gris oscuro

        glBegin(GL_LINE_LOOP)
        segments = 100
        for i in range(segments):
            theta = 2.0 * math.pi * float(i) / float(segments)
            x = self.orbit_radius * math.cos(theta)
            z = self.orbit_radius * math.sin(theta)
            glVertex3f(x, 0.0, z)
        glEnd()

        glEnable(GL_LIGHTING)
        glEndList()

    def _draw_geometry(self):
        """
        Dibuja la esfera dentro de la Display List.
        Se llama una sola vez durante compile_display_list().
        """
        # Establecer color (material)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glColor3f(1.0, 1.0, 1.0)  # Blanco para que la textura se vea bien
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(*self.color)

        # Dibujar esfera
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        if self.texture_id:
            gluQuadricTexture(quadric, GL_TRUE)

        # Rotar -90 grados en X para que los polos queden en el eje Y (vertical)
        # gluSphere dibuja alrededor del eje Z por defecto.
        # Rotar 90 grados en X para que los polos queden en el eje Y (vertical)
        # gluSphere dibuja alrededor del eje Z por defecto.
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)

        # gluSphere(quadric, radius, slices, stacks)
        gluSphere(quadric, self.radius, 32, 32)

        glPopMatrix()

        gluDeleteQuadric(quadric)

        if self.texture_id:
            glDisable(GL_TEXTURE_2D)

    def update(self, dt):
        """Actualiza el ángulo de órbita y la posición."""
        self.orbit_angle += self.orbit_speed * dt
        if self.orbit_angle >= 360.0:
            self.orbit_angle -= 360.0

        # Actualizar rotación sobre su eje
        self.rotation_angle += self.rotation_speed * dt
        if self.rotation_angle >= 360.0:
            self.rotation_angle -= 360.0

        # Calcular posición actual (x, y, z)

        # Calcular posición actual (x, y, z)
        # glRotatef(angle, 0, 1, 0) -> Rotación en Y
        # glTranslatef(radius, 0, 0) -> Traslación en X
        # x = r * cos(angle)
        # z = -r * sin(angle) (Depende de la mano del sistema, pero para distancia no importa el signo)
        # En OpenGL estándar:
        # Rotar en Y positivo es antihorario.
        # (1, 0, 0) rotado theta es (cos theta, 0, -sin theta)
        rad = math.radians(self.orbit_angle)
        self.position[0] = self.orbit_radius * math.cos(rad)
        self.position[1] = 0.0
        self.position[2] = -self.orbit_radius * math.sin(rad)

    def draw(self):
        """
        Aplica transformaciones y llama a la Display List.
        """
        glPushMatrix()

        # Dibujar la órbita (estática respecto al padre)
        if self.orbit_list_id:
            glCallList(self.orbit_list_id)

        # 1. Rotación orbital (alrededor del sol/origen)
        glRotatef(self.orbit_angle, 0, 1, 0)

        # 2. Traslación a la posición orbital
        glTranslatef(self.orbit_radius, 0, 0)

        # 3. Aplicar inclinación axial y rotación
        # Primero deshacemos la rotación orbital para alinear el eje con el mundo
        glRotatef(-self.orbit_angle, 0, 1, 0)

        # Aplicar inclinación axial (fija en el espacio)
        # Rotamos en X o Z para inclinar el eje Y (polos)
        # Usamos X para inclinar "hacia adelante/atrás" o Z para "izquierda/derecha"
        # Asumimos inclinación hacia una dirección fija arbitraria (e.g. eje X)
        glRotatef(self.axial_tilt, 1, 0, 0)

        # Aplicar rotación diaria sobre su propio eje (ahora inclinado)
        glRotatef(self.rotation_angle, 0, 1, 0)

        # 4. Dibujar la geometría compilada
        self.draw_list()

        # 5. Dibujar etiqueta (Billboard)
        # Necesitamos deshacer las rotaciones locales para que la etiqueta flote recta
        # O simplemente dibujarla en la posición del planeta pero sin las rotaciones de eje
        # La etiqueta se dibuja en _draw_label usando la matriz actual.
        # Si llamamos a _draw_label aquí, estará afectada por axial_tilt y rotation_angle.
        # Queremos que la etiqueta esté encima del planeta pero NO rotando como loca.

        # Guardamos matriz antes de dibujar etiqueta
        glPushMatrix()
        # Deshacer rotación diaria y tilt para la etiqueta?
        # Mejor: Resetear rotación manteniendo posición.
        # _draw_label ya hace un reset de rotación usando glLoadIdentity y extrayendo traslación.
        # Así que debería funcionar bien.
        self._draw_label()
        glPopMatrix()

        glPopMatrix()

    def _draw_label(self):
        # Obtener textura del nombre
        texture_id, width, height = UIRenderer.get_text_texture(self.name, 32)
        if not texture_id:
            return

        glPushMatrix()

        # Get the current modelview matrix BEFORE applying any label offset
        # This gives us the planet center position in camera space
        modelview = glGetFloatv(GL_MODELVIEW_MATRIX)

        # Extract the planet's position in camera/view space
        planet_x = modelview[3][0]
        planet_y = modelview[3][1]
        planet_z = modelview[3][2]

        # Billboard: Reset to identity and position label above planet
        # The offset is applied in world Y direction (always up), not in tilted coordinates
        offset = self.radius + 1.0

        glLoadIdentity()
        # Position at planet center, then offset upward in screen space
        glTranslatef(planet_x, planet_y + offset, planet_z)

        # Dibujar Quad
        # Desactivar iluminación para que el texto sea siempre legible
        glDisable(GL_LIGHTING)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Escalar tamaño pixel a mundo
        scale = 0.02
        w = width * scale
        h = height * scale

        glColor3f(1.0, 1.0, 1.0)

        glBegin(GL_QUADS)
        # Mapeo de coordenadas de textura
        # Si el texto sale invertido, invertimos las coordenadas T.
        # T=0 (Top Image) -> Y=0 (Bottom Quad)
        # T=1 (Bottom Image) -> Y=h (Top Quad)

        glTexCoord2f(0, 0)
        glVertex3f(-w/2, 0, 0)
        glTexCoord2f(1, 0)
        glVertex3f(w/2, 0, 0)
        glTexCoord2f(1, 1)
        glVertex3f(w/2, h, 0)
        glTexCoord2f(0, 1)
        glVertex3f(-w/2, h, 0)
        glEnd()

        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)

        glPopMatrix()
