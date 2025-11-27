"""
Game Complete State - Victory screen displayed when all missions are completed.
"""
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.ui_renderer import UIRenderer
from src.graphics.skybox import Skybox
from src.graphics.texture_loader import TextureLoader
from src.core.mission_manager import MissionManager, get_trophy_for_planet
from src.entities.trophies.trophy_base import TrophyRenderer
import math


class GameCompleteState(BaseState):
    """
    Victory screen state - shown when all planets have been visited and quizzes completed.
    Displays all collected trophies and final stats.
    """

    def __init__(self):
        self.mission_manager = MissionManager()
        self.trophy_renderer = None
        self.skybox = None

        # Animation
        self.time = 0.0
        self.stars_angle = 0.0
        self.trophy_rotation = 0.0

        # Trophy display
        self.trophies = []
        self.selected_trophy = 0

    def enter(self):
        print("[GameCompleteState] Entering victory screen!")

        # Load skybox
        bg_texture = TextureLoader.load_texture(
            "assets/textures/background/stars.jpg")
        self.skybox = Skybox(size=300.0, texture_id=bg_texture)

        # Initialize trophy renderer
        self.trophy_renderer = TrophyRenderer()

        # Get all earned trophies
        self.trophies = list(self.mission_manager.get_all_trophies().keys())
        if not self.trophies:
            # Fallback - get from mission order if trophies dict is empty
            self.trophies = self.mission_manager.mission_order.copy()

        print(f"[GameCompleteState] Displaying {len(self.trophies)} trophies")

    def exit(self):
        if self.trophy_renderer:
            self.trophy_renderer.cleanup()

    def update(self, dt):
        self.time += dt
        self.stars_angle += dt * 2.0
        self.trophy_rotation += dt * 30.0

        if self.trophy_rotation >= 360:
            self.trophy_rotation -= 360

        # Update trophy animations
        if self.trophy_renderer:
            self.trophy_renderer.update_all(dt)

    def handle_input(self, event, x, y):
        if event[0] == 'KEY_DOWN':
            key = event[1]

            # Navigate trophies
            if key == GLUT_KEY_LEFT or key == b'a':
                self.selected_trophy = (
                    self.selected_trophy - 1) % max(1, len(self.trophies))
            elif key == GLUT_KEY_RIGHT or key == b'd':
                self.selected_trophy = (
                    self.selected_trophy + 1) % max(1, len(self.trophies))

            # Return to main menu
            elif key == b'\r' or key == b' ' or key == b'm' or key == b'M':
                if hasattr(self, 'state_machine'):
                    from src.states.welcome_state import WelcomeState
                    # Reset mission manager for new game
                    self.mission_manager.reset()
                    # Clear states and go to welcome
                    while self.state_machine.states:
                        self.state_machine.pop()
                    self.state_machine.push(WelcomeState())

    def draw(self):
        glClearColor(0.0, 0.0, 0.05, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Setup 3D for skybox and trophies
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / max(1, h), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Camera looking at trophy showcase
        gluLookAt(0, 2, 10,  0, 1, 0,  0, 1, 0)

        # Draw rotating skybox
        glPushMatrix()
        glRotatef(self.stars_angle, 0, 1, 0)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        if self.skybox:
            self.skybox.draw()
        glEnable(GL_DEPTH_TEST)
        glPopMatrix()

        # Draw 3D trophies
        self._draw_trophy_showcase()

        # Draw UI overlay
        self._draw_ui(w, h)

    def _draw_trophy_showcase(self):
        """Draw 3D trophy models in a showcase arrangement."""
        if not self.trophy_renderer or not self.trophies:
            return

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # Set up dramatic lighting
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.8, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

        # Draw selected trophy larger in center
        if 0 <= self.selected_trophy < len(self.trophies):
            planet = self.trophies[self.selected_trophy]
            glPushMatrix()
            glTranslatef(0, 1.5, 0)
            self.trophy_renderer.render_trophy(
                planet, 0, 0, 0, 2.5, self.trophy_rotation)
            glPopMatrix()

        # Draw other trophies smaller around the main one
        num_trophies = len(self.trophies)
        if num_trophies > 1:
            for i, planet in enumerate(self.trophies):
                if i == self.selected_trophy:
                    continue

                # Calculate position in arc
                relative_idx = i - self.selected_trophy
                if relative_idx > num_trophies // 2:
                    relative_idx -= num_trophies
                elif relative_idx < -num_trophies // 2:
                    relative_idx += num_trophies

                x_pos = relative_idx * 1.8
                z_pos = abs(relative_idx) * 0.5
                scale = max(0.3, 1.0 - abs(relative_idx) * 0.15)
                alpha = max(0.3, 1.0 - abs(relative_idx) * 0.2)

                glPushMatrix()
                glTranslatef(x_pos, 0, z_pos)
                self.trophy_renderer.render_trophy(
                    planet, 0, 0, 0, scale, self.trophy_rotation * 0.5)
                glPopMatrix()

        glDisable(GL_LIGHTING)

    def _draw_ui(self, w, h):
        """Draw 2D UI elements."""
        UIRenderer.setup_2d(w, h)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Title with glow effect
        pulse = 0.8 + 0.2 * math.sin(self.time * 3)
        title = "MISSION ACCOMPLISHED"
        title_size = 48
        title_width = len(title) * title_size * 0.55
        UIRenderer.draw_text((w - title_width) / 2, h - 80, title,
                             size=title_size, color=(pulse, 0.8 * pulse, 0.0))

        # Subtitle
        subtitle = "You have explored the entire Solar System!"
        sub_size = 22
        sub_width = len(subtitle) * sub_size * 0.5
        UIRenderer.draw_text((w - sub_width) / 2, h - 130, subtitle,
                             size=sub_size, color=(0.8, 0.8, 0.8))

        # Stats box
        stats_x = w / 2 - 200
        stats_y = 180
        stats_w = 400
        stats_h = 120

        glColor4f(0.0, 0.1, 0.2, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(stats_x, stats_y)
        glVertex2f(stats_x + stats_w, stats_y)
        glVertex2f(stats_x + stats_w, stats_y + stats_h)
        glVertex2f(stats_x, stats_y + stats_h)
        glEnd()

        glColor3f(0.0, 0.8, 1.0)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(stats_x, stats_y)
        glVertex2f(stats_x + stats_w, stats_y)
        glVertex2f(stats_x + stats_w, stats_y + stats_h)
        glVertex2f(stats_x, stats_y + stats_h)
        glEnd()

        # Stats content
        planets_visited = len(self.trophies)
        trophies_earned = planets_visited

        UIRenderer.draw_text(stats_x + 20, stats_y + stats_h - 35, "FINAL STATISTICS",
                             size=18, color=(0.0, 1.0, 1.0))

        UIRenderer.draw_text(stats_x + 20, stats_y + stats_h - 70,
                             f"Planets Explored: {planets_visited} of 9",
                             size=16, color=(0.9, 0.9, 0.9))

        UIRenderer.draw_text(stats_x + 20, stats_y + stats_h - 95,
                             f"Trophies Collected: {trophies_earned} of 9",
                             size=16, color=(1.0, 0.8, 0.2))

        # Selected trophy info
        if self.trophies and 0 <= self.selected_trophy < len(self.trophies):
            planet = self.trophies[self.selected_trophy]
            trophy_type = get_trophy_for_planet(planet)
            trophy_name = trophy_type.replace('_', ' ').title()

            info_text = f"{planet} - {trophy_name}"
            info_size = 20
            info_width = len(info_text) * info_size * 0.5
            UIRenderer.draw_text((w - info_width) / 2, 340, info_text,
                                 size=info_size, color=(1.0, 0.8, 0.2))

        # Navigation hints
        nav_text = "A D - Navigate Trophies"
        nav_size = 16
        nav_width = len(nav_text) * nav_size * 0.5
        UIRenderer.draw_text((w - nav_width) / 2, 100, nav_text,
                             size=nav_size, color=(0.6, 0.6, 0.6))

        # Return instruction
        return_text = "Press SPACE or ENTER for Main Menu"
        ret_size = 18
        ret_width = len(return_text) * ret_size * 0.5
        UIRenderer.draw_text((w - ret_width) / 2, 50, return_text,
                             size=ret_size, color=(0.0, 0.8, 1.0))

        glDisable(GL_BLEND)
        UIRenderer.restore_3d()
