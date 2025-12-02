from src.states.gameplay_state import GameplayState
from src.states.welcome_state import WelcomeState
from src.core.window_manager import WindowManager
from src.core.transition_manager import get_transition_manager
import sys
import os

# Aseguramos que el directorio raíz del proyecto esté en el path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # 1. Instanciar WindowManager
    window = WindowManager(

        title="Solar Explorer", width=3000, height=2000)

    # 2. Inicializar subsistemas (GLUT, OpenGL)
    window.initialize()

    # 3. Start with the Welcome State (Title Screen) - push without transition
    welcome_state = WelcomeState()
    window.state_machine.push_immediate(welcome_state)

    # 4. Start with a fade-in from black
    transition = get_transition_manager()
    transition.start_fade_in(duration=0.8)

    # 5. Iniciar el bucle principal
    window.start_main_loop()


if __name__ == "__main__":
    main()
