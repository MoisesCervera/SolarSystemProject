from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import os
import time
from src.core.state_machine import StateMachine
from src.core.session import GameContext
from src.core.input_manager import InputManager
from src.states.pause_state import PauseState


class WindowManager:
    """
    Encargado de crear la ventana, inicializar el contexto OpenGL/GLUT
    y gestionar el bucle principal (Main Loop).
    """

    def __init__(self, title="Solar Explorer", width=1024, height=768):
        self.title = title
        self.width = width
        self.height = height
        self.window_id = None
        self.should_exit = False

        # Componentes Core
        self.state_machine = StateMachine()
        self.session = GameContext()
        self.input_manager = InputManager()

        # Control de tiempo
        self.last_time = 0
        
        # FPS tracking and limiting
        self.target_fps = 60
        self.target_frame_time = 1.0 / self.target_fps
        self.fps = 0
        self.frame_count = 0
        self.fps_timer = 0.0

    def initialize(self):
        """Configura GLUT, crea la ventana y establece los callbacks."""
        glutInit(sys.argv)
        glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

        # Start in fullscreen mode
        glutInitWindowSize(self.width, self.height)
        glutInitWindowPosition(0, 0)

        self.window_id = glutCreateWindow(self.title.encode('ascii'))

        # Enter fullscreen mode
        glutFullScreen()

        # Configuración inicial de OpenGL
        glEnable(GL_DEPTH_TEST)       # Z-Buffer
        glEnable(GL_CULL_FACE)        # Optimización: no dibujar caras traseras
        glEnable(GL_LIGHTING)         # Iluminación
        glEnable(GL_LIGHT0)           # Luz por defecto
        glEnable(GL_COLOR_MATERIAL)   # Materiales usan color actual
        # Normalizar vectores para iluminación correcta
        glEnable(GL_NORMALIZE)

        # Color de fondo (Negro espacio)
        glClearColor(0.0, 0.0, 0.0, 1.0)

        # Asignar Callbacks de GLUT
        glutDisplayFunc(self._display_callback)
        glutIdleFunc(self._idle_callback)
        glutReshapeFunc(self._reshape_callback)

        # Callbacks de teclado mejorados (InputManager)
        glutKeyboardFunc(self._keyboard_down_callback)
        glutKeyboardUpFunc(self._keyboard_up_callback)
        glutSpecialFunc(self._special_down_callback)
        glutSpecialUpFunc(self._special_up_callback)

        glutMouseFunc(self._mouse_callback)
        glutMotionFunc(self._motion_callback)

        print(
            f"[WindowManager] Sistema inicializado. OpenGL Version: {glGetString(GL_VERSION).decode()}")

    def start_main_loop(self):
        """Inicia el bucle de eventos de GLUT."""
        self.last_time = time.time()
        print("[WindowManager] Iniciando bucle principal...")
        glutMainLoop()

    def _display_callback(self):
        """Callback de renderizado (se llama cuando GLUT necesita redibujar)."""
        # 1. Limpiar buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # 2. Dibujar estado actual
        # Nota: El estado es responsable de configurar la cámara si es necesario
        self.state_machine.draw()

        # 3. Intercambiar buffers (Double Buffering)
        glutSwapBuffers()

    def _idle_callback(self):
        """Callback de actualización (se llama cuando no hay eventos pendientes)."""
        # Check for exit flag first
        if self.should_exit:
            # Use os._exit(0) to terminate immediately without cleanup
            # This avoids the SystemExit exception in ctypes callbacks
            # and prevents segfaults from glutDestroyWindow on macOS
            os._exit(0)

        current_time = time.time()
        
        # FPS limiting - skip this frame if not enough time has passed
        time_since_last_frame = current_time - self.last_time
        if time_since_last_frame < self.target_frame_time:
            return  # Don't process this frame yet
        
        dt = time_since_last_frame
        self.last_time = current_time

        # Evitar saltos grandes de tiempo (spiral of death prevention simple)
        if dt > 0.1:
            dt = 0.1

        # FPS tracking
        self.frame_count += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.fps_timer -= 1.0

        # Actualizar lógica del estado actual
        # Inyectar state_machine al estado actual si no la tiene (Hack para navegación)
        current_state = self.state_machine.get_current_state()
        if current_state and not hasattr(current_state, 'state_machine'):
            current_state.state_machine = self.state_machine
        
        # Pass FPS to current state for display
        if current_state:
            current_state.current_fps = self.fps

        self.state_machine.update(dt)

        # Solicitar redibujado forzoso
        glutPostRedisplay()

    def _reshape_callback(self, w, h):
        """Maneja el redimensionamiento de la ventana."""
        if h == 0:
            h = 1
        self.width = w
        self.height = h

        glViewport(0, 0, w, h)

        # Configuración de la cámara por defecto (Perspectiva)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / h, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def _keyboard_down_callback(self, key, x, y):
        """Tecla presionada."""
        if key == b'\x1b':  # ESC to open pause menu
            # Check if we're already in pause state or welcome state
            current_state = self.state_machine.get_current_state()
            current_type = type(
                current_state).__name__ if current_state else ""

            # If in pause state, let it handle ESC (to resume)
            if current_type == "PauseState":
                self.state_machine.handle_input(('KEY_DOWN', key), x, y)
                return

            # Don't pause on welcome screen - it handles its own navigation
            if current_type == "WelcomeState":
                return

            # Don't pause when player is dead (showing restart menu)
            if current_type == "GameplayState":
                if hasattr(current_state, 'is_dead') and current_state.is_dead:
                    return
                if hasattr(current_state, 'asteroid_impact_pending') and current_state.asteroid_impact_pending:
                    return

            # Push pause state on top of current state
            pause_state = PauseState()
            pause_state.state_machine = self.state_machine
            self.state_machine.push(pause_state)
            return
        self.input_manager.key_down(key, x, y)
        # Forward event to state machine
        self.state_machine.handle_input(('KEY_DOWN', key), x, y)

    def _keyboard_up_callback(self, key, x, y):
        """Tecla soltada."""
        self.input_manager.key_up(key, x, y)
        self.state_machine.handle_input(('KEY_UP', key), x, y)

    def _special_down_callback(self, key, x, y):
        """Tecla especial presionada."""
        self.input_manager.special_key_down(key, x, y)
        # Forward special key to state machine
        self.state_machine.handle_input(('SPECIAL_KEY_DOWN', key), x, y)

    def _special_up_callback(self, key, x, y):
        """Tecla especial soltada."""
        self.input_manager.special_key_up(key, x, y)
        self.state_machine.handle_input(('SPECIAL_KEY_UP', key), x, y)

    def _mouse_callback(self, button, state, x, y):
        """Callback para clics del mouse."""
        # Pasamos el evento como una tupla ('MOUSE_BUTTON', button, state)
        self.state_machine.handle_input(('MOUSE_BUTTON', button, state), x, y)

    def _motion_callback(self, x, y):
        """Callback para movimiento del mouse (arrastrando)."""
        # Pasamos el evento como una tupla ('MOUSE_MOTION',)
        self.state_machine.handle_input(('MOUSE_MOTION',), x, y)
