from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.ui_renderer import UIRenderer
from src.graphics.skybox import Skybox
from src.core.resource_loader import ResourceManager
from src.graphics.draw_utils import draw_sphere, draw_torus, set_material_color
import math
import random


class WelcomeState(BaseState):
    """
    Estado de bienvenida con pantalla de título y botón de inicio.
    Features a beautiful top-down view of the solar system as background.
    """

    def __init__(self):
        self.skybox = None
        self.animation_time = 0.0
        self.title_pulse = 0.0
        self.stars = []  # For animated stars
        self.shooting_stars = []  # Shooting star effects
        self.nebula_particles = []  # Background nebula particles

        # Solar system data for background rendering (scaled for visual appeal)
        # Format: (name, color, radius, orbit_radius, orbit_speed)
        # Colors made brighter for better visibility
        self.planets = [
            ("Sun", (1.0, 0.95, 0.4), 8.0, 0, 0),
            ("Mercury", (0.85, 0.85, 0.85), 1.2, 18, 4.14),
            ("Venus", (1.0, 0.9, 0.6), 1.8, 28, 1.62),
            ("Earth", (0.4, 0.6, 1.0), 2.0, 40, 1.0),
            ("Mars", (1.0, 0.5, 0.35), 1.5, 54, 0.53),
            ("Jupiter", (1.0, 0.8, 0.6), 5.0, 90, 0.084),
            ("Saturn", (1.0, 0.9, 0.7), 4.2, 130, 0.034),
            ("Uranus", (0.6, 0.9, 1.0), 2.8, 165, 0.012),
            ("Neptune", (0.3, 0.45, 1.0), 2.6, 200, 0.006),
        ]

        # Precomputed planet angles (start at different positions for visual appeal)
        # Spread planets around the orbit for an interesting initial view
        self.planet_angles = [
            0.0,          # Sun (doesn't move)
            0.8,          # Mercury
            2.5,          # Venus
            4.2,          # Earth
            1.0,          # Mars
            5.5,          # Jupiter
            3.2,          # Saturn
            0.5,          # Uranus
            4.8,          # Neptune
        ]

        # Background stars for the solar system view
        self.bg_stars = []

        # Sci-fi UI variables
        self.scan_line_y = 0.0
        self.hex_timer = 0.0
        self.hex_text = "0x00 0x00"
        # Pre-generate hex codes to prevent texture cache explosion
        self.hex_codes = [
            f"0x{random.randint(0, 255):02X} 0x{random.randint(0, 255):02X}" for _ in range(32)]

        # Glitch effect variables
        self.glitch_timer = 0.0
        self.glitch_duration = 0.0
        self.glitch_offset_x = 0.0
        self.glitch_offset_y = 0.0

        # Store button rectangles for mouse interaction
        self.button_rects = {}

    def enter(self):
        print("[WelcomeState] Entrando al estado de bienvenida")

        # Cargar skybox (no longer used but kept for compatibility)
        bg_texture = ResourceManager.load_texture("background/stars.jpg")
        self.skybox = Skybox(size=100.0, texture_id=bg_texture)

        # Generate background stars for the solar system view - DENSE star field
        import random
        for _ in range(1500):  # Many more stars for beautiful background
            # Spread stars in a dome around the solar system
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(220, 450)
            x = dist * math.cos(angle)
            z = dist * math.sin(angle)
            y = random.uniform(-80, -3)  # Below the viewing plane, more spread
            self.bg_stars.append({
                'x': x, 'y': y, 'z': z,
                'brightness': random.uniform(0.5, 1.0),  # Brighter stars
                'size': random.uniform(1.0, 3.0),
                'twinkle_speed': random.uniform(1, 5),
                'twinkle_offset': random.uniform(0, math.pi * 2),
                'color': random.choice([
                    (1.0, 1.0, 1.0),   # White
                    (0.9, 0.95, 1.0),  # Blue-white
                    (1.0, 0.98, 0.9),  # Warm white
                    (0.85, 0.9, 1.0),  # Cool blue
                    (1.0, 0.9, 0.8),   # Warm yellow
                ])
            })

        # Generate random stars for particle effect - MORE stars
        import random
        for _ in range(300):
            self.stars.append({
                'x': random.uniform(-80, 80),
                'y': random.uniform(-50, 50),
                'z': random.uniform(-100, -10),
                'size': random.uniform(0.5, 2.5),
                'speed': random.uniform(0.3, 1.5),
                'brightness': random.uniform(0.3, 1.0),
                'twinkle_speed': random.uniform(2, 8),
                'twinkle_offset': random.uniform(0, math.pi * 2),
                'color': random.choice([
                    (1.0, 1.0, 1.0),   # White
                    (0.8, 0.9, 1.0),   # Blue-white
                    (1.0, 0.95, 0.8),  # Yellow-white
                    (0.7, 0.8, 1.0),   # Light blue
                    (1.0, 0.8, 0.7),   # Orange tint
                ])
            })

        # Generate shooting stars
        for _ in range(5):
            self._spawn_shooting_star()

        # Generate nebula particles
        for _ in range(50):
            self.nebula_particles.append({
                'x': random.uniform(-60, 60),
                'y': random.uniform(-40, 40),
                'z': random.uniform(-90, -30),
                'size': random.uniform(5, 15),
                'alpha': random.uniform(0.02, 0.08),
                'color': random.choice([
                    (0.2, 0.1, 0.4),   # Purple
                    (0.1, 0.2, 0.4),   # Blue
                    (0.0, 0.3, 0.3),   # Teal
                ]),
                'drift_x': random.uniform(-0.5, 0.5),
                'drift_y': random.uniform(-0.3, 0.3),
            })

    def _spawn_shooting_star(self):
        import random
        self.shooting_stars.append({
            'x': random.uniform(-80, 80),
            'y': random.uniform(20, 50),
            'z': random.uniform(-60, -30),
            'vx': random.uniform(-2, -0.5) if random.random() > 0.5 else random.uniform(0.5, 2),
            'vy': random.uniform(-1.5, -0.5),
            'length': random.uniform(3, 8),
            'life': random.uniform(1.0, 3.0),
            'max_life': random.uniform(1.0, 3.0),
            'brightness': random.uniform(0.7, 1.0)
        })

    def update(self, dt):
        import random
        self.animation_time += dt
        self.title_pulse = math.sin(self.animation_time * 2.0) * 0.5 + 0.5

        # Update planet orbital positions
        for i, (name, color, radius, orbit_radius, orbit_speed) in enumerate(self.planets):
            if orbit_speed > 0:
                self.planet_angles[i] += orbit_speed * \
                    dt * 0.3  # Slow down for visual appeal

        # Animate stars (flying towards viewer)
        for star in self.stars:
            star['z'] += star['speed'] * dt * 15
            if star['z'] > 5:
                star['z'] = -100
                star['x'] = random.uniform(-80, 80)
                star['y'] = random.uniform(-50, 50)

        # Animate shooting stars
        for star in self.shooting_stars:
            star['x'] += star['vx'] * dt * 30
            star['y'] += star['vy'] * dt * 30
            star['life'] -= dt

        # Remove dead shooting stars and spawn new ones
        self.shooting_stars = [s for s in self.shooting_stars if s['life'] > 0]
        if len(self.shooting_stars) < 3 and random.random() < 0.02:
            self._spawn_shooting_star()

        # Animate nebula particles
        for p in self.nebula_particles:
            p['x'] += p['drift_x'] * dt
            p['y'] += p['drift_y'] * dt
            # Wrap around
            if p['x'] < -70:
                p['x'] = 70
            if p['x'] > 70:
                p['x'] = -70
            if p['y'] < -50:
                p['y'] = 50
            if p['y'] > 50:
                p['y'] = -50

        # Update sci-fi UI elements
        self.scan_line_y += dt * 150
        h = glutGet(GLUT_WINDOW_HEIGHT)
        if self.scan_line_y > h:
            self.scan_line_y = 0

        self.hex_timer += dt
        if self.hex_timer > 0.08:
            self.hex_timer = 0
            self.hex_text = random.choice(self.hex_codes)

        # Glitch logic
        if self.glitch_duration > 0:
            self.glitch_duration -= dt
            if self.glitch_duration <= 0:
                self.glitch_offset_x = 0
                self.glitch_offset_y = 0
        else:
            self.glitch_timer -= dt
            if self.glitch_timer <= 0:
                # Trigger glitch
                self.glitch_duration = random.uniform(0.05, 0.2)
                self.glitch_timer = random.uniform(2.0, 5.0)

        if self.glitch_duration > 0:
            self.glitch_offset_x = random.uniform(-5, 5)
            self.glitch_offset_y = random.uniform(-2, 2)

    def handle_input(self, event, x, y):
        if event[0] == 'KEY_DOWN':
            key = event[1]
            # S key to start (gameplay with ship)
            if key == b's' or key == b'S':
                self._go_to_ship_select()
            # O key for orbital view (no ship, just observation)
            elif key == b'o' or key == b'O':
                self._go_to_orbital_view()
            # Q key to quit
            elif key == b'q' or key == b'Q':
                self._quit_game()
            # Also allow Enter/Space for ship select
            elif key == b'\r' or key == b' ':
                self._go_to_ship_select()
        elif event[0] == 'MOUSE_BUTTON':
            button, state = event[1], event[2]
            if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
                # Convert Y coordinate (GLUT is top-left, OpenGL is bottom-left)
                h = glutGet(GLUT_WINDOW_HEIGHT)
                gl_y = h - y

                # Check buttons
                if 'start' in self.button_rects:
                    bx, by, bw, bh = self.button_rects['start']
                    if bx <= x <= bx + bw and by <= gl_y <= by + bh:
                        self._go_to_ship_select()
                        return

                if 'orbital' in self.button_rects:
                    bx, by, bw, bh = self.button_rects['orbital']
                    if bx <= x <= bx + bw and by <= gl_y <= by + bh:
                        self._go_to_orbital_view()
                        return

                if 'quit' in self.button_rects:
                    bx, by, bw, bh = self.button_rects['quit']
                    if bx <= x <= bx + bw and by <= gl_y <= by + bh:
                        self._quit_game()
                        return

    def _go_to_ship_select(self):
        from src.states.ship_select_state import ShipSelectState
        if hasattr(self, 'state_machine') and self.state_machine:
            new_state = ShipSelectState()
            new_state.state_machine = self.state_machine
            self.state_machine.change(new_state)

    def _go_to_orbital_view(self):
        """Go directly to orbital view without ship selection."""
        from src.states.gameplay_state import GameplayState
        from src.core.session import GameContext
        # Set flag for orbital-only mode (no ship)
        GameContext.orbital_only = True
        if hasattr(self, 'state_machine') and self.state_machine:
            new_state = GameplayState()
            new_state.state_machine = self.state_machine
            self.state_machine.change(new_state)

    def _quit_game(self):
        """Exit the application."""
        import os
        os._exit(0)

    def draw(self):
        glClearColor(0.0, 0.0, 0.02, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Setup 3D for solar system (top-down view)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, w / h, 1.0, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Top-down camera looking at solar system from above
        # Position camera high above, looking down at center
        gluLookAt(0, 350, 0,    # Camera position (high above)
                  0, 0, 0,       # Look at center
                  0, 0, -1)      # Up vector (towards -Z for proper orientation)

        # Draw the solar system background
        self._draw_solar_system()

        # Setup 2D for UI (draw on top)
        UIRenderer.setup_2d(w, h)

        try:
            # Draw a subtle dark overlay to make text more readable
            self._draw_overlay(w, h)

            # Draw title
            self._draw_title(w, h)

            # Draw start button
            self._draw_start_button(w, h)

            # Draw credits/info
            self._draw_info(w, h)

            # Draw extra sci-fi details
            self._draw_sci_fi_details(w, h)
        finally:
            UIRenderer.restore_3d()

    def _draw_sci_fi_details(self, w, h):
        """Draw extra sci-fi UI elements."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_TEXTURE_2D)

        # 1. Corner Brackets
        glColor4f(0.0, 0.8, 1.0, 0.5)
        glLineWidth(2.0)
        gap = 20
        length = 100
        corner_cut = 15

        # Top Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(gap, h - gap - length)
        glVertex2f(gap, h - gap - corner_cut)
        glVertex2f(gap + corner_cut, h - gap)
        glVertex2f(gap + length, h - gap)
        glEnd()

        # Top Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(w - gap - length, h - gap)
        glVertex2f(w - gap - corner_cut, h - gap)
        glVertex2f(w - gap, h - gap - corner_cut)
        glVertex2f(w - gap, h - gap - length)
        glEnd()

        # Bottom Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(gap, gap + length)
        glVertex2f(gap, gap + corner_cut)
        glVertex2f(gap + corner_cut, gap)
        glVertex2f(gap + length, gap)
        glEnd()

        # Bottom Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(w - gap - length, gap)
        glVertex2f(w - gap - corner_cut, gap)
        glVertex2f(w - gap, gap + corner_cut)
        glVertex2f(w - gap, gap + length)
        glEnd()

        # 2. Scanning Line
        glColor4f(0.0, 1.0, 1.0, 0.15)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(0, self.scan_line_y)
        glVertex2f(w, self.scan_line_y)
        glEnd()

        # 3. Rotating Circles around Title
        # Title is at h * 0.75, center x is w/2
        center_x = w / 2
        center_y = h * 0.75 + 40  # Adjust for title height

        glLineWidth(1.5)
        for i in range(3):
            radius = 350 + i * 25
            speed = (i + 1) * 0.15 * (1 if i % 2 == 0 else -1)
            angle_offset = self.animation_time * speed

            glColor4f(0.0, 0.6, 0.8, 0.15)
            glBegin(GL_LINE_STRIP)
            segments = 128
            for j in range(segments + 1):
                theta = (j / segments) * 2 * math.pi + angle_offset
                # Create gaps
                if math.sin(theta * 4) > 0.7:
                    continue
                x = center_x + radius * math.cos(theta)
                # Flattened circle (ellipse)
                y = center_y + radius * math.sin(theta) * 0.3
                glVertex2f(x, y)
            glEnd()

        # 4. Data Blocks
        from src.graphics.ui_renderer import UIRenderer

        # Top Left Data
        UIRenderer.draw_text(gap + 15, h - gap - 25, "SYS.STATUS: ONLINE",
                             size=12, color=(0.0, 0.8, 1.0), font_name="radiospace")
        UIRenderer.draw_text(
            gap + 15, h - gap - 40, f"MEM: {self.hex_text}", size=12, color=(0.0, 0.6, 0.8), font_name="radiospace")

        # Top Right Data
        UIRenderer.draw_text(w - gap - 160, h - gap - 25, "NET.LINK: SECURE",
                             size=12, color=(0.0, 0.8, 1.0), font_name="radiospace")
        UIRenderer.draw_text(w - gap - 160, h - gap - 40,
                             f"T: {self.animation_time:.2f}", size=12, color=(0.0, 0.6, 0.8), font_name="radiospace")

        glDisable(GL_BLEND)

    def _draw_solar_system(self):
        """Draw the solar system from a top-down view."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        # Draw background stars first - brighter and colored
        for star in self.bg_stars:
            twinkle = 0.7 + 0.3 * \
                math.sin(self.animation_time *
                         star['twinkle_speed'] + star['twinkle_offset'])
            brightness = star['brightness'] * twinkle

            # Get star color if available, otherwise white
            color = star.get('color', (1.0, 1.0, 1.0))

            # Draw larger stars with glow
            size = star['size'] * \
                (1.0 + 0.2 * math.sin(self.animation_time *
                 2 + star['twinkle_offset']))
            glPointSize(size)
            glBegin(GL_POINTS)
            glColor4f(color[0] * brightness, color[1] *
                      brightness, color[2] * brightness, 0.9)
            glVertex3f(star['x'], star['y'], star['z'])
            glEnd()

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw orbit paths first (thin rings) - brighter orbit lines
        glLineWidth(1.5)
        for i, (name, color, radius, orbit_radius, orbit_speed) in enumerate(self.planets):
            if orbit_radius > 0:
                # Draw orbit as a thin circle - brighter
                glColor4f(0.3, 0.4, 0.5, 0.5)
                glBegin(GL_LINE_LOOP)
                segments = 64
                for j in range(segments):
                    angle = (2 * math.pi * j) / segments
                    x = orbit_radius * math.cos(angle)
                    z = orbit_radius * math.sin(angle)
                    glVertex3f(x, 0, z)
                glEnd()

        # Enable lighting for planets with brighter settings
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # Setup light at sun position - very bright for dramatic effect
        light_position = [0.0, 100.0, 0.0, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        # Bright warm light
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.5, 1.4, 1.2, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [
                  0.5, 0.5, 0.55, 1.0])  # Strong ambient

        # Draw planets
        for i, (name, color, radius, orbit_radius, orbit_speed) in enumerate(self.planets):
            glPushMatrix()

            if orbit_radius > 0:
                # Calculate planet position on orbit
                angle = self.planet_angles[i]
                x = orbit_radius * math.cos(angle)
                z = orbit_radius * math.sin(angle)
                glTranslatef(x, 0, z)

            # Draw planet
            if name == "Sun":
                # Sun glows - draw with emissive material
                glDisable(GL_LIGHTING)
                glColor3f(*color)

                # Draw sun with glow effect
                pulse = 0.9 + 0.1 * math.sin(self.animation_time * 3)
                glColor3f(color[0] * pulse, color[1] * pulse, color[2] * pulse)

                quadric = gluNewQuadric()
                gluQuadricNormals(quadric, GLU_SMOOTH)
                gluSphere(quadric, radius, 32, 32)
                gluDeleteQuadric(quadric)

                # Add outer glow
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE)
                for glow_layer in range(3):
                    glow_radius = radius * (1.2 + glow_layer * 0.15)
                    alpha = 0.15 - glow_layer * 0.04
                    glColor4f(1.0, 0.8, 0.3, alpha)
                    quadric = gluNewQuadric()
                    gluSphere(quadric, glow_radius, 16, 16)
                    gluDeleteQuadric(quadric)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

                glEnable(GL_LIGHTING)
            else:
                # Regular planet
                set_material_color(color, shininess=50.0)
                quadric = gluNewQuadric()
                gluQuadricNormals(quadric, GLU_SMOOTH)
                gluSphere(quadric, radius, 24, 24)
                gluDeleteQuadric(quadric)

                # Saturn's rings
                if name == "Saturn":
                    glDisable(GL_LIGHTING)
                    glColor4f(0.85, 0.75, 0.55, 0.7)
                    glRotatef(90, 1, 0, 0)  # Rotate to horizontal
                    draw_torus(inner_radius=radius * 0.3, outer_radius=radius * 1.8,
                               color=(0.85, 0.75, 0.55, 0.7))
                    glEnable(GL_LIGHTING)

                # Uranus rings (subtle)
                if name == "Uranus":
                    glDisable(GL_LIGHTING)
                    glColor4f(0.5, 0.7, 0.8, 0.4)
                    glRotatef(90, 1, 0, 0)
                    draw_torus(inner_radius=radius * 0.2, outer_radius=radius * 1.3,
                               color=(0.5, 0.7, 0.8, 0.4))
                    glEnable(GL_LIGHTING)

            glPopMatrix()

        # Draw asteroid belt (denser, more visible)
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        import random
        random.seed(42)  # Consistent asteroid positions

        # Draw more asteroids with varying sizes
        for _ in range(400):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(64, 80)
            x = dist * math.cos(angle + self.animation_time * 0.02)
            z = dist * math.sin(angle + self.animation_time * 0.02)
            y = random.uniform(-3, 3)
            size = random.uniform(1.0, 2.5)
            brightness = random.uniform(0.4, 0.8)

            glPointSize(size)
            glColor4f(brightness * 0.7, brightness *
                      0.65, brightness * 0.6, 0.7)
            glBegin(GL_POINTS)
            glVertex3f(x, y, z)
            glEnd()

        # Add some brighter distant objects (Kuiper belt hint)
        random.seed(123)
        for _ in range(100):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(210, 240)
            x = dist * math.cos(angle + self.animation_time * 0.005)
            z = dist * math.sin(angle + self.animation_time * 0.005)
            y = random.uniform(-5, 5)

            glPointSize(1.5)
            glColor4f(0.5, 0.5, 0.6, 0.4)
            glBegin(GL_POINTS)
            glVertex3f(x, y, z)
            glEnd()

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_BLEND)

    def _draw_overlay(self, w, h):
        """Draw a subtle gradient overlay to improve text readability."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Very subtle overlay - mostly transparent to show solar system
        center_x = w / 2
        center_y = h / 2

        # Draw very light overlay (just enough for text readability)
        glBegin(GL_QUADS)
        glColor4f(0.0, 0.0, 0.02, 0.25)  # Even more transparent
        glVertex2f(0, 0)
        glVertex2f(w, 0)
        glVertex2f(w, h)
        glVertex2f(0, h)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_title(self, w, h):
        # Main title with pulsing effect
        title = "SOLAR EXPLORER"
        title_size = 80  # Reduced size

        # Calculate centered position dynamically
        _, title_w, _ = UIRenderer.get_text_texture(
            title, title_size, font_name="space_armor")
        title_x = (w - title_w) / 2
        title_y = h * 0.75  # Position in upper portion of screen

        # Apply glitch offset
        gx = self.glitch_offset_x
        gy = self.glitch_offset_y

        # Glow effect (multiple layers)
        glow_intensity = 0.3 + self.title_pulse * 0.2

        # Draw glow layers
        for i in range(3):
            offset = (3 - i) * 3
            alpha = glow_intensity / (i + 1)
            UIRenderer.draw_text(title_x - offset + gx, title_y - offset + gy, title,
                                 size=title_size, color=(0.0, alpha, alpha), font_name="space_armor")

        # Glitch chromatic aberration
        if self.glitch_duration > 0:
            UIRenderer.draw_text(title_x + gx - 4, title_y + gy,
                                 title, size=title_size, color=(1.0, 0.0, 0.0, 0.7), font_name="space_armor")
            UIRenderer.draw_text(title_x + gx + 4, title_y + gy,
                                 title, size=title_size, color=(0.0, 0.0, 1.0, 0.7), font_name="space_armor")

        # Main title
        cyan_pulse = 0.7 + self.title_pulse * 0.3
        UIRenderer.draw_text(title_x + gx, title_y + gy, title, size=title_size,
                             color=(0.0, cyan_pulse, cyan_pulse), font_name="space_armor")

        # Subtitle - LARGER
        subtitle = "A JOURNEY THROUGH THE COSMOS"
        sub_size = 32  # Much bigger (was 20)

        # Calculate centered position dynamically
        _, sub_w, _ = UIRenderer.get_text_texture(
            subtitle, sub_size, font_name="radiospace")
        sub_x = (w - sub_w) / 2

        sub_y = title_y - 80  # More space below title
        # Subtle glow for subtitle
        UIRenderer.draw_text(sub_x + 2, sub_y - 2, subtitle, size=sub_size,
                             color=(0.0, 0.3, 0.3), font_name="radiospace")
        UIRenderer.draw_text(sub_x, sub_y, subtitle, size=sub_size,
                             color=(0.5, 0.7, 0.8), font_name="radiospace")

    def _draw_start_button(self, w, h):
        # Main start button dimensions
        btn_width = 300
        btn_height = 60
        btn_x = (w - btn_width) / 2
        btn_y = h * 0.26  # Moved up to make room for other buttons

        # Pulsing border
        pulse = 0.5 + self.title_pulse * 0.5

        # Draw button background
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Dark background with chamfered corners
        glColor4f(0.0, 0.1, 0.15, 0.8)
        chamfer = 10
        glBegin(GL_POLYGON)
        glVertex2f(btn_x + chamfer, btn_y)
        glVertex2f(btn_x + btn_width - chamfer, btn_y)
        glVertex2f(btn_x + btn_width, btn_y + chamfer)
        glVertex2f(btn_x + btn_width, btn_y + btn_height - chamfer)
        glVertex2f(btn_x + btn_width - chamfer, btn_y + btn_height)
        glVertex2f(btn_x + chamfer, btn_y + btn_height)
        glVertex2f(btn_x, btn_y + btn_height - chamfer)
        glVertex2f(btn_x, btn_y + chamfer)
        glEnd()

        # Glowing border
        glLineWidth(2.0)
        glColor3f(0.0, pulse, pulse)
        glBegin(GL_LINE_LOOP)
        glVertex2f(btn_x + chamfer, btn_y)
        glVertex2f(btn_x + btn_width - chamfer, btn_y)
        glVertex2f(btn_x + btn_width, btn_y + chamfer)
        glVertex2f(btn_x + btn_width, btn_y + btn_height - chamfer)
        glVertex2f(btn_x + btn_width - chamfer, btn_y + btn_height)
        glVertex2f(btn_x + chamfer, btn_y + btn_height)
        glVertex2f(btn_x, btn_y + btn_height - chamfer)
        glVertex2f(btn_x, btn_y + chamfer)
        glEnd()

        glDisable(GL_BLEND)

        # Button text - USE CUSTOM FONT with glow
        text = "START"
        text_size = 36

        # Calculate centered position dynamically
        _, text_w, text_h = UIRenderer.get_text_texture(
            text, text_size, font_name="radiospace")
        text_x = btn_x + (btn_width - text_w) / 2

        text_y = btn_y + (btn_height - text_h) / 2

        # Glow effect
        glow_color = (0.0, pulse * 0.5, pulse * 0.5)
        UIRenderer.draw_text(text_x + 2, text_y - 2, text, size=text_size,
                             color=glow_color, font_name="radiospace")
        # Main text
        UIRenderer.draw_text(text_x, text_y, text, size=text_size,
                             color=(0.0, 1.0, 1.0), font_name="radiospace")

        # ---- ORBITAL VIEW BUTTON ----
        orbital_btn_y = btn_y - 80  # Below the start button
        orbital_btn_width = 280
        orbital_btn_height = 50
        orbital_btn_x = (w - orbital_btn_width) / 2

        # Draw orbital button background
        glEnable(GL_BLEND)
        glColor4f(0.0, 0.08, 0.12, 0.7)
        chamfer2 = 8
        glBegin(GL_POLYGON)
        glVertex2f(orbital_btn_x + chamfer2, orbital_btn_y)
        glVertex2f(orbital_btn_x + orbital_btn_width - chamfer2, orbital_btn_y)
        glVertex2f(orbital_btn_x + orbital_btn_width, orbital_btn_y + chamfer2)
        glVertex2f(orbital_btn_x + orbital_btn_width,
                   orbital_btn_y + orbital_btn_height - chamfer2)
        glVertex2f(orbital_btn_x + orbital_btn_width -
                   chamfer2, orbital_btn_y + orbital_btn_height)
        glVertex2f(orbital_btn_x + chamfer2,
                   orbital_btn_y + orbital_btn_height)
        glVertex2f(orbital_btn_x, orbital_btn_y +
                   orbital_btn_height - chamfer2)
        glVertex2f(orbital_btn_x, orbital_btn_y + chamfer2)
        glEnd()

        # Orbital button border (orange/gold)
        glLineWidth(1.5)
        orange_pulse = 0.6 + self.title_pulse * 0.3
        glColor3f(orange_pulse, orange_pulse * 0.6, 0.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(orbital_btn_x + chamfer2, orbital_btn_y)
        glVertex2f(orbital_btn_x + orbital_btn_width - chamfer2, orbital_btn_y)
        glVertex2f(orbital_btn_x + orbital_btn_width, orbital_btn_y + chamfer2)
        glVertex2f(orbital_btn_x + orbital_btn_width,
                   orbital_btn_y + orbital_btn_height - chamfer2)
        glVertex2f(orbital_btn_x + orbital_btn_width -
                   chamfer2, orbital_btn_y + orbital_btn_height)
        glVertex2f(orbital_btn_x + chamfer2,
                   orbital_btn_y + orbital_btn_height)
        glVertex2f(orbital_btn_x, orbital_btn_y +
                   orbital_btn_height - chamfer2)
        glVertex2f(orbital_btn_x, orbital_btn_y + chamfer2)
        glEnd()
        glDisable(GL_BLEND)

        # Orbital button text
        orbital_text = "ORBITAL VIEW"
        orbital_text_size = 28

        # Calculate centered position dynamically
        _, orbital_text_w, orbital_text_h = UIRenderer.get_text_texture(
            orbital_text, orbital_text_size, font_name="radiospace")
        orbital_text_x = orbital_btn_x + \
            (orbital_btn_width - orbital_text_w) / 2

        orbital_text_y = orbital_btn_y + \
            (orbital_btn_height - orbital_text_h) / 2
        UIRenderer.draw_text(orbital_text_x, orbital_text_y, orbital_text, size=orbital_text_size,
                             color=(1.0, 0.7, 0.2), font_name="radiospace")

        # ---- QUIT BUTTON ----
        quit_btn_y = orbital_btn_y - 70  # Below orbital button
        quit_btn_width = 200
        quit_btn_height = 45
        quit_btn_x = (w - quit_btn_width) / 2

        # Draw quit button background
        glEnable(GL_BLEND)
        glColor4f(0.1, 0.0, 0.0, 0.6)
        chamfer3 = 6
        glBegin(GL_POLYGON)
        glVertex2f(quit_btn_x + chamfer3, quit_btn_y)
        glVertex2f(quit_btn_x + quit_btn_width - chamfer3, quit_btn_y)
        glVertex2f(quit_btn_x + quit_btn_width, quit_btn_y + chamfer3)
        glVertex2f(quit_btn_x + quit_btn_width,
                   quit_btn_y + quit_btn_height - chamfer3)
        glVertex2f(quit_btn_x + quit_btn_width -
                   chamfer3, quit_btn_y + quit_btn_height)
        glVertex2f(quit_btn_x + chamfer3, quit_btn_y + quit_btn_height)
        glVertex2f(quit_btn_x, quit_btn_y + quit_btn_height - chamfer3)
        glVertex2f(quit_btn_x, quit_btn_y + chamfer3)
        glEnd()

        # Quit button border (red)
        glLineWidth(1.5)
        red_pulse = 0.5 + self.title_pulse * 0.2
        glColor3f(red_pulse, 0.2, 0.2)
        glBegin(GL_LINE_LOOP)
        glVertex2f(quit_btn_x + chamfer3, quit_btn_y)
        glVertex2f(quit_btn_x + quit_btn_width - chamfer3, quit_btn_y)
        glVertex2f(quit_btn_x + quit_btn_width, quit_btn_y + chamfer3)
        glVertex2f(quit_btn_x + quit_btn_width,
                   quit_btn_y + quit_btn_height - chamfer3)
        glVertex2f(quit_btn_x + quit_btn_width -
                   chamfer3, quit_btn_y + quit_btn_height)
        glVertex2f(quit_btn_x + chamfer3, quit_btn_y + quit_btn_height)
        glVertex2f(quit_btn_x, quit_btn_y + quit_btn_height - chamfer3)
        glVertex2f(quit_btn_x, quit_btn_y + chamfer3)
        glEnd()
        glDisable(GL_BLEND)

        # Quit button text
        quit_text = "QUIT"
        quit_text_size = 22

        # Calculate centered position dynamically
        _, quit_text_w, quit_text_h = UIRenderer.get_text_texture(
            quit_text, quit_text_size, font_name="radiospace")
        quit_text_x = quit_btn_x + (quit_btn_width - quit_text_w) / 2

        quit_text_y = quit_btn_y + (quit_btn_height - quit_text_h) / 2
        UIRenderer.draw_text(quit_text_x, quit_text_y, quit_text, size=quit_text_size,
                             color=(0.8, 0.3, 0.3), font_name="radiospace")

        # Store rects for click detection
        self.button_rects['start'] = (btn_x, btn_y, btn_width, btn_height)
        self.button_rects['orbital'] = (
            orbital_btn_x, orbital_btn_y, orbital_btn_width, orbital_btn_height)
        self.button_rects['quit'] = (
            quit_btn_x, quit_btn_y, quit_btn_width, quit_btn_height)

    def _draw_info(self, w, h):
        # Bottom info - USE CUSTOM FONT
        info = "USE ARROW KEYS TO NAVIGATE - ENTER TO SELECT"
        info_size = 16

        # Calculate centered position dynamically
        _, info_w, _ = UIRenderer.get_text_texture(
            info, info_size, font_name="radiospace")
        info_x = (w - info_w) / 2

        info_y = 35

        # Subtle pulsing
        alpha_pulse = 0.4 + 0.1 * math.sin(self.animation_time * 1.5)
        UIRenderer.draw_text(info_x, info_y, info, size=info_size,
                             color=(alpha_pulse, alpha_pulse, alpha_pulse + 0.1), font_name="radiospace")

        # Version/credit at very bottom
        credit = "SOLAR SYSTEM PROJECT v1.0"
        credit_size = 12

        # Calculate centered position dynamically
        _, credit_w, _ = UIRenderer.get_text_texture(
            credit, credit_size, font_name="radiospace")
        credit_x = (w - credit_w) / 2

        UIRenderer.draw_text(credit_x, 12, credit, size=credit_size,
                             color=(0.25, 0.25, 0.3), font_name="radiospace")
