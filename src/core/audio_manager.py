"""
AudioManager - Centralized Audio System for Solar System Game

This module provides comprehensive audio management including:
- State-based music playlists with seamless transitions
- Cached sound effects for lag-free playback
- Hierarchical volume control (master/music/sfx)
- Fade transitions synchronized with screen transitions

Usage:
    from src.core.audio_manager import AudioManager, get_audio_manager
    from src.core.resource_loader import ResourceManager
    
    # Initialize (typically in main.py or window_manager.py)
    audio = AudioManager(ResourceManager)
    
    # Or use singleton
    audio = get_audio_manager()
    
    # Play state-based music
    audio.play_music('MENU')
    
    # Play sound effects
    audio.play_sfx('click')
    audio.play_sfx('explosion')
    
    # Volume control
    audio.update_volume('master', 0.8)
    audio.update_volume('music', 0.5)
    audio.toggle_mute()
"""

import random
import time
from typing import Dict, List, Optional, Any

try:
    import pygame
    import pygame.mixer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("[AudioManager] Warning: pygame not available. Audio disabled.")


# =============================================================================
# CONFIGURATION - Easy to modify playlists and SFX mappings
# =============================================================================

# Music playlists for each game state
# Each state maps to a list of possible tracks (randomly selected)
MUSIC_PLAYLISTS: Dict[str, List[str]] = {
    # Main menu and ship selection share this playlist
    'MENU': [
        'music/menu_ambient_1.mp3',
        'music/menu_ambient_2.mp3',
        'music/menu_theme.mp3',
    ],

    # Orbital view / exploration
    'ORBIT': [
        'music/orbit_exploration_1.mp3',
        'music/orbit_exploration_2.mp3',
        'music/space_ambient_1.mp3',
    ],

    # Active gameplay / flying around
    'GAMEPLAY': [
        'music/gameplay_action_1.mp3',
        'music/gameplay_action_2.mp3',
        'music/gameplay_ambient_1.mp3',
    ],

    # Quiz/challenge state
    'QUIZ': [
        'music/quiz_tension_1.mp3',
        'music/quiz_thinking_1.mp3',
    ],

    # Victory / completion
    'VICTORY': [
        'music/victory_fanfare.mp3',
        'music/victory_celebration.mp3',
    ],

    # Game over / failure
    'DEFEAT': [
        'music/defeat_somber.mp3',
    ],

    # Planet detail view
    'PLANET_DETAIL': [
        'music/planet_wonder_1.mp3',
        'music/planet_ambient_1.mp3',
    ],

    # Pause menu (quieter, ambient)
    'PAUSE': [
        'music/pause_ambient.mp3',
    ],
}

# Sound effects mapping
# Key: event name used in code -> Value: path relative to assets/
SFX_REGISTRY: Dict[str, str] = {
    # UI sounds
    'click': 'sound/fx/ui_click.wav',
    'hover': 'sound/fx/ui_hover.wav',
    'select': 'sound/fx/ui_select.wav',
    'back': 'sound/fx/ui_back.wav',
    'error': 'sound/fx/ui_error.wav',
    'success': 'sound/fx/ui_success.wav',
    'notification': 'sound/fx/ui_notification.wav',

    # Ship/movement sounds
    'thruster': 'sound/fx/ship_thruster.wav',
    'thruster_boost': 'sound/fx/ship_thruster_boost.wav',
    'ship_impact': 'sound/fx/ship_impact.wav',
    'ship_damage': 'sound/fx/ship_damage.wav',

    # Space/environment sounds
    'asteroid_explosion': 'sound/fx/asteroid_explosion.wav',
    'asteroid_hit': 'sound/fx/asteroid_hit.wav',
    'whoosh': 'sound/fx/whoosh.wav',
    'ambient_space': 'sound/fx/ambient_space.wav',

    # Quiz sounds
    'quiz_start': 'sound/fx/quiz_start.wav',
    'quiz_correct': 'sound/fx/quiz_correct.wav',
    'quiz_wrong': 'sound/fx/quiz_wrong.wav',
    'quiz_timeout': 'sound/fx/quiz_timeout.wav',
    'quiz_direction_change': 'sound/fx/quiz_direction.wav',
    'quiz_complete': 'sound/fx/quiz_complete.wav',

    # Achievement/reward sounds
    'trophy_earned': 'sound/fx/trophy_earned.wav',
    'level_up': 'sound/fx/level_up.wav',
    'coin_collect': 'sound/fx/coin_collect.wav',

    # Transition sounds
    'transition_whoosh': 'sound/fx/transition_whoosh.wav',
    'warp': 'sound/fx/warp.wav',
}

