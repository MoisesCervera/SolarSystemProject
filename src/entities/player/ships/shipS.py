from src.graphics import draw_utils as du
from OpenGL.GL import *

# --- Paleta de Colores ---
COLOR_CHASIS = (0.1, 0.2, 0.7)      # Azul oscuro mate
COLOR_ALAS = (0.15, 0.25, 0.8)      # Azul contraste
COLOR_OJOS = (0.9, 1.0, 0.2)        # Amarillo SÓLIDO
COLOR_BORDE_OJOS = (0.05, 0.1, 0.3)  # Azul casi negro
COLOR_PATAS = (0.1, 0.15, 0.4)      # Azul oscuro
COLOR_DETALLES = (0.7, 0.7, 0.8)    # Gris plateado
COLOR_PROPULSOR = (1.0, 0.5, 0.0)   # Naranja

NAVE_BASE_Y_OFFSET = 1.21

# Display list cache for static geometry (compiled once for performance)
_static_display_list = None
_is_compiled = False


def _dibujar_cuerpo_base():

    du.set_material_color(COLOR_CHASIS, shininess=30.0)
    du.glPushMatrix()
    du.glScalef(1.4, 0.9, 1.3)
    du.draw_sphere(radius=1.0)
    du.glPopMatrix()

    du.set_material_color(COLOR_BORDE_OJOS)
    du.glPushMatrix()
    du.glScalef(1.42, 0.92, 0.1)
    du.draw_sphere(radius=1.0)
    du.glPopMatrix()


def _dibujar_alitas():
    du.set_material_color(COLOR_ALAS, shininess=50.0)
    # Ala Izquierda
    du.glPushMatrix()
    du.glTranslatef(-0.5, 0.6, 0.3)
    du.glRotatef(15, 0, 0, 1)
    du.glRotatef(5, 1, 0, 0)
    du.glScalef(0.5, 0.15, 0.9)
    du.draw_sphere(radius=1.0)
    du.glPopMatrix()
    # Ala Derecha
    du.glPushMatrix()
    du.glTranslatef(0.5, 0.6, 0.3)
    du.glRotatef(-15, 0, 0, 1)
    du.glRotatef(5, 1, 0, 0)
    du.glScalef(0.5, 0.15, 0.9)
    du.draw_sphere(radius=1.0)
    du.glPopMatrix()


def _dibujar_ojos():
    posiciones = [(-0.6, 0.2, 0.9), (0.6, 0.2, 0.9)]
    rotaciones = [-20, 20]

    for i in range(2):
        du.glPushMatrix()
        du.glTranslatef(posiciones[i][0], posiciones[i][1], posiciones[i][2])
        du.glRotatef(rotaciones[i], 0, 1, 0)

        # 1. El Marco
        du.set_material_color(COLOR_BORDE_OJOS)
        du.glPushMatrix()
        du.glScalef(0.65, 0.65, 0.45)
        du.draw_sphere(radius=1.0)
        du.glPopMatrix()

        du.glPopMatrix()


def _dibujar_antenas():
    posiciones = [(-0.3, 0.8, 0.8), (0.3, 0.8, 0.8)]
    for x, y, z in posiciones:
        du.glPushMatrix()
        du.glTranslatef(x, y, z)

        angulo = 35 if x < 0 else -35
        du.glRotatef(angulo, 0, 0, 1)
        du.glRotatef(20, 1, 0, 0)

        du.set_material_color(COLOR_DETALLES, shininess=40.0)
        du.draw_sphere(0.08)

        du.set_material_color(COLOR_DETALLES, shininess=40.0)
        du.draw_cylinder(base_radius=0.03, top_radius=0.02, height=0.5)

        # Punta
        du.glPushMatrix()
        du.glTranslatef(0.0, 0.25, 0.0)
        du.set_material_color(COLOR_PROPULSOR, shininess=80.0)
        du.draw_sphere(0.05)
        du.glPopMatrix()

        du.glPopMatrix()


