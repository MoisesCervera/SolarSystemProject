from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.graphics.ui_renderer import UIRenderer
from src.graphics.skybox import Skybox
from src.core.resource_loader import ResourceManager
from src.graphics.draw_utils import draw_sphere, draw_cylinder, draw_torus, draw_cone, set_material_color
from src.core.session import GameContext
from src.core.audio_manager import get_audio_manager
# Import actual ship models
from src.entities.player.ships.shipM import ShipModel
from src.entities.player.ships.shipS import dibujar_nave as draw_ship_s
from src.entities.player.ships.shipZ import draw_nave as draw_ship_z
import math
import random


class ShipSelectState(BaseState):
    """
    Arcade-style ship selection with roulette carousel.
    """

    # Ship data with names and descriptions
    SHIPS = [
        {
            'id': 'shipM',
            'name': 'UFO PHANTOM',
            'description': 'CLASSIC FLYING SAUCER WITH ABDUCTION BEAM',
            'color_scheme': (0.55, 0.6, 0.65),
            'accent': (0.3, 0.8, 1.0),
            'stats': {'speed': 3, 'boost': 3, 'armor': 4, 'weapons': 2}
        },
        {
            'id': 'shipS',
            'name': 'BUG CRAWLER',
            'description': 'AGILE INSECTOID SCOUT WITH MULTIPLE LEGS',
            'color_scheme': (0.1, 0.2, 0.7),
            'accent': (0.9, 1.0, 0.2),
            'stats': {'speed': 5, 'boost': 5, 'armor': 2, 'weapons': 3}
        },
        {
            'id': 'shipZ',
            'name': 'STARFIGHTER',
            'description': 'HEAVY COMBAT VESSEL WITH DUAL CANNONS',
            'color_scheme': (0.3, 0.3, 0.4),
            'accent': (1.0, 0.5, 0.0),
            'stats': {'speed': 4, 'boost': 2, 'armor': 3, 'weapons': 5}
        }
    ]

    def __init__(self):
        self.skybox = None
        self.animation_time = 0.0
        self.last_input_time = -1.0  # Debouncer for input

        # Carousel state
        self.current_index = 0
        self.target_angle = 0.0
        self.current_angle = 0.0
        self.rotation_speed = 5.0

        # Ship rotation
        self.ship_rotation = 0.0

        # Selection state
        self.is_spinning = False
        self.spin_speed = 0.0
        self.spin_deceleration = 0.5
        self.selected = False

        # Particle effects
        self.particles = []

        # Platform animation
        self.platform_glow = 0.0

        # Stars for background
        self.stars = []

        # Store button rectangles for mouse interaction
        self.button_rects = {}

        # UFO ship model instance for shipM
        self.ufo_model = ShipModel()

        # Enhanced Visuals State
        self.camera_sway_time = 0.0
        self.floor_grid_offset = 0.0
        self.ring_rotations = [0.0, 0.0, 0.0]  # For 3 platform rings
        self.pulse_time = 0.0

    def enter(self):
        print("[ShipSelectState] Ship selection screen")

        # Continue menu music (seamless from welcome state)
        audio = get_audio_manager()
        audio.play_music('MENU')  # Won't restart if already playing

        # Load skybox
        bg_texture = ResourceManager.load_texture("background/stars.jpg")
        self.skybox = Skybox(size=200.0, texture_id=bg_texture)

        # Generate stars
        for _ in range(150):
            self.stars.append({
                'x': random.uniform(-100, 100),
                'y': random.uniform(-60, 60),
                'z': random.uniform(-150, -50),
                'size': random.uniform(0.1, 0.5),
                'twinkle': random.uniform(0, math.pi * 2)
            })

        # Initialize particles
        self._spawn_particles()

    def _spawn_particles(self):
        """Spawn ambient particles around the carousel."""
        self.particles = []
        for _ in range(50):
            angle = random.uniform(0, math.pi * 2)
            radius = random.uniform(8, 15)
            self.particles.append({
                'x': math.cos(angle) * radius,
                'y': random.uniform(-3, 5),
                'z': math.sin(angle) * radius,
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(0.1, 0.5),
                'vz': random.uniform(-0.5, 0.5),
                'life': random.uniform(0.5, 1.0),
                'max_life': 1.0,
                'color': random.choice([(0, 1, 1), (1, 0.5, 0), (0.5, 0.5, 1)])
            })

    def update(self, dt):
        self.animation_time += dt
        self.ship_rotation += dt * 30  # Rotate ships slowly
        self.platform_glow = math.sin(self.animation_time * 3) * 0.3 + 0.7

        # Enhanced animations
        self.camera_sway_time += dt * 0.5
        self.floor_grid_offset = (self.floor_grid_offset + dt * 2.0) % 10.0
        self.ring_rotations[0] += dt * 15.0
        self.ring_rotations[1] -= dt * 10.0
        self.ring_rotations[2] += dt * 25.0
        self.pulse_time += dt * 2.0

        # Update carousel rotation
        if self.is_spinning:
            self.current_angle += self.spin_speed * dt
            self.spin_speed -= self.spin_deceleration * dt * 100

            if self.spin_speed <= 0:
                self.is_spinning = False
                self.spin_speed = 0
                # Snap to nearest ship
                angle_per_ship = 360.0 / len(self.SHIPS)
                self.current_index = int(
                    round(self.current_angle / angle_per_ship)) % len(self.SHIPS)
                self.target_angle = self.current_index * angle_per_ship
        else:
            # Smooth interpolation to target
            diff = self.target_angle - self.current_angle
            # Normalize to -180 to 180
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360
            self.current_angle += diff * self.rotation_speed * dt

        # Update stars twinkle
        for star in self.stars:
            star['twinkle'] += dt * 3

        # Update particles
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['z'] += p['vz'] * dt
            p['life'] -= dt * 0.3

            if p['life'] <= 0:
                # Respawn
                angle = random.uniform(0, math.pi * 2)
                radius = random.uniform(8, 15)
                p['x'] = math.cos(angle) * radius
                p['y'] = -3
                p['z'] = math.sin(angle) * radius
                p['life'] = p['max_life']

    def handle_input(self, event, x, y):
        if self.selected:
            return

        if event[0] == 'KEY_DOWN':
            key = event[1]

            # Left/Right arrows to change selection
            if key == GLUT_KEY_LEFT or key == b'a' or key == b'A':
                self._select_previous()
            elif key == GLUT_KEY_RIGHT or key == b'd' or key == b'D':
                self._select_next()
            # Enter/Space to confirm
            elif key == b'\r' or key == b' ':
                self._confirm_selection()
            # R to spin roulette
            elif key == b'r' or key == b'R':
                self._spin_roulette()

        elif event[0] == 'SPECIAL_KEY_DOWN':
            key = event[1]
            if key == GLUT_KEY_LEFT:
                self._select_previous()
            elif key == GLUT_KEY_RIGHT:
                self._select_next()

        elif event[0] == 'MOUSE_BUTTON':
            button, state = event[1], event[2]
            if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
                # Convert Y coordinate
                h = glutGet(GLUT_WINDOW_HEIGHT)
                gl_y = h - y

                # Check buttons
                if 'select' in self.button_rects:
                    bx, by, bw, bh = self.button_rects['select']
                    if bx <= x <= bx + bw and by <= gl_y <= by + bh:
                        self._confirm_selection()
                        return

                if 'prev' in self.button_rects:
                    bx, by, bw, bh = self.button_rects['prev']
                    if bx <= x <= bx + bw and by <= gl_y <= by + bh:
                        self._select_previous()
                        return

                if 'next' in self.button_rects:
                    bx, by, bw, bh = self.button_rects['next']
                    if bx <= x <= bx + bw and by <= gl_y <= by + bh:
                        self._select_next()
                        return

    def _select_previous(self):
        if not self.is_spinning:
            # Debounce check (0.7s)
            if self.animation_time - self.last_input_time < 0.7:
                return
            self.last_input_time = self.animation_time

            # Play transition sound for ship switching
            from src.core.audio_manager import get_audio_manager
            audio = get_audio_manager()
            audio.play_sfx('transition')

            self.current_index = (self.current_index - 1) % len(self.SHIPS)
            self.target_angle = self.current_index * (360.0 / len(self.SHIPS))

    def _select_next(self):
        if not self.is_spinning:
            # Debounce check (0.7s)
            if self.animation_time - self.last_input_time < 0.7:
                return
            self.last_input_time = self.animation_time

            # Play transition sound for ship switching
            from src.core.audio_manager import get_audio_manager
            audio = get_audio_manager()
            audio.play_sfx('transition')

            self.current_index = (self.current_index + 1) % len(self.SHIPS)
            self.target_angle = self.current_index * (360.0 / len(self.SHIPS))

    def _spin_roulette(self):
        """Start the roulette spin."""
        if not self.is_spinning:
            self.is_spinning = True
            self.spin_speed = random.uniform(300, 500)  # Random initial speed

    def _confirm_selection(self):
        """Confirm ship selection and proceed to game."""
        self.selected = True
        selected_ship = self.SHIPS[self.current_index]

        # Play click sound
        from src.core.audio_manager import get_audio_manager
        audio = get_audio_manager()
        audio.play_sfx('click')

        # Store in session
        GameContext.selected_ship = selected_ship['id']
        print(f"[ShipSelect] Selected: {selected_ship['name']}")

        # Transition to gameplay with fade
        from src.states.gameplay_state import GameplayState
        if hasattr(self, 'state_machine') and self.state_machine:
            new_state = GameplayState()
            new_state.state_machine = self.state_machine
            self.state_machine.change(
                new_state, use_transition=True, duration=0.5)

    def draw(self):
        glClearColor(0.0, 0.0, 0.02, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Setup 3D
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / h, 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Camera looking at carousel
        # Lower camera angle for more dramatic view
        gluLookAt(0, 5, 23,   0, 3, 0,   0, 1, 0)

        # Draw skybox
        if self.skybox:
            glPushMatrix()
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_LIGHTING)
            self.skybox.draw()
            glEnable(GL_DEPTH_TEST)
            glPopMatrix()

        # Draw stars
        self._draw_stars()

        # Draw Holographic Floor
        self._draw_holographic_floor()

        # Enable lighting for 3D objects
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 20.0, 15.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.4, 1.0])

        # Draw carousel platform
        self._draw_platform()

        # Draw ships on carousel
        self._draw_carousel()

        # Draw particles
        self._draw_particles()

        glDisable(GL_LIGHTING)

        # Setup 2D for UI
        UIRenderer.setup_2d(w, h)

        # Draw UI elements
        self._draw_tech_overlay(w, h)  # New background UI
        self._draw_title(w, h)
        self._draw_ship_info(w, h)
        self._draw_stats(w, h)
        self._draw_controls(w, h)
        self._draw_selection_indicator(w, h)

        UIRenderer.restore_3d()

    def _draw_holographic_floor(self):
        """Draws a scrolling sci-fi grid floor."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glPushMatrix()
        glTranslatef(0, -2, 0)

        # Infinite grid effect
        grid_size = 60
        step = 2.0
        offset = self.floor_grid_offset % step

        glLineWidth(1.0)

        # Longitudinal lines
        glColor4f(0.0, 0.2, 0.4, 0.3)
        glBegin(GL_LINES)
        for x in range(-grid_size, grid_size + 1, int(step)):
            glVertex3f(x, 0, -grid_size)
            glVertex3f(x, 0, grid_size)
        glEnd()

        # Lateral lines (moving)
        glBegin(GL_LINES)
        for z in range(-grid_size, grid_size + 1, int(step)):
            z_pos = z + offset
            if z_pos > grid_size:
                continue

            # Fade out in distance
            dist = abs(z_pos) / grid_size
            alpha = 0.3 * (1.0 - dist)
            glColor4f(0.0, 0.2 + alpha, 0.4 + alpha, alpha)

            glVertex3f(-grid_size, 0, z_pos)
            glVertex3f(grid_size, 0, z_pos)
        glEnd()

        glPopMatrix()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_tech_overlay(self, w, h):
        """Draws sci-fi screen details like corners, grids, and data streams."""
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Corner Brackets
        glColor4f(0.0, 0.8, 1.0, 0.5)
        glLineWidth(2.0)
        corner_len = 40
        margin = 20

        # Top-Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(margin, h - margin - corner_len)
        glVertex2f(margin, h - margin)
        glVertex2f(margin + corner_len, h - margin)
        glEnd()

        # Top-Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(w - margin - corner_len, h - margin)
        glVertex2f(w - margin, h - margin)
        glVertex2f(w - margin, h - margin - corner_len)
        glEnd()

        # Bottom-Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(margin, margin + corner_len)
        glVertex2f(margin, margin)
        glVertex2f(margin + corner_len, margin)
        glEnd()

        # Bottom-Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(w - margin - corner_len, margin)
        glVertex2f(w - margin, margin)
        glVertex2f(w - margin, margin + corner_len)
        glEnd()

        # Scanlines
        glColor4f(0.0, 1.0, 1.0, 0.03)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for y in range(0, h, 4):
            glVertex2f(0, y)
            glVertex2f(w, y)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_stars(self):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glPointSize(2.0)
        glBegin(GL_POINTS)
        for star in self.stars:
            brightness = 0.5 + 0.5 * math.sin(star['twinkle'])
            glColor4f(0.8, 0.9, 1.0, brightness)
            glVertex3f(star['x'], star['y'], star['z'])
        glEnd()

        glDisable(GL_BLEND)

    def _draw_platform(self):
        """Draw an enhanced circular platform for the carousel."""
        glPushMatrix()

        # Main platform disc
        glTranslatef(0, -0.5, 0)

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glPushMatrix()
        glRotatef(90, 1, 0, 0)

        quadric = gluNewQuadric()

        # 1. Outer Rotating Ring (Tech Ring)
        glPushMatrix()
        glRotatef(self.ring_rotations[0], 0, 0, 1)
        glColor4f(0.0, 0.3, 0.5, 0.6)
        gluDisk(quadric, 11.0, 12.0, 64, 1)
        # Add details to ring
        glColor4f(0.0, 0.8, 1.0, 0.8)
        for i in range(12):
            glPushMatrix()
            glRotatef(i * 30, 0, 0, 1)
            glTranslatef(11.5, 0, 0)
            glScalef(0.5, 0.1, 1)
            # Draw simple quad marker
            glBegin(GL_QUADS)
            glVertex2f(-0.5, -0.5)
            glVertex2f(0.5, -0.5)
            glVertex2f(0.5, 0.5)
            glVertex2f(-0.5, 0.5)
            glEnd()
            glPopMatrix()
        glPopMatrix()

        # 2. Middle Counter-Rotating Ring
        glPushMatrix()
        glRotatef(self.ring_rotations[1], 0, 0, 1)
        glColor4f(0.0, 0.5, 0.6, 0.4)
        gluDisk(quadric, 9.0, 10.5, 64, 1)
        # Dashed line
        glColor4f(0.0, 1.0, 0.8, 0.5)
        gluDisk(quadric, 9.7, 9.8, 64, 1)
        glPopMatrix()

        # 3. Inner Fast Ring
        glPushMatrix()
        glRotatef(self.ring_rotations[2], 0, 0, 1)
        glColor4f(0.0, 0.6, 1.0, 0.3)
        gluDisk(quadric, 4.0, 6.0, 32, 1)
        glPopMatrix()

        # Center core glow
        core_glow = 0.3 + 0.2 * math.sin(self.animation_time * 2.5)
        glColor4f(0.0, core_glow, core_glow * 1.2, 0.4)
        gluDisk(quadric, 0, 3.5, 32, 1)

        # Bright center point
        glColor4f(0.0, 0.8, 1.0, 0.8)
        gluDisk(quadric, 0, 1.0, 16, 1)

        gluDeleteQuadric(quadric)
        glPopMatrix()

        # Draw hexagonal accent pattern around center
        hex_radius = 3.0
        for i in range(6):
            angle1 = math.radians(i * 60 + self.animation_time * 10)
            angle2 = math.radians((i + 1) * 60 + self.animation_time * 10)

            x1 = math.sin(angle1) * hex_radius
            z1 = math.cos(angle1) * hex_radius
            x2 = math.sin(angle2) * hex_radius
            z2 = math.cos(angle2) * hex_radius

            hex_bright = 0.4 + 0.2 * math.sin(self.animation_time * 4 + i)
            glColor4f(0.0, hex_bright, hex_bright, 0.6)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            glVertex3f(x1, 0.02, z1)
            glVertex3f(x2, 0.02, z2)
            glEnd()

        # Draw triangular markers pointing to ship positions
        num_ships = len(self.SHIPS)
        for i in range(num_ships):
            marker_angle = math.radians(
                i * (360.0 / num_ships) - self.current_angle)

            # Triangle pointing outward at radius 5.5
            tri_r = 7.5
            tri_size = 0.6
            cx = math.sin(marker_angle) * tri_r
            cz = math.cos(marker_angle) * tri_r

            # Calculate perpendicular for triangle width
            perp_angle = marker_angle + math.pi / 2
            px = math.sin(perp_angle) * tri_size
            pz = math.cos(perp_angle) * tri_size

            # Tip pointing outward
            tip_x = math.sin(marker_angle) * (tri_r + 1.0)
            tip_z = math.cos(marker_angle) * (tri_r + 1.0)

            is_selected = (i == self.current_index) and not self.is_spinning
            if is_selected:
                tri_glow = 0.7 + 0.3 * math.sin(self.animation_time * 6)
                glColor4f(0.0, tri_glow, tri_glow, 0.9)
            else:
                glColor4f(0.0, 0.3, 0.4, 0.5)

            glBegin(GL_TRIANGLES)
            glVertex3f(cx - px, 0.02, cz - pz)
            glVertex3f(cx + px, 0.02, cz + pz)
            glVertex3f(tip_x, 0.02, tip_z)
            glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

        # Platform base (dark metallic)
        glColor3f(0.02, 0.04, 0.06)
        glPushMatrix()
        glRotatef(-90, 1, 0, 0)
        quadric = gluNewQuadric()
        gluCylinder(quadric, 10.0, 10.0, 0.3, 64, 1)
        gluDisk(quadric, 0, 10.0, 64, 1)
        gluDeleteQuadric(quadric)
        glPopMatrix()

        # Draw 3D torus rim around the platform edge
        glEnable(GL_LIGHTING)
        glPushMatrix()
        glTranslatef(0, 0.2, 0)  # Raise above platform
        glRotatef(90, 1, 0, 0)  # Lay flat

        # Main torus rim - metallic dark
        set_material_color((0.06, 0.08, 0.1), shininess=100)
        draw_torus(inner_radius=0.35, outer_radius=12.2, sides=24, rings=64)
        glPopMatrix()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)  # Ensure lights render on top

        # Draw rotating lights on the torus rim - MORE VISIBLE
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        num_rim_lights = 48
        rim_rotation = self.animation_time * 50  # Faster rotation

        for i in range(num_rim_lights):
            light_angle = math.radians(
                i * (360.0 / num_rim_lights) + rim_rotation)

            # Position on torus outer edge
            lx = math.sin(light_angle) * 12.2
            lz = math.cos(light_angle) * 12.2
            ly = 0.35  # Higher up on the rim

            # Chase pattern - sequential lights
            chase_offset = (self.animation_time * 6 + i * 0.4) % (math.pi * 2)
            brightness = 0.4 + 0.6 * max(0, math.sin(chase_offset))

            # Outer glow - larger
            glColor4f(0.0, brightness * 0.8, brightness, brightness * 0.5)
            glPointSize(12.0 + brightness * 6)
            glBegin(GL_POINTS)
            glVertex3f(lx, ly, lz)
            glEnd()

            # Inner bright core
            glColor4f(0.2, brightness, brightness * 1.2, brightness)
            glPointSize(6.0 + brightness * 3)
            glBegin(GL_POINTS)
            glVertex3f(lx, ly, lz)
            glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        # Draw enhanced pedestal markers for each ship position
        num_ships = len(self.SHIPS)
        for i in range(num_ships):
            angle = math.radians(i * (360.0 / num_ships) - self.current_angle)
            x = math.sin(angle) * 7
            z = math.cos(angle) * 7

            glPushMatrix()
            glTranslatef(x, 0.1, z)

            is_selected = (i == self.current_index) and not self.is_spinning

            # Pedestal glow ring (below)
            glDisable(GL_LIGHTING)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE)

            if is_selected:
                # Multi-layer glow for selected
                ped_glow = 0.6 + 0.4 * math.sin(self.animation_time * 5)

                # Outer glow
                glColor4f(0.0, ped_glow * 0.5, ped_glow * 0.5, 0.3)
                glPushMatrix()
                glRotatef(90, 1, 0, 0)
                quadric = gluNewQuadric()
                gluDisk(quadric, 2.0, 3.5, 32, 1)
                gluDeleteQuadric(quadric)
                glPopMatrix()

                # Inner bright ring
                glColor4f(0.0, ped_glow, ped_glow, 0.8)
                glPushMatrix()
                glRotatef(90, 1, 0, 0)
                quadric = gluNewQuadric()
                gluDisk(quadric, 1.7, 2.1, 32, 1)
                gluDeleteQuadric(quadric)
                glPopMatrix()
            else:
                glColor4f(0.05, 0.1, 0.15, 0.4)
                glPushMatrix()
                glRotatef(90, 1, 0, 0)
                quadric = gluNewQuadric()
                gluDisk(quadric, 1.5, 2.0, 32, 1)
                gluDeleteQuadric(quadric)
                glPopMatrix()

            glDisable(GL_BLEND)
            glEnable(GL_LIGHTING)

            # Main pedestal cylinder
            if is_selected:
                glColor3f(0.0, 0.35, 0.4)
            else:
                glColor3f(0.08, 0.1, 0.12)

            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            quadric = gluNewQuadric()
            gluCylinder(quadric, 1.7, 1.5, 0.2, 32, 1)
            gluDisk(quadric, 0, 1.7, 32, 1)
            gluDeleteQuadric(quadric)
            glPopMatrix()

            glPopMatrix()

        glPopMatrix()

    def _draw_carousel(self):
        """Draw the ships on the carousel."""
        num_ships = len(self.SHIPS)
        carousel_radius = 7.0

        for i, ship in enumerate(self.SHIPS):
            angle = math.radians(i * (360.0 / num_ships) - self.current_angle)
            x = math.sin(angle) * carousel_radius
            z = math.cos(angle) * carousel_radius

            # Normalize angle for smooth scaling
            norm_angle = angle
            while norm_angle > math.pi:
                norm_angle -= 2 * math.pi
            while norm_angle < -math.pi:
                norm_angle += 2 * math.pi

            # Smooth scale interpolation based on how close to front (0 rad)
            dist = abs(norm_angle)
            # Linear falloff within ~85 degrees
            scale_factor = max(0.0, 1.0 - (dist / 1.5))
            scale_factor = scale_factor * scale_factor  # Quadratic ease-in

            base_scale = 1.5
            max_scale = 2.5
            current_scale = base_scale + \
                (max_scale - base_scale) * scale_factor

            glPushMatrix()
            glTranslatef(x, 1.5, z)

            # Face center
            facing_angle = math.degrees(math.atan2(x, z))
            glRotatef(facing_angle + 180, 0, 1, 0)

            # Add rotation animation
            glRotatef(self.ship_rotation, 0, 1, 0)

            # Apply smooth scale
            glScalef(current_scale, current_scale, current_scale)

            # Bobbing animation
            bob = math.sin(self.animation_time * 2 + i) * 0.2
            glTranslatef(0, bob, 0)

            # Draw simplified ship representation
            # Pass true if scale is near max to trigger any high-detail modes if needed
            self._draw_ship_model(ship, current_scale > 2.0)

            glPopMatrix()

    def _draw_ship_model(self, ship_data, highlighted=False):
        """Draw the actual ship model based on ship data."""
        ship_id = ship_data['id']

        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

        if ship_id == 'shipM':
            # Draw the actual UFO model
            glPushMatrix()
            glScalef(0.35, 0.35, 0.35)  # Scale down for carousel
            # Update animation
            self.ufo_model.update(0.016)  # ~60fps delta
            self.ufo_model.draw()
            glPopMatrix()

        elif ship_id == 'shipS':
            # Draw the actual Bug Crawler model
            glPushMatrix()
            glScalef(0.8, 0.8, 0.8)  # Scale appropriately
            glRotatef(180, 0, 1, 0)  # Face forward
            # Create animation state for the ship
            anim_state = {
                "hover_y": math.sin(self.animation_time * 2) * 0.1,
                "balanceo_pata_z": math.sin(self.animation_time * 3) * 5
            }
            draw_ship_s(anim_state)
            glPopMatrix()

        elif ship_id == 'shipZ':
            # Draw the actual Starfighter model
            glPushMatrix()
            glScalef(0.5, 0.5, 0.5)  # Scale appropriately
            glRotatef(180, 0, 1, 0)  # Face forward
            draw_ship_z()
            glPopMatrix()

    def _draw_particles(self):
        """Draw ambient particles."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        glPointSize(3.0)
        glBegin(GL_POINTS)
        for p in self.particles:
            alpha = p['life'] / p['max_life']
            glColor4f(p['color'][0], p['color'][1], p['color'][2], alpha * 0.5)
            glVertex3f(p['x'], p['y'], p['z'])
        glEnd()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_title(self, w, h):
        """Draw the title with glow effect."""
        title = "SELECT YOUR SHIP"
        title_size = 80  # Slightly smaller for radiospace

        # Get exact width for centering
        _, title_real_width, title_real_height = UIRenderer.get_text_texture(
            title, title_size, font_name="radiospace")
        title_x = (w - title_real_width) / 2
        title_y = h - 180  # Lowered position

        # Pulsing glow
        pulse = 0.7 + 0.3 * math.sin(self.animation_time * 2)

        # Draw glow layers
        for i in range(3):
            offset = (3 - i) * 2
            glow_alpha = (0.3 / (i + 1)) * pulse
            UIRenderer.draw_text(title_x - offset, title_y - offset, title,
                                 size=title_size, color=(0.0, glow_alpha, glow_alpha), font_name="radiospace")

        # Main title
        UIRenderer.draw_text(title_x, title_y, title, size=title_size,
                             color=(0.0, pulse, pulse), font_name="radiospace")

        # Subtitle
        subtitle = "CHOOSE YOUR VESSEL FOR THE JOURNEY"
        sub_size = 24

        # Get exact width for centering
        _, sub_real_width, _ = UIRenderer.get_text_texture(
            subtitle, sub_size, font_name="radiospace")
        sub_x = (w - sub_real_width) / 2

        UIRenderer.draw_text(sub_x, title_y - 50, subtitle, size=sub_size,
                             color=(0.4, 0.5, 0.6), font_name="radiospace")

    def _draw_ship_info(self, w, h):
        """Draw current ship info panel - positioned in bottom-left."""
        if self.is_spinning:
            return

        ship = self.SHIPS[self.current_index]

        # Panel background - Bottom-Left
        panel_w = min(570, w * 0.45)  # Wider
        panel_h = 220
        panel_x = 40
        panel_y = 40

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Dark background with better opacity
        glColor4f(0.0, 0.03, 0.06, 0.92)
        chamfer = 18
        glBegin(GL_POLYGON)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glVertex2f(panel_x, panel_y + chamfer)
        glEnd()

        # Glowing border
        border_glow = 0.6 + 0.2 * math.sin(self.animation_time * 2)
        glLineWidth(2.5)
        glColor3f(0.0, border_glow, border_glow)
        glBegin(GL_LINE_LOOP)
        glVertex2f(panel_x + chamfer, panel_y)
        glVertex2f(panel_x + panel_w - chamfer, panel_y)
        glVertex2f(panel_x + panel_w, panel_y + chamfer)
        glVertex2f(panel_x + panel_w, panel_y + panel_h - chamfer)
        glVertex2f(panel_x + panel_w - chamfer, panel_y + panel_h)
        glVertex2f(panel_x + chamfer, panel_y + panel_h)
        glVertex2f(panel_x, panel_y + panel_h - chamfer)
        glVertex2f(panel_x, panel_y + chamfer)
        glEnd()

        # Inner accent line
        glLineWidth(1.0)
        glColor4f(0.0, 0.4, 0.5, 0.4)
        inner_margin = 8
        glBegin(GL_LINE_LOOP)
        glVertex2f(panel_x + chamfer + inner_margin, panel_y + inner_margin)
        glVertex2f(panel_x + panel_w - chamfer -
                   inner_margin, panel_y + inner_margin)
        glVertex2f(panel_x + panel_w - inner_margin,
                   panel_y + chamfer + inner_margin)
        glVertex2f(panel_x + panel_w - inner_margin,
                   panel_y + panel_h - chamfer - inner_margin)
        glVertex2f(panel_x + panel_w - chamfer - inner_margin,
                   panel_y + panel_h - inner_margin)
        glVertex2f(panel_x + chamfer + inner_margin,
                   panel_y + panel_h - inner_margin)
        glVertex2f(panel_x + inner_margin, panel_y +
                   panel_h - chamfer - inner_margin)
        glVertex2f(panel_x + inner_margin, panel_y + chamfer + inner_margin)
        glEnd()

        glDisable(GL_BLEND)

        # Ship name - LARGER with glow - USE SPACE ARMOR
        name_glow = 0.7 + 0.3 * math.sin(self.animation_time * 3)
        name_y = panel_y + panel_h - 55

        # Dynamic height calculation for name
        _, _, name_h = UIRenderer.get_text_texture(
            ship['name'], 36, font_name="space_armor")

        UIRenderer.draw_text(panel_x + 27, name_y - 2, ship['name'],
                             size=36, color=(0.0, name_glow * 0.3, name_glow * 0.3), font_name="space_armor")
        UIRenderer.draw_text(panel_x + 25, name_y, ship['name'],
                             size=36, color=(0.0, 1.0, 1.0), font_name="space_armor")

        # Separator line under name
        sep_y = name_y - 15
        glColor3f(0.0, 0.5, 0.5)
        glLineWidth(1.5)
        glBegin(GL_LINES)
        glVertex2f(panel_x + 25, sep_y)
        glVertex2f(panel_x + panel_w - 25, sep_y)
        glEnd()

        # Description - LARGER and easier to read - USE RADIOSPACE
        UIRenderer.draw_text(panel_x + 25, sep_y - 35, ship['description'],
                             size=18, color=(0.6, 0.75, 0.85), font_name="radiospace")

    def _draw_stats(self, w, h):
        """Draw ship stats (Speed, Boost) with animated bars."""
        if self.is_spinning:
            return

        ship = self.SHIPS[self.current_index]
        stats = ship['stats']

        # Calculate panel position - Match _draw_ship_info
        panel_w = min(500, w * 0.45)
        panel_h = 220
        panel_x = 40
        panel_y = 40

        bar_w = panel_w - 140  # Dynamic width

        # Draw Speed
        self._draw_stat_bar(panel_x + 25, panel_y + 85,
                            "SPEED", stats['speed'], 5, width=bar_w)

        # Draw Boost
        self._draw_stat_bar(panel_x + 25, panel_y + 45,
                            "BOOST", stats.get('boost', 0), 5, width=bar_w)

    def _draw_stat_bar(self, x, y, label, value, max_val, width=200):
        # Label
        UIRenderer.draw_text(x, y, label, size=16, color=(
            0.0, 0.85, 0.85), font_name="radiospace")

        # Bar dimensions
        bar_x = x + 100  # More space for label
        bar_y = y + 4
        bar_w = width
        bar_h = 12

        # Background track
        glEnable(GL_BLEND)
        glColor4f(0.0, 0.2, 0.3, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + bar_w, bar_y)
        glVertex2f(bar_x + bar_w, bar_y + bar_h)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()

        # Fill
        fill_pct = value / max_val
        fill_w = bar_w * fill_pct

        # Animated fill pattern
        glBegin(GL_QUADS)
        # Gradient fill
        glColor4f(0.0, 0.8, 1.0, 0.8)
        glVertex2f(bar_x, bar_y)
        glColor4f(0.0, 0.4, 0.8, 0.8)
        glVertex2f(bar_x + fill_w, bar_y)
        glVertex2f(bar_x + fill_w, bar_y + bar_h)
        glColor4f(0.0, 0.8, 1.0, 0.8)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()

        # Segments
        glColor4f(0.0, 0.0, 0.0, 0.5)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        for i in range(1, max_val):
            sx = bar_x + (bar_w / max_val) * i
            glVertex2f(sx, bar_y)
            glVertex2f(sx, bar_y + bar_h)
        glEnd()

        glDisable(GL_BLEND)

    def _draw_controls(self, w, h):
        """Draw a big SELECT button instead of control hints."""
        if self.is_spinning:
            return

        # Big SELECT button at the bottom center
        btn_width = 320
        btn_height = 80
        btn_x = (w - btn_width) / 2
        btn_y = 50

        # Button pulse
        pulse = 0.6 + 0.4 * math.sin(self.animation_time * 3)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Button background
        glColor4f(0.0, 0.1, 0.15, 0.9)
        chamfer = 12
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
        glLineWidth(3.0)
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

        # Inner glow line
        glLineWidth(1.5)
        glColor4f(0.0, pulse * 0.5, pulse * 0.5, 0.5)
        inner = 5
        glBegin(GL_LINE_LOOP)
        glVertex2f(btn_x + chamfer + inner, btn_y + inner)
        glVertex2f(btn_x + btn_width - chamfer - inner, btn_y + inner)
        glVertex2f(btn_x + btn_width - inner, btn_y + chamfer + inner)
        glVertex2f(btn_x + btn_width - inner, btn_y +
                   btn_height - chamfer - inner)
        glVertex2f(btn_x + btn_width - chamfer -
                   inner, btn_y + btn_height - inner)
        glVertex2f(btn_x + chamfer + inner, btn_y + btn_height - inner)
        glVertex2f(btn_x + inner, btn_y + btn_height - chamfer - inner)
        glVertex2f(btn_x + inner, btn_y + chamfer + inner)
        glEnd()

        glDisable(GL_BLEND)

        # Button text
        text = "SELECT"
        text_size = 36

        # Dynamic centering
        _, text_w, text_h = UIRenderer.get_text_texture(
            text, text_size, font_name="radiospace")
        text_x = btn_x + (btn_width - text_w) / 2
        text_y = btn_y + (btn_height - text_h) / 2

        # Text glow
        UIRenderer.draw_text(text_x + 2, text_y - 2, text, size=text_size,
                             color=(0.0, pulse * 0.3, pulse * 0.3), font_name="radiospace")
        # Main text
        UIRenderer.draw_text(text_x, text_y, text, size=text_size,
                             color=(0.0, 1.0, 1.0), font_name="radiospace")

        # Store rect
        self.button_rects['select'] = (btn_x, btn_y, btn_width, btn_height)

        # Draw navigation arrows
        self._draw_nav_arrows(w, h)

    def _draw_nav_arrows(self, w, h):
        """Draw clickable navigation arrows on sides."""
        arrow_size = 60
        y_pos = h / 2

        # Left Arrow
        left_x = 50
        pulse = 0.5 + 0.3 * math.sin(self.animation_time * 3)

        UIRenderer.draw_text(left_x, y_pos, "<", size=arrow_size,
                             color=(0.0, pulse, pulse), font_name="radiospace")

        # Store rect (approximate)
        self.button_rects['prev'] = (
            left_x - 20, y_pos - 20, arrow_size + 40, arrow_size + 40)

        # Right Arrow
        right_x = w - 50 - arrow_size
        UIRenderer.draw_text(right_x, y_pos, ">", size=arrow_size,
                             color=(0.0, pulse, pulse), font_name="radiospace")

        # Store rect
        self.button_rects['next'] = (
            right_x - 20, y_pos - 20, arrow_size + 40, arrow_size + 40)

    def _draw_selection_indicator(self, w, h):
        """Draw spinning indicator only when spinning."""
        if self.is_spinning:
            # Show "SPINNING..." text with glow
            text = "SPINNING..."
            text_size = 36

            # Dynamic centering
            _, text_w, _ = UIRenderer.get_text_texture(
                text, text_size, font_name="radiospace")
            x = (w - text_w) / 2
            y = h * 0.15

            pulse = 0.5 + 0.5 * math.sin(self.animation_time * 10)
            # Glow
            UIRenderer.draw_text(x + 2, y - 2, text, size=text_size,
                                 color=(pulse * 0.3, pulse * 0.15, 0.0), font_name="radiospace")
            # Main
            UIRenderer.draw_text(x, y, text, size=text_size,
                                 color=(1.0, pulse, 0.0), font_name="radiospace")
        # No arrows needed - navigation is intuitive
