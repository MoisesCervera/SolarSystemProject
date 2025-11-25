from OpenGL.GL import *
from OpenGL.GLU import *


class Renderer:
    """
    Clase estática para configurar el estado de renderizado de OpenGL.
    """

    @staticmethod
    def setup_3d(width, height):
        """Configura el viewport y la proyección para renderizado 3D."""
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 1000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Habilitar características 3D
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)  # Optimización importante para esferas
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)

        # La posición de la luz se debe configurar DESPUÉS de la cámara en el loop de renderizado
        # para que sea relativa al mundo y no a la cámara.

    @staticmethod
    def setup_2d(width, height):
        """Configura la proyección ortogonal para UI (2D)."""
        if height == 0:
            height = 1

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, width, 0, height)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Deshabilitar características 3D innecesarias para UI
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_CULL_FACE)
