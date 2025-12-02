"""
Cylindrical Quiz System - Interactive space tunnel quiz mechanic.

The player flies through a cylindrical corridor and must shoot the correct
answer asteroid to progress. Wrong answers cause strikes.

REFACTORED VERSION:
- Cardinal movement system (4 positions: N/E/S/W)
- Auto-forward movement
- SF-Pro font for all non-title text
- Improved cylinder rendering
"""
import math
import random
import time
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from src.states.base_state import BaseState
from src.core.input_manager import InputManager
from src.core.session import GameContext
from src.entities.player.ship import get_ufo_model
from src.entities.player.ships.shipS import dibujar_nave as draw_ship_s
from src.entities.player.ships.shipZ import draw_nave as draw_ship_z


# Cardinal directions as angles (radians)
# Align so North points +Y, East +X, South -Y, West -X
CARDINAL_NORTH = math.pi / 2            # Top (90°)
CARDINAL_EAST = 0.0                     # Right (0°)
CARDINAL_SOUTH = 3 * math.pi / 2        # Bottom (270°)
CARDINAL_WEST = math.pi                 # Left (180°)

CARDINAL_ANGLES = [CARDINAL_NORTH,
                   CARDINAL_EAST, CARDINAL_SOUTH, CARDINAL_WEST]
CARDINAL_NAMES = ["North", "East", "South", "West"]


def smoothstep(edge0, edge1, x):
    """Smooth interpolation between edge0 and edge1."""
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def lerp_angle(a, b, t):
    """Lerp between two angles, taking the shortest path."""
    # Normalize angles to 0-2PI
    a = a % (2 * math.pi)
    b = b % (2 * math.pi)

    # Find shortest direction
    diff = b - a
    if diff > math.pi:
        diff -= 2 * math.pi
    elif diff < -math.pi:
        diff += 2 * math.pi

    return a + diff * t


class CardinalShip:
    """
    Player ship that moves around the inside of a cylinder.
    CARDINAL MOVEMENT ONLY - can only be at N/E/S/W positions.
    Auto-moves forward at constant speed.
    """

    def __init__(self, cylinder_radius=8.0):
        self.cylinder_radius = cylinder_radius

        # Cardinal position system
        self.cardinal_index = 2  # 0=North, 1=East, 2=South, 3=West
        self.target_cardinal_index = 2
        self.current_angle = CARDINAL_SOUTH  # Actual rendered angle
        self.transition_progress = 1.0  # 1.0 = at target, <1.0 = transitioning
        self.transition_speed = 5.0  # How fast to interpolate

        # Auto-forward movement
        self.z_pos = 0.0
        self.auto_forward_speed = 12.0  # Constant forward speed

        # Ship visual
        self.ship_scale = 1
        self.tilt = 0.0  # Visual tilt when turning

        # Shooting
        self.projectiles = []
        self.shoot_cooldown = 0.0
        self.shoot_delay = 0.2  # Seconds between shots

        # Input tracking for WASD movement
        self.held_cardinal = None

        # Track destroyed correct asteroid for passing through
        # (cardinal_index, z_pos) of destroyed correct asteroid
        self.pending_correct_pass = None
        self.selected_ship = getattr(GameContext, 'selected_ship', 'shipM')
        self.ufo_model = get_ufo_model()
        self.animation_time = 0.0
        self._anim_state = {"hover_y": 0.0, "balanceo_pata_z": 0.0}

    def get_world_position(self):
        """Convert cylindrical position to world coordinates."""
        x = self.cylinder_radius * math.cos(self.current_angle)
        y = self.cylinder_radius * math.sin(self.current_angle)
        z = self.z_pos
        return [x, y, z]

    def get_cardinal_angle(self, index):
        """Get angle for a cardinal index."""
        return CARDINAL_ANGLES[index % 4]

    def _begin_transition(self, target_index):
        """Start movement toward the requested cardinal."""
        self.target_cardinal_index = target_index % 4
        self.transition_progress = 0.0

    def update(self, dt, input_manager):
        """Update ship position based on input."""
        self.animation_time += dt
        self.ufo_model.update(dt)
        self.selected_ship = getattr(GameContext, 'selected_ship', 'shipM')
        # WASD direct movement (W=North, D=East, S=South, A=West)
        move_keys = [('w', 0), ('d', 1), ('s', 2), ('a', 3)]
        requested = None
        for key, target in move_keys:
            if input_manager.is_key_pressed(key):
                requested = target
                break
        self.held_cardinal = requested

        # If a direction is held, attempt to start movement when possible
        if (self.held_cardinal is not None and
            self.transition_progress >= 1.0 and
            self.cardinal_index == self.target_cardinal_index and
                self.held_cardinal % 4 != self.cardinal_index):
            self._begin_transition(self.held_cardinal)

        # Smooth angle interpolation with easing
        if self.transition_progress < 1.0:
            self.transition_progress += self.transition_speed * dt
            self.transition_progress = min(1.0, self.transition_progress)

            # Use smoothstep for easing
            eased_t = smoothstep(0.0, 1.0, self.transition_progress)

            start_angle = self.get_cardinal_angle(self.cardinal_index)
            target_angle = self.get_cardinal_angle(self.target_cardinal_index)
            self.current_angle = lerp_angle(start_angle, target_angle, eased_t)

            # Visual tilt based on direction
            direction = (self.target_cardinal_index - self.cardinal_index) % 4
            if direction == 1:
                self.tilt = -25.0 * (1.0 - eased_t)
            elif direction == 3:
                self.tilt = 25.0 * (1.0 - eased_t)
            else:
                self.tilt = 0.0
        else:
            # Snap to target when transition complete
            self.cardinal_index = self.target_cardinal_index
            self.current_angle = self.get_cardinal_angle(self.cardinal_index)
            self.tilt *= 0.9  # Decay tilt
            self.transition_progress = 1.0
            # If key still held toward another lane, honor it immediately
            if (self.held_cardinal is not None and
                    self.held_cardinal % 4 != self.cardinal_index):
                self._begin_transition(self.held_cardinal)

        # Auto-forward movement (constant speed)
        self.z_pos -= self.auto_forward_speed * dt

        # Shooting (Space)
        self.shoot_cooldown = max(0, self.shoot_cooldown - dt)
        if input_manager.is_key_pressed(' ') and self.shoot_cooldown <= 0:
            self.shoot()
            self.shoot_cooldown = self.shoot_delay

        # Update projectiles
        self._update_projectiles(dt)

    def shoot(self):
        """Fire a projectile."""
        pos = self.get_world_position()
        projectile = {
            'x': pos[0] * 0.75,  # Start slightly inside cylinder
            'y': pos[1] * 0.75,
            'z': pos[2] - 1.5,  # Start in front of ship
            'vz': -100.0,  # Fast projectile speed
            'life': 2.0,
            'cardinal_index': self.cardinal_index  # Track which cardinal it was fired from
        }
        self.projectiles.append(projectile)

    def _update_projectiles(self, dt):
        """Update all projectiles."""
        to_remove = []
        for i, proj in enumerate(self.projectiles):
            proj['z'] += proj['vz'] * dt
            proj['life'] -= dt
            if proj['life'] <= 0 or proj['z'] < -800:  # Extended range for distant asteroids
                to_remove.append(i)
        for i in reversed(to_remove):
            self.projectiles.pop(i)

    def draw(self):
        """Draw the ship."""
        pos = self.get_world_position()

        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])

        # Keep the ship upright while positioned on the cylinder wall
        glScalef(self.ship_scale, self.ship_scale, self.ship_scale)
        self._draw_selected_ship()
        glPopMatrix()

    def draw_projectiles(self):
        """Draw all projectiles."""
        glDisable(GL_LIGHTING)

        for proj in self.projectiles:
            glPushMatrix()
            glTranslatef(proj['x'], proj['y'], proj['z'])

            # Glowing projectile beam
            glColor3f(0.0, 1.0, 0.5)
            glBegin(GL_LINES)
            glVertex3f(0, 0, 0)
            glVertex3f(0, 0, 2.0)
            glEnd()

            # Glow point at projectile tip
            glPointSize(6.0)
            glBegin(GL_POINTS)
            glVertex3f(0, 0, 0)
            glEnd()

            glPopMatrix()

        glEnable(GL_LIGHTING)

    def _draw_selected_ship(self):
        """Render the currently selected ship model with basic animation."""
        ship_id = self.selected_ship or 'shipM'

        glPushMatrix()

        if ship_id == 'shipM':
            glScalef(0.3, 0.3, 0.3)
            glRotatef(180, 0, 1, 0)
            self.ufo_model.draw()
        elif ship_id == 'shipS':
            glScalef(0.6, 0.6, 0.6)
            self._anim_state["hover_y"] = math.sin(
                self.animation_time * 2.0) * 0.05
            self._anim_state["balanceo_pata_z"] = math.sin(
                self.animation_time * 4.0) * 3.0
            draw_ship_s(self._anim_state)
        elif ship_id == 'shipZ':
            glScalef(0.4, 0.4, 0.4)
            draw_ship_z()
        else:
            self._draw_placeholder_ship()

        glPopMatrix()

    def _draw_placeholder_ship(self):
        """Fallback simple ship if selection is missing."""
        glDisable(GL_LIGHTING)

        glColor3f(0.0, 0.9, 1.0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, -2.0)
        glVertex3f(-0.8, 0.3, 1.0)
        glVertex3f(0.8, 0.3, 1.0)
        glVertex3f(0, 0, -2.0)
        glVertex3f(0.8, -0.3, 1.0)
        glVertex3f(-0.8, -0.3, 1.0)
        glVertex3f(0, 0, -2.0)
        glVertex3f(-0.8, -0.3, 1.0)
        glVertex3f(-0.8, 0.3, 1.0)
        glVertex3f(0, 0, -2.0)
        glVertex3f(0.8, 0.3, 1.0)
        glVertex3f(0.8, -0.3, 1.0)
        glEnd()

        glColor3f(0.0, 0.6, 0.8)
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.8, 0, 0.5)
        glVertex3f(-2.0, 0, 1.2)
        glVertex3f(-0.8, 0, 1.0)
        glVertex3f(0.8, 0, 0.5)
        glVertex3f(2.0, 0, 1.2)
        glVertex3f(0.8, 0, 1.0)
        glEnd()

        glColor3f(1.0, 0.5, 0.0)
        glBegin(GL_TRIANGLES)
        glVertex3f(-0.3, 0, 1.0)
        glVertex3f(0.3, 0, 1.0)
        glVertex3f(0, 0, 2.0)
        glEnd()

        glEnable(GL_LIGHTING)


