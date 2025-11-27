from OpenGL.GLU import gluLookAt
import math


class Camera:
    MODE_ORBIT = 0
    MODE_FOLLOW = 1

    def __init__(self):
        self.mode = self.MODE_ORBIT

        # Orbit parameters (Spherical coordinates)
        self.target = [0.0, 0.0, 0.0]
        self.radius = 30.0
        self.yaw = 0.0
        self.pitch = 30.0

        # Follow parameters
        self.position = [0.0, 10.0, 20.0]
        self.follow_target = None  # Objeto con propiedad .position (x,y,z)
        self.follow_smoothness = 5.0  # Factor de interpolación

    def update(self, dt):
        if self.mode == self.MODE_FOLLOW and self.follow_target:
            # Lerp para suavizar el movimiento de la cámara
            target_x = self.follow_target.position[0]
            target_y = self.follow_target.position[1]
            target_z = self.follow_target.position[2]

            # Posición deseada: Detrás y arriba de la nave
            # Calculamos el vector "atrás" basado en la rotación de la nave
            rad = math.radians(self.follow_target.rotation_y)
            offset_dist = 8.0  # Closer to ship
            offset_height = 3.5  # Lower height

            # Nota el doble negativo por la convención -Z
            desired_x = target_x - (-math.sin(rad) * offset_dist)
            desired_z = target_z - (-math.cos(rad) * offset_dist)
            desired_y = target_y + offset_height

            # Frame-rate independent interpolation using exponential decay
            # This ensures consistent camera behavior regardless of frame rate
            # Formula: lerp_factor = 1 - (1 - base_factor)^(dt * 60)
            # At 60 FPS, dt=1/60, so we get base_factor
            # At higher FPS, we get smaller steps that compound correctly
            base_smoothness = 0.15  # Amount to move per frame at 60 FPS
            lerp_factor = 1.0 - math.pow(1.0 - base_smoothness, dt * 60)

            self.position[0] += (desired_x - self.position[0]) * lerp_factor
            self.position[1] += (desired_y - self.position[1]) * lerp_factor
            self.position[2] += (desired_z - self.position[2]) * lerp_factor

            # Camera looks slightly ahead of the ship for better forward view
            look_ahead_dist = 3.0  # Reduced - closer to ship
            look_ahead_x = target_x + (-math.sin(rad) * look_ahead_dist)
            look_ahead_z = target_z + (-math.cos(rad) * look_ahead_dist)
            look_ahead_y = target_y + 0.5  # Just slightly above ship

            self.target = [look_ahead_x, look_ahead_y, look_ahead_z]

    def apply(self):
        """Aplica la matriz de vista (View Matrix) usando gluLookAt."""
        if self.mode == self.MODE_ORBIT:
            # Convertir coordenadas esféricas a cartesianas
            rad_yaw = math.radians(self.yaw)
            rad_pitch = math.radians(self.pitch)

            # Calcular posición de la cámara
            cam_x = self.target[0] + self.radius * \
                math.sin(rad_yaw) * math.cos(rad_pitch)
            cam_y = self.target[1] + self.radius * math.sin(rad_pitch)
            cam_z = self.target[2] + self.radius * \
                math.cos(rad_yaw) * math.cos(rad_pitch)

            gluLookAt(cam_x, cam_y, cam_z,
                      self.target[0], self.target[1], self.target[2],
                      0, 1, 0)

        elif self.mode == self.MODE_FOLLOW:
            gluLookAt(self.position[0], self.position[1], self.position[2],
                      self.target[0], self.target[1], self.target[2],
                      0, 1, 0)

    def rotate(self, dx, dy):
        """Rota la cámara en modo órbita."""
        if self.mode == self.MODE_ORBIT:
            self.yaw += dx
            self.pitch += dy
            # Limitar el pitch para evitar el gimbal lock o inversión
            self.pitch = max(-89.0, min(89.0, self.pitch))

    def zoom(self, amount):
        """Acerca o aleja la cámara."""
        if self.mode == self.MODE_ORBIT:
            self.radius -= amount
            self.radius = max(5.0, min(200.0, self.radius))
