import math


def check_collision(pos1, pos2, radius_sum):
    """
    Verifica si la distancia entre dos puntos es menor a la suma de sus radios.
    Usa distancia al cuadrado para optimizar (evita sqrt).
    """
    dx = pos1[0] - pos2[0]
    dy = pos1[1] - pos2[1]
    dz = pos1[2] - pos2[2]

    dist_sq = dx*dx + dy*dy + dz*dz
    radius_sq = radius_sum * radius_sum

    return dist_sq < radius_sq