class CardinalAsteroid:
    """
    An asteroid representing a quiz answer.
    ONLY spawns at cardinal positions (N/E/S/W).
    """

    def __init__(self, cardinal_index, z_pos, answer_text, is_correct, cylinder_radius=10.0):
        self.cardinal_index = cardinal_index  # 0=N, 1=E, 2=S, 3=W
        self.angle = CARDINAL_ANGLES[cardinal_index]
        self.z_pos = z_pos
        self.answer_text = answer_text
        self.is_correct = is_correct
        self.cylinder_radius = cylinder_radius

        # Visual properties
        self.radius = 1.2
        self.rotation = random.uniform(0, 360)
        self.rotation_speed = random.uniform(15, 30)

        # State
        self.destroyed = False
        self.hit_flash = 0.0
        self.destruction_time = 0.0
        self.destruction_particles = []

        # Hitbox
        self.hitbox_radius = self.radius * 1.5

    def get_world_position(self):
        """Get world coordinates."""
        wall_radius = self.cylinder_radius * 0.55
        x = wall_radius * math.cos(self.angle)
        y = wall_radius * math.sin(self.angle)
        return [x, y, self.z_pos]

    def update(self, dt):
        """Update asteroid state."""
        self.rotation += self.rotation_speed * dt
        self.hit_flash = max(0, self.hit_flash - dt * 3.0)

        if self.destroyed:
            self.destruction_time += dt
            for p in self.destruction_particles:
                p['x'] += p['vx'] * dt
                p['y'] += p['vy'] * dt
                p['z'] += p['vz'] * dt
                p['vy'] -= 2.0 * dt  # Slight gravity
                p['life'] -= dt

    def check_projectile_hit(self, projectile):
        """Check if a projectile hits this asteroid based on 3D position."""
        if self.destroyed:
            return False

        pos = self.get_world_position()

        # Check actual 3D distance between projectile and asteroid
        dx = projectile['x'] - pos[0]
        dy = projectile['y'] - pos[1]
        dz = projectile['z'] - pos[2]

        # Use 2D distance in XY plane (same lane) and Z distance
        xy_dist = math.sqrt(dx * dx + dy * dy)

        # Projectile must be close in XY (same lane area) and Z
        return xy_dist < self.hitbox_radius * 1.5 and abs(dz) < self.hitbox_radius * 2

    def check_ship_collision(self, ship_pos, ship_cardinal, ship_radius=1.0):
        """Check if ship collides with this asteroid."""
        if self.destroyed:
            return False

        # Must be at same cardinal position
        if ship_cardinal != self.cardinal_index:
            return False

        pos = self.get_world_position()
        dz = ship_pos[2] - pos[2]

        return abs(dz) < (self.hitbox_radius + ship_radius)

    def hit(self):
        """Called when asteroid is hit by projectile. Returns True if correct answer."""
        if self.is_correct:
            self.destroy()
            return True
        else:
            # Wrong answer - just flash red, don't destroy
            self.hit_flash = 1.0
            return False

    def destroy(self):
        """Destroy the asteroid with explosion effect (fire/debris)."""
        self.destroyed = True
        self.destruction_time = 0.0

        pos = self.get_world_position()
        self.destruction_particles = []

        # 1. Fire/Explosion particles (80 count)
        for _ in range(80):
            speed = random.uniform(2.5, 12.5)
            angle1 = random.uniform(0, 2 * math.pi)
            angle2 = random.uniform(-math.pi/2, math.pi/2)

            color = random.choice([
                (1.0, 0.5, 0.0),  # Orange
                (1.0, 0.8, 0.0),  # Yellow
                (1.0, 0.2, 0.0),  # Red
                (1.0, 0.3, 0.1),  # Deep orange
                (0.6, 0.6, 0.6),  # Gray debris
                (0.4, 0.4, 0.4),  # Dark debris
            ])

            self.destruction_particles.append({
                'x': pos[0],
                'y': pos[1],
                'z': pos[2],
                'vx': math.cos(angle1) * math.cos(angle2) * speed,
                'vy': math.sin(angle2) * speed,
                'vz': math.sin(angle1) * math.cos(angle2) * speed,
                'life': random.uniform(1.5, 3.0),
                'size': random.uniform(0.15, 0.6),
                'color': color
            })

        # 2. Debris chunks (15 count)
        for _ in range(15):
            speed = random.uniform(4, 9)
            angle1 = random.uniform(0, 2 * math.pi)
            angle2 = random.uniform(-math.pi/3, math.pi/3)

            self.destruction_particles.append({
                'x': pos[0],
                'y': pos[1],
                'z': pos[2],
                'vx': math.cos(angle1) * math.cos(angle2) * speed,
                'vy': math.sin(angle2) * speed + random.uniform(1, 2.5),
                'vz': math.sin(angle1) * math.cos(angle2) * speed,
                'life': random.uniform(2.0, 4.0),
                'size': random.uniform(0.4, 0.75),
                'color': (0.3, 0.3, 0.35)  # Metal debris
            })

    def draw(self):
        """Draw the asteroid - irregular rocky shape like a real asteroid."""
        if self.destroyed:
            self._draw_explosion()
            return

        pos = self.get_world_position()

        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])

        # Apply tumbling rotation on multiple axes
        glRotatef(self.rotation, 1, 0, 0)
        glRotatef(self.rotation * 0.7, 0, 1, 0)
        glRotatef(self.rotation * 0.3, 0, 0, 1)

        glDisable(GL_LIGHTING)

        # Main asteroid body - color based on state
        if self.hit_flash > 0:
            glColor3f(1.0, 0.3, 0.3)  # Red flash
        else:
            glColor3f(0.38, 0.36, 0.40)  # Dark gray space rock

        glutSolidSphere(self.radius, 16, 16)

        # Add irregular bumps for realistic asteroid shape
        if self.hit_flash > 0:
            glColor3f(0.9, 0.4, 0.4)
        else:
            glColor3f(0.42, 0.40, 0.44)
        bump_positions = [
            (0.7, 0.3, 0.2), (-0.5, 0.6, 0.3), (0.2, -0.7, 0.4),
            (-0.3, 0.2, 0.7), (0.5, -0.3, -0.5), (-0.6, -0.4, 0.2)
        ]
        for bx, by, bz in bump_positions:
            glPushMatrix()
            glTranslatef(bx * self.radius, by * self.radius, bz * self.radius)
            glutSolidSphere(self.radius * 0.35, 8, 8)
            glPopMatrix()

        # Add darker craters/indentations
        if self.hit_flash > 0:
            glColor3f(0.6, 0.2, 0.2)
        else:
            glColor3f(0.22, 0.20, 0.24)
        crater_positions = [
            (0.85, 0, 0), (-0.85, 0.1, 0), (0, 0.85, 0.1),
            (0.4, 0.4, 0.6), (-0.3, -0.5, 0.5)
        ]
        for cx, cy, cz in crater_positions:
            glPushMatrix()
            glTranslatef(cx * self.radius, cy * self.radius, cz * self.radius)
            glutSolidSphere(self.radius * 0.2, 6, 6)
            glPopMatrix()

        # Add lighter mineral/ice spots
        if self.hit_flash > 0:
            glColor3f(1.0, 0.6, 0.6)
        else:
            glColor3f(0.55, 0.55, 0.58)
        for i in range(4):
            glPushMatrix()
            angle = i * 90 + 45
            glRotatef(angle, 1, 1, 0)
            glTranslatef(self.radius * 0.8, 0, 0)
            glutSolidSphere(self.radius * 0.12, 4, 4)
            glPopMatrix()

        glEnable(GL_LIGHTING)
        glPopMatrix()

        # Store label position for 2D drawing
        self._label_world_pos = [pos[0], pos[1] + self.radius + 1.2, pos[2]]

    def draw_label_2d(self, modelview, projection, viewport, w, h):
        """Draw the answer text label in 2D screen space."""
        if self.destroyed:
            return

        if not hasattr(self, '_label_world_pos'):
            return

        from src.graphics.ui_renderer import UIRenderer

        try:
            pos = self._label_world_pos
            win_x, win_y, win_z = gluProject(
                pos[0], pos[1], pos[2],
                modelview, projection, viewport
            )
        except Exception:
            return

        if win_z > 1.0 or win_z < 0:
            return

        # Calculate panel & text layout with wrapping to support longer answers
        font_size = 14
        padding = 10
        max_box_w = min(300, int(w * 0.35))  # Don't let box grow too much

        # Use word wrapping by measuring actual rendered widths
        def wrap_text_to_lines(text, size, max_width, max_lines=3, font_name=None, bold=False, stroke_width=0, scale=1):
            from src.graphics.ui_renderer import UIRenderer
            words = text.split()
            if not words:
                return [""]
            lines = []
            current = words[0]
            for word in words[1:]:
                # If current + ' ' + word fits, append; else push line
                _, cw, ch = UIRenderer.get_text_texture(
                    current, size, font_name, bold=bold, stroke_width=stroke_width, scale=scale)
                _, tw, th = UIRenderer.get_text_texture(
                    current + ' ' + word, size, font_name, bold=bold, stroke_width=stroke_width, scale=scale)
                if tw <= max_width:
                    current = current + ' ' + word
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
            # If there are more than max_lines, combine the overflow into the last line with an ellipsis
            if len(lines) > max_lines:
                allowed = lines[:max_lines]
                overflow = ' '.join(lines[max_lines - 1:])
                # Trim overflow to fit
                if len(overflow) > 3:
                    overflow = overflow[:max(0, max_width // 8 - 3)] + '...'
                allowed[-1] = overflow
                return allowed
            return lines

        lines = wrap_text_to_lines(self.answer_text, font_size, max_box_w - padding * 2,
                                   font_name="sfpro", bold=False, stroke_width=0, scale=2)
        # If single word is longer than max, reduce font size until it fits
        _, widest, line_h = UIRenderer.get_text_texture(max(lines, key=len), font_size,
                                                        font_name="sfpro", bold=False, stroke_width=0, scale=2)
        if widest + padding * 2 > max_box_w:
            # Try reducing font size a few steps
            for fs in range(font_size, 8, -1):
                _, wtest, htest = UIRenderer.get_text_texture(max(lines, key=len), fs,
                                                              font_name="sfpro", bold=False, stroke_width=0, scale=2)
                if wtest + padding * 2 <= max_box_w:
                    font_size = fs
                    line_h = htest
                    widest = wtest
                    break

        box_w = min(max_box_w, widest + padding * 2)
        box_h = line_h * len(lines) + padding * 2
        box_x = win_x - box_w / 2
        box_y = win_y - box_h / 2

        # Draw a scifi panel background for the label
        UIRenderer.draw_scifi_panel(box_x, box_y, box_w, box_h)
        # Optionally overlay a red border for hit flash
        if self.hit_flash > 0:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1.0, 0.3, 0.3, 0.9)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(box_x + 2, box_y + 2)
            glVertex2f(box_x + box_w - 2, box_y + 2)
            glVertex2f(box_x + box_w - 2, box_y + box_h - 2)
            glVertex2f(box_x + 2, box_y + box_h - 2)
            glEnd()
            glDisable(GL_BLEND)

        # Draw text using custom font with scifi look. Use red text for hit flash.
        text_color = (1.0, 0.4, 0.4) if self.hit_flash > 0 else (1.0, 1.0, 1.0)
        # Draw multiple wrapped lines centered inside the panel
        text_y = box_y + box_h - padding - line_h
        for line in lines:
            # Use a mild bold strength for improved readability without being too heavy
            _, line_w, _ = UIRenderer.get_text_texture(
                line, font_size, font_name="sfpro", bold=False, stroke_width=0, bold_strength=1, scale=2)
            text_x = box_x + (box_w - line_w) / 2
            # Use SF-Pro for answer labels for readability
            UIRenderer.draw_text(text_x, text_y, line, size=font_size, color=text_color,
                                 font_name="sfpro", bold=False, stroke_width=0, bold_strength=1, scale=2)
            text_y -= line_h

    def _draw_explosion(self):
        """Draw explosion particles."""
        if self.destruction_time > 4.0:
            return

        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        for p in self.destruction_particles:
            if p['life'] > 0:
                alpha = min(1.0, p['life'])
                c = p['color']
                glColor4f(c[0], c[1], c[2], alpha)

                glPushMatrix()
                glTranslatef(p['x'], p['y'], p['z'])
                glutSolidSphere(p['size'] * alpha, 6, 6)
                glPopMatrix()

        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)


