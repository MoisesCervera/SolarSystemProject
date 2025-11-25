import random
import math
from OpenGL.GL import *
from OpenGL.GLUT import *
from src.entities.base.renderable import Renderable


class Skybox(Renderable):
    """
    Fondo espacial representado por un cubo gigante.
    """

    def __init__(self, size=1000.0, texture_id=None):
        self.size = size
        self.texture_id = texture_id
        super().__init__()
        self.compile_display_list()

    def _draw_geometry(self):
        """
        Dibuja un cubo con coordenadas de textura manuales.
        Si no hay textura, dibuja un campo de estrellas procedural mejorado con galaxias y colores.
        """
        half_size = self.size / 2.0

        # Force procedural stars if texture is missing or failed to load
        use_texture = False
        if self.texture_id and use_texture:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glColor3f(1.0, 1.0, 1.0)

            glBegin(GL_QUADS)
            # ... (Texture coords omitted)
            glEnd()
            glDisable(GL_TEXTURE_2D)

        else:
            # Fallback: Fondo negro
            glDisable(GL_TEXTURE_2D)
            glColor3f(0.0, 0.0, 0.0)
            glutSolidCube(self.size)

            rng = random.Random(42)

            # Paleta de colores estelares (Clases espectrales simplificadas)
            star_colors = [
                (1.0, 1.0, 1.0),  # Blanco (Tipo A/F)
                (0.6, 0.8, 1.0),  # Azulado (Tipo O/B)
                (1.0, 1.0, 0.8),  # Amarillo pálido (Tipo G)
                (1.0, 0.9, 0.6),  # Naranja (Tipo K)
                (1.0, 0.4, 0.4),  # Rojo (Tipo M)
            ]

            # 1. Campo de estrellas de fondo (Uniforme)
            glPointSize(1.0)
            glBegin(GL_POINTS)
            for _ in range(4000):
                x = rng.uniform(-half_size, half_size)
                y = rng.uniform(-half_size, half_size)
                z = rng.uniform(-half_size, half_size)

                # Proyectar hacia los bordes para que no queden en medio de la escena
                # Si está dentro del 80% central, lo empujamos a una cara aleatoria
                if abs(x) < half_size * 0.9 and abs(y) < half_size * 0.9 and abs(z) < half_size * 0.9:
                    axis = rng.choice([0, 1, 2])
                    sign = rng.choice([-1, 1])
                    if axis == 0:
                        x = sign * half_size * 0.95
                    elif axis == 1:
                        y = sign * half_size * 0.95
                    else:
                        z = sign * half_size * 0.95

                # Color y brillo aleatorio
                base_color = rng.choice(star_colors)
                brightness = rng.uniform(0.3, 1.0)
                glColor3f(base_color[0] * brightness,
                          base_color[1] * brightness,
                          base_color[2] * brightness)
                glVertex3f(x, y, z)
            glEnd()

            # 2. Generación de "Galaxias" / Cúmulos estelares
            # Generamos centros aleatorios en la esfera lejana
            num_galaxies = 8
            for _ in range(num_galaxies):
                # Dirección aleatoria
                gx = rng.uniform(-1, 1)
                gy = rng.uniform(-1, 1)
                gz = rng.uniform(-1, 1)
                length = math.sqrt(gx*gx + gy*gy + gz*gz)
                if length == 0:
                    continue

                # Posicionar el centro de la galaxia en el borde del skybox
                dist = half_size * 0.9
                gx, gy, gz = (gx/length)*dist, (gy/length) * \
                    dist, (gz/length)*dist

                # Tinte de la galaxia
                galaxy_tint = rng.choice(star_colors)

                # Dibujar estrellas de la galaxia
                # Estrellas un poco más grandes
                glPointSize(rng.choice([1.5, 2.0]))
                glBegin(GL_POINTS)
                num_stars_in_galaxy = rng.randint(200, 500)

                # Dispersión (Spread)
                spread = half_size * 0.15

                for _ in range(num_stars_in_galaxy):
                    # Distribución Gaussiana alrededor del centro
                    sx = gx + rng.gauss(0, spread)
                    sy = gy + rng.gauss(0, spread)
                    sz = gz + rng.gauss(0, spread)

                    # Variación de color mezclando con el tinte de la galaxia
                    brightness = rng.uniform(0.5, 1.0)
                    glColor3f(galaxy_tint[0] * brightness,
                              galaxy_tint[1] * brightness,
                              galaxy_tint[2] * brightness)
                    glVertex3f(sx, sy, sz)
                glEnd()

    def draw(self):
        """
        Dibuja el skybox con trucos de Z-Buffer para que siempre esté al fondo.
        """
        glPushMatrix()
        try:
            # Desactivar escritura en Z-Buffer y Lighting
            glDepthMask(GL_FALSE)
            glDisable(GL_LIGHTING)
            # Importante: Estamos dentro del cubo, necesitamos ver las caras internas
            glDisable(GL_CULL_FACE)

            # Dibujar la lista compilada
            self.draw_list()

            # Restaurar estado
            glEnable(GL_CULL_FACE)
            glEnable(GL_LIGHTING)
            glDepthMask(GL_TRUE)
        finally:
            glPopMatrix()
