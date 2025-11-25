from OpenGL.GL import *


class Renderable:
    """
    Clase base para objetos que usan OpenGL Display Lists para optimización.
    """

    def __init__(self):
        self.display_list_id = None

    def compile_display_list(self):
        """
        Genera una Display List de OpenGL.
        Llama a _draw_geometry() dentro de la lista.
        """
        self.display_list_id = glGenLists(1)
        glNewList(self.display_list_id, GL_COMPILE)
        self._draw_geometry()
        glEndList()

    def _draw_geometry(self):
        """
        Método abstracto/hook para dibujar la geometría cruda.
        Debe ser sobrescrito por las subclases.
        """
        pass

    def draw_list(self):
        """
        Ejecuta la Display List si existe.
        """
        if self.display_list_id is not None:
            glCallList(self.display_list_id)