class HyperspaceWarpTunnel:
    """
    A hyperspace/warp tunnel effect with streaking stars and speed lines.
    Creates the illusion of moving very fast through space.
    """

    def __init__(self, radius=10.0, length=500.0):
        self.radius = radius
        self.length = length
        self.scroll_offset = 0.0

        # Generate persistent star particles - very far distant stars
        random.seed(42)  # Consistent star field
        self.num_stars = 1500  # Lots of stars
        self.stars = []
        for _ in range(self.num_stars):
            star = {
                'angle': random.uniform(0, 2 * math.pi),
                # Extremely far out - like real distant stars
                'r': random.uniform(15.0, 50.0) * self.radius,
                'z_offset': random.uniform(0, 500),  # Spread along full tunnel
                # Very slow - distant parallax
                'speed_mult': random.uniform(0.05, 0.15),
                'brightness': random.uniform(0.3, 0.7),
                'size': random.uniform(0.5, 1.2),  # Tiny points
                'color': (1.0, 1.0, 1.0)  # All white
            }
            self.stars.append(star)

        # Speed lines (longer streaks at edges)
        self.num_speed_lines = 200  # More speed lines
        self.speed_lines = []
        for _ in range(self.num_speed_lines):
            line = {
                'angle': random.uniform(0, 2 * math.pi),
                # Far out at edges
                'r': random.uniform(1.8, 3.5) * self.radius,
                'z_offset': random.uniform(0, 500),  # Full tunnel length
                'length': random.uniform(20, 60),  # Streak length
                'brightness': random.uniform(0.3, 0.6),
            }
            self.speed_lines.append(line)

        random.seed(time.time())  # Reset random

        # Tunnel boundary ring spacing
        self.ring_spacing = 25.0

    def update(self, dt, forward_speed):
        """Update tunnel scroll."""
        self.scroll_offset += forward_speed * dt

    def draw(self):
        """Draw the hyperspace tunnel."""
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Draw vanishing point glow at center/distance
        self._draw_vanishing_point()

        # Draw speed lines (long streaks)
        self._draw_speed_lines()

        # Draw star particles
        self._draw_stars()

        # Draw subtle tunnel boundary rings
        self._draw_boundary_rings()

        # Draw cardinal lane indicators
        self._draw_lane_guides()

        glEnable(GL_LIGHTING)
        glDisable(GL_BLEND)

    def _draw_vanishing_point(self):
        """Draw glowing vanishing point in the distance."""
        far_z = -500

        # Outer glow - white/gray
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(0.1, 0.1, 0.1, 0.0)
        glVertex3f(0, 0, far_z)
        glColor4f(0.02, 0.02, 0.02, 0.8)
        for i in range(49):
            angle = (i / 48) * 2 * math.pi
            x = self.radius * 2 * math.cos(angle)
            y = self.radius * 2 * math.sin(angle)
            glVertex3f(x, y, far_z)
        glEnd()

        # Inner bright core - white
        glBegin(GL_TRIANGLE_FAN)
        glColor4f(0.6, 0.6, 0.6, 0.4)
        glVertex3f(0, 0, far_z + 100)
        glColor4f(0.1, 0.1, 0.1, 0.0)
        for i in range(33):
            angle = (i / 32) * 2 * math.pi
            x = self.radius * 0.5 * math.cos(angle)
            y = self.radius * 0.5 * math.sin(angle)
            glVertex3f(x, y, far_z + 100)
        glEnd()

    def _draw_stars(self):
        """Draw distant star particles - always visible."""
        glPointSize(1.5)
        glBegin(GL_POINTS)

        visible_range = 500.0

        for star in self.stars:
            # Each star has a unique phase based on its z_offset
            phase = star['z_offset'] / visible_range

            # Animate: scroll moves stars toward camera
            # Use fmod for consistent behavior with any scroll value
            progress = math.fmod(phase + self.scroll_offset *
                                 star['speed_mult'] / visible_range, 1.0)
            if progress < 0:
                progress += 1.0

            # Map progress to Z: 0 = far (-visible_range), 1 = near (0)
            z = -visible_range * (1.0 - progress)

            if z > 5 or z < -490:
                continue

            x = star['r'] * math.cos(star['angle'])
            y = star['r'] * math.sin(star['angle'])

            alpha = star['brightness']
            glColor4f(alpha, alpha, alpha, alpha)
            glVertex3f(x, y, z)

        glEnd()

    def _draw_speed_lines(self):
        """Draw speed lines streaking toward camera."""
        glLineWidth(2.0)

        visible_range = 250.0
        speed_multiplier = 12.0  # Very fast

        for line in self.speed_lines:
            # Each line has a unique phase
            phase = line['z_offset'] / visible_range

            # Animate with fmod for consistency
            progress = math.fmod(phase + self.scroll_offset *
                                 speed_multiplier / visible_range, 1.0)
            if progress < 0:
                progress += 1.0

            # Map to Z position
            z_base = -visible_range * (1.0 - progress)

            if z_base > 10 or z_base < -240:
                continue

            x = line['r'] * math.cos(line['angle'])
            y = line['r'] * math.sin(line['angle'])

            z_tail = z_base - line['length']

            alpha = line['brightness']
            glBegin(GL_LINES)
            glColor4f(alpha, alpha, alpha, alpha)
            glVertex3f(x, y, z_base)
            glColor4f(alpha * 0.1, alpha * 0.1, alpha * 0.1, 0.0)
            glVertex3f(x, y, z_tail)
            glEnd()

    def _draw_boundary_rings(self):
        """Draw subtle rings showing tunnel boundary - always around ship."""
        glLineWidth(1.0)

        # Fixed alpha for uniform appearance
        alpha = 0.15
        glColor4f(alpha, alpha, alpha, alpha)

        # Draw rings relative to current scroll position
        ring_offset = self.scroll_offset % self.ring_spacing

        for ring in range(0, 20):
            z = -ring * self.ring_spacing + ring_offset

            if z > 10 or z < -480:
                continue

            glBegin(GL_LINE_LOOP)
            for i in range(48):
                angle = (i / 48) * 2 * math.pi
                x = self.radius * math.cos(angle)
                y = self.radius * math.sin(angle)
                glVertex3f(x, y, z)
            glEnd()

    def _draw_lane_guides(self):
        """Draw glowing markers at cardinal positions - always around ship."""
        ring_offset = self.scroll_offset % self.ring_spacing

        for cardinal_idx, angle in enumerate(CARDINAL_ANGLES):
            x = self.radius * 0.95 * math.cos(angle)
            y = self.radius * 0.95 * math.sin(angle)

            # Subtle pulsing
            pulse = 0.8 + 0.2 * \
                math.sin(time.time() * 2.0 + cardinal_idx * 0.5)

            # Draw guide dots along the lane
            glPointSize(4.0)
            alpha = 0.3 * pulse
            glColor4f(alpha, alpha, alpha, alpha)

            glBegin(GL_POINTS)
            for ring in range(0, 15):
                z = -ring * self.ring_spacing + ring_offset
                if z > 10 or z < -350:
                    continue
                glVertex3f(x, y, z)
            glEnd()

            # Continuous line for nearest section - white
            glLineWidth(1.5)
            alpha = 0.25 * pulse
            glColor4f(alpha, alpha, alpha, alpha)
            glBegin(GL_LINES)
            glVertex3f(x, y, 5)
            glVertex3f(x, y, -100)
            glEnd()


