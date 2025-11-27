import math
from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.GLUT import *
from src.graphics import draw_utils as du

# Display list cache for static geometry (compiled once for performance)
_static_display_list = None
_is_compiled = False


def draw_fuselaje():
    glEnable(GL_DEPTH_TEST)

    glColor3f(0.3, 0.3, 0.4)
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glScalef(0.8, 0.4, 2.5)
    du.draw_sphere(radius=1.5, slices=16, stacks=12)  # Reduced from 30x30
    glPopMatrix()

    # Cabina
    glColor4f(0.2, 0.3, 0.6, 0.7)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPushMatrix()
    glTranslatef(0, 0.5, 0.3)
    glScalef(0.6, 0.5, 0.8)
    du.draw_sphere(radius=1.0, slices=12, stacks=10)  # Reduced from 20x20
    glPopMatrix()
    glDisable(GL_BLEND)


def draw_alas():
    glEnable(GL_DEPTH_TEST)

    glColor3f(0.4, 0.4, 0.5)
    glPushMatrix()
    glTranslatef(0, -0.2, 0)
    glScalef(3.0, 0.1, 1.5)
    du.draw_sphere(radius=1.0, slices=4, stacks=4)
    glPopMatrix()

    glColor3f(0.35, 0.35, 0.45)
    glPushMatrix()
    glTranslatef(-1.8, -0.1, 0)
    glScalef(0.8, 0.05, 1.2)
    du.draw_sphere(radius=1.0, slices=4, stacks=4)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1.8, -0.1, 0)
    glScalef(0.8, 0.05, 1.2)
    du.draw_sphere(radius=1.0, slices=4, stacks=4)
    glPopMatrix()

    glColor3f(0.3, 0.3, 0.4)
    glPushMatrix()
    glTranslatef(-1.0, 0.2, -1.8)
    glScalef(0.1, 0.8, 0.3)
    du.draw_sphere(radius=1.0, slices=4, stacks=4)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1.0, 0.2, -1.8)
    glScalef(0.1, 0.8, 0.3)
    du.draw_sphere(radius=1.0, slices=4, stacks=4)
    glPopMatrix()


def draw_propulsores():
    glEnable(GL_DEPTH_TEST)

    glColor3f(0.2, 0.2, 0.3)
    glPushMatrix()
    glTranslatef(0, -0.1, -2.2)
    glScalef(0.6, 0.6, 0.4)
    du.draw_cylinder(base_radius=0.8, top_radius=0.5, height=1.0, slices=20)
    glPopMatrix()

    glColor3f(0.2, 0.2, 0.3)
    glPushMatrix()
    glTranslatef(-1.5, -0.1, -0.5)
    glScalef(0.3, 0.3, 0.3)
    du.draw_cylinder(base_radius=0.5, top_radius=0.3, height=1.0, slices=15)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1.5, -0.1, -0.5)
    glScalef(0.3, 0.3, 0.3)
    du.draw_cylinder(base_radius=0.5, top_radius=0.3, height=1.0, slices=15)
    glPopMatrix()


def draw_armamento():
    glEnable(GL_DEPTH_TEST)

    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(-0.5, 0.1, 1.8)
    glRotatef(90, 1, 0, 0)
    du.draw_cylinder(base_radius=0.1, top_radius=0.1, height=1.0, slices=8)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.5, 0.1, 1.8)
    glRotatef(90, 1, 0, 0)
    du.draw_cylinder(base_radius=0.1, top_radius=0.1, height=1.0, slices=8)
    glPopMatrix()

    glColor3f(0.25, 0.25, 0.3)
    glPushMatrix()
    glTranslatef(-1.8, 0.1, 0)
    glScalef(0.1, 0.1, 0.8)
    du.draw_sphere(radius=1.0, slices=8, stacks=6)  # Reduced from 10x10
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1.8, 0.1, 0)
    glScalef(0.1, 0.1, 0.8)
    du.draw_sphere(radius=1.0, slices=8, stacks=6)  # Reduced from 10x10
    glPopMatrix()


def _compile_static_geometry():
    """Compile entire starfighter into a display list for performance."""
    global _static_display_list, _is_compiled

    if _static_display_list is not None:
        glDeleteLists(_static_display_list, 1)

    _static_display_list = glGenLists(1)
    glNewList(_static_display_list, GL_COMPILE)

    draw_fuselaje()
    draw_alas()
    draw_propulsores()
    draw_armamento()

    glEndList()
    _is_compiled = True


def draw_nave():
    """Draw the starfighter using cached display list for performance."""
    global _is_compiled

    # Compile on first draw
    if not _is_compiled:
        _compile_static_geometry()

    # Draw from display list (fast)
    if _static_display_list is not None:
        glCallList(_static_display_list)
