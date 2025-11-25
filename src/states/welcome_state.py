from OpenGL.GL import *
from src.states.base_state import BaseState


class WelcomeState(BaseState):
    """
    Estado de bienvenida.
    Por ahora, solo muestra un fondo de color para verificar el funcionamiento.
    """

    def enter(self):
        print("[WelcomeState] Entrando al estado de bienvenida")

    def update(self, dt):
        pass

    def draw(self):
        # Cambiamos el color de fondo a Azul Oscuro
        glClearColor(0.1, 0.1, 0.3, 1.0)

        # Limpiamos la pantalla nuevamente con el nuevo color
        # (Aunque WindowManager ya limpió, necesitamos aplicar este color específico)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
