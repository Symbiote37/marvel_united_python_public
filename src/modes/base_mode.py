import random
import json
import os
from src.entities.locations import Location
from src.entities.threats import Threat
from src.utils.helpers import Col

class BaseMode:
    """The default 'Business as Usual' game mode handler."""
    def __init__(self, engine):
        self.engine = engine
        # We add a dummy state to prevent 'BaseMode has no attribute state' errors
        from types import SimpleNamespace
        self.state = SimpleNamespace(stage_index=0)

    def perform_setup(self):
        pass

    def execute_villain_turn(self, forced_extra_card=False):
        from src.systems.villain_system import VillainSystem
        VillainSystem.execute_turn(self.engine, forced_extra_card)

    def render_center_dashboard(self):
        return None

    def get_location_presence(self, loc_idx):
        if self.engine.villain and loc_idx == self.engine.villain.location_index:
            return Col.wrap("V", Col.RED)
        return ""

    def is_eot_blocked(self, loc_idx):
        loc = self.engine.locations[loc_idx]
        return loc.threat and not loc.threat.cleared

    def get_turn_interval(self):
        m = self.engine.missions
        # 🧪 PACING LOGIC: 3 hero turns normally, 2 if under pressure (2+ threats cleared)
        if m.get("threats", 0) >= 2:
            return 2

        # Original completed check for backward compatibility with other mission types
        completed = sum(1 for k in ["civilians", "thugs", "threats"] if m.get(k, 0) >= m.get(f"{k}_max", 1))
        return 2 if completed >= 1 else 3

    # --- 🔌 CAMPAIGN INTERFACE HOOKS (STUBS) ---

    def try_intercept_threat_token(self):
        """Standard modes never intercept tokens. Returns False to proceed to mission."""
        return False

    def get_custom_commands(self, engine, hero, pool):
        """Standard modes have no extra menu options."""
        return []

    def handle_custom_command(self, engine, hero, cmd, pool):
        """Standard modes don't process custom inputs."""
        return False

    def apply_passives(self, engine, hero, pool):
        """Standard modes have no campaign arsenal passives."""
        pass