class CylindricalQuizManager:
    """
    Manages the cylindrical quiz game mode.
    ALL questions spawn at the start - visible from the beginning.
    """

    STATE_INTRO = 0
    STATE_PLAYING = 1
    STATE_QUESTION_TRANSITION = 2
    STATE_SUCCESS = 3
    STATE_FAILED = 4
    STATE_COMPLETE = 5

    def __init__(self, planet_name, questions):
        self.planet_name = planet_name
        self.questions = questions
        self.current_question_index = 0

        # Game objects - use hyperspace warp tunnel
        self.cylinder = HyperspaceWarpTunnel(radius=5.5, length=500.0)
        self.ship = CardinalShip(cylinder_radius=4.0)
        self.asteroids = []  # All asteroids for all questions

        # Question tracking
        self.question_asteroid_groups = []  # List of asteroid lists per question
        self.question_z_positions = []  # Z position of each question's asteroids

        # State
        self.state = self.STATE_INTRO
        self.strikes = 0
        self.max_strikes = 3
        self.score = 0

        # Timing
        self.intro_timer = 2.0
        self.transition_timer = 0.0
        self.transition_duration = 0.5  # Shorter transition since questions are pre-spawned
        self.success_timer = 0.0

        # Current question
        self.current_question = None

        # Input
        self.input_manager = None

        # Callbacks
        self.on_complete = None
        self.on_fail = None

        # Message display
        self.message = ""
        self.message_timer = 0.0

        # Screen shake
        self.screen_shake = 0.0

        # Matrices for 2D label drawing
        self._modelview_matrix = None
        self._projection_matrix = None

        # Spacing between question groups
        self.question_spacing = 80.0  # Distance between each question's asteroids

    def start(self, input_manager):
        """Start the quiz and spawn ALL questions at once."""
        self.input_manager = input_manager
        self.state = self.STATE_INTRO
        self.intro_timer = 2.0
        # Do not show entering message in order to keep UI clean
        self.message = ""
        self.message_timer = 0.0

        # Spawn ALL questions at the start
        self._spawn_all_questions()

        # Set current question
        if self.questions:
            self.current_question = self.questions[0]

    def _spawn_all_questions(self):
        """Spawn asteroids for ALL questions at once - visible from start."""
        self.asteroids.clear()
        self.question_asteroid_groups.clear()
        self.question_z_positions.clear()

        base_z = self.ship.z_pos - 60.0  # First question starts ahead of ship

        for q_idx, question in enumerate(self.questions):
            options = question.get('options', [])
            correct_idx = question.get('correct', 0)

            num_options = min(len(options), 4)  # Max 4 options
            # Each question further ahead
            z_position = base_z - (q_idx * self.question_spacing)

            self.question_z_positions.append(z_position)
            question_asteroids = []

            # Randomly assign options to cardinal positions
            available_cardinals = list(range(4))
            random.shuffle(available_cardinals)

            for i in range(num_options):
                cardinal = available_cardinals[i]
                is_correct = (i == correct_idx)

                asteroid = CardinalAsteroid(
                    cardinal_index=cardinal,
                    z_pos=z_position,  # All asteroids for this question at same Z
                    answer_text=options[i],
                    is_correct=is_correct,
                    cylinder_radius=5.5  # Match tunnel radius
                )
                asteroid.question_index = q_idx  # Track which question this belongs to
                self.asteroids.append(asteroid)
                question_asteroids.append(asteroid)

            self.question_asteroid_groups.append(question_asteroids)

        print(
            f"[CylindricalQuiz] Spawned {len(self.asteroids)} asteroids for {len(self.questions)} questions")

    def _spawn_question_asteroids(self):
        """Legacy method - now just updates current question reference."""
        # Clear any pending correct pass from previous question
        self.ship.pending_correct_pass = None

        if self.current_question_index >= len(self.questions):
            return

        self.current_question = self.questions[self.current_question_index]

    def _check_collisions(self):
        """Check for projectile and ship collisions with asteroids."""
        ship_pos = self.ship.get_world_position()
        ship_cardinal = self.ship.cardinal_index

        # Only check asteroids for current question
        if self.current_question_index >= len(self.question_asteroid_groups):
            return
        current_asteroids = self.question_asteroid_groups[self.current_question_index]

        # Check projectile hits
        projectiles_to_remove = []
        for i, proj in enumerate(self.ship.projectiles):
            for asteroid in current_asteroids:
                if asteroid.check_projectile_hit(proj):
                    projectiles_to_remove.append(i)
                    if asteroid.hit():
                        # Don't score yet - track position for when ship passes through
                        self.ship.pending_correct_pass = (
                            asteroid.cardinal_index, asteroid.z_pos)
                        self.message = ""
                        self.message_timer = 0.0
                    else:
                        self.message = ""
                        self.message_timer = 0.0
                    break

        for i in reversed(projectiles_to_remove):
            if i < len(self.ship.projectiles):
                self.ship.projectiles.pop(i)

        # Check if ship passes through the destroyed correct asteroid's position
        if self.ship.pending_correct_pass:
            target_cardinal, target_z = self.ship.pending_correct_pass
            # Ship must be at the correct cardinal AND have passed the Z position
            if ship_cardinal == target_cardinal and ship_pos[2] < target_z - 2.0:
                self.score += 1
                self.ship.pending_correct_pass = None
                self._on_correct_answer()

        # Check ship collisions with asteroids (current question only)
        for asteroid in current_asteroids:
            if asteroid.check_ship_collision(ship_pos, ship_cardinal):
                if asteroid.is_correct and not asteroid.destroyed:
                    self._on_strike("Missed the correct answer!")
                    asteroid.destroy()
                elif not asteroid.is_correct and not asteroid.destroyed:
                    self._on_strike("Crashed into wrong answer!")
                    asteroid.destroy()

    def _on_correct_answer(self):
        """Handle correct answer."""
        self.message = ""
        self.message_timer = 0.0
        self.state = self.STATE_QUESTION_TRANSITION
        self.transition_timer = self.transition_duration

    def _on_strike(self, reason):
        """Handle a strike."""
        self.strikes += 1
        self.screen_shake = 1.5
        # Map common reason strings to a more cinematic sci-fi phrasing
        cinematic_reason_map = {
            "Missed the correct answer!": "TARGET LOCK FAILURE",
            "Crashed into wrong answer!": "INCORRECT TARGET IMPACT",
            "Didn't fly through the opened path!": "NAVIGATION FAILURE: NO PASS",
            "Passed without answering!": "NO RESPONSE: TARGET NOT ACQUIRED"
        }

        reason_text = cinematic_reason_map.get(reason, reason.upper())
        # Use 'OF' format to avoid symbols the custom font can't render
        self.message = f"STRIKE {self.strikes} OF {self.max_strikes}: {reason_text}"
        self.message_timer = 2.0

        if self.strikes >= self.max_strikes:
            self.state = self.STATE_FAILED
            self.message = "CRITICAL FAILURE"
            self.message_timer = 3.0
        else:
            self.state = self.STATE_QUESTION_TRANSITION
            self.transition_timer = self.transition_duration

    def _advance_question(self):
        """Move to the next question."""
        self.current_question_index += 1
        self.ship.pending_correct_pass = None  # Clear pending pass

        if self.current_question_index >= len(self.questions):
            self.state = self.STATE_COMPLETE
            self.message = f"{self.planet_name} Quiz Complete!"
            self.message_timer = 3.0
            self.success_timer = 3.0
        else:
            # Just update current question reference - asteroids already exist
            self.current_question = self.questions[self.current_question_index]
            self.state = self.STATE_PLAYING

    def update(self, dt):
        """Update the quiz state."""
        self.message_timer = max(0, self.message_timer - dt)
        self.screen_shake = max(0, self.screen_shake - dt * 3.0)

        if self.state == self.STATE_INTRO:
            self.intro_timer -= dt

            # Still update ship and asteroids during intro for visual effect
            if self.input_manager:
                self.ship.update(dt, self.input_manager)
            for asteroid in self.asteroids:
                asteroid.update(dt)
            self.cylinder.update(dt, self.ship.auto_forward_speed)

            if self.intro_timer <= 0:
                # Questions already spawned in start() - just switch to playing
                self.state = self.STATE_PLAYING

        elif self.state == self.STATE_PLAYING:
            if self.input_manager:
                self.ship.update(dt, self.input_manager)

            # Update ALL asteroids (they're all visible)
            for asteroid in self.asteroids:
                asteroid.update(dt)

            self.cylinder.update(dt, self.ship.auto_forward_speed)

            self._check_collisions()

            # Check if current question's asteroids are all behind the ship
            if self.current_question_index < len(self.question_asteroid_groups):
                current_asteroids = self.question_asteroid_groups[self.current_question_index]
                all_passed = all(
                    asteroid.destroyed or asteroid.z_pos > self.ship.z_pos + 8
                    for asteroid in current_asteroids
                )
                if all_passed and current_asteroids:
                    # Check if there's still a pending correct pass (destroyed but not flown through)
                    if self.ship.pending_correct_pass:
                        # Player destroyed correct asteroid but didn't fly through
                        self.ship.pending_correct_pass = None
                        self._on_strike("Didn't fly through the opened path!")
                    else:
                        correct_destroyed = any(
                            a.is_correct and a.destroyed for a in current_asteroids
                        )
                        if not correct_destroyed:
                            self._on_strike("Passed without answering!")

        elif self.state == self.STATE_QUESTION_TRANSITION:
            self.transition_timer -= dt

            if self.input_manager:
                self.ship.update(dt, self.input_manager)
            self.cylinder.update(dt, self.ship.auto_forward_speed)

            for asteroid in self.asteroids:
                asteroid.update(dt)

            if self.transition_timer <= 0:
                self._advance_question()

        elif self.state == self.STATE_COMPLETE:
            self.success_timer -= dt
            if self.input_manager:
                self.ship.update(dt, self.input_manager)
            self.cylinder.update(dt, self.ship.auto_forward_speed)
            if self.success_timer <= 0 and self.on_complete:
                self.on_complete(True, self.score, self.strikes)

        elif self.state == self.STATE_FAILED:
            self.message_timer -= dt
            if self.message_timer <= 0 and self.on_fail:
                self.on_fail()

    def draw(self):
        """Draw the entire quiz scene."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Camera follows ship, looking forward along axis
        ship_pos = self.ship.get_world_position()

        # Apply screen shake
        shake_x = (random.random() - 0.5) * self.screen_shake * 2.0
        shake_y = (random.random() - 0.5) * self.screen_shake * 2.0

        # Camera positioned behind and slightly toward center
        cam_offset = 0.2
        gluLookAt(
            ship_pos[0] * cam_offset + shake_x, ship_pos[1] *
            cam_offset + shake_y, ship_pos[2] + 10,
            ship_pos[0] * 0.3, ship_pos[1] * 0.3, ship_pos[2] - 30,
            0, 1, 0
        )

        # Shift entire scene upward slightly so bottom UI has breathing room
        glTranslatef(0.0, 1.0, 0.0)

        # Draw cylinder - move with ship so it's infinite
        glPushMatrix()
        glTranslatef(0, 0, ship_pos[2])
        self.cylinder.draw()
        glPopMatrix()

        # Draw asteroids
        for asteroid in self.asteroids:
            asteroid.draw()

        # Draw ship
        self.ship.draw()
        self.ship.draw_projectiles()

        # Store matrices for 2D label drawing
        self._modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
        self._projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)

    def draw_ui(self, w, h):
        """Draw 2D UI overlay - uses SF-Pro for all non-title text."""
        from src.graphics.ui_renderer import UIRenderer

        UIRenderer.setup_2d(w, h)

        # Draw futuristic HUD overlay
        self._draw_hud_overlay(w, h)

        # Draw asteroid labels - ONLY for current question's asteroids
        if self._modelview_matrix is not None and self._projection_matrix is not None:
            viewport = [0, 0, w, h]
            # Only render labels for asteroids belonging to current question
            if self.current_question_index < len(self.question_asteroid_groups):
                current_asteroids = self.question_asteroid_groups[self.current_question_index]
                for asteroid in current_asteroids:
                    asteroid.draw_label_2d(
                        self._modelview_matrix,
                        self._projection_matrix,
                        viewport,
                        w, h
                    )

        # Draw question box at bottom
        if self.current_question and self.state in [self.STATE_PLAYING, self.STATE_QUESTION_TRANSITION]:
            self._draw_question_box(w, h)

        # Draw message
        if self.message_timer > 0 and self.message:
            self._draw_message(w, h)

        # Controls hint intentionally hidden - keeping HUD minimal

        # Draw intro overlay
        if self.state == self.STATE_INTRO:
            self._draw_intro_overlay(w, h)

        UIRenderer.restore_3d()

    def _draw_hud_overlay(self, w, h):
        """Draw intricate futuristic HUD overlay."""
        from src.graphics.ui_renderer import UIRenderer

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_TEXTURE_2D)

        # HUD Color Theme - Cyan/Blue
        hud_color = (0.0, 0.8, 1.0)
        hud_alpha = 0.5

        glColor4f(hud_color[0], hud_color[1], hud_color[2], hud_alpha)
        glLineWidth(2.0)

        # 1. Corner Brackets (Intricate)
        bracket_len = 80
        bracket_gap = 25
        corner_cut = 15

        # Top-Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(bracket_gap, h - bracket_gap - bracket_len)
        glVertex2f(bracket_gap, h - bracket_gap - corner_cut)
        glVertex2f(bracket_gap + corner_cut, h - bracket_gap)
        glVertex2f(bracket_gap + bracket_len, h - bracket_gap)
        glEnd()
        # Inner detail
        glBegin(GL_LINES)
        glVertex2f(bracket_gap + 5, h - bracket_gap - bracket_len + 10)
        glVertex2f(bracket_gap + 5, h - bracket_gap - corner_cut - 2)
        glVertex2f(bracket_gap + 5, h - bracket_gap - corner_cut - 2)
        glVertex2f(bracket_gap + corner_cut + 2, h - bracket_gap - 5)
        glEnd()

        # Top-Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(w - bracket_gap - bracket_len, h - bracket_gap)
        glVertex2f(w - bracket_gap - corner_cut, h - bracket_gap)
        glVertex2f(w - bracket_gap, h - bracket_gap - corner_cut)
        glVertex2f(w - bracket_gap, h - bracket_gap - bracket_len)
        glEnd()
        # Inner detail
        glBegin(GL_LINES)
        glVertex2f(w - bracket_gap - bracket_len + 10, h - bracket_gap - 5)
        glVertex2f(w - bracket_gap - corner_cut - 2, h - bracket_gap - 5)
        glVertex2f(w - bracket_gap - corner_cut - 2, h - bracket_gap - 5)
        glVertex2f(w - bracket_gap - 5, h - bracket_gap - corner_cut - 2)
        glEnd()

        # Bottom-Left
        glBegin(GL_LINE_STRIP)
        glVertex2f(bracket_gap, bracket_gap + bracket_len)
        glVertex2f(bracket_gap, bracket_gap + corner_cut)
        glVertex2f(bracket_gap + corner_cut, bracket_gap)
        glVertex2f(bracket_gap + bracket_len, bracket_gap)
        glEnd()
        # Inner detail
        glBegin(GL_LINES)
        glVertex2f(bracket_gap + 5, bracket_gap + bracket_len - 10)
        glVertex2f(bracket_gap + 5, bracket_gap + corner_cut + 2)
        glVertex2f(bracket_gap + 5, bracket_gap + corner_cut + 2)
        glVertex2f(bracket_gap + corner_cut + 2, bracket_gap + 5)
        glEnd()

        # Bottom-Right
        glBegin(GL_LINE_STRIP)
        glVertex2f(w - bracket_gap - bracket_len, bracket_gap)
        glVertex2f(w - bracket_gap - corner_cut, bracket_gap)
        glVertex2f(w - bracket_gap, bracket_gap + corner_cut)
        glVertex2f(w - bracket_gap, bracket_gap + bracket_len)
        glEnd()
        # Inner detail
        glBegin(GL_LINES)
        glVertex2f(w - bracket_gap - bracket_len + 10, bracket_gap + 5)
        glVertex2f(w - bracket_gap - corner_cut - 2, bracket_gap + 5)
        glVertex2f(w - bracket_gap - corner_cut - 2, bracket_gap + 5)
        glVertex2f(w - bracket_gap - 5, bracket_gap + corner_cut + 2)
        glEnd()

        # 2. Side Bars (Vertical data strips with ticks)
        bar_height = 250
        bar_x_offset = 50

        # Left Bar
        glBegin(GL_LINES)
        glVertex2f(bar_x_offset, h/2 - bar_height/2)
        glVertex2f(bar_x_offset, h/2 + bar_height/2)
        glEnd()

        glBegin(GL_LINES)
        for i in range(21):
            y = h/2 - bar_height/2 + (bar_height * i / 20)
            tick_len = 12 if i % 5 == 0 else 6
            glVertex2f(bar_x_offset, y)
            glVertex2f(bar_x_offset - tick_len, y)
        glEnd()

        # Right Bar
        glBegin(GL_LINES)
        glVertex2f(w - bar_x_offset, h/2 - bar_height/2)
        glVertex2f(w - bar_x_offset, h/2 + bar_height/2)
        glEnd()

        glBegin(GL_LINES)
        for i in range(21):
            y = h/2 - bar_height/2 + (bar_height * i / 20)
            tick_len = 12 if i % 5 == 0 else 6
            glVertex2f(w - bar_x_offset, y)
            glVertex2f(w - bar_x_offset + tick_len, y)
        glEnd()

        # 3. Center Reticle (Targeting System) - REMOVED per request
        # The laser fires at specific cardinal directions, so a center crosshair is misleading.

        # 3a. Shield Integrity Monitor (Bottom Left)
        # Visual bars representing remaining strikes allowed
        shield_x = bracket_gap + 20
        shield_y = bracket_gap + 80
        shield_w = 120
        shield_h = 15

        # Label
        UIRenderer.draw_text(shield_x, shield_y + 20, "SHIELD INTEGRITY",
                             size=10, color=(0.0, 0.6, 0.8), font_name="radiospace")

        # Bars
        remaining_strikes = self.max_strikes - self.strikes
        for i in range(self.max_strikes):
            bar_color = (0.0, 0.8, 1.0) if i < remaining_strikes else (
                0.2, 0.1, 0.1)
            bar_alpha = 0.8 if i < remaining_strikes else 0.3

            bx = shield_x + (i * (shield_w / self.max_strikes))
            bw = (shield_w / self.max_strikes) - 4

            glColor4f(bar_color[0], bar_color[1], bar_color[2], bar_alpha)
            glBegin(GL_QUADS)
            glVertex2f(bx, shield_y)
            glVertex2f(bx + bw, shield_y)
            glVertex2f(bx + bw, shield_y + shield_h)
            glVertex2f(bx, shield_y + shield_h)
            glEnd()

        # 3b. Speed/Thrust Graph (Bottom Right)
        # Dynamic graph simulating engine output
        graph_w = 120
        graph_h = 40
        graph_x = w - bracket_gap - 20 - graph_w
        graph_y = bracket_gap + 80

        # Label
        UIRenderer.draw_text(graph_x, graph_y + graph_h + 5, "ENGINE OUTPUT",
                             size=10, color=(0.0, 0.6, 0.8), font_name="radiospace")

        # Graph lines
        glLineWidth(1.0)
        glBegin(GL_LINE_STRIP)
        for i in range(20):
            gx = graph_x + (i * (graph_w / 19))
            # Simulated noise
            noise = math.sin(time.time() * 10 + i) * 0.5 + 0.5
            gy = graph_y + (noise * graph_h * 0.8)

            alpha = 0.3 + (i / 20) * 0.7
            glColor4f(0.0, 0.8, 1.0, alpha)
            glVertex2f(gx, gy)
        glEnd()

        # Base line
        glBegin(GL_LINES)
        glColor4f(0.0, 0.4, 0.5, 0.5)
        glVertex2f(graph_x, graph_y)
        glVertex2f(graph_x + graph_w, graph_y)
        glEnd()

        # 3c. Horizon Lines (Faint depth cues)
        # Horizontal lines near center to give orientation
        horizon_y = h / 2
        horizon_w = 150
        horizon_gap = 200

        glColor4f(0.0, 0.8, 1.0, 0.15)
        glLineWidth(1.0)

        # Left Horizon
        glBegin(GL_LINES)
        glVertex2f(w/2 - horizon_gap - horizon_w, horizon_y)
        glVertex2f(w/2 - horizon_gap, horizon_y)
        # Ticks
        glVertex2f(w/2 - horizon_gap, horizon_y - 10)
        glVertex2f(w/2 - horizon_gap, horizon_y + 10)
        glEnd()

        # Right Horizon
        glBegin(GL_LINES)
        glVertex2f(w/2 + horizon_gap, horizon_y)
        glVertex2f(w/2 + horizon_gap + horizon_w, horizon_y)
        # Ticks
        glVertex2f(w/2 + horizon_gap, horizon_y - 10)
        glVertex2f(w/2 + horizon_gap, horizon_y + 10)
        glEnd()

        # 3d. System Status Text Blocks (Decorative)
        # Small "code" blocks
        block_font_size = 8

        # Top Left Block
        UIRenderer.draw_text(bracket_gap + 100, h - bracket_gap - 20, "SYS: NOMINAL",
                             size=block_font_size, color=(0.0, 0.5, 0.6), font_name="radiospace")
        UIRenderer.draw_text(bracket_gap + 100, h - bracket_gap - 32, "WPN: ARMED",
                             size=block_font_size, color=(0.0, 0.5, 0.6), font_name="radiospace")

        # Top Right Block
        UIRenderer.draw_text(w - bracket_gap - 160, h - bracket_gap - 20, "TGT: ACQUIRED",
                             size=block_font_size, color=(0.0, 0.5, 0.6), font_name="radiospace")
        UIRenderer.draw_text(w - bracket_gap - 160, h - bracket_gap - 32, "LNK: STABLE",
                             size=block_font_size, color=(0.0, 0.5, 0.6), font_name="radiospace")

        # 4. Top Status Bar (Compass/Heading)
        top_bar_y = h - 60
        top_bar_w = 300

        glBegin(GL_LINE_STRIP)
        glVertex2f(w/2 - top_bar_w/2, top_bar_y)
        glVertex2f(w/2 - top_bar_w/2 + 20, top_bar_y + 20)
        glVertex2f(w/2 + top_bar_w/2 - 20, top_bar_y + 20)
        glVertex2f(w/2 + top_bar_w/2, top_bar_y)
        glVertex2f(w/2 + top_bar_w/2 - 10, top_bar_y - 10)
        glVertex2f(w/2 - top_bar_w/2 + 10, top_bar_y - 10)
        glVertex2f(w/2 - top_bar_w/2, top_bar_y)
        glEnd()

        # Compass ticks
        glBegin(GL_LINES)
        for i in range(-5, 6):
            x = w/2 + i * 20
            h_tick = 8 if i == 0 else 4
            glVertex2f(x, top_bar_y + 20)
            glVertex2f(x, top_bar_y + 20 - h_tick)
        glEnd()

        # 5. Bottom Decorative Lines (Framing the question box)
        bottom_y = 140
        glBegin(GL_LINES)
        # Left wing
        glVertex2f(w/2 - 350, bottom_y)
        glVertex2f(w/2 - 150, bottom_y)
        glVertex2f(w/2 - 350, bottom_y)
        glVertex2f(w/2 - 370, bottom_y - 20)

        # Right wing
        glVertex2f(w/2 + 350, bottom_y)
        glVertex2f(w/2 + 150, bottom_y)
        glVertex2f(w/2 + 350, bottom_y)
        glVertex2f(w/2 + 370, bottom_y - 20)
        glEnd()

        glDisable(GL_BLEND)

        # Draw Integrated HUD Text
        bracket_gap = 25

        # Top Left - Strikes
        strikes_label = "STRIKES"
        strikes_val = f"{self.strikes} / {self.max_strikes}"
        strike_color = (1.0, 0.3, 0.3) if self.strikes > 0 else (0.0, 0.8, 1.0)

        UIRenderer.draw_text(bracket_gap + 15, h - bracket_gap - 25,
                             strikes_label, size=14, color=(0.0, 0.6, 0.8), font_name="radiospace")
        UIRenderer.draw_text(bracket_gap + 15, h - bracket_gap - 50,
                             strikes_val, size=24, color=strike_color, font_name="radiospace")

        # Top Right - Progress
        prog_label = "QUESTION"
        prog_val = f"{self.current_question_index + 1} / {len(self.questions)}"

        # Calculate width to right-align
        _, lbl_w, _ = UIRenderer.get_text_texture(
            prog_label, 14, font_name="radiospace")
        _, val_w, _ = UIRenderer.get_text_texture(
            prog_val, 24, font_name="radiospace")

        UIRenderer.draw_text(w - bracket_gap - 15 - lbl_w, h - bracket_gap -
                             25, prog_label, size=14, color=(0.0, 0.6, 0.8), font_name="radiospace")
        UIRenderer.draw_text(w - bracket_gap - 15 - val_w, h - bracket_gap -
                             50, prog_val, size=24, color=(0.0, 0.9, 1.0), font_name="radiospace")

    def _draw_question_box(self, w, h):
        """Draw the question text box."""
        from src.graphics.ui_renderer import UIRenderer

        question_text = self.current_question.get('question', '')

        box_width = min(w - 240, 640)
        box_left = (w - box_width) / 2
        box_right = box_left + box_width
        box_bottom = 35
        box_top = box_bottom + 90
        chamfer = 18

        # Precompute chamfered rectangle points (clockwise)
        points = [
            (box_left + chamfer, box_bottom),
            (box_right - chamfer, box_bottom),
            (box_right, box_bottom + chamfer),
            (box_right, box_top - chamfer),
            (box_right - chamfer, box_top),
            (box_left + chamfer, box_top),
            (box_left, box_top - chamfer),
            (box_left, box_bottom + chamfer)
        ]

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Glow halo
        glColor4f(0.0, 0.6, 0.9, 0.15)
        glBegin(GL_POLYGON)
        for x, y in points:
            glVertex2f(x, y + 8)
        glEnd()

        # Question background (bottom of screen)
        glColor4f(0.0, 0.05, 0.1, 0.9)
        glBegin(GL_POLYGON)
        for x, y in points:
            glVertex2f(x, y)
        glEnd()

        # Border with bright corners
        glColor4f(0.0, 0.8, 1.0, 0.9)
        glLineWidth(2.5)
        glBegin(GL_LINE_LOOP)
        for x, y in points:
            glVertex2f(x, y)
        glEnd()
        glDisable(GL_BLEND)

        # Question text (SF-Pro) anchored to bottom box
        # Word wrap
        max_line_width = box_width - 60
        text_y = box_top - 40
        lines = []

        words = question_text.split()
        current_line = ""
        for word in words:
            test_line = (current_line + " " + word).strip()
            if len(test_line) * 10 > max_line_width and current_line:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

        if not lines:
            lines = [question_text]

        for idx, line in enumerate(lines[:2]):
            text_width = len(line) * 10
            text_x = box_left + (box_width - text_width) / 2
            UIRenderer.draw_text(text_x, text_y - idx * 25, line,
                                 size=18, color=(1.0, 1.0, 1.0), font_name="sfpro")

    def _draw_message(self, w, h):
        """Draw centered message."""
        from src.graphics.ui_renderer import UIRenderer

        if "Correct" in self.message or "Complete" in self.message:
            color = (0.0, 1.0, 0.5)
        elif "STRIKE" in self.message or "FAILED" in self.message:
            color = (1.0, 0.3, 0.3)
        else:
            color = (1.0, 1.0, 1.0)

        # Special-case: Completed quiz message -> fancy panel
        if "Quiz Complete" in self.message:
            # Use a nice scifi panel and a big title
            title = "ANALYSIS COMPLETE"
            subtitle = "DATA ACQUISITION SUCCESSFUL"

            # Calculate text sizes
            _, title_w, title_h = UIRenderer.get_text_texture(title, 42)
            _, sub_w, sub_h = UIRenderer.get_text_texture(subtitle, 18)

            box_w = max(title_w, sub_w) + 80
            box_h = title_h + sub_h + 48
            box_x = (w - box_w) / 2
            box_y = (h - box_h) / 2

            # Draw scifi panel
            UIRenderer.setup_2d(w, h)
            UIRenderer.draw_scifi_panel(box_x, box_y, box_w, box_h)

            # Draw title and subtitle centered
            UIRenderer.draw_text(box_x + (box_w - title_w) / 2, box_y + box_h - 54,
                                 title, size=42, color=(0.0, 1.0, 1.0), font_name="radiospace")
            UIRenderer.draw_text(box_x + (box_w - sub_w) / 2, box_y + 18,
                                 subtitle, size=18, color=(0.7, 0.9, 1.0), font_name="radiospace")
            UIRenderer.restore_3d()
            return

        # Special-case: Failed quiz message -> fancy red panel
        if "CRITICAL FAILURE" in self.message:
            # Use a nice scifi panel and a big title
            title = "MISSION FAILED"
            subtitle = "CRITICAL SYSTEM FAILURE"

            # Calculate text sizes
            _, title_w, title_h = UIRenderer.get_text_texture(title, 42)
            _, sub_w, sub_h = UIRenderer.get_text_texture(subtitle, 18)

            box_w = max(title_w, sub_w) + 100
            box_h = title_h + sub_h + 60
            box_x = (w - box_w) / 2
            box_y = (h - box_h) / 2

            UIRenderer.setup_2d(w, h)

            # Draw RED scifi panel manually
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Red background
            glColor4f(0.2, 0.0, 0.0, 0.85)
            chamfer = 18.0
            glBegin(GL_POLYGON)
            glVertex2f(box_x + chamfer, box_y)
            glVertex2f(box_x + box_w - chamfer, box_y)
            glVertex2f(box_x + box_w, box_y + chamfer)
            glVertex2f(box_x + box_w, box_y + box_h - chamfer)
            glVertex2f(box_x + box_w - chamfer, box_y + box_h)
            glVertex2f(box_x + chamfer, box_y + box_h)
            glVertex2f(box_x, box_y + box_h - chamfer)
            glVertex2f(box_x, box_y + chamfer)
            glEnd()

            # Red border
            glLineWidth(2.5)
            glColor3f(1.0, 0.0, 0.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(box_x + chamfer, box_y)
            glVertex2f(box_x + box_w - chamfer, box_y)
            glVertex2f(box_x + box_w, box_y + chamfer)
            glVertex2f(box_x + box_w, box_y + box_h - chamfer)
            glVertex2f(box_x + box_w - chamfer, box_y + box_h)
            glVertex2f(box_x + chamfer, box_y + box_h)
            glVertex2f(box_x, box_y + box_h - chamfer)
            glVertex2f(box_x, box_y + chamfer)
            glEnd()
            glDisable(GL_BLEND)

            # Draw title and subtitle centered
            UIRenderer.draw_text(box_x + (box_w - title_w) / 2, box_y + box_h - 54,
                                 title, size=42, color=(1.0, 0.2, 0.2), font_name="radiospace")
            UIRenderer.draw_text(box_x + (box_w - sub_w) / 2, box_y + 18,
                                 subtitle, size=18, color=(1.0, 0.6, 0.6), font_name="radiospace")
            UIRenderer.restore_3d()
            return

        # Special-case: Strike messages - render a compact scifi panel for cinematic flair
        if "STRIKE" in self.message:
            UIRenderer.setup_2d(w, h)
            # Compute text size and panel size
            _, msg_w, msg_h = UIRenderer.get_text_texture(self.message, 24)
            box_w = msg_w + 80
            box_h = msg_h + 28
            box_x = (w - box_w) / 2
            box_y = (h - box_h) / 2

            # Draw RED scifi panel manually
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Red background
            glColor4f(0.3, 0.0, 0.0, 0.7)
            chamfer = 10.0
            glBegin(GL_POLYGON)
            glVertex2f(box_x + chamfer, box_y)
            glVertex2f(box_x + box_w - chamfer, box_y)
            glVertex2f(box_x + box_w, box_y + chamfer)
            glVertex2f(box_x + box_w, box_y + box_h - chamfer)
            glVertex2f(box_x + box_w - chamfer, box_y + box_h)
            glVertex2f(box_x + chamfer, box_y + box_h)
            glVertex2f(box_x, box_y + box_h - chamfer)
            glVertex2f(box_x, box_y + chamfer)
            glEnd()

            # Red border
            glLineWidth(2.0)
            glColor3f(1.0, 0.0, 0.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(box_x + chamfer, box_y)
            glVertex2f(box_x + box_w - chamfer, box_y)
            glVertex2f(box_x + box_w, box_y + chamfer)
            glVertex2f(box_x + box_w, box_y + box_h - chamfer)
            glVertex2f(box_x + box_w - chamfer, box_y + box_h)
            glVertex2f(box_x + chamfer, box_y + box_h)
            glVertex2f(box_x, box_y + box_h - chamfer)
            glVertex2f(box_x, box_y + chamfer)
            glEnd()
            glDisable(GL_BLEND)

            # Use custom font for cinematic strike panel (no font_name -> custom font)
            UIRenderer.draw_text(box_x + (box_w - msg_w) / 2, box_y + (box_h - msg_h) / 2,
                                 self.message, size=24, color=color, font_name="radiospace")
            UIRenderer.restore_3d()
            return

        msg_width = len(self.message) * 12
        msg_x = (w - msg_width) / 2

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        alpha = min(1.0, self.message_timer)
        glColor4f(0.0, 0.0, 0.0, 0.85 * alpha)
        glBegin(GL_QUADS)
        glVertex2f(msg_x - 25, h/2 - 35)
        glVertex2f(msg_x + msg_width + 25, h/2 - 35)
        glVertex2f(msg_x + msg_width + 25, h/2 + 35)
        glVertex2f(msg_x - 25, h/2 + 35)
        glEnd()

        # Border
        glColor4f(color[0], color[1], color[2], alpha)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(msg_x - 25, h/2 - 35)
        glVertex2f(msg_x + msg_width + 25, h/2 - 35)
        glVertex2f(msg_x + msg_width + 25, h/2 + 35)
        glVertex2f(msg_x - 25, h/2 + 35)
        glEnd()
        glDisable(GL_BLEND)

        # Message text - use custom font for HUD consistency
        UIRenderer.draw_text(msg_x, h/2 - 8, self.message,
                             size=24, color=color)

    def _draw_intro_overlay(self, w, h):
        """Draw intro screen overlay."""
        from src.graphics.ui_renderer import UIRenderer

        # Title (can use title font)
        title = f"PLANETARY ANALYSIS: {self.planet_name.upper()}"
        subtitle = "INITIALIZING..."

        _, title_w, title_h = UIRenderer.get_text_texture(title, 36)
        _, sub_w, sub_h = UIRenderer.get_text_texture(subtitle, 18)

        box_w = max(title_w, sub_w) + 100
        box_h = title_h + sub_h + 60
        box_x = (w - box_w) / 2
        box_y = (h - box_h) / 2

        UIRenderer.setup_2d(w, h)
        UIRenderer.draw_scifi_panel(box_x, box_y, box_w, box_h)

        UIRenderer.draw_text(box_x + (box_w - title_w) / 2, box_y + box_h - 50, title,
                             size=36, color=(0.0, 1.0, 1.0), font_name="radiospace")

        # Blinking subtitle
        alpha = 0.5 + 0.5 * math.sin(time.time() * 10.0)
        UIRenderer.draw_text(box_x + (box_w - sub_w) / 2, box_y + 30, subtitle,
                             size=18, color=(0.0, 1.0, 1.0), scale=1, font_name="radiospace")  # scale=1 to avoid blur if any

        UIRenderer.restore_3d()

    def is_complete(self):
        """Check if quiz is complete."""
        return self.state in [self.STATE_COMPLETE, self.STATE_FAILED]

    def passed(self):
        """Check if quiz was passed."""
        return self.state == self.STATE_COMPLETE


def create_cylindrical_quiz(planet_name, quiz_manager):
    """
    Factory function to create a cylindrical quiz for a planet.
    """
    questions = quiz_manager.all_questions.get(planet_name, [])
    if not questions:
        print(f"[CylindricalQuiz] No questions for {planet_name}")
        return None

    random.seed(time.time())
    num_questions = min(10, len(questions))
    selected = random.sample(questions, num_questions)
    random.shuffle(selected)

    return CylindricalQuizManager(planet_name, selected)


class CylindricalQuizState(BaseState):
    """
    State that handles the cylindrical quiz experience.
    """

    def __init__(self, planet_name, quiz_manager, on_complete_callback=None):
        self.planet_name = planet_name
        self.quiz_manager_ref = quiz_manager
        self.on_complete_callback = on_complete_callback
        self.quiz = None
        self.input_manager = InputManager()
        self.finished = False
        self.result_passed = False
        self.result_score = 0
        self.result_strikes = 0

    def enter(self):
        """Initialize the quiz."""
        print(f"[CylindricalQuizState] Entering quiz for {self.planet_name}")

        self.quiz = create_cylindrical_quiz(
            self.planet_name, self.quiz_manager_ref)
        if not self.quiz:
            print("[CylindricalQuizState] Failed to create quiz - no questions!")
            self.finished = True
            return

        self.quiz.on_complete = self._on_quiz_complete
        self.quiz.on_fail = self._on_quiz_fail
        self.quiz.start(self.input_manager)

    def exit(self):
        """Clean up."""
        print(f"[CylindricalQuizState] Exiting quiz for {self.planet_name}")
        self.input_manager.key_state.clear()
        self.input_manager.special_key_state.clear()

    def _on_quiz_complete(self, passed, score, strikes):
        """Called when quiz is completed."""
        self.finished = True
        self.result_passed = True
        self.result_score = score
        self.result_strikes = strikes

    def _on_quiz_fail(self):
        """Called when quiz is failed."""
        self.finished = True
        self.result_passed = False

    def update(self, dt):
        """Update the quiz."""
        if not self.quiz:
            return

        self.quiz.update(dt)

        if self.finished and not getattr(self, '_exit_triggered', False):
            self._exit_triggered = True  # Prevent multiple triggers
            if self.on_complete_callback:
                self.on_complete_callback(
                    self.result_passed, self.result_score, self.result_strikes)
            if hasattr(self, 'state_machine') and self.state_machine:
                self.state_machine.pop(use_transition=True, duration=0.5)

    def draw(self):
        """Draw the quiz."""
        glClearColor(0.0, 0.0, 0.02, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if not self.quiz:
            return

        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)

        # Set up projection with slightly narrower FOV to reduce distortion
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50.0, w / h if h > 0 else 1.0, 0.1, 500.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glEnable(GL_DEPTH_TEST)

        self.quiz.draw()
        self.quiz.draw_ui(w, h)

    def handle_input(self, event, x, y):
        """Handle input events."""
        if event[0] == 'KEY_DOWN':
            key = event[1]

            if key == b'\x1b':  # ESC
                self._on_quiz_fail()
                return

            self.input_manager.key_down(key, x, y)

        elif event[0] == 'KEY_UP':
            key = event[1]
            self.input_manager.key_up(key, x, y)

        elif event[0] == 'SPECIAL_KEY_DOWN':
            key = event[1]
            self.input_manager.special_key_down(key, x, y)

        elif event[0] == 'SPECIAL_KEY_UP':
            key = event[1]
            self.input_manager.special_key_up(key, x, y)
