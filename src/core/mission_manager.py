"""Mission Manager - Handles the randomized planet visit order and progress tracking.
"""
import random
import time


class MissionManager:
    """
    Manages the game's mission system:
    - Generates randomized planet visit order at game start
    - Tracks current mission target
    - Marks missions as completed
    - Manages trophy collection
    """
    _instance = None

    # All visitable celestial bodies
    ALL_PLANETS = ["Mercury", "Venus", "Earth", "Mars",
                   "Jupiter", "Saturn", "Uranus", "Neptune", "Sun"]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MissionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.reset()

    def reset(self):
        """Reset mission state for a new game."""
        self.mission_order = []  # Randomized list of planets to visit
        self.current_index = 0   # Current mission index
        self.completed_missions = set()  # Set of completed planet names
        self.trophies = {}  # Dict of planet_name -> trophy_earned
        self.game_started = False
        self.game_completed = False

    def start_new_game(self):
        """Initialize a new game with randomized planet order."""
        self.reset()
        # Seed random with current time for true randomization
        random.seed(time.time())
        # Create randomized order of all planets
        self.mission_order = self.ALL_PLANETS.copy()
        random.shuffle(self.mission_order)
        self.game_started = True
        self.game_completed = False
        print(
            f"[MissionManager] New game started! Mission order: {self.mission_order}")
        return self.mission_order

    def get_current_target(self):
        """Get the current mission target planet name."""
        if not self.game_started or self.game_completed:
            return None
        if self.current_index >= len(self.mission_order):
            return None
        return self.mission_order[self.current_index]

    def get_current_mission_number(self):
        """Get the current mission number (1-indexed for display)."""
        return self.current_index + 1

    def get_total_missions(self):
        """Get total number of missions."""
        return len(self.mission_order)

    def is_target_planet(self, planet_name):
        """Check if the given planet is the current mission target."""
        return planet_name == self.get_current_target()

    def complete_current_mission(self, trophy_type="default"):
        """
        Mark the current mission as completed and award trophy.
        Returns True if this was the final mission.
        """
        current_target = self.get_current_target()
        if current_target is None:
            return False

        self.completed_missions.add(current_target)
        self.trophies[current_target] = trophy_type
        print(
            f"[MissionManager] Mission completed: {current_target} - Trophy: {trophy_type}")

        # Move to next mission
        self.current_index += 1

        # Check if all missions complete
        if self.current_index >= len(self.mission_order):
            self.game_completed = True
            print("[MissionManager] ALL MISSIONS COMPLETE! Game won!")
            return True

        print(f"[MissionManager] Next target: {self.get_current_target()}")
        return False

    def is_mission_completed(self, planet_name):
        """Check if a specific planet's mission has been completed."""
        return planet_name in self.completed_missions

    def get_progress_percentage(self):
        """Get completion percentage."""
        if not self.mission_order:
            return 0
        return (len(self.completed_missions) / len(self.mission_order)) * 100

    def get_completed_count(self):
        """Get number of completed missions."""
        return len(self.completed_missions)

    def get_all_trophies(self):
        """Get dict of all earned trophies."""
        return self.trophies.copy()

    def is_game_complete(self):
        """Check if all missions are completed."""
        return self.game_completed


# Trophy types for each planet (unique characteristic)
PLANET_TROPHIES = {
    "Mercury": "winged_helmet",      # Messenger god
    "Venus": "heart_gem",            # Goddess of love
    "Earth": "blue_marble",          # Our blue planet
    "Mars": "red_crystal",           # The red planet
    "Jupiter": "lightning_bolt",     # King of gods
    "Saturn": "golden_ring",         # Famous rings
    "Uranus": "ice_diamond",         # Ice giant
    "Neptune": "trident",            # God of the sea
    "Sun": "solar_crown"             # The star
}


def get_trophy_for_planet(planet_name):
    """Get the trophy type for a specific planet."""
    return PLANET_TROPHIES.get(planet_name, "star_medal")
