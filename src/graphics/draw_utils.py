"""
Drawing utilities module with primitive shape functions.
Provides modular functions for rendering basic 3D shapes.
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math


def set_material_color(color, shininess=32.0, specular_strength=0.5):
    """
    Set material properties for Phong lighting.

    Args:
        color (tuple): RGB or RGBA color for ambient and diffuse
        shininess (float): Material shininess (0-128), default 32
        specular_strength (float): Strength of specular highlights (0-1), default 0.5
    """
    if color:
        # Set ambient and diffuse (affected by GL_COLOR_MATERIAL)
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

        # Set specular component for Phong highlights
        specular = (specular_strength, specular_strength,
                    specular_strength, 1.0)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)


def draw_cube(size=1.0, color=None, shininess=32.0):
    """
    Draw a cube centered at the origin.

    Uses glPushMatrix/glPopMatrix to isolate transformations.
    Automatically generates normals for proper lighting.

    Args:
        size (float): Size of the cube (edge length)
        color (tuple): Optional RGB or RGBA color
        shininess (float): Material shininess for specular highlights
    """
    glPushMatrix()

    set_material_color(color, shininess)

    # Scale to desired size
    glScalef(size, size, size)

    # Draw cube using glutSolidCube for automatic normals
    glutSolidCube(1.0)

    glPopMatrix()


def draw_sphere(radius=1.0, slices=32, stacks=32, color=None, shininess=32.0):
    """
    Draw a sphere centered at the origin.

    Uses gluSphere with automatically generated normals for proper lighting.

    Args:
        radius (float): Sphere radius
        slices (int): Number of subdivisions around Z axis
        stacks (int): Number of subdivisions along Z axis
        color (tuple): Optional RGB or RGBA color
        shininess (float): Material shininess for specular highlights
    """
    glPushMatrix()

    set_material_color(color, shininess)

    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluQuadricTexture(quadric, GL_TRUE)
    gluSphere(quadric, radius, slices, stacks)
    gluDeleteQuadric(quadric)

    glPopMatrix()


def draw_cylinder(base_radius=1.0, top_radius=1.0, height=1.0,
                  slices=32, stacks=1, color=None, shininess=32.0):
    """
    Draw a cylinder along the Y axis, centered at the origin.

    Args:
        base_radius (float): Radius at the base (y=-height/2)
        top_radius (float): Radius at the top (y=+height/2)
        height (float): Height of the cylinder
        slices (int): Number of subdivisions around the axis
        stacks (int): Number of subdivisions along the axis
        color (tuple): Optional RGB or RGBA color
        shininess (float): Material shininess for specular highlights
    """
    glPushMatrix()

    set_material_color(color, shininess)

    # Rotate so cylinder axis (originally Z) aligns with Y (upright)
    glRotatef(-90, 1, 0, 0)

    # Move to center the cylinder (apply translate before rotation in object space)
    glTranslatef(0, 0, -height / 2.0)

    # Draw cylinder body
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluQuadricTexture(quadric, GL_TRUE)
    gluCylinder(quadric, base_radius, top_radius, height, slices, stacks)

    # Draw bottom cap (at z=0 before rotation)
    glPushMatrix()
    glRotatef(180, 1, 0, 0)
    gluDisk(quadric, 0, base_radius, slices, 1)
    glPopMatrix()

    # Draw top cap (at z=height before rotation)
    glPushMatrix()
    glTranslatef(0, 0, height)
    gluDisk(quadric, 0, top_radius, slices, 1)
    glPopMatrix()

    gluDeleteQuadric(quadric)
    glPopMatrix()


def draw_cone(base_radius=1.0, height=1.0, slices=32, stacks=1, color=None):
    """
    Draw a cone along the Z axis, with base centered at origin.

    Args:
        base_radius (float): Radius at the base
        height (float): Height of the cone
        slices (int): Number of subdivisions around the Z axis
        stacks (int): Number of subdivisions along the Z axis
        color (tuple): Optional RGB or RGBA color
    """
    draw_cylinder(base_radius, 0.0, height, slices, stacks, color)


def draw_plane(width=1.0, height=1.0, color=None, normal=(0, 1, 0)):
    """
    Draw a rectangular plane in the XZ plane (horizontal) or custom orientation.

    Args:
        width (float): Width along the X axis
        height (float): Height along the Z axis
        color (tuple): Optional RGB or RGBA color
        normal (tuple): Normal vector for lighting (default: up)
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    # Draw plane as a quad
    w = width / 2.0
    h = height / 2.0

    glBegin(GL_QUADS)
    glNormal3f(*normal)
    glVertex3f(-w, 0, -h)
    glVertex3f(w, 0, -h)
    glVertex3f(w, 0, h)
    glVertex3f(-w, 0, h)
    glEnd()

    glPopMatrix()


