from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.ui_renderer import UIRenderer
import math


class PauseState(BaseState):
    """
    Pause menu state with options to resume, return to main menu, or quit.
    This state is pushed on top of the current state and renders a semi-transparent overlay.
    """

    def __init__(self):
        self.animation_time = 0.0
        self.selected_option = 0  # 0=Resume, 1=Main Menu, 2=Quit
        self.options = ["RESUME", "MAIN MENU", "QUIT GAME"]
        self.fade_in = 0.0  # For smooth fade-in effect

    def enter(self):
        print("[PauseState] Game paused")
        self.fade_in = 0.0

    def exit(self):
        print("[PauseState] Resuming game")

    def update(self, dt):
        self.animation_time += dt
        # Smooth fade-in
        if self.fade_in < 1.0:
            self.fade_in += dt * 3.0
            if self.fade_in > 1.0:
                self.fade_in = 1.0

    def draw(self):
        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Setup 2D rendering
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, w, 0, h)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        # Draw semi-transparent dark overlay
        self._draw_overlay(w, h)

        # Draw pause menu box
        self._draw_menu_box(w, h)

        # Draw title
        self._draw_title(w, h)

        # Draw options
        self._draw_options(w, h)

        # Draw controls hint
        self._draw_controls(w, h)

        # Restore state
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def handle_input(self, event, x, y):
        if event[0] == 'KEY_DOWN':
            key = event[1]

            # ESC to resume
            if key == b'\x1b':
                self._resume()
                return

            # Enter to select current option
            if key == b'\r' or key == b' ':
                self._select_option()
                return

            # Navigation with W/S or number keys
            if key == b'w' or key == b'W':
                self.selected_option = (
                    self.selected_option - 1) % len(self.options)
            elif key == b's' or key == b'S':
                self.selected_option = (
                    self.selected_option + 1) % len(self.options)
            elif key == b'1':
                self.selected_option = 0
                self._select_option()
            elif key == b'2':
                self.selected_option = 1
                self._select_option()
            elif key == b'3':
                self.selected_option = 2
                self._select_option()
            # R for resume shortcut
            elif key == b'r' or key == b'R':
                self._resume()
            # M for main menu shortcut
            elif key == b'm' or key == b'M':
                self._go_to_main_menu()
            # Q for quit shortcut
            elif key == b'q' or key == b'Q':
                self._quit_game()

        elif event[0] == 'SPECIAL_KEY_DOWN':
            key = event[1]
            # Arrow key navigation
            if key == GLUT_KEY_UP:
                self.selected_option = (
                    self.selected_option - 1) % len(self.options)
            elif key == GLUT_KEY_DOWN:
                self.selected_option = (
                    self.selected_option + 1) % len(self.options)

    def _resume(self):
        """Resume the game by popping this state."""
        if hasattr(self, 'state_machine'):
            self.state_machine.pop()

    def _go_to_main_menu(self):
        """Return to the main menu (welcome state)."""
        if hasattr(self, 'state_machine'):
            # Import here to avoid circular imports
            from src.states.welcome_state import WelcomeState
            # Clear the entire state stack and push welcome state
            while self.state_machine.states:
                self.state_machine.pop()
            self.state_machine.push(WelcomeState())

    def _quit_game(self):
        """Quit the game entirely."""
        import os
        os._exit(0)

    def _select_option(self):
        """Execute the currently selected option."""
        if self.selected_option == 0:
            self._resume()
        elif self.selected_option == 1:
            self._go_to_main_menu()
        elif self.selected_option == 2:
            self._quit_game()

    def _draw_overlay(self, w, h):
        """Draw semi-transparent dark overlay."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Dark overlay with fade-in
        alpha = 0.7 * self.fade_in
        glColor4f(0.0, 0.0, 0.05, alpha)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(w, 0)
        glVertex2f(w, h)
        glVertex2f(0, h)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_menu_box(self, w, h):
        """Draw the central menu box."""
        box_width = 400
        box_height = 350
        box_x = (w - box_width) / 2
        box_y = (h - box_height) / 2

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Main box background
        alpha = 0.85 * self.fade_in
        glColor4f(0.02, 0.05, 0.08, alpha)
        chamfer = 20
        glBegin(GL_POLYGON)
        glVertex2f(box_x + chamfer, box_y)
        glVertex2f(box_x + box_width - chamfer, box_y)
        glVertex2f(box_x + box_width, box_y + chamfer)
        glVertex2f(box_x + box_width, box_y + box_height - chamfer)
        glVertex2f(box_x + box_width - chamfer, box_y + box_height)
        glVertex2f(box_x + chamfer, box_y + box_height)
        glVertex2f(box_x, box_y + box_height - chamfer)
        glVertex2f(box_x, box_y + chamfer)
        glEnd()

        # Glowing border
        pulse = 0.5 + 0.3 * math.sin(self.animation_time * 2)
        glLineWidth(2.0)
        glColor4f(0.0, pulse * self.fade_in,
                  pulse * self.fade_in, self.fade_in)
        glBegin(GL_LINE_LOOP)
        glVertex2f(box_x + chamfer, box_y)
        glVertex2f(box_x + box_width - chamfer, box_y)
        glVertex2f(box_x + box_width, box_y + chamfer)
        glVertex2f(box_x + box_width, box_y + box_height - chamfer)
        glVertex2f(box_x + box_width - chamfer, box_y + box_height)
        glVertex2f(box_x + chamfer, box_y + box_height)
        glVertex2f(box_x, box_y + box_height - chamfer)
        glVertex2f(box_x, box_y + chamfer)
        glEnd()

        # Inner glow line
        inner_offset = 8
        glLineWidth(1.0)
        glColor4f(0.0, pulse * 0.3 * self.fade_in, pulse *
                  0.3 * self.fade_in, self.fade_in * 0.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(box_x + chamfer + inner_offset, box_y + inner_offset)
        glVertex2f(box_x + box_width - chamfer -
                   inner_offset, box_y + inner_offset)
        glVertex2f(box_x + box_width - inner_offset,
                   box_y + chamfer + inner_offset)
        glVertex2f(box_x + box_width - inner_offset, box_y +
                   box_height - chamfer - inner_offset)
        glVertex2f(box_x + box_width - chamfer - inner_offset,
                   box_y + box_height - inner_offset)
        glVertex2f(box_x + chamfer + inner_offset,
                   box_y + box_height - inner_offset)
        glVertex2f(box_x + inner_offset, box_y +
                   box_height - chamfer - inner_offset)
        glVertex2f(box_x + inner_offset, box_y + chamfer + inner_offset)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_title(self, w, h):
        """Draw PAUSED title."""
        title = "PAUSED"
        title_size = 60
        char_width = title_size * 0.6
        title_width = len(title) * char_width
        title_x = (w - title_width) / 2
        title_y = h / 2 + 100

        # Glow effect
        pulse = 0.7 + 0.3 * math.sin(self.animation_time * 2)
        glow_alpha = 0.3 * self.fade_in
        for i in range(3):
            offset = (3 - i) * 2
            UIRenderer.draw_text(title_x - offset, title_y - offset, title,
                                 size=title_size, color=(0.0, glow_alpha / (i + 1), glow_alpha / (i + 1)))

        # Main title
        cyan = pulse * self.fade_in
        UIRenderer.draw_text(title_x, title_y, title, size=title_size,
                             color=(0.0, cyan, cyan))

    def _draw_options(self, w, h):
        """Draw menu options."""
        start_y = h / 2 + 20
        spacing = 60

        for i, option in enumerate(self.options):
            opt_size = 28
            char_width = opt_size * 0.55
            opt_width = len(option) * char_width
            opt_x = (w - opt_width) / 2
            opt_y = start_y - i * spacing

            is_selected = (i == self.selected_option)

            if is_selected:
                # Draw selection highlight
                self._draw_selection_highlight(w, opt_y, opt_size)

                # Selected option - bright cyan with glow
                pulse = 0.8 + 0.2 * math.sin(self.animation_time * 4)
                # Glow
                UIRenderer.draw_text(opt_x + 2, opt_y - 2, option,
                                     size=opt_size, color=(0.0, 0.3 * self.fade_in, 0.3 * self.fade_in))
                # Main text
                UIRenderer.draw_text(opt_x, opt_y, option,
                                     size=opt_size, color=(0.0, pulse * self.fade_in, pulse * self.fade_in))

                # Draw arrows
                arrow_offset = 15 + 5 * math.sin(self.animation_time * 5)
                UIRenderer.draw_text(opt_x - 40 - arrow_offset, opt_y, ">",
                                     size=opt_size, color=(0.0, pulse * self.fade_in, pulse * self.fade_in))
                UIRenderer.draw_text(opt_x + opt_width + 20 + arrow_offset, opt_y, "<",
                                     size=opt_size, color=(0.0, pulse * self.fade_in, pulse * self.fade_in))
            else:
                # Non-selected option - dimmer
                dim = 0.4 * self.fade_in
                UIRenderer.draw_text(opt_x, opt_y, option,
                                     size=opt_size, color=(dim, dim, dim))

    def _draw_selection_highlight(self, w, y, size):
        """Draw a subtle highlight behind the selected option."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        highlight_width = 300
        highlight_height = size + 20
        highlight_x = (w - highlight_width) / 2
        highlight_y = y - 8

        # Gradient highlight
        pulse = 0.15 + 0.05 * math.sin(self.animation_time * 3)
        glBegin(GL_QUADS)
        glColor4f(0.0, pulse * self.fade_in, pulse * self.fade_in, 0.0)
        glVertex2f(highlight_x, highlight_y)
        glColor4f(0.0, pulse * self.fade_in, pulse *
                  self.fade_in, pulse * self.fade_in)
        glVertex2f(highlight_x + highlight_width / 2, highlight_y)
        glColor4f(0.0, pulse * self.fade_in, pulse *
                  self.fade_in, pulse * self.fade_in)
        glVertex2f(highlight_x + highlight_width /
                   2, highlight_y + highlight_height)
        glColor4f(0.0, pulse * self.fade_in, pulse * self.fade_in, 0.0)
        glVertex2f(highlight_x, highlight_y + highlight_height)
        glEnd()

        glBegin(GL_QUADS)
        glColor4f(0.0, pulse * self.fade_in, pulse *
                  self.fade_in, pulse * self.fade_in)
        glVertex2f(highlight_x + highlight_width / 2, highlight_y)
        glColor4f(0.0, pulse * self.fade_in, pulse * self.fade_in, 0.0)
        glVertex2f(highlight_x + highlight_width, highlight_y)
        glColor4f(0.0, pulse * self.fade_in, pulse * self.fade_in, 0.0)
        glVertex2f(highlight_x + highlight_width,
                   highlight_y + highlight_height)
        glColor4f(0.0, pulse * self.fade_in, pulse *
                  self.fade_in, pulse * self.fade_in)
        glVertex2f(highlight_x + highlight_width /
                   2, highlight_y + highlight_height)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_controls(self, w, h):
        """Draw control hints at the bottom."""
        pass
