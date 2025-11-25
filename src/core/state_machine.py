class StateMachine:
    """
    Gestor de la pila de estados del juego.
    Permite navegar entre pantallas (Welcome -> CharSelect -> Gameplay)
    y delega los ciclos de actualización y renderizado al estado activo.
    """

    def __init__(self):
        self.states = []

    def push(self, state):
        """Agrega un nuevo estado a la pila y lo activa."""
        self.states.append(state)
        if hasattr(state, 'enter'):
            state.enter()

    def pop(self):
        """Remueve el estado actual y regresa al anterior."""
        if self.states:
            state = self.states.pop()
            if hasattr(state, 'exit'):
                state.exit()

    def change(self, state):
        """Reemplaza el estado actual por uno nuevo (pop + push)."""
        if self.states:
            self.pop()
        self.push(state)

    def update(self, dt):
        """Delega la actualización lógica al estado en el tope de la pila."""
        if self.states:
            self.states[-1].update(dt)

    def draw(self):
        """Delega el renderizado al estado en el tope de la pila."""
        if self.states:
            self.states[-1].draw()

    def handle_input(self, event, x, y):
        """Delega el manejo de entrada al estado en el tope de la pila."""
        if self.states:
            self.states[-1].handle_input(event, x, y)

    def get_current_state(self):
        if self.states:
            return self.states[-1]
        return None