def draw_torus(inner_radius=0.5, outer_radius=1.0, sides=32, rings=32, color=None):
    """
    Draw a torus (donut shape) centered at the origin.

    Args:
        inner_radius (float): Inner radius
        outer_radius (float): Outer radius
        sides (int): Number of sides for each ring
        rings (int): Number of rings
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    glutSolidTorus(inner_radius, outer_radius, sides, rings)

    glPopMatrix()


def draw_teapot(size=1.0, color=None):
    """
    Draw the classic Utah teapot.

    Args:
        size (float): Size of the teapot
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    glutSolidTeapot(size)

    glPopMatrix()


def draw_capsule(radius=0.5, height=2.0, slices=32, stacks=16, color=None):
    """
    Draw a capsule (cylinder with hemisphere caps) along the Y axis.
    Useful for character body parts.

    Args:
        radius (float): Radius of the capsule
        height (float): Total height including hemispheres
        slices (int): Number of subdivisions
        stacks (int): Number of subdivisions for spheres
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    cylinder_height = max(0, height - 2 * radius)

    # Bottom hemisphere
    glPushMatrix()
    glTranslatef(0, -cylinder_height / 2.0, 0)
    glRotatef(-90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluSphere(quadric, radius, slices, stacks // 2)
    gluDeleteQuadric(quadric)
    glPopMatrix()

    # Middle cylinder
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    glTranslatef(0, 0, -cylinder_height / 2.0)
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluCylinder(quadric, radius, radius, cylinder_height, slices, 1)
    gluDeleteQuadric(quadric)
    glPopMatrix()

    # Top hemisphere
    glPushMatrix()
    glTranslatef(0, cylinder_height / 2.0, 0)
    glRotatef(-90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluSphere(quadric, radius, slices, stacks // 2)
    gluDeleteQuadric(quadric)
    glPopMatrix()

    glPopMatrix()


def draw_grid(size=10, spacing=1.0, color=None):
    """
    Draw a grid in the XZ plane for reference.

    Args:
        size (int): Number of grid lines in each direction
        spacing (float): Distance between grid lines
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)
    else:
        glColor3f(0.3, 0.3, 0.3)  # Default gray

    # Disable lighting for grid
    glDisable(GL_LIGHTING)

    half_size = (size * spacing) / 2.0

    glBegin(GL_LINES)
    for i in range(size + 1):
        offset = i * spacing - half_size
        # Lines parallel to X axis
        glVertex3f(-half_size, 0, offset)
        glVertex3f(half_size, 0, offset)
        # Lines parallel to Z axis
        glVertex3f(offset, 0, -half_size)
        glVertex3f(offset, 0, half_size)
    glEnd()

    # Re-enable lighting
    glEnable(GL_LIGHTING)

    glPopMatrix()


