from OpenGL.GL import *
from OpenGL.GLU import *
import random
import math
from src.entities.base.renderable import Renderable


class AsteroidBelt(Renderable):
    def __init__(self, num_asteroids, min_radius, max_radius, color=(0.5, 0.5, 0.5)):
        self.num_asteroids = num_asteroids
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.base_color = color

        # Configuración de bandas para realismo
        self.num_bands = 12  # Cantidad de anillos concéntricos
        # Lista de diccionarios {'list_id', 'speed', 'angle'}
        self.rings = []

        # No llamamos a super().compile_display_list() porque usaremos múltiples listas
        super().__init__()
        self._init_rings()

    def _init_rings(self):
        """
        Genera múltiples anillos concéntricos, cada uno con su propia velocidad y lista de visualización.
        """
        asteroids_per_band = self.num_asteroids // self.num_bands
        band_width = (self.max_radius - self.min_radius) / self.num_bands

        for i in range(self.num_bands):
            r_inner = self.min_radius + i * band_width
            r_outer = r_inner + band_width

            # Velocidad orbital basada en leyes de Kepler (aprox 1/sqrt(r))
            # Ajustamos un factor base arbitrario para que se vea bien
            avg_radius = (r_inner + r_outer) / 2
            speed = 15.0 / math.sqrt(avg_radius)

            # Variación aleatoria de velocidad entre bandas vecinas para que no sea tan uniforme
            speed *= random.uniform(0.9, 1.1)

            # Crear Display List para esta banda
            list_id = glGenLists(1)
            glNewList(list_id, GL_COMPILE)
            self._draw_band_geometry(asteroids_per_band, r_inner, r_outer)
            glEndList()

            self.rings.append({
                'list_id': list_id,
                'speed': speed,
                'angle': random.uniform(0, 360)
            })

    def _draw_band_geometry(self, count, r_min, r_max):
        """
        Dibuja los asteroides de una sola banda.
        - Pequeños: Puntos redondos (GL_POINT_SMOOTH).
        - Grandes: Esferas low-poly (gluSphere).
        """
        # 1. Polvo/Pequeños (70%) - Puntos
        # 2. Rocas Medias (25%) - Esferas pequeñas
        # 3. Grandes (5%) - Esferas grandes

        count_dust = int(count * 0.70)
        count_rocks = int(count * 0.25)
        count_boulders = int(count * 0.05)

        # --- GRUPO 1: POLVO (Puntos) ---
        glPushAttrib(GL_POINT_BIT | GL_LIGHTING_BIT)
        glDisable(GL_LIGHTING)       # Puntos brillantes sin sombra
        glEnable(GL_POINT_SMOOTH)    # Puntos redondos
        glPointSize(1.5)

        glBegin(GL_POINTS)
        for _ in range(count_dust):
            angle = random.uniform(0, 2 * math.pi)
            radius = math.sqrt(random.uniform(r_min**2, r_max**2))
            height = random.gauss(0, 0.2)  # Más concentrado

            x = radius * math.cos(angle)
            z = radius * math.sin(angle)

            # Color base con mínima variación
            var = random.uniform(0.9, 1.1)
            glColor3f(self.base_color[0] * var,
                      self.base_color[1] * var,
                      self.base_color[2] * var)
            glVertex3f(x, height, z)
        glEnd()
        glPopAttrib()

        # --- GRUPO 2 & 3: ROCAS (Esferas Low-Poly) ---
        # Habilitamos iluminación para que parezcan rocas 3D
        glEnable(GL_LIGHTING)
        # Material grisáceo mate
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [*self.base_color, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [
                     0.1, 0.1, 0.1, 1.0])  # Poco brillo
        glMaterialf(GL_FRONT, GL_SHININESS, 5.0)

        quadric = gluNewQuadric()

        # Función auxiliar para dibujar rocas
        def draw_rocks(num, size_base):
            for _ in range(num):
                angle = random.uniform(0, 2 * math.pi)
                radius = math.sqrt(random.uniform(r_min**2, r_max**2))
                height = random.gauss(0, 0.3)

                x = radius * math.cos(angle)
                z = radius * math.sin(angle)

                glPushMatrix()
                glTranslatef(x, height, z)

                # Rotación aleatoria de la roca
                glRotatef(random.uniform(0, 360), 1, 0, 0)
                glRotatef(random.uniform(0, 360), 0, 1, 0)

                # Tamaño variable
                s = size_base * random.uniform(0.8, 1.2)
                glScalef(s, s, s)

                # Esfera muy low-poly (4 slices, 3 stacks) -> Parece una roca irregular
                gluSphere(quadric, 1.0, 4, 3)
                glPopMatrix()

        # Rocas medianas (Radio ~0.05 - 0.08)
        draw_rocks(count_rocks, 0.06)

        # Rocas grandes (Radio ~0.1 - 0.15)
        draw_rocks(count_boulders, 0.12)

        gluDeleteQuadric(quadric)

    def _draw_geometry(self):
        # No se usa en esta implementación multianillo
        pass

    def update(self, dt):
        # Actualizar ángulo de cada anillo independientemente
        for ring in self.rings:
            ring['angle'] += ring['speed'] * dt
            if ring['angle'] >= 360:
                ring['angle'] -= 360

    def draw(self):
        """
        Dibuja todos los anillos.
        """
        # No deshabilitamos iluminación globalmente aquí,
        # porque las esferas la necesitan.
        # La gestión de estado se hace dentro de la Display List.

        for ring in self.rings:
            glPushMatrix()
            glRotatef(ring['angle'], 0, 1, 0)
            glCallList(ring['list_id'])
            glPopMatrix()
