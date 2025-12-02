from src.core.transition_manager import get_transition_manager


class StateMachine:
    """
    Gestor de la pila de estados del juego.
    Permite navegar entre pantallas (Welcome -> CharSelect -> Gameplay)
    y delega los ciclos de actualización y renderizado al estado activo.

    Supports smooth fade transitions between states.
    """

    def __init__(self):
        self.states = []
        self.transition = get_transition_manager()

        # Pending state operations (executed during transition)
        self._pending_push = None
        self._pending_pop = False
        self._pending_change = None

    def push(self, state, use_transition=True, duration=0.5):
        """
        Agrega un nuevo estado a la pila y lo activa.

        Args:
            state: The state to push
            use_transition: If True, use fade transition
            duration: Total transition duration (fade out + fade in)
        """
        if use_transition and not self.transition.is_transitioning():
            self._pending_push = state
            self.transition.start_transition(
                duration=duration,
                on_midpoint=self._execute_pending_push
            )
        else:
            self._direct_push(state)

    def _direct_push(self, state):
        """Push state without transition."""
        self.states.append(state)
        if hasattr(state, 'enter'):
            state.enter()

    def _execute_pending_push(self):
        """Execute pending push at transition midpoint."""
        if self._pending_push:
            self._direct_push(self._pending_push)
            self._pending_push = None

    def pop(self, use_transition=True, duration=0.5):
        """
        Remueve el estado actual y regresa al anterior.

        Args:
            use_transition: If True, use fade transition
            duration: Total transition duration
        """
        if use_transition and not self.transition.is_transitioning():
            self._pending_pop = True
            self.transition.start_transition(
                duration=duration,
                on_midpoint=self._execute_pending_pop
            )
        else:
            self._direct_pop()

    def _direct_pop(self):
        """Pop state without transition."""
        if self.states:
            state = self.states.pop()
            if hasattr(state, 'exit'):
                state.exit()

    def _execute_pending_pop(self):
        """Execute pending pop at transition midpoint."""
        if self._pending_pop:
            self._direct_pop()
            self._pending_pop = False

    def change(self, state, use_transition=True, duration=0.5):
        """
        Reemplaza el estado actual por uno nuevo (pop + push).

        Args:
            state: The new state to change to
            use_transition: If True, use fade transition
            duration: Total transition duration
        """
        if use_transition and not self.transition.is_transitioning():
            self._pending_change = state
            self.transition.start_transition(
                duration=duration,
                on_midpoint=self._execute_pending_change
            )
        else:
            self._direct_change(state)

    def _direct_change(self, state):
        """Change state without transition."""
        if self.states:
            self._direct_pop()
        self._direct_push(state)

    def _execute_pending_change(self):
        """Execute pending change at transition midpoint."""
        if self._pending_change:
            self._direct_change(self._pending_change)
            self._pending_change = None

    def update(self, dt):
        """Delega la actualización lógica al estado en el tope de la pila."""
        # Update transition
        self.transition.update(dt)

        if self.states:
            self.states[-1].update(dt)

    def draw(self):
        """Delega el renderizado al estado en el tope de la pila."""
        if self.states:
            self.states[-1].draw()

        # Draw transition overlay LAST (on top of everything)
        from OpenGL.GLUT import glutGet, GLUT_WINDOW_WIDTH, GLUT_WINDOW_HEIGHT
        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)
        self.transition.draw(w, h)

    def handle_input(self, event, x, y):
        """Delega el manejo de entrada al estado en el tope de la pila."""
        # Block input during transitions
        if self.transition.is_transitioning():
            return

        if self.states:
            self.states[-1].handle_input(event, x, y)

    def get_current_state(self):
        if self.states:
            return self.states[-1]
        return None

    # Convenience methods for non-transition operations
    def push_immediate(self, state):
        """Push state without transition."""
        self._direct_push(state)

    def pop_immediate(self):
        """Pop state without transition."""
        self._direct_pop()

    def change_immediate(self, state):
        """Change state without transition."""
        self._direct_change(state)
