class GameContext:
    """
    Singleton que mantiene el estado global de la sesión de juego.
    Actúa como una 'pizarra' compartida entre los diferentes estados y entidades.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameContext, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.reset()

    def reset(self):
        """Reinicia los datos de la sesión a sus valores por defecto."""
        # ID del personaje/nave seleccionado (0, 1, 2)
        self.selected_character_id = 0

        # Planeta objetivo actual (para visitar/escanear)
        self.target_planet = None

        # Aquí podemos agregar más estado global:
        # self.score = 0
        # self.current_level = 1
        # self.is_paused = False

    def set_character(self, char_id):
        self.selected_character_id = char_id
        print(f"[Session] Personaje seleccionado: {char_id}")
