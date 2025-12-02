"""
Transition Manager - Modular fade-in/fade-out screen transitions.

Provides smooth visual transitions between game states with customizable
duration, color, and callback support.
"""
from OpenGL.GL import *
from OpenGL.GLUT import *


class TransitionManager:
    """
    Manages screen fade transitions between states.

    Usage:
        transition = TransitionManager()
        transition.start_fade_out(duration=0.5, on_complete=lambda: change_state())

    In update loop:
        transition.update(dt)

    In draw loop (after all other drawing):
        transition.draw(screen_width, screen_height)
    """

    # Transition states
    IDLE = 0
    FADING_OUT = 1
    FADING_IN = 2

    def __init__(self):
        self.state = self.IDLE
        self.alpha = 0.0  # 0.0 = fully transparent, 1.0 = fully opaque
        self.duration = 0.5
        self.timer = 0.0
        self.color = (0.0, 0.0, 0.0)  # Default to black fade

        # Callbacks
        self.on_fade_out_complete = None
        self.on_fade_in_complete = None

        # For chained transitions (fade out -> action -> fade in)
        self._pending_fade_in = False
        self._fade_in_duration = 0.5

    def start_fade_out(self, duration=0.5, color=(0.0, 0.0, 0.0), on_complete=None,
                       auto_fade_in=True, fade_in_duration=0.5):
        """
        Start a fade-out transition (screen goes dark).

        Args:
            duration: Time in seconds for the fade
            color: RGB tuple for fade color (default black)
            on_complete: Callback when fade-out finishes
            auto_fade_in: If True, automatically start fade-in after on_complete
            fade_in_duration: Duration for the automatic fade-in
        """
        self.state = self.FADING_OUT
        self.duration = duration
        self.timer = 0.0
        self.alpha = 0.0
        self.color = color
        self.on_fade_out_complete = on_complete
        self._pending_fade_in = auto_fade_in
        self._fade_in_duration = fade_in_duration

    def start_fade_in(self, duration=0.5, color=(0.0, 0.0, 0.0), on_complete=None):
        """
        Start a fade-in transition (screen becomes visible).

        Args:
            duration: Time in seconds for the fade
            color: RGB tuple for fade color (default black)
            on_complete: Callback when fade-in finishes
        """
        self.state = self.FADING_IN
        self.duration = duration
        self.timer = 0.0
        self.alpha = 1.0
        self.color = color
        self.on_fade_in_complete = on_complete

    def start_transition(self, duration=0.5, color=(0.0, 0.0, 0.0),
                         on_midpoint=None, on_complete=None):
        """
        Start a full transition (fade out -> action -> fade in).

        Args:
            duration: Total duration (half for fade-out, half for fade-in)
            color: RGB tuple for fade color
            on_midpoint: Callback at the midpoint (when fully dark) - use for state changes
            on_complete: Callback when entire transition finishes
        """
        half_duration = duration / 2.0

        def on_fade_out_done():
            # Execute the midpoint callback (e.g., state change)
            if on_midpoint:
                on_midpoint()
            # Start fade in
            self.start_fade_in(
                duration=half_duration,
                color=color,
                on_complete=on_complete
            )

        self.start_fade_out(
            duration=half_duration,
            color=color,
            on_complete=on_fade_out_done,
            auto_fade_in=False  # We handle it manually
        )

    def is_transitioning(self):
        """Check if a transition is currently active."""
        return self.state != self.IDLE

    def is_fully_dark(self):
        """Check if screen is fully covered (useful for hiding state changes)."""
        return self.alpha >= 0.99

    def update(self, dt):
        """Update the transition state."""
        if self.state == self.IDLE:
            return

        self.timer += dt
        progress = min(1.0, self.timer / max(0.001, self.duration))

        # Smooth easing (ease-in-out)
        eased = self._ease_in_out(progress)

        if self.state == self.FADING_OUT:
            self.alpha = eased

            if progress >= 1.0:
                self.alpha = 1.0
                callback = self.on_fade_out_complete
                self.on_fade_out_complete = None

                if callback:
                    callback()

                # Auto fade-in if requested
                if self._pending_fade_in:
                    self._pending_fade_in = False
                    self.start_fade_in(
                        duration=self._fade_in_duration, color=self.color)
                elif self.state == self.FADING_OUT:
                    # Only go idle if we didn't start a new transition
                    self.state = self.IDLE

        elif self.state == self.FADING_IN:
            self.alpha = 1.0 - eased

            if progress >= 1.0:
                self.alpha = 0.0
                self.state = self.IDLE

                if self.on_fade_in_complete:
                    callback = self.on_fade_in_complete
                    self.on_fade_in_complete = None
                    callback()

    def draw(self, width, height):
        """
        Draw the fade overlay. Call this LAST in your render pipeline.

        Args:
            width: Screen width
            height: Screen height
        """
        if self.alpha <= 0.001:
            return

        # Save OpenGL state
        glPushAttrib(GL_ALL_ATTRIB_BITS)

        # Setup 2D overlay
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Disable 3D features
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)

        # Enable blending
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw full-screen quad
        glColor4f(self.color[0], self.color[1], self.color[2], self.alpha)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(width, 0)
        glVertex2f(width, height)
        glVertex2f(0, height)
        glEnd()

        # Restore OpenGL state
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        glPopAttrib()

    def _ease_in_out(self, t):
        """Smooth ease-in-out function (smoothstep)."""
        return t * t * (3.0 - 2.0 * t)

    def skip(self):
        """Skip the current transition immediately."""
        if self.state == self.FADING_OUT:
            self.alpha = 1.0
            self.timer = self.duration
            if self.on_fade_out_complete:
                callback = self.on_fade_out_complete
                self.on_fade_out_complete = None
                callback()
            if self._pending_fade_in:
                self._pending_fade_in = False
                self.start_fade_in(duration=0.01, color=self.color)
        elif self.state == self.FADING_IN:
            self.alpha = 0.0
            self.state = self.IDLE
            if self.on_fade_in_complete:
                callback = self.on_fade_in_complete
                self.on_fade_in_complete = None
                callback()


# Global singleton for easy access
_global_transition_manager = None


def get_transition_manager():
    """Get the global TransitionManager instance."""
    global _global_transition_manager
    if _global_transition_manager is None:
        _global_transition_manager = TransitionManager()
    return _global_transition_manager
