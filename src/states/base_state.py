class BaseState:
    """
    Clase abstracta base para todos los estados del juego.
    Define la interfaz que deben implementar los estados concretos.
    """

    def update(self, dt):
        """
        Actualiza la lógica del estado.
        :param dt: Delta time (tiempo transcurrido desde el último frame en segundos)
        """
        pass

    def draw(self):
        """
        Renderiza el contenido del estado.
        """
        pass

    def enter(self):
        """
        Se llama cuando el estado entra a la pila (se vuelve activo).
        """
        pass

    def exit(self):
        """
        Se llama cuando el estado sale de la pila.
        """
        pass

    def handle_input(self, event, x, y):
        """
        Maneja eventos de entrada (teclado, mouse).
        :param event: Tupla o objeto con detalles del evento.
        :param x: Posición X del mouse.
        :param y: Posición Y del mouse.
        """
        pass
