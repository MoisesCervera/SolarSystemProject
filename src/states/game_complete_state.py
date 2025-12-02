"""
Game Complete State - Victory screen displayed when all missions are completed.
"""
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.ui_renderer import UIRenderer
from src.graphics.skybox import Skybox
from src.core.resource_loader import ResourceManager
from src.core.mission_manager import MissionManager, get_trophy_for_planet
from src.entities.trophies.trophy_base import TrophyRenderer
import math
import random


class GameCompleteState(BaseState):
    """
    Victory screen state - shown when all planets have been visited and quizzes completed.
    Displays all collected trophies and final stats with a high-tech sci-fi aesthetic.
    """

    def __init__(self):
        self.mission_manager = MissionManager()
        self.trophy_renderer = None
        self.skybox = None

        # Animation
        self.time = 0.0
        self.stars_angle = 0.0
        self.trophy_rotation = 0.0

        # Particles for background effect
        self.particles = []
        self.num_particles = 200

        # Trophy display
        self.trophies = []
        self.selected_trophy = 0

        # UI Animation
        self.text_reveal_timer = 0.0
        self.scan_line_y = 0.0

    def enter(self):
        print("[GameCompleteState] Entering victory screen!")

        # Load skybox
        bg_texture = ResourceManager.load_texture("background/stars.jpg")
        self.skybox = Skybox(size=300.0, texture_id=bg_texture)

        # Initialize trophy renderer
        self.trophy_renderer = TrophyRenderer()

        # Get all earned trophies
        self.trophies = list(self.mission_manager.get_all_trophies().keys())
        if not self.trophies:
            # Fallback - get from mission order if trophies dict is empty
            self.trophies = self.mission_manager.mission_order.copy()

        print(f"[GameCompleteState] Displaying {len(self.trophies)} trophies")

        # Initialize particles
        self._init_particles()

    def _init_particles(self):
        self.particles = []
        for _ in range(self.num_particles):
            self.particles.append({
                'x': random.uniform(-50, 50),
                'y': random.uniform(-30, 30),
                'z': random.uniform(-50, 0),
                'speed': random.uniform(10, 30),
                'size': random.uniform(0.1, 0.3),
                'color': (random.uniform(0.5, 1.0), random.uniform(0.8, 1.0), 1.0)
            })

    def exit(self):
        if self.trophy_renderer:
            self.trophy_renderer.cleanup()

    def update(self, dt):
        self.time += dt
        self.stars_angle += dt * 2.0
        self.trophy_rotation += dt * 30.0
        self.text_reveal_timer += dt

        # Scan line animation
        self.scan_line_y += dt * 0.5
        if self.scan_line_y > 1.0:
            self.scan_line_y = 0.0

        if self.trophy_rotation >= 360:
            self.trophy_rotation -= 360

        # Update trophy animations
        if self.trophy_renderer:
            self.trophy_renderer.update_all(dt)

        # Update particles
        for p in self.particles:
            p['z'] += p['speed'] * dt
            if p['z'] > 10:
                p['z'] = random.uniform(-100, -50)
                p['x'] = random.uniform(-50, 50)
                p['y'] = random.uniform(-30, 30)

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

        # Draw particles
        self._draw_particles()

        # Draw 3D trophies
        self._draw_trophy_showcase()

        # Draw UI overlay
        self._draw_ui(w, h)

    def _draw_particles(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glBegin(GL_POINTS)
        for p in self.particles:
            glColor3f(*p['color'])
            glVertex3f(p['x'], p['y'], p['z'])
        glEnd()

        # Draw speed lines
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for p in self.particles:
            if p['z'] > -40:  # Only draw trails for closer particles
                alpha = min(1.0, (p['z'] + 50) / 50.0) * 0.5
                glColor4f(p['color'][0], p['color'][1], p['color'][2], alpha)
                glVertex3f(p['x'], p['y'], p['z'])
                glVertex3f(p['x'], p['y'], p['z'] - p['speed'] * 0.1)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_trophy_showcase(self):
        """Draw 3D trophy models in a showcase arrangement."""
        if not self.trophy_renderer or not self.trophies:
            return

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        # Set up dramatic lighting
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.95, 0.8, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

        # Draw holographic platform
        self._draw_holographic_platform()

        # Draw selected trophy larger in center
        if 0 <= self.selected_trophy < len(self.trophies):
            planet = self.trophies[self.selected_trophy]
            glPushMatrix()
            glTranslatef(0, 1.5, 0)

            # Bobbing animation
            bob = math.sin(self.time * 2.0) * 0.1
            glTranslatef(0, bob, 0)

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

                # Only draw if within visible range
                if abs(relative_idx) > 3:
                    continue

                x_pos = relative_idx * 2.5
                z_pos = abs(relative_idx) * 1.0 - 2.0
                scale = max(0.3, 1.0 - abs(relative_idx) * 0.2)

                glPushMatrix()
                glTranslatef(x_pos, 0.5, z_pos)
                self.trophy_renderer.render_trophy(
                    planet, 0, 0, 0, scale, self.trophy_rotation * 0.5)
                glPopMatrix()

        glDisable(GL_LIGHTING)

    def _draw_holographic_platform(self):
        """Draws a sci-fi platform under the main trophy."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDisable(GL_LIGHTING)

        glPushMatrix()
        glTranslatef(0, 0.5, 0)
        glRotatef(self.time * 10, 0, 1, 0)

        # Rings
        for i in range(3):
            radius = 1.5 + i * 0.5
            alpha = 0.6 - i * 0.15
            glColor4f(0.0, 0.8, 1.0, alpha)

            glBegin(GL_LINE_LOOP)
            segments = 32
            for j in range(segments):
                theta = 2.0 * math.pi * j / segments
                x = radius * math.cos(theta)
                z = radius * math.sin(theta)
                glVertex3f(x, 0, z)
            glEnd()

        # Vertical beams
        glColor4f(0.0, 0.5, 1.0, 0.3)
        glBegin(GL_LINES)
        for i in range(8):
            theta = 2.0 * math.pi * i / 8
            x = 2.0 * math.cos(theta)
            z = 2.0 * math.sin(theta)
            glVertex3f(x, 0, z)
            glVertex3f(x, 2, z)
        glEnd()

        glPopMatrix()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_ui(self, w, h):
        """Draw 2D UI elements with sci-fi aesthetic."""
        UIRenderer.setup_2d(w, h)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 1. Top Header - "MISSION ACCOMPLISHED"
        pulse = 0.8 + 0.2 * math.sin(self.time * 3)
        title = "MISSION ACCOMPLISHED"
        title_size = 48

        # Glitch effect for title
        offset_x = 0
        if random.random() < 0.05:
            offset_x = random.randint(-5, 5)

        _, title_w, _ = UIRenderer.get_text_texture(
            title, title_size, font_name="space_armor")
        UIRenderer.draw_text((w - title_w) / 2 + offset_x, h - 80, title,
                             size=title_size, color=(pulse, 0.8 * pulse, 0.0), font_name="space_armor")

        # Subtitle
        subtitle = "SOLAR SYSTEM EXPLORATION COMPLETE"
        sub_size = 22
        sub_width = len(subtitle) * sub_size * 0.5
        UIRenderer.draw_text((w - sub_width) / 2, h - 120, subtitle,
                             size=sub_size, color=(0.0, 0.8, 1.0), font_name="radiospace")

        # 2. Bottom Stats Panel
        self._draw_stats_panel(w, h)

        # 3. Side Panels (Decorative)
        self._draw_side_panels(w, h)

        # 4. Selected trophy info
        if self.trophies and 0 <= self.selected_trophy < len(self.trophies):
            planet = self.trophies[self.selected_trophy]
            trophy_type = get_trophy_for_planet(planet)
            trophy_name = trophy_type.replace('_', ' ').title()

            # Trophy Name Label
            info_text = f"{planet.upper()}"
            info_size = 32
            info_width = len(info_text) * info_size * 0.6
            UIRenderer.draw_text((w - info_width) / 2, 380, info_text,
                                 size=info_size, color=(1.0, 1.0, 1.0), font_name="radiospace")

            sub_text = f"[{trophy_name}]"
            sub_size = 20
            sub_width = len(sub_text) * sub_size * 0.5
            UIRenderer.draw_text((w - sub_width) / 2, 350, sub_text,
                                 size=sub_size, color=(1.0, 0.8, 0.2), font_name="radiospace")

        # 5. Navigation hints
        nav_text = "< A   NAVIGATE TROPHIES   D >"
        nav_size = 16
        nav_width = len(nav_text) * nav_size * 0.5
        UIRenderer.draw_text((w - nav_width) / 2, 120, nav_text,
                             size=nav_size, color=(0.6, 0.8, 0.9), font_name="radiospace")

        # 6. Return instruction with pulsing background
        ret_text = "PRESS SPACE TO RETURN TO MAIN MENU"
        ret_size = 18
        _, ret_w, ret_h = UIRenderer.get_text_texture(
            ret_text, ret_size, font_name="radiospace")

        # Button background
        btn_w = ret_w + 60
        btn_h = 50
        btn_x = (w - btn_w) / 2
        btn_y = 40

        glColor4f(0.0, 0.2, 0.4, 0.6 + 0.2 * math.sin(self.time * 4))
        glBegin(GL_QUADS)
        glVertex2f(btn_x, btn_y)
        glVertex2f(btn_x + btn_w, btn_y)
        glVertex2f(btn_x + btn_w, btn_y + btn_h)
        glVertex2f(btn_x, btn_y + btn_h)
        glEnd()

        glColor4f(0.0, 1.0, 1.0, 0.8)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(btn_x, btn_y)
        glVertex2f(btn_x + btn_w, btn_y)
        glVertex2f(btn_x + btn_w, btn_y + btn_h)
        glVertex2f(btn_x, btn_y + btn_h)
        glEnd()

        text_x = btn_x + (btn_w - ret_w) / 2
        text_y = btn_y + (btn_h - ret_h) / 2 + 2
        UIRenderer.draw_text(text_x, text_y, ret_text,
                             size=ret_size, color=(1.0, 1.0, 1.0), font_name="radiospace")

        glDisable(GL_BLEND)
        UIRenderer.restore_3d()

    def _draw_stats_panel(self, w, h):
        """Draws the central statistics panel."""
        panel_w = 600
        panel_h = 150
        panel_x = (w - panel_w) / 2
        panel_y = 160

        # Tech background with gradient-like effect
        glColor4f(0.0, 0.05, 0.1, 0.85)
        glBegin(GL_QUADS)
        glVertex2f(panel_x, panel_y)
        glVertex2f(panel_x + panel_w, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h)
        glEnd()

        # Header background
        header_h = 40
        glColor4f(0.0, 0.2, 0.4, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(panel_x, panel_y + panel_h - header_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - header_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h)
        glEnd()

        # Borders with corner accents
        glColor4f(0.0, 0.6, 0.8, 0.8)
        glLineWidth(2.0)

        # Main border
        glBegin(GL_LINE_LOOP)
        glVertex2f(panel_x, panel_y)
        glVertex2f(panel_x + panel_w, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h)
        glEnd()

        # Separator line
        glBegin(GL_LINES)
        glVertex2f(panel_x, panel_y + panel_h - header_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - header_h)
        glEnd()

        # Corner accents
        accent_len = 20
        glLineWidth(3.0)
        glBegin(GL_LINES)
        # Top Left
        glVertex2f(panel_x, panel_y + panel_h)
        glVertex2f(panel_x + accent_len, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - accent_len)
        # Top Right
        glVertex2f(panel_x + panel_w, panel_y + panel_h)
        glVertex2f(panel_x + panel_w - accent_len, panel_y + panel_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - accent_len)
        # Bottom Left
        glVertex2f(panel_x, panel_y)
        glVertex2f(panel_x + accent_len, panel_y)
        glVertex2f(panel_x, panel_y)
        glVertex2f(panel_x, panel_y + accent_len)
        # Bottom Right
        glVertex2f(panel_x + panel_w, panel_y)
        glVertex2f(panel_x + panel_w - accent_len, panel_y)
        glVertex2f(panel_x + panel_w, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + accent_len)
        glEnd()

        # Stats Content
        planets_visited = len(self.trophies)

        # Grid layout for stats
        col1_x = panel_x + 40
        col2_x = panel_x + panel_w / 2 + 20
        row1_y = panel_y + panel_h - 70
        row2_y = panel_y + panel_h - 110

        # Header
        title = "MISSION REPORT"
        _, title_w, _ = UIRenderer.get_text_texture(
            title, 24, font_name="space_armor")
        UIRenderer.draw_text(panel_x + (panel_w - title_w) / 2, panel_y + panel_h - 30, title,
                             size=24, color=(0.0, 1.0, 1.0), font_name="space_armor")

        # Stat 1: Planets
        UIRenderer.draw_text(col1_x, row1_y, "PLANETS EXPLORED:", size=14, color=(
            0.7, 0.7, 0.7), font_name="radiospace")
        UIRenderer.draw_text(
            col1_x + 200, row1_y, f"{planets_visited}/9", size=14, color=(0.0, 1.0, 0.0), font_name="radiospace")

        # Stat 2: Trophies
        UIRenderer.draw_text(col1_x, row2_y, "TROPHIES EARNED:", size=14, color=(
            0.7, 0.7, 0.7), font_name="radiospace")
        UIRenderer.draw_text(
            col1_x + 200, row2_y, f"{planets_visited}/9", size=14, color=(1.0, 0.8, 0.0), font_name="radiospace")

        # Stat 3: Status
        UIRenderer.draw_text(col2_x, row1_y, "MISSION STATUS:", size=14, color=(
            0.7, 0.7, 0.7), font_name="radiospace")
        UIRenderer.draw_text(col2_x + 180, row1_y, "SUCCESS",
                             size=14, color=(0.0, 1.0, 0.0), font_name="radiospace")

        # Stat 4: Rank
        UIRenderer.draw_text(col2_x, row2_y, "PILOT RANK:", size=14, color=(
            0.7, 0.7, 0.7), font_name="radiospace")
        UIRenderer.draw_text(col2_x + 180, row2_y, "LEGENDARY",
                             size=14, color=(1.0, 0.0, 1.0), font_name="radiospace")

    def _draw_side_panels(self, w, h):
        """Draws decorative side panels."""
        panel_w = 60
        panel_h = h - 200

        # Left Panel
        x = 20
        y = 100
        glColor4f(0.0, 0.1, 0.2, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + panel_w, y)
        glVertex2f(x + panel_w, y + panel_h)
        glVertex2f(x, y + panel_h)
        glEnd()

        glColor4f(0.0, 0.5, 0.8, 0.3)
        glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + panel_w, y)
        glVertex2f(x + panel_w, y + panel_h)
        glVertex2f(x, y + panel_h)
        glEnd()

        # Animated bars inside left panel
        bar_h = 10
        gap = 20
        # Calculate available height for bars (panel_h minus padding)
        available_h = panel_h - 100
        num_bars = int(available_h / (bar_h + gap))

        for i in range(num_bars):
            bar_y = y + 50 + i * (bar_h + gap)
            width_mod = math.sin(self.time * 2 + i * 0.5) * 0.5 + 0.5
            bar_w = (panel_w - 20) * width_mod

            glColor4f(0.0, 0.8, 1.0, 0.4)
            glBegin(GL_QUADS)
            glVertex2f(x + 10, bar_y)
            glVertex2f(x + 10 + bar_w, bar_y)
            glVertex2f(x + 10 + bar_w, bar_y + bar_h)
            glVertex2f(x + 10, bar_y + bar_h)
            glEnd()

        # Right Panel
        x = w - 20 - panel_w
        glColor4f(0.0, 0.1, 0.2, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + panel_w, y)
        glVertex2f(x + panel_w, y + panel_h)
        glVertex2f(x, y + panel_h)
        glEnd()

        glColor4f(0.0, 0.5, 0.8, 0.3)
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + panel_w, y)
        glVertex2f(x + panel_w, y + panel_h)
        glVertex2f(x, y + panel_h)
        glEnd()

        # Scrolling data text on right
        # Just lines representing data
        line_spacing = 25
        available_h = panel_h - 60
        num_lines = int(available_h / line_spacing)

        for i in range(num_lines):
            line_y = y + panel_h - 40 - i * line_spacing
            # Scroll effect
            offset = (self.time * 20) % line_spacing
            line_y -= offset

            if line_y < y + 20:
                continue

            glColor4f(0.0, 1.0, 0.5, 0.3)
            glBegin(GL_LINES)
            glVertex2f(x + 10, line_y)
            glVertex2f(x + panel_w - 10, line_y)
            glEnd()
