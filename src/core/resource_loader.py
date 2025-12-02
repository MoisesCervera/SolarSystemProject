import os
import json
from OpenGL.GL import *
try:
    from PIL import Image
except ImportError:
    Image = None
    print("[ResourceManager] Error: Pillow (PIL) not installed. Textures will not load.")


class ResourceManager:
    """
    Centralized resource manager for loading assets (textures, fonts, sounds, data).
    """

    # Calculate base paths relative to this file (src/core/resource_loader.py)
    # Go up 2 levels: src/core -> src -> root
    PROJECT_ROOT = os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")

    TEXTURES_DIR = os.path.join(ASSETS_DIR, "textures")
    FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
    SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
    DATA_DIR = os.path.join(ASSETS_DIR, "data")

    @classmethod
    def get_absolute_path(cls, category, filename):
        """Get absolute path for an asset."""
        if category == "textures":
            return os.path.join(cls.TEXTURES_DIR, filename)
        elif category == "fonts":
            return os.path.join(cls.FONTS_DIR, filename)
        elif category == "sounds":
            return os.path.join(cls.SOUNDS_DIR, filename)
        elif category == "data":
            return os.path.join(cls.DATA_DIR, filename)
        else:
            return os.path.join(cls.ASSETS_DIR, filename)

    @classmethod
    def load_texture(cls, relative_path):
        """
        Load a texture from the assets/textures directory.
        Args:
            relative_path: Path relative to assets/textures/ (e.g. "planets/earth.jpg")
        """
        full_path = cls.get_absolute_path("textures", relative_path)
        return cls._load_gl_texture(full_path)

    @classmethod
    def _load_gl_texture(cls, full_path):
        """Internal method to load texture using PIL and OpenGL."""
        if Image is None:
            print("[ResourceManager] Cannot load texture because PIL is missing.")
            return None

        if not os.path.exists(full_path):
            print(f"[ResourceManager] Error: File not found at {full_path}")
            return None

        try:
            img = Image.open(full_path)
            # Convert to RGBA for consistency
            img = img.convert("RGBA")

            img_data = img.tobytes("raw", "RGBA", 0, -1)
            width, height = img.size

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Configure texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Load data
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                         0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

            print(
                f"[ResourceManager] Successfully loaded texture: {os.path.basename(full_path)} (ID: {texture_id})")
            return texture_id
        except Exception as e:
            print(f"[ResourceManager] Failed to load texture {full_path}: {e}")
            return None

    @classmethod
    def get_font_path(cls, font_filename):
        """Get absolute path for a font file."""
        return cls.get_absolute_path("fonts", font_filename)

    @classmethod
    def load_json(cls, filename):
        """Load a JSON file from assets/data."""
        full_path = cls.get_absolute_path("data", filename)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ResourceManager] Error loading JSON {filename}: {e}")
            return None

    @classmethod
    def load_sound(cls, filename):
        """
        Load a sound file from assets/sounds.
        (Placeholder for future implementation)
        """
        full_path = cls.get_absolute_path("sounds", filename)
        if os.path.exists(full_path):
            print(
                f"[ResourceManager] Sound found at {full_path} (Loading not implemented)")
            return full_path
        else:
            print(f"[ResourceManager] Sound file not found: {filename}")
            return None
