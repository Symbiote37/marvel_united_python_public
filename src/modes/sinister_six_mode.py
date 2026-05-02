import json
import random
from src.modes.base_mode import BaseMode
from src.utils.helpers import Col
from src.entities.threats import Threat
from src.entities.actors import Villain # 🛡️ CRITICAL: Restored Actor Factory Import

class SinisterSixMode(BaseMode):
    """Modular logic for the Sinister Six team-boss fight."""
    
    def perform_setup(self):
        super().perform_setup()

        roster_names = ["kraven", "sandman", "electro", "vulture", "doctor_octopus", "mysterio"]
        initials = ["K", "S", "E", "V", "D", "M"]
        
        # 🛡️ THE FIX: Initialize BOTH the Data Roster and the Physical Actors List
        self.sinister_six_roster = {}
        self.engine.sinister_six_roster = self.sinister_six_roster
        self.engine.villains = [] 
        
        board_offset = random.randint(0, 5)
        start_positions = [0, 0, 1, 1, 5, 5]
        random.shuffle(start_positions)
        
        # Grab target HP from the placeholder villain created by the generic setup
        target_hp = getattr(self.engine.villain, 'hp', len(self.engine.heroes))

        with open("data/threats/sinister_six_threats.json", 'r') as f:
            threat_data = json.load(f)
            
        for i in range(6):
            v_idx = (i + board_offset) % 6
            v_id = roster_names[v_idx]
            
            # 1. Setup the Logic Roster Data
            self.sinister_six_roster[v_id] = {
                "loc": start_positions[v_idx],
                "initials": initials[v_idx],
                "defeated": False,
                "internal_id": v_id,
                "hp": target_hp,
                "max_hp": target_hp,
                "weak_spot_cleared": False
            }

            # 2. 🛡️ THE RESTORATION: Setup the Physical UI Actors for the HUD
            new_v = Villain({
                "name": v_id.replace('_', ' ').title(),
                "internal_id": v_id,
                "hp": target_hp
            })
            new_v.location_index = start_positions[v_idx]
            self.engine.villains.append(new_v)

            # 3. Setup the Weak Spot Threats
            t_data = next((t for t in threat_data if t["id_internal"] == f"weak_spot_{v_id}"), None)
            if t_data:
                self.engine.locations[i].threat = Threat(t_data)
                self.engine.locations[i].threat.villain_owner = v_id

        # 4. Point the "master" villain reference to the first actor for deck-drawing
        self.engine.villain = self.engine.villains[0]

        for h in self.engine.heroes:
            h.location_index = 3

        self.engine.log.append(Col.wrap(" 🚩 SINISTER SIX MODE: The hunt begins! ", Col.YLW))

    def get_turn_interval(self):
        return 2

    def execute_villain_turn(self, forced_extra_card=False):
        """OVERRIDE: Custom Sinister Six turn rotation logic to prevent base mode takeover."""
        from src.systems.villain_system import VillainSystem
        from src.logic.registry import get_villain_logic
        from src.systems.turn_system import TurnSystem
        from src.systems.token_system import TokenSystem

        TurnSystem.reset_boss_defenses(self.engine)
        plan = self.engine.villain.draw_plan()
        if not plan:
            self.engine.game_over = True
            self.engine.victory_status = "VILLAIN_WINS"
            self.engine.loss_reason = "TIME EXPIRED: The Six completed their Master Plan!"
            return

        self.engine.storyline.add(plan)
        self.engine.turn_count += 1
        self.engine.log = []

        order = plan.get("villain_order", [])
        is_all = plan.get("special_id") == "return_of_sinister_six"
        
        # Identify which villains act this turn
        active_names = [v for v in order if not self.sinister_six_roster[v]["defeated"]]
        if not is_all: 
            active_names = active_names[:2]

        v_logic = get_villain_logic("sinister_six")

        for i, v_name in enumerate(active_names):
            v_data = self.sinister_six_roster[v_name]
            display_name = v_name.replace('_', ' ').title()
            
            # Update logical position
            v_data["loc"] = (v_data["loc"] + plan.get("move", 0)) % 6
            loc = self.engine.locations[v_data["loc"]]
            
            # 🛡️ SYNC HOOK: Update Physical Actor Position for HUD/Map rendering
            for actor in self.engine.villains:
                if actor.internal_id == v_name:
                    actor.location_index = v_data["loc"]

            self.engine.log.append(Col.wrap(f" 🏃 {display_name} stalks into {loc.name}. ", Col.CYAN))
            
            if plan.get("bam"):
                v_logic.on_bam(self.engine, v_data)
            
            tracker = set()
            if i == 0 or is_all:
                TokenSystem.add_token(self.engine, v_data["loc"], "thugs", tracker)
            if i == 1 or is_all:
                TokenSystem.add_token(self.engine, v_data["loc"], "civilians", tracker)
            
            VillainSystem.process_event_queue(self.engine)
            if getattr(self.engine, 'game_over', False): 
                break

    def render_center_dashboard(self):
        roster = self.engine.sinister_six_roster
        v_names = list(roster.keys())
        rows = []
        for start_idx in [0, 3]:
            parts = []
            for j in range(3):
                name = v_names[start_idx + j]
                data = roster[name]
                if data["defeated"]:
                    status = Col.wrap("✅ ", Col.GRN)
                elif data.get("weak_spot_cleared", False):
                    status = Col.wrap(f"HP:{data['hp']}/{data['max_hp']}", Col.RED + Col.BOLD)
                else:
                    status = Col.wrap("🛡️ ", Col.CYAN)
                parts.append(f"{data['initials']}:{status}")
            
            prefix = " ROSTER: " if start_idx == 0 else "         "
            rows.append(f"{prefix}| {' | '.join(parts)} ")
            
        return rows

    def get_location_presence(self, loc_idx):
        icons = ""
        for name, data in self.engine.sinister_six_roster.items():
            if data["loc"] == loc_idx and not data["defeated"]:
                icons += Col.wrap(data["initials"], Col.RED + Col.BOLD)
        return icons

    def is_eot_blocked(self, loc_idx):
        return any(v["loc"] == loc_idx and not v["defeated"] 
                  for v in self.engine.sinister_six_roster.values())
