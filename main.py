from src.states.gameplay_state import GameplayState
from src.states.welcome_state import WelcomeState
from src.core.window_manager import WindowManager
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

    # 3. Start with the Welcome State (Title Screen)
    welcome_state = WelcomeState()
    window.state_machine.push(welcome_state)

    # 4. Iniciar el bucle principal
    window.start_main_loop()


if __name__ == "__main__":
    main()
