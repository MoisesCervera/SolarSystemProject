from OpenGL.GL import *
from OpenGL.GLU import *
from src.entities.celestial.planet import Planet
from src.graphics.texture_loader import TextureLoader


class RingedPlanet(Planet):
    def __init__(self, radius, orbit_radius, orbit_speed, color, ring_inner, ring_outer, ring_color, axial_tilt=0.0, rotation_speed=1.0, texture_path=None, ring_texture_path=None, name="Ringed Planet"):
        self.ring_inner = ring_inner
        self.ring_outer = ring_outer
        self.ring_color = ring_color
        # self.ring_inclination ya no se usa, usamos axial_tilt
        self.ring_list_id = None
        self.ring_texture_path = ring_texture_path
        self.ring_texture_id = None

        if self.ring_texture_path:
            self.ring_texture_id = TextureLoader.load_texture(
                self.ring_texture_path)

        # Inicializa el planeta base
        super().__init__(radius, orbit_radius, orbit_speed,
                         color, texture_path=texture_path, name=name, axial_tilt=axial_tilt, rotation_speed=rotation_speed)

        # Compilar el anillo
        self._compile_ring_list()

    def _compile_ring_list(self):
        self.ring_list_id = glGenLists(1)
        glNewList(self.ring_list_id, GL_COMPILE)

        # Desactivar Culling para ver caras internas si es necesario
        glDisable(GL_CULL_FACE)

        if self.ring_texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.ring_texture_id)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(*self.ring_color)

        # NO rotamos aquí. La inclinación se aplica en draw() con axial_tilt.
        # Pero necesitamos alinear los anillos con el ecuador del planeta.
        # En _draw_geometry (abajo), usamos gluSphere por defecto (Polos en Z).
        # gluDisk dibuja en plano XY (Normal Z).
        # Así que los anillos (XY) ya están alineados con el ecuador de la esfera (XY).
        # No necesitamos rotación extra aquí.

        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        if self.ring_texture_id:
            gluQuadricTexture(quadric, GL_TRUE)

        thickness = 0.02  # Grosor del anillo reducido

        if self.ring_texture_id:
            # 1. Cara Superior
            glPushMatrix()
            glTranslatef(0, 0, thickness/2)
            gluDisk(quadric, self.ring_inner, self.ring_outer, 64, 1)
            glPopMatrix()

            # 2. Cara Inferior
            glPushMatrix()
            glTranslatef(0, 0, -thickness/2)
            # Rotamos para que la normal apunte hacia abajo
            glRotatef(180, 1, 0, 0)
            gluDisk(quadric, self.ring_inner, self.ring_outer, 64, 1)
            glPopMatrix()
        else:
            # Simular anillos con bandas de colores si no hay textura
            num_bands = 10
            band_width = (self.ring_outer - self.ring_inner) / num_bands

            import random
            base_r, base_g, base_b = self.ring_color

            for i in range(num_bands):
                r_inner = self.ring_inner + i * band_width
                r_outer = r_inner + band_width

                # Variar ligeramente el color
                variation = random.uniform(0.8, 1.2)
                glColor3f(min(1.0, base_r * variation),
                          min(1.0, base_g * variation),
                          min(1.0, base_b * variation))

                # Cara Superior
                glPushMatrix()
                glTranslatef(0, 0, thickness/2)
                gluDisk(quadric, r_inner, r_outer, 64, 1)
                glPopMatrix()

                # Cara Inferior
                glPushMatrix()
                glTranslatef(0, 0, -thickness/2)
                glRotatef(180, 1, 0, 0)
                gluDisk(quadric, r_inner, r_outer, 64, 1)
                glPopMatrix()

        # 3. Borde Exterior
        glPushMatrix()
        glTranslatef(0, 0, -thickness/2)
        gluCylinder(quadric, self.ring_outer,
                    self.ring_outer, thickness, 64, 1)
        glPopMatrix()

        # 4. Borde Interior
        glPushMatrix()
        glTranslatef(0, 0, -thickness/2)
        # Invertir normales para el interior
        gluQuadricOrientation(quadric, GLU_INSIDE)
        gluCylinder(quadric, self.ring_inner,
                    self.ring_inner, thickness, 64, 1)
        gluQuadricOrientation(quadric, GLU_OUTSIDE)  # Restaurar
        glPopMatrix()

        gluDeleteQuadric(quadric)

        # Eliminamos el glPopMatrix extra que cerraba el glRotatef de inclinación
        # glPopMatrix()

        if self.ring_texture_id:
            glDisable(GL_TEXTURE_2D)

        # Restaurar Culling
        glEnable(GL_CULL_FACE)

        glEndList()

    def _draw_geometry(self):
        """
        Sobrescribimos para NO rotar 90 grados, ya que los anillos están en el plano XY
        y queremos que el ecuador del planeta (textura) se alinee con ellos.
        """
        # Establecer color (material)
        if self.texture_id:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glDisable(GL_TEXTURE_2D)
            glColor3f(*self.color)

        # Dibujar esfera
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        if self.texture_id:
            gluQuadricTexture(quadric, GL_TRUE)

        # NO rotamos 90 grados. Dejamos que el eje sea Z, para que el ecuador sea XY.
        # Así coincide con gluDisk (anillos) que está en XY.
        # PERO: Planet.draw() asume que el eje Y es el polo para aplicar axial_tilt (glRotatef(tilt, 1, 0, 0)).
        # Si aquí el polo es Z, y rotamos en X, el polo Z baja a -Y.
        # Si Planet.draw() rota en X, inclina el eje Y hacia Z.

        # Necesitamos que la geometría base tenga el polo en Y para que la lógica de Planet.draw funcione igual.
        # Si el polo es Y, el ecuador es XZ.
        # Los anillos (gluDisk) están en XY.
        # Así que debemos rotar los anillos 90 grados en X para que estén en XZ.

        # O podemos cambiar _draw_geometry para que sea igual que Planet (Polo Y).
        # Y en _compile_ring_list rotar los anillos para que estén en XZ.

        # Vamos a alinear todo al eje Y (Vertical) como base.
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)  # Polo Z -> Polo Y
        gluSphere(quadric, self.radius, 32, 32)
        glPopMatrix()

        gluDeleteQuadric(quadric)

        if self.texture_id:
            glDisable(GL_TEXTURE_2D)

    def draw(self):
        """
        Sobrescribimos draw para dibujar el anillo junto con el planeta.
        Usamos la lógica de Planet.draw() pero añadimos los anillos.
        """
        glPushMatrix()

        # Dibujar la órbita (estática respecto al padre)
        if self.orbit_list_id:
            glCallList(self.orbit_list_id)

        # 1. Rotación orbital
        glRotatef(self.orbit_angle, 0, 1, 0)

        # 2. Traslación
        glTranslatef(self.orbit_radius, 0, 0)

        # 3. Aplicar inclinación axial y rotación (Lógica de Planet)
        glRotatef(-self.orbit_angle, 0, 1, 0)  # Deshacer rotación orbital
        glRotatef(self.axial_tilt, 1, 0, 0)   # Inclinar eje Y
        # Rotar sobre eje Y (inclinado)
        glRotatef(self.rotation_angle, 0, 1, 0)

        # 4. Dibujar el planeta (Esfera)
        self.draw_list()

        # 5. Dibujar el anillo
        # Los anillos deben estar alineados con el ecuador.
        # Si el polo es Y, el ecuador es XZ.
        # gluDisk dibuja en XY.
        # Necesitamos rotar los anillos 90 grados en X para llevarlos de XY a XZ.
        if self.ring_list_id:
            glPushMatrix()
            glRotatef(90, 1, 0, 0)  # XY -> XZ
            glCallList(self.ring_list_id)
            glPopMatrix()

        # 6. Dibujar etiqueta
        # Resetear rotaciones para billboard
        glPushMatrix()
        self._draw_label()
        glPopMatrix()

        glPopMatrix()
