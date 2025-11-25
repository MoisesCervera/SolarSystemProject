class InputManager:
    """
    Singleton que gestiona el estado de las teclas para permitir
    pulsaciones simultáneas y movimiento fluido.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InputManager, cls).__new__(cls)
            cls._instance.key_state = {}
            cls._instance.special_key_state = {}
        return cls._instance

    def key_down(self, key, x, y):
        """Registra que una tecla normal ha sido presionada."""
        # Convertir bytes a string si es necesario
        if isinstance(key, bytes):
            try:
                key = key.decode('utf-8').lower()
            except:
                pass
        self.key_state[key] = True

    def key_up(self, key, x, y):
        """Registra que una tecla normal ha sido soltada."""
        if isinstance(key, bytes):
            try:
                key = key.decode('utf-8').lower()
            except:
                pass
        self.key_state[key] = False

    def special_key_down(self, key, x, y):
        """Registra que una tecla especial (flechas, F1, etc) ha sido presionada."""
        self.special_key_state[key] = True

    def special_key_up(self, key, x, y):
        """Registra que una tecla especial ha sido soltada."""
        self.special_key_state[key] = False

    def is_key_pressed(self, key):
        """Retorna True si la tecla está presionada."""
        key = key.lower()
        return self.key_state.get(key, False)

    def is_special_key_pressed(self, key):
        """Retorna True si la tecla especial está presionada."""
        return self.special_key_state.get(key, False)
