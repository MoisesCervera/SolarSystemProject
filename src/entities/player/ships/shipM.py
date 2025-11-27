"""
Ship model module.
Defines a UFO/flying saucer spaceship built from primitive shapes.
"""

from OpenGL.GL import *
from src.graphics.draw_utils import *
import math


class ShipModel:
    COLORS = {
        'red': (1.0, 0.2, 0.2),
        'green': (0.2, 1.0, 0.2),
        'blue': (0.2, 0.4, 1.0),
        'yellow': (1.0, 1.0, 0.2),
        'cyan': (0.2, 1.0, 1.0),
        'magenta': (1.0, 0.2, 1.0),
        'white': (1.0, 1.0, 1.0),
        'gray': (0.5, 0.5, 0.5),
        'dark_gray': (0.3, 0.3, 0.3),
        'orange': (1.0, 0.5, 0.0),
        'purple': (0.6, 0.2, 0.8),
    }
    """
    Represents a classic UFO/flying saucer.

    The UFO is composed of:
    - Main saucer body (flattened disc using cylinders)
    - Transparent dome (hemisphere with transparency)
    - Bottom dome (inverted hemisphere)
    - Rim lights (repeating pattern around the edge)
    - Optional landing gear or details

    Attributes:
        position (list): Ship position [x, y, z]
        rotation (list): Ship rotation [x, y, z] in degrees
        scale (float): Overall scale multiplier
        light_phase (float): Light animation phase for rim lights
    """

    def __init__(self, position=None, rotation=None, scale=1.0):
        """
        Initialize the UFO model.

        Args:
            position (list): Initial position [x, y, z]
            rotation (list): Initial rotation [x, y, z]
            scale (float): Scale factor
        """
        self.position = position or [0.0, 0.0, 0.0]
        self.rotation = rotation or [0.0, 0.0, 0.0]
        self.scale = scale
        self.light_phase = 0.0
        self.animation_time = 0.0

        # UFO proportions (all literal for easy editing)
        # Main saucer disc
        self.saucer_radius = 3.5
        self.saucer_height = 0.3

        # Dome
        self.dome_radius = 1.5
        self.dome_height = 0.6

        # Propulsors
        self.propulsor_count = 5
        self.propulsor_radius = 0.4

        # Rim details - OPTIMIZED: reduced light counts for performance
        self.rim_light_count = 8  # Reduced from 16 for performance
        self.rim_light_radius = 0.2
        self.dome_rim_light_count = 12  # Reduced from 24 for performance

        # Display list for static geometry (compiled once)
        self._static_display_list = None
        self._is_compiled = False

        # CINEMATIC COLORS - More vibrant and atmospheric
        # Metallic hull with blue-tinted steel
        self.saucer_main = (0.55, 0.6, 0.65)   # Lighter steel blue
        self.saucer_dark = (0.25, 0.28, 0.35)  # Dark blue-gray metallic
        self.saucer_accent = (0.35, 0.42, 0.5)  # Medium blue accent

        # Dome - more vibrant cyan with higher transparency
        # Bright cyan, more transparent
        self.dome_color = (0.2, 0.7, 0.9, 0.25)

        # Lights - bright electric blue/cyan
        self.light_color_off = (0.05, 0.08, 0.15)  # Deep blue when off
        self.light_color_on = (0.3, 0.8, 1.0)      # Bright electric cyan

        # Bottom - darker for contrast
        self.bottom_color = (0.15, 0.18, 0.22)  # Very dark blue-gray

        # Propulsors - bright red/orange glow
        self.propulsor_glow_color = (1.0, 0.2, 0.1)  # Bright red-orange
        self.propulsor_rim_color = (0.1, 0.1, 0.1)
        self.propulsor_inner_color = (1.0, 0.4, 0.1)  # Bright orange core

        # Abduction beam
        self.beam_color = (0.4, 0.9, 1.0, 0.2)  # Bright cyan with transparency
        self.beam_intensity = 0.0  # Animated beam intensity

    def update(self, delta_time):
        """
        Update UFO animation and effects.

        Args:
            delta_time (float): Time since last update in seconds
        """
        self.animation_time += delta_time

        # Animate rim lights (rotating pattern)
        self.light_phase += delta_time * 2.0  # Speed of light rotation

        # Pulsate abduction beam
        self.beam_intensity = 0.5 + 0.5 * math.sin(self.animation_time * 3.0)

    def _compile_static_geometry(self):
        """Compile static UFO geometry into a display list for performance."""
        if self._static_display_list is not None:
            glDeleteLists(self._static_display_list, 1)

        self._static_display_list = glGenLists(1)
        glNewList(self._static_display_list, GL_COMPILE)

        # Static components (no animation)
        self._draw_bottom_hull()
        self._draw_propulsors()
        self._draw_main_saucer()
        self._draw_rim_details()

        glEndList()
        self._is_compiled = True

    def draw(self):
        """Draw the complete UFO model."""
        # Compile static geometry on first draw
        if not self._is_compiled:
            self._compile_static_geometry()

        glPushMatrix()

        # Apply model transformation
        glTranslatef(*self.position)
        glRotatef(self.rotation[1], 0, 1, 0)  # Yaw
        glRotatef(self.rotation[0], 1, 0, 0)  # Pitch
        glRotatef(self.rotation[2], 0, 0, 1)  # Roll
        glScalef(self.scale, self.scale, self.scale)

        glTranslate(0, 1.3, 0)

        # Draw static geometry from display list (fast)
        if self._static_display_list is not None:
            glCallList(self._static_display_list)

        # Draw animated components (must be drawn each frame)
        self._draw_rim_lights()
        self._draw_abduction_beam()
        self._draw_dome()  # Transparent dome last
        self._draw_dome_rim_lights()

        glPopMatrix()

    def _draw_main_saucer(self):
        """Draw the main flying saucer disc using cylinders."""
        glPushMatrix()

        # Main disc body - wide at middle, tapered at edges
        # Bottom half of disc
        glPushMatrix()
        glTranslatef(0, -self.saucer_height / 2, 0)
        draw_cylinder(
            base_radius=2.6,      # Wide at bottom (proportional to 3.5)
            top_radius=3.5,       # Wider at middle
            height=self.saucer_height / 2,
            slices=32,
            stacks=1,
            color=self.saucer_main
        )
        glPopMatrix()

        # Top half of disc
        glPushMatrix()
        glTranslatef(0, 0.15, 0)
        draw_cylinder(
            base_radius=3.5,      # Wide at middle
            top_radius=2.6,       # Tapered at top (proportional)
            height=self.saucer_height / 1.5,
            slices=32,
            stacks=1,
            color=self.saucer_accent
        )
        glPopMatrix()

        glPopMatrix()

    def _draw_bottom_hull(self):
        """Draw the bottom dome/hull of the UFO."""
        glPushMatrix()

        # Position at bottom of saucer
        glTranslatef(0, -0.5, 0)

        # Draw inverted hemisphere for bottom
        glPushMatrix()
        glRotatef(180, 1, 0, 0)  # Flip upside down
        glColor3f(*self.bottom_color)
        draw_cylinder(2.6, 0.8, 0.7)  # Proportional to new size
        glPopMatrix()

        glPopMatrix()

    def _draw_propulsors(self):
        """Draw red propulsors with torus rims on the bottom of the UFO."""
        glPushMatrix()

        propulsor_ring_radius = 2.5  # Distance from center
        propulsor_height = -0.25       # Height position (below hull)

        # Draw propulsors in a triangular pattern (3 propulsors)
        for i in range(self.propulsor_count):
            # Calculate angle for this propulsor (120 degrees apart)
            angle = (2 * math.pi * i) / self.propulsor_count

            glPushMatrix()

            # Position the propulsor
            x = propulsor_ring_radius * math.cos(angle)
            z = propulsor_ring_radius * math.sin(angle)
            glTranslatef(x, propulsor_height, z)

            # Draw torus rim (dark red)
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            draw_torus(
                inner_radius=0.15,
                outer_radius=self.propulsor_radius,
                color=self.propulsor_rim_color
            )
            glPopMatrix()

            # Draw glowing propulsor core (bright red-orange sphere)
            draw_sphere(
                radius=self.propulsor_radius * 0.7,
                slices=16,
                stacks=16,
                color=self.propulsor_glow_color
            )

            # Draw bright inner core (orange glow)
            draw_sphere(
                radius=self.propulsor_radius * 0.4,
                slices=12,
                stacks=12,
                color=self.propulsor_inner_color
            )

            glPopMatrix()

        glPopMatrix()

    def _draw_dome(self):
        """Draw the transparent dome/cockpit on top."""
        glPushMatrix()

        # Dome rim
        glPushMatrix()
        glTranslatef(0, 0.3, 0)
        glRotatef(90, 1, 0, 0)
        draw_torus(
            inner_radius=0.15,
            outer_radius=1.5,  # Proportional to new dome size
            color=self.saucer_dark
        )
        glPopMatrix()

        # Position dome on top of saucer
        glTranslatef(0, self.saucer_height / 2, 0)

        # Enable transparency for the dome
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # Keep depth write enabled so dome properly occludes objects behind it
        glDepthMask(GL_TRUE)

        # Draw transparent hemisphere dome with increased opacity
        # Using slightly more opaque dome to reduce optical illusion
        dome_color_adjusted = (
            self.dome_color[0],
            self.dome_color[1],
            self.dome_color[2],
            0.35  # Increased from 0.25 to 0.35 for better depth perception
        )

        draw_half_sphere(
            radius=self.dome_radius,
            slices=32,
            stacks=16,
            upper=True,
            closed=False,  # No bottom cap (open to saucer)
            color=dome_color_adjusted
        )

        # Restore normal rendering
        glDisable(GL_BLEND)

        glPopMatrix()

    def _draw_rim_details(self):
        """Draw metallic rim detail around the edge."""
        glPushMatrix()

        # Rim band around the widest part
        glTranslatef(0, 0, 0)
        draw_cylinder(
            # Slightly larger than main disc (proportional)
            base_radius=3.6,
            top_radius=3.6,
            height=0.15,          # Thin band
            slices=32,
            stacks=1,
            color=self.saucer_dark
        )

        glPopMatrix()

    def _draw_rim_lights(self):
        """Draw repeating lights around the rim using a for loop."""
        glPushMatrix()

        light_ring_radius = 3.6  # Distance from center (proportional)
        light_height = 0.0         # Height position (at rim level)

        # Draw lights in a circle around the rim
        for i in range(self.rim_light_count):
            # Calculate angle for this light
            angle = (2 * math.pi * i) / self.rim_light_count

            # Animate lights (chase pattern)
            light_offset = (self.light_phase + i * 0.3) % (2 * math.pi)
            brightness = 0.5 + 0.5 * math.sin(light_offset)

            # Interpolate between on and off colors
            light_color = (
                self.light_color_off[0] + (self.light_color_on[0] -
                                           self.light_color_off[0]) * brightness,
                self.light_color_off[1] + (self.light_color_on[1] -
                                           self.light_color_off[1]) * brightness,
                self.light_color_off[2] + (self.light_color_on[2] -
                                           self.light_color_off[2]) * brightness
            )

            glPushMatrix()

            # Position at the rim
            x = light_ring_radius * math.cos(angle)
            z = light_ring_radius * math.sin(angle)
            glTranslatef(x, light_height, z)

            # Rotate to lean toward center (point inward)
            # Calculate angle to center in XZ plane
            angle_to_center = math.atan2(-z, -x) * 180 / math.pi
            # Rotate around Y to face center
            glRotatef(angle_to_center, 0, 1, 0)
            glRotatef(45, 1, 0, 0)  # Tilt down 45 degrees toward center

            # Draw light sphere - OPTIMIZED: reduced polygon count
            draw_sphere(
                radius=self.rim_light_radius,
                slices=8,
                stacks=6,
                color=light_color
            )

            glPopMatrix()

        glPopMatrix()

    def _draw_abduction_beam(self):
        """Draw the pulsating abduction beam from below the UFO."""
        glPushMatrix()

        # Position beam at bottom center
        glTranslatef(0, -2.3, 0)

        # Enable transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)

        # Calculate beam color with pulsating alpha
        beam_alpha = self.beam_color[3] * self.beam_intensity
        beam_color_pulsed = (
            self.beam_color[0],
            self.beam_color[1],
            self.beam_color[2],
            beam_alpha
        )

        # Draw main beam cylinder (widens as it goes down)
        glPushMatrix()
        glRotatef(180, 1, 0, 0)  # Point downward
        draw_cylinder(
            base_radius=0.3,      # Narrow at UFO
            top_radius=1.2,       # Wide at bottom
            height=3.0,           # Long beam
            slices=32,
            stacks=1,
            color=beam_color_pulsed
        )
        glPopMatrix()

        # Draw inner bright core
        brighter_beam = (
            min(1.0, self.beam_color[0] * 1.5),
            min(1.0, self.beam_color[1] * 1.5),
            min(1.0, self.beam_color[2] * 1.5),
            beam_alpha * 1.5
        )

        glPushMatrix()
        glRotatef(180, 1, 0, 0)
        draw_cylinder(
            base_radius=0.15,
            top_radius=0.6,
            height=3.0,
            slices=16,
            stacks=1,
            color=brighter_beam
        )
        glPopMatrix()

        # Restore normal rendering
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

        glPopMatrix()

    def _draw_dome_rim_lights(self):
        """Draw lights around the dome torus rim."""
        glPushMatrix()

        # Position at dome rim height
        glTranslatef(0, 0.3, 0)

        torus_radius = 1.65  # Radius of the torus center (proportional)

        # Draw more lights around the dome rim
        for i in range(self.dome_rim_light_count):
            # Calculate angle for this light
            angle = (2 * math.pi * i) / self.dome_rim_light_count

            # Animate with different phase than bottom lights
            light_offset = (self.light_phase * 1.5 + i * 0.2) % (2 * math.pi)
            brightness = 0.6 + 0.4 * math.sin(light_offset)

            # Interpolate colors
            light_color = (
                self.light_color_off[0] + (self.light_color_on[0] -
                                           self.light_color_off[0]) * brightness,
                self.light_color_off[1] + (self.light_color_on[1] -
                                           self.light_color_off[1]) * brightness,
                self.light_color_off[2] + (self.light_color_on[2] -
                                           self.light_color_off[2]) * brightness
            )

            glPushMatrix()

            # Position on the torus rim
            x = torus_radius * math.cos(angle)
            z = torus_radius * math.sin(angle)
            glTranslatef(x, 0, z)

            # Draw small light - OPTIMIZED: reduced polygon count
            draw_sphere(
                radius=0.1,
                slices=6,
                stacks=4,
                color=light_color
            )

            glPopMatrix()

        glPopMatrix()

    def set_position(self, x, y, z):
        """
        Set ship position.

        Args:
            x, y, z (float): New position
        """
        self.position = [x, y, z]

    def set_rotation(self, x, y, z):
        """
        Set ship rotation.

        Args:
            x, y, z (float): New rotation in degrees
        """
        self.rotation = [x, y, z]

    def move(self, dx, dy, dz):
        """
        Move ship by offset.

        Args:
            dx, dy, dz (float): Movement offset
        """
        self.position[0] += dx
        self.position[1] += dy
        self.position[2] += dz

    def rotate(self, dx, dy, dz):
        """
        Rotate ship by offset.

        Args:
            dx, dy, dz (float): Rotation offset in degrees
        """
        self.rotation[0] += dx
        self.rotation[1] += dy
        self.rotation[2] += dz

    def set_engine_power(self, power):
        """
        Set engine power/glow intensity.

        Args:
            power (float): Power level (0-1)
        """
        self.engine_glow = max(0.0, min(1.0, power))