def draw_axes(length=1.0):
    """
    Draw coordinate axes for debugging.
    X=Red, Y=Green, Z=Blue

    Args:
        length (float): Length of each axis
    """
    glPushMatrix()

    # Disable lighting for axes
    glDisable(GL_LIGHTING)

    glBegin(GL_LINES)
    # X axis - Red
    glColor3f(1, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(length, 0, 0)

    # Y axis - Green
    glColor3f(0, 1, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, length, 0)

    # Z axis - Blue
    glColor3f(0, 0, 1)
    glVertex3f(0, 0, 0)
    glVertex3f(0, 0, length)
    glEnd()

    # Re-enable lighting
    glEnable(GL_LIGHTING)

    glPopMatrix()


def draw_rectangle(width=1.0, height=1.0, depth=0.1, color=None):
    """
    Draw a flat rectangle (thin box) centered at origin.
    Useful for eyebrows, flat panels, etc.

    Args:
        width (float): Width (X dimension)
        height (float): Height (Y dimension)
        depth (float): Depth/thickness (Z dimension), default is thin
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    glScalef(width, height, depth)
    glutSolidCube(1.0)

    glPopMatrix()


def draw_half_sphere(radius=1.0, slices=40, stacks=20, upper=True, closed=True, color=None):
    """
    Draw a half sphere (hemisphere).

    Args:
        radius (float): Radius of the hemisphere
        slices (int): Number of subdivisions around the Y axis
        stacks (int): Number of subdivisions along the Y axis (affects smoothness)
        upper (bool): If True, draws upper hemisphere (+Y), if False draws lower hemisphere (-Y)
        closed (bool): If True, draws a flat base to close the hemisphere (solid)
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    glScalef(radius, radius, radius)

    # Draw hemisphere using triangle strips
    for i in range(stacks):
        lat0 = (math.pi * 0.5 * i) / \
            stacks if upper else (math.pi * 0.5 * (i - stacks)) / stacks
        lat1 = (math.pi * 0.5 * (i + 1)) / \
            stacks if upper else (math.pi * 0.5 * (i + 1 - stacks)) / stacks

        glBegin(GL_TRIANGLE_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * j / slices

            # First vertex
            x0 = math.cos(lat0) * math.cos(lng)
            y0 = math.sin(lat0)
            z0 = math.cos(lat0) * math.sin(lng)
            glNormal3f(x0, y0, z0)
            glVertex3f(x0, y0, z0)

            # Second vertex
            x1 = math.cos(lat1) * math.cos(lng)
            y1 = math.sin(lat1)
            z1 = math.cos(lat1) * math.sin(lng)
            glNormal3f(x1, y1, z1)
            glVertex3f(x1, y1, z1)
        glEnd()

    # Draw flat base to close the hemisphere if requested
    if closed:
        glBegin(GL_TRIANGLE_FAN)
        # Normal pointing DOWN for upper hemisphere, UP for lower hemisphere
        glNormal3f(0, -1 if upper else 1, 0)
        # Center point
        glVertex3f(0, 0, 0)
        # Outer rim - need to reverse winding order for lower hemisphere
        if upper:
            for j in range(slices + 1):
                lng = 2 * math.pi * j / slices
                x = math.cos(lng)
                z = math.sin(lng)
                glVertex3f(x, 0, z)
        else:
            # Reverse winding for lower hemisphere so normal faces outward
            for j in range(slices, -1, -1):
                lng = 2 * math.pi * j / slices
                x = math.cos(lng)
                z = math.sin(lng)
                glVertex3f(x, 0, z)
        glEnd()

    glPopMatrix()


def draw_half_torus(inner_radius=0.5, outer_radius=1.0, sides=16, rings=16, upper=True, color=None):
    """
    Draw a half torus (half donut shape).

    Args:
        inner_radius (float): Inner radius of the torus tube
        outer_radius (float): Outer radius from center to tube center
        sides (int): Number of sides for each tube segment
        rings (int): Number of segments around the torus
        upper (bool): If True, draws upper half (+Y), if False draws lower half (-Y)
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    # Calculate the tube radius
    tube_radius = (outer_radius - inner_radius) / 2.0
    center_radius = inner_radius + tube_radius

    # Draw the curved surface using quad strips
    for i in range(rings):
        angle1 = math.pi * i / \
            rings if upper else math.pi * (i + rings) / rings
        angle2 = math.pi * \
            (i + 1) / rings if upper else math.pi * (i + 1 + rings) / rings

        glBegin(GL_QUAD_STRIP)
        for j in range(sides + 1):
            tube_angle = 2.0 * math.pi * j / sides

            # First ring
            cos_tube1 = math.cos(tube_angle)
            sin_tube1 = math.sin(tube_angle)
            x1 = (center_radius + tube_radius * cos_tube1) * math.cos(angle1)
            y1 = tube_radius * sin_tube1
            z1 = (center_radius + tube_radius * cos_tube1) * math.sin(angle1)
            glVertex3f(x1, y1, z1)

            # Second ring
            x2 = (center_radius + tube_radius * cos_tube1) * math.cos(angle2)
            y2 = tube_radius * sin_tube1
            z2 = (center_radius + tube_radius * cos_tube1) * math.sin(angle2)
            glVertex3f(x2, y2, z2)
        glEnd()

    # Draw end caps to close the half torus
    # Left end cap (at angle 0 or pi)
    cap_angle = 0.0 if upper else math.pi
    glBegin(GL_TRIANGLE_FAN)
    # Center point
    x_center = center_radius * math.cos(cap_angle)
    z_center = center_radius * math.sin(cap_angle)
    glVertex3f(x_center, 0, z_center)
    # Circle around the tube
    for j in range(sides + 1):
        tube_angle = 2.0 * math.pi * j / sides
        cos_tube = math.cos(tube_angle)
        sin_tube = math.sin(tube_angle)
        x = (center_radius + tube_radius * cos_tube) * math.cos(cap_angle)
        y = tube_radius * sin_tube
        z = (center_radius + tube_radius * cos_tube) * math.sin(cap_angle)
        glVertex3f(x, y, z)
    glEnd()

    # Right end cap (at angle pi or 2*pi)
    cap_angle = math.pi if upper else 2.0 * math.pi
    glBegin(GL_TRIANGLE_FAN)
    x_center = center_radius * math.cos(cap_angle)
    z_center = center_radius * math.sin(cap_angle)
    glVertex3f(x_center, 0, z_center)
    for j in range(sides + 1):
        tube_angle = 2.0 * math.pi * j / sides
        cos_tube = math.cos(tube_angle)
        sin_tube = math.sin(tube_angle)
        x = (center_radius + tube_radius * cos_tube) * math.cos(cap_angle)
        y = tube_radius * sin_tube
        z = (center_radius + tube_radius * cos_tube) * math.sin(cap_angle)
        glVertex3f(x, y, z)
    glEnd()

    glPopMatrix()


def draw_crescent_moon(outer_radius=1.0, inner_radius=0.7, offset=0.3, segments=16, depth=0.1, color=None):
    """
    Draw a crescent moon shape with depth (perfect for eyebrows!).

    Args:
        outer_radius (float): Radius of the outer arc
        inner_radius (float): Radius of the inner arc (controls thickness)
        offset (float): How much to offset the inner circle (controls crescent width)
        segments (int): Number of segments for smoothness
        depth (float): Thickness in the Z direction
        color (tuple): Optional RGB or RGBA color
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    half_depth = depth / 2.0

    # Draw front face
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        angle = math.pi * i / segments  # 0 to 180 degrees

        # Outer arc point
        x_outer = outer_radius * math.cos(angle)
        y_outer = outer_radius * math.sin(angle)
        glVertex3f(x_outer, y_outer, half_depth)

        # Inner arc point (offset to create crescent)
        x_inner = inner_radius * math.cos(angle)
        y_inner = inner_radius * math.sin(angle) + offset
        glVertex3f(x_inner, y_inner, half_depth)
    glEnd()

    # Draw back face
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        angle = math.pi * i / segments

        x_outer = outer_radius * math.cos(angle)
        y_outer = outer_radius * math.sin(angle)
        glVertex3f(x_outer, y_outer, -half_depth)

        x_inner = inner_radius * math.cos(angle)
        y_inner = inner_radius * math.sin(angle) + offset
        glVertex3f(x_inner, y_inner, -half_depth)
    glEnd()

    # Draw outer edge (connecting front and back outer arcs)
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        angle = math.pi * i / segments
        x = outer_radius * math.cos(angle)
        y = outer_radius * math.sin(angle)
        glVertex3f(x, y, half_depth)
        glVertex3f(x, y, -half_depth)
    glEnd()

    # Draw inner edge (connecting front and back inner arcs)
    glBegin(GL_TRIANGLE_STRIP)
    for i in range(segments + 1):
        angle = math.pi * i / segments
        x = inner_radius * math.cos(angle)
        y = inner_radius * math.sin(angle) + offset
        glVertex3f(x, y, half_depth)
        glVertex3f(x, y, -half_depth)
    glEnd()

    # Draw left end cap (at angle 0)
    glBegin(GL_TRIANGLE_STRIP)
    x_outer = outer_radius
    y_outer = 0
    x_inner = inner_radius
    y_inner = offset
    glVertex3f(x_outer, y_outer, half_depth)
    glVertex3f(x_outer, y_outer, -half_depth)
    glVertex3f(x_inner, y_inner, half_depth)
    glVertex3f(x_inner, y_inner, -half_depth)
    glEnd()

    # Draw right end cap (at angle pi)
    glBegin(GL_TRIANGLE_STRIP)
    x_outer = -outer_radius
    y_outer = 0
    x_inner = -inner_radius
    y_inner = offset
    glVertex3f(x_outer, y_outer, half_depth)
    glVertex3f(x_outer, y_outer, -half_depth)
    glVertex3f(x_inner, y_inner, half_depth)
    glVertex3f(x_inner, y_inner, -half_depth)
    glEnd()

    glPopMatrix()


def draw_platform(width=1.0, height=1.0, depth=1.0, color=None):
    """
    Draw a rectangular platform (like a Mario brick/ground).

    Args:
        width (float): Width of the platform
        height (float): Height of the platform
        depth (float): Depth of the platform
        color (tuple): Optional RGB or RGBA color (default: greenish)
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)
    else:
        glColor3f(0.4, 0.6, 0.3)  # Default greenish platform color

    glScalef(width, height, depth)
    glutSolidCube(1.0)

    glPopMatrix()


def draw_skybox(size=50.0, colors=None):
    """
    Draw a simple colored skybox.

    Args:
        size (float): Size of the skybox
        colors (dict): Optional dictionary with face colors
                      Keys: 'bottom', 'top', 'front', 'back', 'left', 'right'
    """
    glPushMatrix()

    # Disable lighting for skybox
    glDisable(GL_LIGHTING)
    # Disable depth test so skybox is always in background
    glDisable(GL_DEPTH_TEST)

    # Default colors
    default_colors = {
        'bottom': (0.2, 0.3, 0.4),
        'top': (0.5, 0.7, 1.0),
        'front': (0.6, 0.8, 1.0),
        'back': (0.6, 0.8, 1.0),
        'left': (0.6, 0.8, 1.0),
        'right': (0.6, 0.8, 1.0)
    }

    if colors:
        default_colors.update(colors)

    # Draw each face with different colors
    faces = [
        # Bottom (darker)
        ([(-1, -1, -1), (1, -1, -1), (1, -1, 1),
         (-1, -1, 1)], default_colors['bottom']),
        # Top (sky blue)
        ([(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)], default_colors['top']),
        # Front
        ([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], default_colors['front']),
        # Back
        ([(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)], default_colors['back']),
        # Left
        ([(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)], default_colors['left']),
        # Right
        ([(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], default_colors['right']),
    ]

    glBegin(GL_QUADS)
    for vertices, color in faces:
        glColor3f(*color)
        for x, y, z in vertices:
            glVertex3f(x * size, y * size, z * size)
    glEnd()

    # Re-enable depth test and lighting
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

    glPopMatrix()


def draw_spiral(radius=0.5, height=2.0, turns=2.5, tube_radius=0.15, segments=64, color=None):
    """
    Draw a spiral/coil shape - perfect for curly pug tails!

    The spiral goes upward along the Y axis with the specified number of turns.

    Args:
        radius (float): Radius of the spiral (how wide the coil is)
        height (float): Total height of the spiral along Y axis
        turns (float): Number of complete rotations (2.5 = two and a half loops)
        tube_radius (float): Thickness of the spiral tube
        segments (int): Number of segments for smoothness (higher = smoother)
        color (tuple): Optional RGB or RGBA color

    Perfect for: curly tails, springs, coils, decorative spirals
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    # Create quadric for the tube segments
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)

    # Draw the spiral as a series of small cylinder segments
    steps = segments
    for i in range(steps):
        t = i / float(steps)  # 0 to 1

        # Calculate position along spiral
        angle = 2 * math.pi * turns * t
        y = -height/2 + height * t
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)

        # Calculate next position for orientation
        t_next = (i + 1) / float(steps)
        angle_next = 2 * math.pi * turns * t_next
        y_next = -height/2 + height * t_next
        x_next = radius * math.cos(angle_next)
        z_next = radius * math.sin(angle_next)

        # Direction vector
        dx = x_next - x
        dy = y_next - y
        dz = z_next - z
        segment_length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if segment_length > 0:
            glPushMatrix()

            # Move to current position
            glTranslatef(x, y, z)

            # Calculate rotation to align cylinder with direction
            # Default cylinder is along Z axis, need to rotate to point along (dx, dy, dz)
            length_xz = math.sqrt(dx*dx + dz*dz)
            if length_xz > 0:
                # Rotate around Y axis to point in XZ direction
                angle_y = math.atan2(dx, dz) * 180 / math.pi
                glRotatef(angle_y, 0, 1, 0)

                # Rotate around X axis to point upward/downward
                angle_x = -math.atan2(dy, length_xz) * 180 / math.pi
                glRotatef(angle_x, 1, 0, 0)

            # Draw small cylinder segment
            gluCylinder(quadric, tube_radius,
                        tube_radius, segment_length, 8, 1)

            # Draw cap at start (only for first segment)
            if i == 0:
                glPushMatrix()
                glRotatef(180, 1, 0, 0)
                gluDisk(quadric, 0, tube_radius, 8, 1)
                glPopMatrix()

            # Draw cap at end (only for last segment)
            if i == steps - 1:
                glPushMatrix()
                glTranslatef(0, 0, segment_length)
                gluDisk(quadric, 0, tube_radius, 8, 1)
                glPopMatrix()

            glPopMatrix()

    gluDeleteQuadric(quadric)
    glPopMatrix()


