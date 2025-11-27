"""
Trophy Base - Base trophy class and renderer for planet trophies.
Each planet has a unique trophy that reflects its characteristics.
"""
import math
from OpenGL.GL import *
from OpenGL.GLU import *


class Trophy:
    """
    Base trophy class that renders unique 3D trophy for each planet.
    """

    # Trophy colors for each planet
    TROPHY_COLORS = {
        "Mercury": (0.7, 0.7, 0.7),       # Silver/gray - messenger
        "Venus": (1.0, 0.4, 0.6),         # Pink - goddess of love
        "Earth": (0.2, 0.5, 1.0),         # Blue - blue marble
        "Mars": (0.9, 0.3, 0.2),          # Red - red planet
        "Jupiter": (1.0, 0.8, 0.2),       # Gold/yellow - king of gods
        "Saturn": (0.9, 0.7, 0.3),        # Gold - golden rings
        "Uranus": (0.5, 0.9, 1.0),        # Cyan - ice giant
        "Neptune": (0.2, 0.4, 0.9),       # Deep blue - god of sea
        "Sun": (1.0, 0.6, 0.0)            # Orange - the star
    }

    # Trophy accent colors
    ACCENT_COLORS = {
        "Mercury": (0.9, 0.9, 0.9),
        "Venus": (1.0, 0.8, 0.9),
        "Earth": (0.4, 0.8, 0.4),
        "Mars": (1.0, 0.6, 0.4),
        "Jupiter": (0.8, 0.5, 0.2),
        "Saturn": (1.0, 0.9, 0.5),
        "Uranus": (0.8, 1.0, 1.0),
        "Neptune": (0.4, 0.6, 1.0),
        "Sun": (1.0, 1.0, 0.4)
    }

    def __init__(self, planet_name):
        self.planet_name = planet_name
        self.display_list = None
        self.rotation = 0.0
        self._create_display_list()

    def _create_display_list(self):
        """Create optimized display list for the trophy."""
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)
        self._render_trophy()
        glEndList()

    def _render_trophy(self):
        """Render the trophy based on planet type."""
        color = self.TROPHY_COLORS.get(self.planet_name, (1.0, 0.8, 0.2))
        accent = self.ACCENT_COLORS.get(self.planet_name, (1.0, 1.0, 1.0))

        # Call specific trophy renderer based on planet
        render_func = getattr(
            self, f'_render_{self.planet_name.lower()}_trophy', self._render_default_trophy)
        render_func(color, accent)

    def _render_default_trophy(self, color, accent):
        """Default star trophy."""
        glColor3f(*color)
        self._draw_star(0, 0.5, 0.3, 5)

        # Base pedestal
        glColor3f(*accent)
        self._draw_cylinder(0, -0.2, 0.15, 0.3, 16)

    def _render_mercury_trophy(self, color, accent):
        """Elegant winged messenger trophy for Mercury - classic trophy cup with wings."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Trophy cup bowl (classic trophy shape)
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.15, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.06, 0.16, 0.22, 20, 5)
        glPopMatrix()

        # Cup rim (top lip)
        glPushMatrix()
        glTranslatef(0, 0.37, 0)
        glRotatef(-90, 1, 0, 0)
        gluDisk(quadric, 0.13, 0.17, 20, 2)
        glPopMatrix()

        # Trophy handle horizontal parts
        glPushMatrix()
        glTranslatef(-0.3, 0.17, 0)
        glRotatef(90, 0, 1, 0)
        gluCylinder(quadric, 0.015, 0.015, 0.6, 8, 1)
        glPopMatrix()

        # Cup interior shadow
        glColor3f(color[0] * 0.6, color[1] * 0.6, color[2] * 0.6)
        glPushMatrix()
        glTranslatef(0, 0.37, 0)
        glRotatef(90, 1, 0, 0)
        gluDisk(quadric, 0, 0.13, 20, 1)
        glPopMatrix()

        # Trophy handles (curved like real trophy)
        for side in [-1, 1]:
            # Vertical part of handle
            glPushMatrix()
            glTranslatef(side * 0.26, 0.18, 0)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quadric, 0.015, 0.015, 0.12, 8, 1)
            glPopMatrix()

        # Decorative wings (Mercury's signature)
        glColor3f(*accent)
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 0.12, 0.32, 0)
            glScalef(side, 1, 1)
            self._draw_detailed_wing(0.22)
            glPopMatrix()

        # Trophy stem/neck
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.02, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.035, 0.05, 0.13, 12, 1)
        glPopMatrix()

        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, -0.08, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.08, 0.05, 0.15, 12, 1)
        glPopMatrix()

        # Base - multi-tiered pedestal
        self._draw_trophy_base(0, -0.18, 0.16, 0.1)

        # Star ornament on top
        glColor3f(*accent)
        glPushMatrix()
        glTranslatef(0, 0.42, 0.01)
        self._draw_star(0, 0, 0.06, 5)
        glPopMatrix()

        gluDeleteQuadric(quadric)

    def _render_venus_trophy(self, color, accent):
        """Elegant heart trophy on pedestal for Venus (goddess of love)."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Main 3D heart with depth
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        self._draw_3d_heart(0.22)
        glPopMatrix()

        # Decorative gems around heart
        glColor3f(*accent)
        for i in range(6):
            angle = math.radians(i * 60)
            x = 0.28 * math.cos(angle)
            y = 0.35 + 0.2 * math.sin(angle)
            glPushMatrix()
            glTranslatef(x, y, 0)
            gluSphere(quadric, 0.025, 8, 8)
            glPopMatrix()

        # Elegant thin stem
        glColor3f(0.85, 0.65, 0.75)
        glPushMatrix()
        glTranslatef(0, 0.05, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.025, 0.04, 0.12, 12, 1)
        glPopMatrix()

        # Decorative collar at stem top
        glColor3f(*accent)
        glPushMatrix()
        glTranslatef(0, 0.17, 0)
        glRotatef(-90, 1, 0, 0)
        # Draw torus rim using glutSolidTorus or manual approximation
        inner_radius = 0.015
        outer_radius = 0.04
        for i in range(20):
            theta1 = i * 2 * math.pi / 20
            theta2 = (i + 1) * 2 * math.pi / 20
            glBegin(GL_QUAD_STRIP)
            for j in range(13):
                phi = j * 2 * math.pi / 12
                for theta in [theta1, theta2]:
                    x = (outer_radius + inner_radius *
                         math.cos(phi)) * math.cos(theta)
                    y = (outer_radius + inner_radius *
                         math.cos(phi)) * math.sin(theta)
                    z = inner_radius * math.sin(phi)
                    glVertex3f(x, y, z)
            glEnd()
        glPopMatrix()

        # Base pedestal - heart themed
        glColor3f(0.9, 0.6, 0.7)
        self._draw_trophy_base(0, -0.15, 0.15, 0.1)

        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, -0.08, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.08, 0.05, 0.15, 12, 1)
        glPopMatrix()

        gluDeleteQuadric(quadric)

    def _render_earth_trophy(self, color, accent):
        """Globe trophy on stand for Earth - world championship style."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Globe sphere (Earth)
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        gluSphere(quadric, 0.2, 24, 24)

        # Continent patches (green landmasses)
        glColor3f(*accent)
        # Add multiple smaller spheres to simulate continents
        continent_positions = [
            (0.15, 0.1, 0.1),    # North America area
            (-0.1, 0.05, 0.15),  # Europe area
            (0.05, -0.1, 0.15),  # Africa area
            (-0.15, 0.0, -0.1),  # Asia area
            (0.1, -0.12, -0.1),  # South America area
        ]
        for pos in continent_positions:
            glPushMatrix()
            glTranslatef(*pos)
            gluSphere(quadric, 0.06, 8, 8)
            glPopMatrix()
        glPopMatrix()

        # Tilted ring stand (like a globe stand)
        glColor3f(0.6, 0.5, 0.3)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        glRotatef(23.5, 0, 0, 1)  # Earth's axial tilt
        glRotatef(90, 1, 0, 0)
        gluCylinder(quadric, 0.24, 0.24, 0.015, 24, 1)
        glPopMatrix()

        # Vertical support arc
        glPushMatrix()
        glTranslatef(0, -0.1, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.015, 0.015, 0.3, 8, 1)
        glPopMatrix()

        # Stem
        glColor3f(0.5, 0.4, 0.3)
        glPushMatrix()
        glTranslatef(0, 0.02, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.03, 0.045, 0.15, 12, 1)
        glPopMatrix()

        # Base - elegant wooden style
        glColor3f(0.45, 0.35, 0.2)
        self._draw_trophy_base(0, -0.18, 0.18, 0.1)

        gluDeleteQuadric(quadric)

    def _render_mars_trophy(self, color, accent):
        """Red crystal cluster trophy for Mars - dramatic red crystals."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Main large crystal
        glColor3f(*color)
        self._draw_hex_crystal(0, 0, 0, 0.12, 0.45)

        # Secondary crystals around main
        glColor3f(color[0] * 0.9, color[1] * 0.8, color[2] * 0.8)
        self._draw_hex_crystal(-0.12, 0, 0.05, 0.07, 0.3)
        self._draw_hex_crystal(0.1, 0, -0.06, 0.06, 0.25)

        # Small accent crystals
        glColor3f(*accent)
        self._draw_hex_crystal(-0.08, 0., -0.1, 0.04, 0.18)
        self._draw_hex_crystal(0.14, 0, 0.08, 0.035, 0.15)
        self._draw_hex_crystal(-0.15, 0.0, 0.1, 0.03, 0.12)

        # Rocky Martian base
        glColor3f(0.5, 0.25, 0.15)
        glPushMatrix()
        glTranslatef(0, -0.05, 0)
        glScalef(1.0, 0.4, 1.0)
        gluSphere(quadric, 0.22, 12, 8)
        glPopMatrix()

        # Add small rocks on base
        glColor3f(0.4, 0.2, 0.1)
        for i in range(5):
            angle = math.radians(i * 72 + 15)
            x = 0.15 * math.cos(angle)
            z = 0.15 * math.sin(angle)
            glPushMatrix()
            glTranslatef(x, -0.1, z)
            gluSphere(quadric, 0.04, 6, 6)
            glPopMatrix()

        gluDeleteQuadric(quadric)

    def _render_jupiter_trophy(self, color, accent):
        """Royal crown trophy for Jupiter (king of gods)."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Crown base ring
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.2, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.18, 0.2, 0.08, 20, 2)
        glPopMatrix()

        # Crown points (5 points like royal crown)
        for i in range(5):
            angle = math.radians(i * 72)
            x = 0.15 * math.cos(angle)
            z = 0.15 * math.sin(angle)
            glPushMatrix()
            glTranslatef(x, 0.28, z)
            # Crown point
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quadric, 0.04, 0.0, 0.2, 8, 3)
            glPopMatrix()

        # Gems on crown points
        glColor3f(*accent)
        for i in range(5):
            angle = math.radians(i * 72)
            x = 0.15 * math.cos(angle)
            z = 0.15 * math.sin(angle)
            glPushMatrix()
            glTranslatef(x, 0.46, z)
            gluSphere(quadric, 0.035, 10, 10)
            glPopMatrix()

        # Central large gem
        glColor3f(0.8, 0.2, 0.2)  # Ruby red
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        gluSphere(quadric, 0.05, 12, 12)
        glPopMatrix()

        # Crown band decoration
        glColor3f(color[0] * 0.8, color[1] * 0.7, color[2] * 0.5)
        glPushMatrix()
        glTranslatef(0, 0.24, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.19, 0.19, 0.02, 20, 1)
        glPopMatrix()

        # Trophy stem
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.02, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.04, 0.06, 0.18, 12, 1)
        glPopMatrix()

        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, -0.08, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.08, 0.05, 0.15, 12, 1)
        glPopMatrix()

        # Royal base
        glColor3f(0.7, 0.55, 0.2)
        self._draw_trophy_base(0, -0.18, 0.17, 0.1)

        gluDeleteQuadric(quadric)

    def _render_saturn_trophy(self, color, accent):
        """Ringed planet trophy for Saturn - iconic ringed sphere on stand."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Planet sphere (slightly flattened like Saturn)
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        glScalef(1.0, 0.85, 1.0)
        gluSphere(quadric, 0.18, 20, 20)
        glPopMatrix()

        # Iconic rings - multiple concentric rings
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        glRotatef(25, 1, 0, 0)  # Tilted rings

        # Inner ring
        glColor3f(accent[0] * 0.8, accent[1] * 0.7, accent[2] * 0.6)
        gluDisk(quadric, 0.22, 0.28, 30, 2)

        # Outer ring
        glColor3f(*accent)
        gluDisk(quadric, 0.3, 0.38, 30, 2)

        # Ring gap (dark band)
        glColor3f(color[0] * 0.5, color[1] * 0.4, color[2] * 0.3)
        gluDisk(quadric, 0.28, 0.3, 30, 1)
        glPopMatrix()

        # Band on planet
        glColor3f(color[0] * 0.85, color[1] * 0.8, color[2] * 0.7)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        glRotatef(90, 1, 0, 0)
        gluCylinder(quadric, 0.19, 0.19, 0.02, 20, 1)
        glPopMatrix()

        # Elegant curved support
        glColor3f(0.65, 0.55, 0.25)
        glPushMatrix()
        glTranslatef(0, 0.05, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.03, 0.04, 0.15, 12, 1)
        glPopMatrix()

        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, -0.08, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.08, 0.05, 0.15, 12, 1)
        glPopMatrix()

        # Base - elegant gold style
        glColor3f(0.7, 0.6, 0.25)
        self._draw_trophy_base(0, -0.15, 0.16, 0.1)

        gluDeleteQuadric(quadric)

    def _render_uranus_trophy(self, color, accent):
        """Elegant tilted ice planet trophy for Uranus - the sideways ice giant."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Main ice planet sphere (tilted like Uranus' famous 98° axial tilt)
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.32, 0)
        glRotatef(82, 0, 0, 1)  # Uranus' iconic tilt
        glScalef(1.0, 0.92, 1.0)  # Slightly flattened
        gluSphere(quadric, 0.18, 24, 24)
        glPopMatrix()

        # Tilted ring system (Uranus has vertical rings due to tilt)
        glColor3f(accent[0], accent[1], accent[2])
        glPushMatrix()
        glTranslatef(0, 0.32, 0)
        glRotatef(82, 0, 0, 1)  # Match planet tilt
        glRotatef(90, 1, 0, 0)
        # Inner ring
        gluDisk(quadric, 0.22, 0.26, 32, 2)
        # Outer ring
        glColor4f(accent[0] * 0.8, accent[1] * 0.9, accent[2], 0.7)
        gluDisk(quadric, 0.27, 0.30, 32, 1)
        glPopMatrix()

        # Elegant crystal stand (ice-themed)
        glColor3f(0.6, 0.8, 0.9)
        # Main stem - twisted ice crystal effect
        glPushMatrix()
        glTranslatef(0, 0.0, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.03, 0.05, 0.14, 6, 1)  # Hexagonal like ice
        glPopMatrix()

        # Crystal collar where planet meets stand
        glColor3f(*accent)
        glPushMatrix()
        glTranslatef(0, 0.14, 0)
        glRotatef(-90, 1, 0, 0)
        gluDisk(quadric, 0.02, 0.07, 6, 1)
        glPopMatrix()

        # Decorative ice crystals around base
        glColor3f(0.7, 0.9, 1.0)
        for i in range(6):
            angle = math.radians(i * 60)
            x = 0.12 * math.cos(angle)
            z = 0.12 * math.sin(angle)
            height = 0.08 + 0.03 * math.sin(i * 2)
            glPushMatrix()
            glTranslatef(x, -0.12, z)
            glRotatef(-90, 1, 0, 0)
            glRotatef(i * 15, 0, 0, 1)  # Slight rotation for variety
            gluCylinder(quadric, 0.02, 0.0, height, 6, 1)
            glPopMatrix()

        # Elegant multi-tiered ice base
        glColor3f(0.5, 0.7, 0.85)
        self._draw_trophy_base(0, -0.18, 0.16, 0.1)

        glPushMatrix()
        glTranslatef(0, -0.08, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.08, 0.05, 0.15, 12, 1)
        glPopMatrix()

        # Small accent gems on base corners
        glColor3f(0.4, 0.9, 1.0)
        for i in range(4):
            angle = math.radians(i * 90 + 45)
            x = 0.13 * math.cos(angle)
            z = 0.13 * math.sin(angle)
            glPushMatrix()
            glTranslatef(x, -0.12, z)
            gluSphere(quadric, 0.02, 8, 8)
            glPopMatrix()

        gluDeleteQuadric(quadric)

    def _render_neptune_trophy(self, color, accent):
        """Trident trophy for Neptune (god of the sea) - classic trident on wave base."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Trident shaft
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, -0.1, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.025, 0.03, 0.5, 12, 1)
        glPopMatrix()

        # Trident head crossbar
        glPushMatrix()
        glTranslatef(0, 0.4, 0)
        glRotatef(90, 0, 1, 0)
        gluCylinder(quadric, 0.02, 0.02, 0.12, 8, 1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.4, 0)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(quadric, 0.02, 0.02, 0.12, 8, 1)
        glPopMatrix()

        # Center prong
        glPushMatrix()
        glTranslatef(0, 0.4, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.02, 0.0, 0.18, 8, 1)
        glPopMatrix()

        # Left prong
        glPushMatrix()
        glTranslatef(-0.12, 0.4, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.018, 0.0, 0.14, 8, 1)
        glPopMatrix()

        # Right prong
        glPushMatrix()
        glTranslatef(0.12, 0.4, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.018, 0.0, 0.14, 8, 1)
        glPopMatrix()

        # Decorative element on shaft
        glColor3f(*accent)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        gluSphere(quadric, 0.04, 10, 10)
        glPopMatrix()

        # Wave-themed base
        glColor3f(accent[0] * 0.7, accent[1] * 0.8, accent[2])
        self._draw_wave_pedestal(0, -0.15, 0.18)

        gluDeleteQuadric(quadric)

    def _render_sun_trophy(self, color, accent):
        """Solar sun trophy - radiant sun with rays on golden pedestal."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        # Central sun orb with glow effect
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        gluSphere(quadric, 0.16, 20, 20)
        glPopMatrix()

        # Radiating sun rays (3D pointed rays)
        glColor3f(*accent)
        for i in range(12):
            angle = math.radians(-i * 30)
            x = 0.18 * math.cos(angle)
            y = 0.38 + 0.18 * math.sin(angle)
            length = 0.18 if i % 2 == 0 else 0.12  # Alternating long/short rays

            glPushMatrix()
            glTranslatef(x, y, 0)
            glRotatef(i * -30, 0, 0, 1)
            glRotatef(90, 0, 1, 0)
            gluCylinder(quadric, 0.025, 0.0, length, 6, 1)
            glPopMatrix()

        # Inner glow ring
        glColor3f(color[0], color[1] * 0.9, color[2] * 0.6)
        glPushMatrix()
        glTranslatef(0, 0.38, 0.01)
        gluDisk(quadric, 0.14, 0.2, 20, 1)
        glPopMatrix()

        # Corona effect (outer glow)
        glColor4f(accent[0], accent[1], accent[2], 0.3)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        glTranslatef(0, 0.38, 0)
        gluSphere(quadric, 0.22, 16, 16)
        glPopMatrix()
        glDisable(GL_BLEND)

        # Elegant stem
        glColor3f(0.85, 0.6, 0.2)
        glPushMatrix()
        glTranslatef(0, 0.02, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.03, 0.05, 0.15, 12, 1)
        glPopMatrix()

        glColor3f(*color)
        glPushMatrix()
        glTranslatef(0, -0.08, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.08, 0.05, 0.15, 12, 1)
        glPopMatrix()

        # Golden sun base
        glColor3f(0.8, 0.5, 0.15)
        self._draw_trophy_base(0, -0.18, 0.17, 0.1)

        gluDeleteQuadric(quadric)

    # Helper drawing methods
    def _draw_star(self, x, y, size, points):
        """Draw a 2D star shape."""
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(x, y, 0)
        for i in range(points * 2 + 1):
            angle = math.pi / 2 + i * math.pi / points
            r = size if i % 2 == 0 else size * 0.4
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            glVertex3f(px, py, 0)
        glEnd()

    def _draw_cylinder(self, x, y, radius, height, slices):
        """Draw a cylinder."""
        quadric = gluNewQuadric()
        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, radius, radius, height, slices, 1)
        gluDisk(quadric, 0, radius, slices, 1)
        glTranslatef(0, 0, height)
        gluDisk(quadric, 0, radius, slices, 1)
        glPopMatrix()
        gluDeleteQuadric(quadric)

    def _draw_wing(self, size):
        """Draw a wing shape."""
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(size, 0.1, 0)
        glVertex3f(size * 0.7, 0.15, 0)

        glVertex3f(0, 0, 0)
        glVertex3f(size * 0.7, 0.15, 0)
        glVertex3f(size * 0.5, 0.2, 0)

        glVertex3f(0, 0, 0)
        glVertex3f(size * 0.5, 0.2, 0)
        glVertex3f(size * 0.3, 0.15, 0)
        glEnd()

    def _draw_heart(self, x, y, size):
        """Draw a 3D heart shape."""
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(x, y - size * 0.5, 0)
        for i in range(37):
            angle = math.radians(i * 10)
            hx = size * 0.5 * (16 * math.sin(angle) ** 3) / 16
            hy = size * 0.5 * (13 * math.cos(angle) - 5 * math.cos(2*angle) -
                               2 * math.cos(3*angle) - math.cos(4*angle)) / 16
            glVertex3f(x + hx, y + hy, 0)
        glEnd()

    def _draw_diamond(self, x, y, size):
        """Draw a small diamond sparkle."""
        glBegin(GL_TRIANGLES)
        glVertex3f(x, y + size, 0)
        glVertex3f(x - size * 0.5, y, 0)
        glVertex3f(x + size * 0.5, y, 0)

        glVertex3f(x, y - size, 0)
        glVertex3f(x - size * 0.5, y, 0)
        glVertex3f(x + size * 0.5, y, 0)
        glEnd()

    def _draw_crystal(self, x, y, base_size, height):
        """Draw a crystal shape."""
        glBegin(GL_TRIANGLES)
        # Four faces of crystal
        for i in range(4):
            angle1 = math.radians(i * 90)
            angle2 = math.radians((i + 1) * 90)
            x1 = x + base_size * math.cos(angle1)
            z1 = base_size * math.sin(angle1)
            x2 = x + base_size * math.cos(angle2)
            z2 = base_size * math.sin(angle2)

            # Top point
            glVertex3f(x, y + height, 0)
            glVertex3f(x1, y, z1)
            glVertex3f(x2, y, z2)
        glEnd()

    def _draw_rocky_base(self, x, y, width, height):
        """Draw an irregular rocky base."""
        quadric = gluNewQuadric()
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(1.0, 0.6, 1.0)
        gluSphere(quadric, width, 8, 6)
        glPopMatrix()
        gluDeleteQuadric(quadric)

    def _draw_lightning_bolt(self, x, y, height):
        """Draw a lightning bolt shape."""
        glBegin(GL_TRIANGLES)
        # Main bolt
        glVertex3f(x + 0.1, y + height * 0.5, 0)
        glVertex3f(x - 0.05, y + height * 0.2, 0)
        glVertex3f(x + 0.05, y + height * 0.25, 0)

        glVertex3f(x + 0.05, y + height * 0.25, 0)
        glVertex3f(x - 0.05, y + height * 0.2, 0)
        glVertex3f(x - 0.1, y - height * 0.5, 0)

        glVertex3f(x + 0.05, y + height * 0.25, 0)
        glVertex3f(x - 0.1, y - height * 0.5, 0)
        glVertex3f(x + 0.02, y, 0)
        glEnd()

    def _draw_cloudy_base(self, x, y, size):
        """Draw a cloudy base."""
        quadric = gluNewQuadric()
        for i in range(5):
            angle = math.radians(i * 72)
            cx = x + size * 0.5 * math.cos(angle)
            cz = size * 0.5 * math.sin(angle)
            glPushMatrix()
            glTranslatef(cx, y, cz)
            gluSphere(quadric, size * 0.4, 8, 8)
            glPopMatrix()
        gluDeleteQuadric(quadric)

    def _draw_elegant_base(self, x, y, size):
        """Draw an elegant pedestal base."""
        quadric = gluNewQuadric()
        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(-90, 1, 0, 0)
        # Bottom disk
        gluDisk(quadric, 0, size * 1.2, 16, 1)
        # Middle section
        gluCylinder(quadric, size, size * 0.8, 0.1, 16, 1)
        glTranslatef(0, 0, 0.1)
        gluCylinder(quadric, size * 0.8, size * 0.6, 0.1, 16, 1)
        glPopMatrix()
        gluDeleteQuadric(quadric)

    def _draw_diamond_3d(self, x, y, size):
        """Draw a 3D diamond shape."""
        glBegin(GL_TRIANGLES)
        # Top pyramid
        for i in range(6):
            angle1 = math.radians(i * 60)
            angle2 = math.radians((i + 1) * 60)
            x1 = x + size * 0.5 * math.cos(angle1)
            z1 = size * 0.5 * math.sin(angle1)
            x2 = x + size * 0.5 * math.cos(angle2)
            z2 = size * 0.5 * math.sin(angle2)

            glVertex3f(x, y + size, 0)
            glVertex3f(x1, y, z1)
            glVertex3f(x2, y, z2)

            # Bottom pyramid
            glVertex3f(x, y - size * 0.5, 0)
            glVertex3f(x2, y, z2)
            glVertex3f(x1, y, z1)
        glEnd()

    def _draw_ice_crystal(self, x, y, z, size):
        """Draw a small ice crystal."""
        glPushMatrix()
        glTranslatef(x, y, z)
        glBegin(GL_LINES)
        # Vertical line
        glVertex3f(0, -size, 0)
        glVertex3f(0, size, 0)
        # Horizontal lines
        for angle in [0, 60, 120]:
            rad = math.radians(angle)
            dx = size * 0.7 * math.cos(rad)
            dz = size * 0.7 * math.sin(rad)
            glVertex3f(-dx, 0, -dz)
            glVertex3f(dx, 0, dz)
        glEnd()
        glPopMatrix()

    def _draw_trident(self, x, y, height):
        """Draw a trident shape."""
        glLineWidth(3.0)
        glBegin(GL_LINES)
        # Main shaft
        glVertex3f(x, y, 0)
        glVertex3f(x, y + height * 0.7, 0)

        # Center prong
        glVertex3f(x, y + height * 0.7, 0)
        glVertex3f(x, y + height, 0)

        # Left prong
        glVertex3f(x - 0.1, y + height * 0.6, 0)
        glVertex3f(x - 0.15, y + height * 0.9, 0)

        # Right prong
        glVertex3f(x + 0.1, y + height * 0.6, 0)
        glVertex3f(x + 0.15, y + height * 0.9, 0)

        # Cross bar
        glVertex3f(x - 0.1, y + height * 0.6, 0)
        glVertex3f(x + 0.1, y + height * 0.6, 0)
        glEnd()
        glLineWidth(1.0)

    def _draw_wave_base(self, x, y, size):
        """Draw a wave-themed base."""
        glBegin(GL_TRIANGLE_STRIP)
        for i in range(21):
            angle = math.radians(i * 18)
            wave = 0.05 * math.sin(i * 0.8)
            outer = size + wave
            inner = size * 0.5 + wave
            glVertex3f(x + outer * math.cos(angle), y +
                       0.05, outer * math.sin(angle))
            glVertex3f(x + inner * math.cos(angle), y -
                       0.05, inner * math.sin(angle))
        glEnd()

    def _draw_ray(self, x, y, length, angle):
        """Draw a sun ray."""
        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(angle, 0, 0, 1)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(length, 0.02, 0)
        glVertex3f(length, -0.02, 0)
        glEnd()
        glPopMatrix()

    # New helper methods for detailed trophy models
    def _draw_trophy_base(self, x, y, radius, height):
        """Draw a multi-tiered trophy pedestal base."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        glPushMatrix()
        glTranslatef(x, y, 0)
        glRotatef(-90, 1, 0, 0)

        # Bottom tier (largest)
        gluDisk(quadric, 0, radius * 1.2, 16, 1)
        gluCylinder(quadric, radius * 1.2, radius * 1.0, height * 0.3, 16, 1)
        glTranslatef(0, 0, height * 0.3)

        # Middle tier
        gluDisk(quadric, 0, radius * 1.0, 16, 1)
        gluCylinder(quadric, radius * 1.0, radius * 0.7, height * 0.4, 16, 1)
        glTranslatef(0, 0, height * 0.4)

        # Top tier (smallest)
        gluDisk(quadric, 0, radius * 0.7, 16, 1)
        gluCylinder(quadric, radius * 0.7, radius * 0.5, height * 0.3, 16, 1)
        glTranslatef(0, 0, height * 0.3)
        gluDisk(quadric, 0, radius * 0.5, 16, 1)

        glPopMatrix()
        gluDeleteQuadric(quadric)

    def _draw_detailed_wing(self, size):
        """Draw a more detailed feathered wing shape."""
        # Main wing surface
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)  # Wing base
        glVertex3f(size * 0.3, 0.08, 0)
        glVertex3f(size * 0.6, 0.12, 0)
        glVertex3f(size * 0.85, 0.1, 0)
        glVertex3f(size, 0.05, 0)
        glVertex3f(size * 0.9, -0.02, 0)
        glVertex3f(size * 0.7, -0.05, 0)
        glVertex3f(size * 0.4, -0.03, 0)
        glEnd()

        # Feather details (lines)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for i in range(5):
            t = (i + 1) / 6.0
            x1 = size * t * 0.3
            y1 = 0.02 * t
            x2 = size * t
            y2 = 0.12 - 0.1 * t
            glVertex3f(x1, y1, 0)
            glVertex3f(x2, y2, 0)
        glEnd()

    def _draw_3d_heart(self, size):
        """Draw a 3D heart shape with depth."""
        quadric = gluNewQuadric()
        # Two spheres for heart top lobes
        glPushMatrix()
        glTranslatef(-size * 0.25, size * 0.15, 0)
        glScalef(1.0, 1.0, 0.4)
        gluSphere(quadric, size * 0.35, 16, 16)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(size * 0.25, size * 0.15, 0)
        glScalef(1.0, 1.0, 0.4)
        gluSphere(quadric, size * 0.35, 16, 16)
        glPopMatrix()

        # Heart point (cone pointing down)
        glPushMatrix()
        glTranslatef(0, -size * 0.05, 0)
        glScalef(1.0, 1.0, 0.35)
        glRotatef(90, 1, 0, 0)
        gluCylinder(quadric, size * 0.45, 0, size * 0.5, 16, 4)
        glPopMatrix()

        gluDeleteQuadric(quadric)

    def _draw_hex_crystal(self, x, y, z, base_radius, height):
        """Draw a hexagonal crystal prism with pointed top."""
        glPushMatrix()
        glTranslatef(x, y, z)

        # Hexagonal prism body
        glBegin(GL_QUAD_STRIP)
        for i in range(7):
            angle = math.radians(i * 60)
            bx = base_radius * math.cos(angle)
            bz = base_radius * math.sin(angle)
            glVertex3f(bx, 0, bz)
            glVertex3f(bx * 0.9, height * 0.7, bz * 0.9)
        glEnd()

        # Pointed top
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, height, 0)  # Apex
        for i in range(7):
            angle = math.radians(i * 60)
            tx = base_radius * 0.9 * math.cos(angle)
            tz = base_radius * 0.9 * math.sin(angle)
            glVertex3f(tx, height * 0.7, tz)
        glEnd()

        # Bottom cap
        glBegin(GL_POLYGON)
        for i in range(6):
            angle = math.radians(i * 60)
            glVertex3f(base_radius * math.cos(angle),
                       0, base_radius * math.sin(angle))
        glEnd()

        glPopMatrix()

    def _draw_faceted_gem(self, x, y, z, size):
        """Draw a faceted gem (diamond cut style)."""
        glPushMatrix()
        glTranslatef(x, y, z)

        # Crown (top octagonal pyramid)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, size * 0.6, 0)  # Top point
        for i in range(9):
            angle = math.radians(i * 45)
            gx = size * 0.7 * math.cos(angle)
            gz = size * 0.7 * math.sin(angle)
            glVertex3f(gx, size * 0.2, gz)
        glEnd()

        # Girdle (middle band)
        glBegin(GL_QUAD_STRIP)
        for i in range(9):
            angle = math.radians(i * 45)
            gx = size * 0.7 * math.cos(angle)
            gz = size * 0.7 * math.sin(angle)
            glVertex3f(gx, size * 0.2, gz)
            glVertex3f(gx * 0.85, 0, gz * 0.85)
        glEnd()

        # Pavilion (bottom pyramid)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, -size * 0.5, 0)  # Bottom point
        for i in range(9):
            angle = math.radians(i * 45)
            gx = size * 0.7 * 0.85 * math.cos(angle)
            gz = size * 0.7 * 0.85 * math.sin(angle)
            glVertex3f(gx, 0, gz)
        glEnd()

        glPopMatrix()

    def _draw_wave_pedestal(self, x, y, size):
        """Draw a wave-themed pedestal base for Neptune trophy."""
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)

        glPushMatrix()
        glTranslatef(x, y, 0)

        # Base disk
        glRotatef(-90, 1, 0, 0)
        gluDisk(quadric, 0, size * 1.1, 16, 1)

        # Wave rings (undulating surface)
        for ring in range(3):
            radius = size * (0.9 - ring * 0.2)
            height = 0.03 + ring * 0.02
            glPushMatrix()
            glTranslatef(0, 0, ring * 0.03)
            gluCylinder(quadric, radius + 0.02, radius, height, 16, 1)
            glPopMatrix()

        glPopMatrix()
        gluDeleteQuadric(quadric)

    def render(self, x=0, y=0, z=0, scale=1.0, rotation=None):
        """Render the trophy at the given position."""
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(scale, scale, scale)
        if rotation is not None:
            glRotatef(rotation, 0, 1, 0)
        elif self.rotation != 0:
            glRotatef(self.rotation, 0, 1, 0)

        if self.display_list:
            glCallList(self.display_list)
        glPopMatrix()

    def update(self, dt):
        """Update trophy animation (rotation)."""
        self.rotation += 45 * dt  # 45 degrees per second
        if self.rotation >= 360:
            self.rotation -= 360

    def cleanup(self):
        """Clean up OpenGL resources."""
        if self.display_list:
            glDeleteLists(self.display_list, 1)
            self.display_list = None