# Default volumes
DEFAULT_MASTER_VOLUME = 0.8
DEFAULT_MUSIC_VOLUME = 0.6
DEFAULT_SFX_VOLUME = 0.8

# Fade durations (in milliseconds)
DEFAULT_FADE_OUT_MS = 500
DEFAULT_FADE_IN_MS = 500


class AudioManager:
    """
    Centralized audio manager for the Solar System game.

    Handles all music and sound effect playback with:
    - State-based music playlists
    - Seamless music continuity within same state
    - Fade transitions between states
    - Cached SFX for instant playback
    - Hierarchical volume control
    """

    def __init__(self, resource_loader=None):
        """
        Initialize the AudioManager.

        Args:
            resource_loader: ResourceManager class or instance for loading assets.
                           If None, will attempt to import ResourceManager.
        """
        self.loader = resource_loader
        if self.loader is None:
            try:
                from src.core.resource_loader import ResourceManager
                self.loader = ResourceManager
            except ImportError:
                print("[AudioManager] Warning: Could not import ResourceManager")

        # Audio system state
        self._initialized = False
        self._enabled = PYGAME_AVAILABLE

        # Volume settings (0.0 to 1.0)
        self._master_volume = DEFAULT_MASTER_VOLUME
        self._music_volume = DEFAULT_MUSIC_VOLUME
        self._sfx_volume = DEFAULT_SFX_VOLUME

        # Mute state (preserves volume settings)
        self._muted = False
        self._pre_mute_master = DEFAULT_MASTER_VOLUME

        # Music state tracking
        self._current_state: Optional[str] = None
        self._current_track: Optional[str] = None
        self._is_music_playing = False
        self._fade_in_progress = False
        self._pending_state: Optional[str] = None

        # SFX cache
        self._sfx_cache: Dict[str, Any] = {}

        # Looping sounds (for continuous effects like thrusters)
        self._looping_sounds: Dict[str, Any] = {}

        # Initialize pygame mixer if available
        if self._enabled:
            self._init_mixer()

    def _init_mixer(self):
        """Initialize pygame mixer with optimal settings."""
        if not PYGAME_AVAILABLE:
            return

        try:
            if not pygame.mixer.get_init():
                # Initialize with good defaults for game audio
                # frequency=44100, size=-16 (signed 16-bit), channels=2 (stereo), buffer=512
                pygame.mixer.init(frequency=44100, size=-
                                  16, channels=2, buffer=512)

            # Reserve channels for different purposes
            pygame.mixer.set_num_channels(16)  # Total channels available

            self._initialized = True
            print("[AudioManager] Mixer initialized successfully")

        except Exception as e:
            print(f"[AudioManager] Failed to initialize mixer: {e}")
            self._enabled = False

    # =========================================================================
    # ASSET LOADING
    # =========================================================================

    def load_assets(self, preload_sfx: bool = True):
        """
        Load and cache audio assets.

        Args:
            preload_sfx: If True, preload all SFX into memory for instant playback
        """
        if not self._enabled or not self.loader:
            return

        if preload_sfx:
            self._preload_sfx()

    def _preload_sfx(self):
        """Preload all registered sound effects into cache."""
        if not self._enabled or not self.loader:
            return

        loaded = 0
        failed = 0

        for name, path in SFX_REGISTRY.items():
            sound = self.loader.load_sound(path)
            if sound is not None:
                self._sfx_cache[name] = sound
                loaded += 1
            else:
                failed += 1

        print(
            f"[AudioManager] Preloaded {loaded} SFX ({failed} missing/failed)")

    def _get_sfx(self, name: str) -> Optional[Any]:
        """
        Get a sound effect by name, loading if not cached.

        Args:
            name: SFX event name (key in SFX_REGISTRY)

        Returns:
            pygame.mixer.Sound object or None
        """
        # Check cache first
        if name in self._sfx_cache:
            return self._sfx_cache[name]

        # Try to load on-demand
        if name in SFX_REGISTRY and self.loader:
            sound = self.loader.load_sound(SFX_REGISTRY[name])
            if sound is not None:
                self._sfx_cache[name] = sound
                return sound

        return None

    # =========================================================================
    # MUSIC PLAYBACK
    # =========================================================================

    def play_music(self, state_key: str, fade_ms: int = DEFAULT_FADE_OUT_MS, force_restart: bool = False):
        """
        Play music for a specific game state.

        Handles:
        - Seamless continuity if same state is already playing
        - Fade transitions between different states
        - Random track selection from playlist

        Args:
            state_key: Game state key (e.g., 'MENU', 'GAMEPLAY', 'QUIZ')
            fade_ms: Fade out duration in milliseconds
            force_restart: If True, restart even if same state
        """
        if not self._enabled:
            return

        state_key = state_key.upper()

        # Check for continuity - don't restart if same state is already playing
        if not force_restart and state_key == self._current_state and self._is_music_playing:
            # Same state, music already playing - do nothing (seamless)
            return

        # If a fade is in progress, queue this state change
        if self._fade_in_progress:
            self._pending_state = state_key
            return

        # Get playlist for this state
        if state_key not in MUSIC_PLAYLISTS:
            print(f"[AudioManager] Unknown music state: {state_key}")
            return

        playlist = MUSIC_PLAYLISTS[state_key]
        if not playlist:
            print(f"[AudioManager] Empty playlist for state: {state_key}")
            return

        # Select a random track (avoid repeating the same track if possible)
        if len(playlist) > 1 and self._current_track in playlist:
            available = [t for t in playlist if t != self._current_track]
            new_track = random.choice(available)
        else:
            new_track = random.choice(playlist)

        # Start transition
        self._transition_to_track(state_key, new_track, fade_ms)

    def _transition_to_track(self, state_key: str, track_path: str, fade_ms: int):
        """
        Handle the transition to a new track with fading.

        Args:
            state_key: New game state
            track_path: Path to the new track
            fade_ms: Fade duration
        """
        if not self._enabled or not self.loader:
            return

        try:
            # Get absolute path for streaming
            full_path = self.loader.get_music_path(track_path)

            if full_path is None:
                print(f"[AudioManager] Music track not found: {track_path}")
                # Try next track in playlist
                playlist = MUSIC_PLAYLISTS.get(state_key, [])
                for alt_track in playlist:
                    if alt_track != track_path:
                        alt_path = self.loader.get_music_path(alt_track)
                        if alt_path:
                            full_path = alt_path
                            track_path = alt_track
                            break

                if full_path is None:
                    return

            # If music is currently playing, fade out first
            if self._is_music_playing and fade_ms > 0:
                self._fade_in_progress = True
                pygame.mixer.music.fadeout(fade_ms)

                # Schedule the new track to start after fade
                # Using a simple approach - the update() method will handle this
                self._pending_state = state_key
                self._pending_track = track_path
                self._pending_path = full_path
                self._fade_start_time = time.time()
                self._fade_duration = fade_ms / 1000.0
            else:
                # No current music, start immediately
                self._start_track(state_key, track_path, full_path, fade_ms)

        except Exception as e:
            print(f"[AudioManager] Error transitioning to track: {e}")

    def _start_track(self, state_key: str, track_path: str, full_path: str, fade_in_ms: int = DEFAULT_FADE_IN_MS):
        """
        Start playing a music track.

        Args:
            state_key: Game state
            track_path: Relative path (for tracking)
            full_path: Absolute path for loading
            fade_in_ms: Fade in duration
        """
        if not self._enabled:
            return

        try:
            pygame.mixer.music.load(full_path)

            # Calculate effective volume
            effective_volume = self._get_effective_music_volume()
            pygame.mixer.music.set_volume(effective_volume)

            # Start with fade in
            if fade_in_ms > 0:
                # -1 = loop forever
                pygame.mixer.music.play(-1, fade_ms=fade_in_ms)
            else:
                pygame.mixer.music.play(-1)

            self._current_state = state_key
            self._current_track = track_path
            self._is_music_playing = True
            self._fade_in_progress = False

            print(
                f"[AudioManager] Now playing: {track_path} (state: {state_key})")

        except Exception as e:
            print(f"[AudioManager] Failed to play music: {e}")
            self._is_music_playing = False

    def stop_music(self, fade_ms: int = DEFAULT_FADE_OUT_MS):
        """
        Stop currently playing music.

        Args:
            fade_ms: Fade out duration in milliseconds (0 for immediate stop)
        """
        if not self._enabled:
            return

        try:
            if fade_ms > 0:
                pygame.mixer.music.fadeout(fade_ms)
            else:
                pygame.mixer.music.stop()

            self._is_music_playing = False
            self._current_state = None
            self._current_track = None

        except Exception as e:
            print(f"[AudioManager] Error stopping music: {e}")

    def pause_music(self):
        """Pause currently playing music."""
        if self._enabled and self._is_music_playing:
            pygame.mixer.music.pause()

    def resume_music(self):
        """Resume paused music."""
        if self._enabled and self._is_music_playing:
            pygame.mixer.music.unpause()

    def update(self, dt: float = 0.0):
        """
        Update audio manager state. Call this each frame.

        Handles:
        - Fade transition completion
        - Queued state changes

        Args:
            dt: Delta time in seconds (optional)
        """
        if not self._enabled:
            return

        # Check if fade out completed and we have a pending track
        if self._fade_in_progress and hasattr(self, '_pending_path'):
            # Check if fade is complete
            if hasattr(self, '_fade_start_time'):
                elapsed = time.time() - self._fade_start_time
                if elapsed >= self._fade_duration:
                    # Fade complete, start new track
                    self._start_track(
                        self._pending_state,
                        self._pending_track,
                        self._pending_path,
                        DEFAULT_FADE_IN_MS
                    )
                    # Clean up pending attributes
                    delattr(self, '_pending_path')
                    delattr(self, '_pending_track')
                    delattr(self, '_fade_start_time')
                    delattr(self, '_fade_duration')
                    self._pending_state = None

    # =========================================================================
    # SOUND EFFECTS PLAYBACK
    # =========================================================================

    def play_sfx(self, name: str, volume_scale: float = 1.0, loops: int = 0) -> Optional[Any]:
        """
        Play a sound effect by name.

        Args:
            name: SFX event name (e.g., 'click', 'explosion')
            volume_scale: Additional volume multiplier (0.0 to 1.0)
            loops: Number of times to loop (-1 = infinite, 0 = play once)

        Returns:
            pygame.mixer.Channel object if playing, None otherwise
        """
        if not self._enabled:
            return None

        sound = self._get_sfx(name)
        if sound is None:
            # Don't spam console for missing sounds during gameplay
            return None

        try:
            # Calculate effective volume
            effective_volume = self._get_effective_sfx_volume() * volume_scale
            sound.set_volume(effective_volume)

            # Play the sound
            channel = sound.play(loops=loops)

            return channel

        except Exception as e:
            print(f"[AudioManager] Error playing SFX '{name}': {e}")
            return None

    def play_sfx_looping(self, name: str, volume_scale: float = 1.0) -> bool:
        """
        Start playing a looping sound effect (e.g., thruster).

        The sound will continue until stop_sfx_looping() is called.

        Args:
            name: SFX event name
            volume_scale: Volume multiplier

        Returns:
            True if started successfully
        """
        if not self._enabled:
            return False

        # Don't start if already looping
        if name in self._looping_sounds:
            return True

        sound = self._get_sfx(name)
        if sound is None:
            return False

        try:
            effective_volume = self._get_effective_sfx_volume() * volume_scale
            sound.set_volume(effective_volume)
            channel = sound.play(loops=-1)

            if channel:
                self._looping_sounds[name] = {
                    'sound': sound,
                    'channel': channel,
                    'volume_scale': volume_scale
                }
                return True

        except Exception as e:
            print(f"[AudioManager] Error starting looping SFX '{name}': {e}")

        return False

    def stop_sfx_looping(self, name: str, fade_ms: int = 100):
        """
        Stop a looping sound effect.

        Args:
            name: SFX event name
            fade_ms: Fade out duration
        """
        if name not in self._looping_sounds:
            return

        try:
            info = self._looping_sounds[name]
            channel = info.get('channel')

            if channel and channel.get_busy():
                if fade_ms > 0:
                    channel.fadeout(fade_ms)
                else:
                    channel.stop()

            del self._looping_sounds[name]

        except Exception as e:
            print(f"[AudioManager] Error stopping looping SFX '{name}': {e}")

    def stop_all_sfx(self):
        """Stop all currently playing sound effects."""
        if not self._enabled:
            return

        try:
            # Stop all looping sounds
            for name in list(self._looping_sounds.keys()):
                self.stop_sfx_looping(name, fade_ms=0)

            # Stop all channels
            pygame.mixer.stop()

        except Exception as e:
            print(f"[AudioManager] Error stopping all SFX: {e}")

    # =========================================================================
    # VOLUME CONTROL
    # =========================================================================

    def _get_effective_music_volume(self) -> float:
        """Calculate effective music volume (master * music)."""
        if self._muted:
            return 0.0
        return self._master_volume * self._music_volume

    def _get_effective_sfx_volume(self) -> float:
        """Calculate effective SFX volume (master * sfx)."""
        if self._muted:
            return 0.0
        return self._master_volume * self._sfx_volume

    def update_volume(self, category: str, value: float):
        """
        Update volume for a specific category.

        Args:
            category: One of 'master', 'music', 'sfx'
            value: Volume level (0.0 to 1.0)
        """
        value = max(0.0, min(1.0, value))  # Clamp to valid range

        if category == 'master':
            self._master_volume = value
        elif category == 'music':
            self._music_volume = value
        elif category == 'sfx':
            self._sfx_volume = value
        else:
            print(f"[AudioManager] Unknown volume category: {category}")
            return

        # Apply changes immediately
        self._apply_volume_changes()

    def _apply_volume_changes(self):
        """Apply current volume settings to all audio."""
        if not self._enabled:
            return

        # Update music volume
        try:
            effective_music = self._get_effective_music_volume()
            pygame.mixer.music.set_volume(effective_music)
        except Exception:
            pass

        # Update looping SFX volumes
        for name, info in self._looping_sounds.items():
            try:
                sound = info.get('sound')
                volume_scale = info.get('volume_scale', 1.0)
                if sound:
                    effective_sfx = self._get_effective_sfx_volume() * volume_scale
                    sound.set_volume(effective_sfx)
            except Exception:
                pass

    def get_volume(self, category: str) -> float:
        """
        Get current volume for a category.

        Args:
            category: One of 'master', 'music', 'sfx'

        Returns:
            Volume level (0.0 to 1.0)
        """
        if category == 'master':
            return self._master_volume
        elif category == 'music':
            return self._music_volume
        elif category == 'sfx':
            return self._sfx_volume
        return 0.0

    def toggle_mute(self) -> bool:
        """
        Toggle mute state.

        Returns:
            True if now muted, False if unmuted
        """
        if self._muted:
            # Unmute - restore previous master volume
            self._muted = False
            self._master_volume = self._pre_mute_master
        else:
            # Mute - save current master volume
            self._pre_mute_master = self._master_volume
            self._muted = True

        self._apply_volume_changes()
        return self._muted

    def set_muted(self, muted: bool):
        """
        Set mute state directly.

        Args:
            muted: True to mute, False to unmute
        """
        if muted and not self._muted:
            self._pre_mute_master = self._master_volume
            self._muted = True
        elif not muted and self._muted:
            self._muted = False
            self._master_volume = self._pre_mute_master

        self._apply_volume_changes()

    @property
    def is_muted(self) -> bool:
        """Check if audio is muted."""
        return self._muted

    @property
    def master_volume(self) -> float:
        """Get master volume."""
        return self._master_volume

    @property
    def music_volume(self) -> float:
        """Get music volume."""
        return self._music_volume

    @property
    def sfx_volume(self) -> float:
        """Get SFX volume."""
        return self._sfx_volume

    # =========================================================================
    # STATE QUERIES
    # =========================================================================

    @property
    def current_music_state(self) -> Optional[str]:
        """Get the current music state key."""
        return self._current_state

    @property
    def is_music_playing(self) -> bool:
        """Check if music is currently playing."""
        if not self._enabled:
            return False
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

    @property
    def is_enabled(self) -> bool:
        """Check if audio system is enabled."""
        return self._enabled

    def get_status(self) -> Dict[str, Any]:
        """
        Get current audio system status.

        Returns:
            Dictionary with status information
        """
        return {
            'enabled': self._enabled,
            'initialized': self._initialized,
            'muted': self._muted,
            'master_volume': self._master_volume,
            'music_volume': self._music_volume,
            'sfx_volume': self._sfx_volume,
            'current_state': self._current_state,
            'current_track': self._current_track,
            'is_music_playing': self.is_music_playing,
            'cached_sfx_count': len(self._sfx_cache),
            'looping_sfx_count': len(self._looping_sounds),
        }

    # =========================================================================
    # CLEANUP
    # =========================================================================

    def cleanup(self):
        """Clean up audio resources. Call before quitting."""
        if not self._enabled:
            return

        try:
            self.stop_all_sfx()
            self.stop_music(fade_ms=0)
            self._sfx_cache.clear()
            self._looping_sounds.clear()
            print("[AudioManager] Cleanup complete")
        except Exception as e:
            print(f"[AudioManager] Error during cleanup: {e}")


# =============================================================================
# SINGLETON PATTERN
# =============================================================================

_audio_manager_instance: Optional[AudioManager] = None


def get_audio_manager() -> AudioManager:
    """
    Get the global AudioManager singleton.

    Creates the instance on first call.

    Returns:
        AudioManager instance
    """
    global _audio_manager_instance
    if _audio_manager_instance is None:
        _audio_manager_instance = AudioManager()
    return _audio_manager_instance


def init_audio_manager(resource_loader=None) -> AudioManager:
    """
    Initialize the global AudioManager singleton.

    Args:
        resource_loader: ResourceManager class/instance

    Returns:
        AudioManager instance
    """
    global _audio_manager_instance
    _audio_manager_instance = AudioManager(resource_loader)
    return _audio_manager_instance