def _dibujar_propulsores():
    """Propulsores traseros."""
    posiciones = [(-0.4, -1.1), (0.4, -1.1)]

    for x, z in posiciones:
        du.glPushMatrix()
        du.glTranslatef(x, 0.0, z)
        du.glRotatef(180, 0, 1, 0)

        # Carcasa
        du.set_material_color(COLOR_BORDE_OJOS, shininess=20.0)
        du.draw_cylinder(base_radius=0.28, top_radius=0.32, height=0.5)

        # Anillo
        du.glPushMatrix()
        du.glTranslatef(0.0, 0.5, 0.0)
        du.set_material_color(COLOR_DETALLES, shininess=60.0)
        du.draw_torus(inner_radius=0.02, outer_radius=0.32, sides=8, rings=16)
        du.glPopMatrix()

        # Fuego
        du.set_material_color(COLOR_PROPULSOR, shininess=80.0)
        du.glPushMatrix()
        du.glTranslatef(0.0, 0.1, 0.0)
        du.draw_cone(base_radius=0.18, height=0.4)
        du.glPopMatrix()

        du.glPopMatrix()


def _dibujar_pata_detallada(lado_derecho=True):
    du.glPushMatrix()
    if not lado_derecho:
        du.glScalef(-1.0, 1.0, 1.0)

    # Hombro
    du.set_material_color(COLOR_DETALLES, shininess=50.0)
    du.draw_sphere(0.22)
    du.set_material_color(COLOR_PATAS, shininess=20.0)

    # Muslo
    du.glPushMatrix()
    du.glRotatef(45, 0, 0, 1)
    du.glRotatef(20, 1, 0, 0)

    du.glPushMatrix()
    du.glTranslatef(0.0, -0.3, 0.0)
    du.draw_cylinder(base_radius=0.12, top_radius=0.12, height=0.6)
    du.glPopMatrix()

    # Rodilla
    du.glTranslatef(0.0, -0.6, 0.0)
    du.set_material_color(COLOR_DETALLES, shininess=50.0)
    du.draw_sphere(0.16)

    # Pantorrilla
    du.glRotatef(-45, 0, 0, 1)
    du.glPushMatrix()
    du.glTranslatef(0.0, -0.25, 0.0)
    du.draw_cylinder(base_radius=0.1, top_radius=0.08, height=0.5)
    du.glPopMatrix()

    # Pie
    du.glTranslatef(0.0, -0.5, 0.0)
    du.set_material_color(COLOR_PATAS, shininess=20.0)
    du.glScalef(1.3, 0.4, 1.5)
    du.draw_sphere(0.15)

    du.glPopMatrix()
    du.glPopMatrix()


# ==========================================================
# FUNCIÓN PRINCIPAL DE DIBUJO
# ==========================================================

def _compile_static_geometry():
    """Compile static ship geometry into a display list for performance."""
    global _static_display_list, _is_compiled

    if _static_display_list is not None:
        glDeleteLists(_static_display_list, 1)

    _static_display_list = glGenLists(1)
    glNewList(_static_display_list, GL_COMPILE)

    # All static components
    _dibujar_cuerpo_base()
    _dibujar_alitas()
    _dibujar_ojos()
    _dibujar_antenas()
    _dibujar_propulsores()

    glEndList()
    _is_compiled = True


def dibujar_nave(anim_state=None):
    """
    Dibuja la nave completa.
    anim_state (dict, opcional): Diccionario con el estado de la animación
                                 (e.g., ángulos de rotación, offsets).    

    Args:
        anim_state (dict, opcional): Estado de la animación (hover, balanceo).
    """
    global _is_compiled

    # Compile static geometry on first draw
    if not _is_compiled:
        _compile_static_geometry()

    du.glPushMatrix()

    glRotatef(180, 0, 1, 0)  # Girar la nave para que mire hacia adelante

    hover_y = anim_state["hover_y"] if anim_state and "hover_y" in anim_state else 0.0
    du.glTranslatef(0.0, NAVE_BASE_Y_OFFSET + hover_y, 0.0)

    # Draw static geometry from display list (fast)
    if _static_display_list is not None:
        glCallList(_static_display_list)

    # Animated parts: legs with movement
    balanceo_z = anim_state["balanceo_pata_z"] if anim_state and "balanceo_pata_z" in anim_state else 0.0

    pata_anclajes = [(0.9, -0.2, 0.5, True), (-0.9, -0.2, 0.5, False),
                     (1.0, -0.1, -0.5, True), (-1.0, -0.1, -0.5, False)]

    for x, y, z, es_derecha in pata_anclajes:
        du.glPushMatrix()
        du.glTranslatef(x, y, z)
        du.glRotatef(balanceo_z if es_derecha else -balanceo_z, 0, 0, 1)
        _dibujar_pata_detallada(es_derecha)
        du.glPopMatrix()

    du.glPopMatrix()
