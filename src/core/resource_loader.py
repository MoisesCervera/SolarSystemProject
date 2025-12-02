"""
ResourceManager - Centralized Asset Loading System

This module provides a single source of truth for all asset I/O operations.
It handles textures, fonts, sounds, music, and JSON data with built-in caching,
error handling, and PyInstaller compatibility.

Usage:
    from src.core.resource_loader import ResourceManager
    
    # Load assets using paths relative to assets/ folder
    texture_id = ResourceManager.load_texture("textures/planets/mars/2k_mars.jpg")
    font = ResourceManager.load_font("Exo Space DEMO.ttf", 24)
    data = ResourceManager.load_json("data/Earth.json")
    sound = ResourceManager.load_sound("sound/fx/click.wav")
    music_path = ResourceManager.get_music_path("sound/music/theme.mp3")
"""

import os
import sys
import json
from OpenGL.GL import *

try:
    from PIL import Image, ImageFont
except ImportError:
    Image = None
    ImageFont = None
    print("[ResourceManager] Error: Pillow (PIL) not installed. Textures and fonts will not load.")


class ResourceManager:
    """
    Centralized resource manager for loading assets (textures, fonts, sounds, data).

    This class is the single source of truth for all asset I/O. It provides:
    - PyInstaller-ready path resolution
    - Automatic caching for textures, fonts, and sounds
    - Graceful error handling with fallbacks
    - Consistent API for all asset types

    All paths should be relative to the assets/ folder.
    """

    # =========================================================================
    # INTERNAL CACHES
    # =========================================================================
    _texture_cache = {}      # {path: texture_id}
    _font_cache = {}         # {(path, size): ImageFont}
    _sound_cache = {}        # {path: Sound object}
    _json_cache = {}         # {path: parsed_data}

    # Fallback texture (generated once on first missing texture)
    _fallback_texture_id = None

    # =========================================================================
    # PATH RESOLUTION (PyInstaller Ready)
    # =========================================================================

    @classmethod
    def _get_base_path(cls):
        """
        Get the base path for assets, handling both development and frozen executables.

        In development: Returns the project root directory
        When frozen (PyInstaller): Returns sys._MEIPASS where assets are extracted
        """
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller bundle
            return sys._MEIPASS
        else:
            # Running in development - go up from src/core to project root
            return os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))

    @classmethod
    def get_path(cls, relative_path):
        """
        Resolve a path relative to the assets/ folder.

        This is the primary path resolution method. It handles:
        - Development environment (relative to project root)
        - Frozen executables (PyInstaller's _MEIPASS)
        - Path normalization across platforms

        Args:
            relative_path: Path relative to assets/ folder
                          e.g., "textures/planets/mars/2k_mars.jpg"
                          e.g., "data/Earth.json"

        Returns:
            Absolute path string that works on the current system
        """
        base = cls._get_base_path()
        assets_dir = os.path.join(base, "assets")

        # Normalize path separators for cross-platform compatibility
        normalized_path = relative_path.replace(
            '/', os.sep).replace('\\', os.sep)

        return os.path.join(assets_dir, normalized_path)

    @classmethod
    def get_absolute_path(cls, category, filename):
        """
        Legacy method for backwards compatibility.

        Args:
            category: One of "textures", "fonts", "sounds", "data"
            filename: Filename or relative path within the category

        Returns:
            Absolute path string
        """
        if category == "textures":
            return cls.get_path(f"textures/{filename}")
        elif category == "fonts":
            return cls.get_path(f"fonts/{filename}")
        elif category == "sounds" or category == "sound":
            return cls.get_path(f"sound/{filename}")
        elif category == "data":
            return cls.get_path(f"data/{filename}")
        else:
            return cls.get_path(filename)

    # =========================================================================
    # TEXTURE LOADING
    # =========================================================================

    @classmethod
    def _create_fallback_texture(cls):
        """
        Create a magenta/black checkerboard fallback texture for missing assets.
        This makes missing textures obvious during debugging.
        """
        if cls._fallback_texture_id is not None:
            return cls._fallback_texture_id

        try:
            # Create a 64x64 magenta/black checkerboard pattern
            size = 64
            checker_size = 8
            pixels = []

            for y in range(size):
                for x in range(size):
                    # Checkerboard pattern
                    is_magenta = ((x // checker_size) +
                                  (y // checker_size)) % 2 == 0
                    if is_magenta:
                        pixels.extend([255, 0, 255, 255])  # Magenta
                    else:
                        pixels.extend([0, 0, 0, 255])  # Black

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, size, size,
                         0, GL_RGBA, GL_UNSIGNED_BYTE, bytes(pixels))

            cls._fallback_texture_id = texture_id
            print(
                f"[ResourceManager] Created fallback texture (ID: {texture_id})")
            return texture_id

        except Exception as e:
            print(f"[ResourceManager] Failed to create fallback texture: {e}")
            return None

    @classmethod
    def load_texture(cls, relative_path, use_cache=True):
        """
        Load a texture from the assets folder.

        This method handles:
        - Caching to prevent duplicate loads
        - Automatic RGBA conversion
        - Fallback texture for missing files
        - OpenGL texture binding

        Args:
            relative_path: Path relative to assets/ folder
                          e.g., "textures/planets/mars/2k_mars.jpg"

                          For legacy compatibility, paths relative to assets/textures/
                          are also accepted: e.g., "planets/mars/2k_mars.jpg"

            use_cache: Whether to use/update the texture cache (default True)

        Returns:
            OpenGL texture ID (int), or fallback texture ID if loading fails
        """
        # Normalize the path - check if it already includes "textures/"
        if not relative_path.startswith("textures/") and not relative_path.startswith("textures\\"):
            # Legacy path format - prepend textures/
            full_relative = f"textures/{relative_path}"
        else:
            full_relative = relative_path

        # Check cache first
        if use_cache and full_relative in cls._texture_cache:
            return cls._texture_cache[full_relative]

        full_path = cls.get_path(full_relative)
        texture_id = cls._load_gl_texture(full_path)

        if texture_id is not None:
            if use_cache:
                cls._texture_cache[full_relative] = texture_id
            return texture_id
        else:
            # Return fallback texture
            fallback = cls._create_fallback_texture()
            print(
                f"[ResourceManager] Using fallback texture for: {relative_path}")
            return fallback

    @classmethod
    def _load_gl_texture(cls, full_path):
        """
        Internal method to load texture using PIL and OpenGL.

        Args:
            full_path: Absolute path to the texture file

        Returns:
            OpenGL texture ID or None on failure
        """
        if Image is None:
            print("[ResourceManager] Cannot load texture: PIL is not installed")
            return None

        if not os.path.exists(full_path):
            print(f"[ResourceManager] Texture not found: {full_path}")
            return None

        try:
            img = Image.open(full_path)
            # Convert to RGBA for consistency
            img = img.convert("RGBA")

            # Flip
            img = img.transpose(Image.FLIP_LEFT_RIGHT)

            img_data = img.tobytes("raw", "RGBA", 0, -1)
            width, height = img.size

            texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture_id)

            # Configure texture parameters
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                            GL_LINEAR_MIPMAP_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            # Load data and generate mipmaps
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height,
                         0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            glGenerateMipmap(GL_TEXTURE_2D)

            print(f"[ResourceManager] Loaded texture: {os.path.basename(full_path)} "
                  f"({width}x{height}, ID: {texture_id})")
            return texture_id

        except Exception as e:
            print(f"[ResourceManager] Failed to load texture {full_path}: {e}")
            return None

    # =========================================================================
    # FONT LOADING
    # =========================================================================

    @classmethod
    def load_font(cls, font_name, size, use_cache=True):
        """
        Load a font from the assets/fonts folder.

        This method handles:
        - Caching based on (font_name, size) tuple
        - Fallback to default font if not found
        - PIL ImageFont loading

        Args:
            font_name: Font filename (e.g., "Exo Space DEMO.ttf")
            size: Font size in points
            use_cache: Whether to use/update the font cache (default True)

        Returns:
            PIL ImageFont object, or default font on failure
        """
        if ImageFont is None:
            print("[ResourceManager] Cannot load font: PIL is not installed")
            return None

        cache_key = (font_name, size)

        # Check cache first
        if use_cache and cache_key in cls._font_cache:
            return cls._font_cache[cache_key]

        full_path = cls.get_path(f"fonts/{font_name}")

        try:
            if os.path.exists(full_path):
                font = ImageFont.truetype(full_path, size)
                if use_cache:
                    cls._font_cache[cache_key] = font
                return font
            else:
                print(f"[ResourceManager] Font not found: {full_path}")
                # Try loading as system font
                try:
                    font = ImageFont.truetype(font_name, size)
                    if use_cache:
                        cls._font_cache[cache_key] = font
                    return font
                except Exception:
                    pass

        except Exception as e:
            print(f"[ResourceManager] Failed to load font {font_name}: {e}")

        # Return default font as fallback
        print(f"[ResourceManager] Using default font instead of: {font_name}")
        default_font = ImageFont.load_default()
        if use_cache:
            cls._font_cache[cache_key] = default_font
        return default_font

    @classmethod
    def get_font_path(cls, font_filename):
        """
        Get absolute path for a font file.

        This is useful when you need the raw path for external libraries
        that handle their own font loading.

        Args:
            font_filename: Font filename (e.g., "Exo Space DEMO.ttf")

        Returns:
            Absolute path to the font file
        """
        return cls.get_path(f"fonts/{font_filename}")

    # =========================================================================
    # JSON LOADING
    # =========================================================================

    @classmethod
    def load_json(cls, relative_path, use_cache=False):
        """
        Load and parse a JSON file from the assets folder.

        Args:
            relative_path: Path relative to assets/ folder
                          e.g., "data/Earth.json"

                          For legacy compatibility, paths relative to assets/data/
                          are also accepted: e.g., "Earth.json"

            use_cache: Whether to cache the parsed data (default False)
                      Set to True for frequently accessed static data

        Returns:
            Parsed JSON data (dict/list), or None on failure
        """
        # Normalize the path
        if not relative_path.startswith("data/") and not relative_path.startswith("data\\"):
            full_relative = f"data/{relative_path}"
        else:
            full_relative = relative_path

        # Check cache
        if use_cache and full_relative in cls._json_cache:
            return cls._json_cache[full_relative]

        full_path = cls.get_path(full_relative)

        try:
            if not os.path.exists(full_path):
                print(f"[ResourceManager] JSON not found: {full_path}")
                return None

            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if use_cache:
                cls._json_cache[full_relative] = data

            print(
                f"[ResourceManager] Loaded JSON: {os.path.basename(full_path)}")
            return data

        except json.JSONDecodeError as e:
            print(f"[ResourceManager] Invalid JSON in {relative_path}: {e}")
            return None
        except Exception as e:
            print(
                f"[ResourceManager] Failed to load JSON {relative_path}: {e}")
            return None

    # =========================================================================
    # SOUND LOADING
    # =========================================================================

    @classmethod
    def load_sound(cls, relative_path, use_cache=True):
        """
        Load a sound effect from the assets folder.

        Note: Requires pygame.mixer to be initialized.

        Args:
            relative_path: Path relative to assets/ folder
                          e.g., "sound/fx/click.wav"

        Returns:
            pygame.mixer.Sound object, or None on failure
        """
        # Normalize path
        if not relative_path.startswith("sound/") and not relative_path.startswith("sound\\"):
            full_relative = f"sound/{relative_path}"
        else:
            full_relative = relative_path

        # Check cache
        if use_cache and full_relative in cls._sound_cache:
            return cls._sound_cache[full_relative]

        full_path = cls.get_path(full_relative)

        if not os.path.exists(full_path):
            print(f"[ResourceManager] Sound not found: {full_path}")
            return None

        try:
            # Lazy import pygame to avoid dependency if not using sounds
            import pygame.mixer

            if not pygame.mixer.get_init():
                print(
                    "[ResourceManager] pygame.mixer not initialized, initializing now...")
                pygame.mixer.init()

            sound = pygame.mixer.Sound(full_path)

            if use_cache:
                cls._sound_cache[full_relative] = sound

            print(
                f"[ResourceManager] Loaded sound: {os.path.basename(full_path)}")
            return sound

        except ImportError:
            print("[ResourceManager] pygame.mixer not available for sound loading")
            return None
        except Exception as e:
            print(
                f"[ResourceManager] Failed to load sound {relative_path}: {e}")
            return None

    @classmethod
    def get_music_path(cls, relative_path):
        """
        Get the absolute path for a music file (for streaming).

        Music files are typically streamed rather than loaded into memory,
        so this returns the path for use with pygame.mixer.music.load().

        Args:
            relative_path: Path relative to assets/ folder
                          e.g., "sound/music/theme.mp3"

        Returns:
            Absolute path string, or None if file doesn't exist
        """
        # Normalize path
        if not relative_path.startswith("sound/") and not relative_path.startswith("sound\\"):
            full_relative = f"sound/{relative_path}"
        else:
            full_relative = relative_path

        full_path = cls.get_path(full_relative)

        if os.path.exists(full_path):
            return full_path
        else:
            print(f"[ResourceManager] Music file not found: {full_path}")
            return None

    # =========================================================================
    # CACHE MANAGEMENT
    # =========================================================================

    @classmethod
    def clear_cache(cls, cache_type=None):
        """
        Clear cached resources.

        Args:
            cache_type: One of "textures", "fonts", "sounds", "json", or None for all
        """
        if cache_type is None or cache_type == "textures":
            # Delete OpenGL textures
            for texture_id in cls._texture_cache.values():
                if texture_id is not None:
                    try:
                        glDeleteTextures(1, [texture_id])
                    except Exception:
                        pass
            cls._texture_cache.clear()
            print("[ResourceManager] Texture cache cleared")

        if cache_type is None or cache_type == "fonts":
            cls._font_cache.clear()
            print("[ResourceManager] Font cache cleared")

        if cache_type is None or cache_type == "sounds":
            cls._sound_cache.clear()
            print("[ResourceManager] Sound cache cleared")

        if cache_type is None or cache_type == "json":
            cls._json_cache.clear()
            print("[ResourceManager] JSON cache cleared")

    @classmethod
    def get_cache_stats(cls):
        """
        Get statistics about cached resources.

        Returns:
            Dictionary with cache counts
        """
        return {
            "textures": len(cls._texture_cache),
            "fonts": len(cls._font_cache),
            "sounds": len(cls._sound_cache),
            "json": len(cls._json_cache),
        }

    @classmethod
    def preload_textures(cls, paths):
        """
        Preload multiple textures at once.

        Useful during loading screens to avoid hitches during gameplay.

        Args:
            paths: List of paths relative to assets/textures/
        """
        loaded = 0
        for path in paths:
            if cls.load_texture(path) is not None:
                loaded += 1
        print(f"[ResourceManager] Preloaded {loaded}/{len(paths)} textures")