def draw_curly_tail(base_radius=0.3, tip_radius=0.1, height=1.5, curl_radius=0.4,
                    turns=1.5, segments=48, color=None):
    """
    Draw a cute curly pug tail that tapers from base to tip!

    This is a tapered spiral - thick at the base, thin at the tip.
    The tail curls upward and inward like a classic pug tail.

    Args:
        base_radius (float): Thickness at the base of the tail
        tip_radius (float): Thickness at the tip of the tail
        height (float): Total height of the tail along Y axis
        curl_radius (float): How wide the curl is (spiral radius)
        turns (float): Number of complete curls (1.5 is typical pug curl)
        segments (int): Number of segments for smoothness
        color (tuple): Optional RGB or RGBA color

    Perfect for: pug tails, curly pig tails, cute animal tails
    """
    glPushMatrix()

    if color:
        if len(color) == 3:
            glColor3f(*color)
        else:
            glColor4f(*color)

    # Create quadric for segments
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)

    steps = segments
    for i in range(steps):
        t = i / float(steps)  # 0 to 1 (base to tip)

        # Taper the thickness from base to tip
        tube_radius = base_radius * (1 - t) + tip_radius * t

        # Calculate position along spiral
        angle = 2 * math.pi * turns * t
        y = height * t  # Grow upward
        x = curl_radius * math.cos(angle)
        z = curl_radius * math.sin(angle)

        # Calculate next position
        t_next = (i + 1) / float(steps)
        tube_radius_next = base_radius * (1 - t_next) + tip_radius * t_next
        angle_next = 2 * math.pi * turns * t_next
        y_next = height * t_next
        x_next = curl_radius * math.cos(angle_next)
        z_next = curl_radius * math.sin(angle_next)

        # Direction vector
        dx = x_next - x
        dy = y_next - y
        dz = z_next - z
        segment_length = math.sqrt(dx*dx + dy*dy + dz*dz)

        if segment_length > 0:
            glPushMatrix()

            # Move to current position
            glTranslatef(x, y, z)

            # Calculate rotation
            length_xz = math.sqrt(dx*dx + dz*dz)
            if length_xz > 0:
                angle_y = math.atan2(dx, dz) * 180 / math.pi
                glRotatef(angle_y, 0, 1, 0)
                angle_x = -math.atan2(dy, length_xz) * 180 / math.pi
                glRotatef(angle_x, 1, 0, 0)

            # Draw tapered cylinder segment
            gluCylinder(quadric, tube_radius, tube_radius_next,
                        segment_length, 12, 1)

            # Draw cap at start
            if i == 0:
                glPushMatrix()
                glRotatef(180, 1, 0, 0)
                gluDisk(quadric, 0, tube_radius, 12, 1)
                glPopMatrix()

            # Draw cap at end
            if i == steps - 1:
                glPushMatrix()
                glTranslatef(0, 0, segment_length)
                gluDisk(quadric, 0, tube_radius_next, 12, 1)
                glPopMatrix()

            glPopMatrix()

    gluDeleteQuadric(quadric)
    glPopMatrix()