class TrophyRenderer:
    """
    Manages rendering of multiple trophies for the trophy collection display.
    """

    def __init__(self):
        self.trophies = {}  # planet_name -> Trophy
        self._create_all_trophies()

    def _create_all_trophies(self):
        """Pre-create all trophy models."""
        for planet in Trophy.TROPHY_COLORS.keys():
            self.trophies[planet] = Trophy(planet)

    def get_trophy(self, planet_name):
        """Get trophy for a specific planet."""
        return self.trophies.get(planet_name)

    def render_trophy(self, planet_name, x=0, y=0, z=0, scale=1.0, rotation=None):
        """Render a specific planet's trophy."""
        trophy = self.trophies.get(planet_name)
        if trophy:
            trophy.render(x, y, z, scale, rotation)

    def render_collection(self, earned_trophies, x_start=0, y=0, z=0, spacing=0.8, scale=0.5):
        """
        Render a collection of earned trophies in a row.
        earned_trophies: dict of planet_name -> trophy_type or list of planet names
        """
        if isinstance(earned_trophies, dict):
            planets = list(earned_trophies.keys())
        else:
            planets = list(earned_trophies)

        for i, planet in enumerate(planets):
            x = x_start + i * spacing
            self.render_trophy(planet, x, y, z, scale)

    def update_all(self, dt):
        """Update all trophy animations."""
        for trophy in self.trophies.values():
            trophy.update(dt)

    def cleanup(self):
        """Clean up all trophy resources."""
        for trophy in self.trophies.values():
            trophy.cleanup()
        self.trophies.clear()
