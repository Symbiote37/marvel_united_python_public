import os
import json
import random
import sys

from src.core.storyline import Storyline
from src.entities.actors import Hero, Villain
from src.entities.locations import Location
from src.entities.threats import Threat
from src.ui.board import BoardRenderer
from src.logic.registry import get_villain_logic 
from src.utils.helpers import wait_for_user, Col, ICON
from src.systems.event_system import EventSystem
from src.systems.token_system import TokenSystem
from src.systems.action_system import ActionSystem
from src.systems.turn_system import TurnSystem
from src.systems.hero_system import HeroSystem
from src.systems.villain_system import VillainSystem

class GameEngine:
    def __init__(self, location_file="data/locations/core_locations.json", controller=None):
        self.heroes = []
        self.villain = None
        self.locations = []
        self.storyline = Storyline()
        self.turn_count = 0
        self.log = []
        self.active_pool = None
        self.game_over = False
        self.victory_status = None
        self.loss_reason = ""
        
        self.queued_events = [] 
        self.forced_extra_cards = 0 
        self.current_hero_index = 0
        self.active_challenges = []
        
        self.missions = {
            "civilians": 0, "civilians_max": 9,
            "thugs": 0, "thugs_max": 9,
            "threats": 0, "threats_max": 4
        }
        self.campaign_manager = None
        self.location_file = location_file
        
        # THE UI ADAPTER PORT: Default to Human, but allow bots to be plugged in
        if controller is None:
            from src.ui.controllers import HumanController
            self.ui = HumanController()
        else:
            self.ui = controller

    def _load_from_folder(self, path, class_type, count=1, file_subset=None):
        if file_subset is not None:
            files = sorted(file_subset)
        else:
            files = sorted([f for f in os.listdir(path) if f.endswith('.json')])
            
        display_names = []
        for f_name in files:
            with open(os.path.join(path, f_name), 'r') as f:
                temp_data = json.load(f)
                display_names.append(temp_data.get("name", f_name.replace('.json', '')))

        selected = []
        while len(selected) < count:
            print(f"\nSelect {count} from {path}:")
            for i, name in enumerate(display_names, 1):
                print(f"{i}. {name}")
            
            raw_input = self.ui.ask_raw(f"Enter {count} index(es) separated by commas: ").strip()
            if not raw_input: continue

            try:
                choices = [int(c.strip()) - 1 for c in raw_input.split(',') if c.strip()]
                if len(set(choices)) != count or any(c < 0 or c >= len(files) for c in choices):
                    continue

                for c in choices:
                    with open(os.path.join(path, files[c]), 'r') as f:
                        data = json.load(f)
                        if class_type == Villain:
                            selected.append(data)
                        else:
                            selected.append(class_type(data))
            except (ValueError, IndexError):
                continue
        
        return selected

    def setup_campaign_mission(self, villain_id, hero_ids, is_solo=False, active_challenges=None, location_set=None):
        """Bypasses the manual terminal prompts for Campaign Mode and explicitly sets mode flags."""
        self.selected_villain = villain_id
        self.selected_heroes = hero_ids
        self.is_solo_mode = is_solo 
        self.active_challenges = active_challenges or []
        
        # 🗺️ THE OVERRIDE: Lock in the specific location set if the campaign node demands it
        if location_set:
            self.location_file = f"data/locations/{location_set}"
        else:
            self.location_file = "data/locations/core_locations.json"
        
    def _reset_state(self):
        self.storyline.cards = []
        self.turn_count = 0; self.log = []; self.active_pool = None
        self.match_stats = {}
        self.game_over = False; self.victory_status = None; self.loss_reason = ""
        self.missions = {"civilians": 0, "thugs": 0, "threats": 0, 
                         "civilians_max": 9, "thugs_max": 9, "threats_max": 4}

    def _load_entities(self):
        if not hasattr(self, 'selected_heroes'):
            print(Col.wrap(" ⚠️ CRITICAL: Engine launched without data.", Col.RED))
            sys.exit(1)

        from src.systems.challenge_system import ChallengeSystem
        
        self.heroes = []
        for h in self.selected_heroes:
            h_data = json.load(open(f"data/heroes/{h}.json", 'r'))
            
            # Challenge System Deck Filter
            h_data['deck'] = ChallengeSystem.filter_hero_deck(h_data['deck'], getattr(self, 'active_challenges', []))
            self.heroes.append(Hero(h_data))

        v_data = json.load(open(f"data/villains/{self.selected_villain}.json", 'r'))
        return v_data

    def _load_locations(self):
        # Purely trusts the engine's location_file attribute (set by Menu or Campaign)
        loc_path = getattr(self, 'location_file', "data/locations/core_locations.json")

        try:
            with open(loc_path, 'r', encoding='utf-8') as f:
                loc_data = json.load(f)
        except FileNotFoundError:
            import time
            print(Col.wrap(f"\n [!] FILE NOT FOUND: {loc_path}", Col.RED + Col.BOLD))
            print(Col.wrap(" Falling back to Core Box in 4 seconds...", Col.YLW))
            time.sleep(4)
            with open("data/locations/core_locations.json", 'r', encoding='utf-8') as f:
                loc_data = json.load(f)

        random.shuffle(loc_data)
        self.locations = [Location(d) for d in loc_data[:6]]
        
    def _load_threats(self):
        threat_path = f"data/threats/{self.villain.internal_id}_threats.json"
        try:
            with open(threat_path, 'r') as f:
                t_data = json.load(f)
            random.shuffle(t_data)
            for i, loc in enumerate(self.locations):
                if i < len(t_data): loc.threat = Threat(t_data[i])
        except FileNotFoundError:
            self.log.append(Col.wrap(f" ⚠️ NOTICE: No threat deck found for {self.villain.internal_id}.", Col.DARK_GRAY))

    def _set_initial_positions(self):
        self.villain.location_index = 0
        for h in self.heroes: 
            h.location_index = 3 

    def _initialize_mode(self):
        v_id = self.villain.internal_id
        
        # 🚨 RESTORED & MERGED: S.H.I.E.L.D. Mode takes priority, followed by Villain modes
        if getattr(self, 'is_solo_mode', False):
            from src.modes.shield_mode import ShieldMode
            self.mode_handler = ShieldMode(self)
        elif v_id == "sinister_six":
            from src.modes.sinister_six_mode import SinisterSixMode
            self.mode_handler = SinisterSixMode(self)
        elif v_id == "dormammu":
            from src.modes.dormammu_mode import DormammuMode
            self.mode_handler = DormammuMode(self)
        elif v_id == "infinity_gauntlet":
            from src.modes.infinity_gauntlet_mode import InfinityGauntletMode
            self.mode_handler = InfinityGauntletMode(self)
        else:
            from src.modes.base_mode import BaseMode
            self.mode_handler = BaseMode(self)

        self.mode_handler.perform_setup()

    def setup_game(self):
        self._reset_state()
        v_data = self._load_entities()
        
        self.villain = Villain(v_data, hero_count=len(self.heroes))
        self.villain_logic = get_villain_logic(self.villain.internal_id)
        
        from src.systems.special_abilities import SpecialAbilitySystem
        SpecialAbilitySystem.initialize_interceptors(self)
        
        self._load_locations()
        self._load_threats()
        self._set_initial_positions()
        self._initialize_mode()
        
        if hasattr(self.villain_logic, 'perform_setup'):
            self.villain_logic.perform_setup(self, self.villain)
            
        from src.systems.challenge_system import ChallengeSystem
        ChallengeSystem.apply_engine_modifiers(self, getattr(self, 'active_challenges', []))

    def hot_swap_villain(self, new_villain_id):
        """Purges the defeated villain and loads the next campaign boss mid-game."""
        from src.entities.actors import Villain
        from src.logic.registry import get_villain_logic
        from src.entities.threats import Threat
        import json
        import random
        
        self.selected_villain = new_villain_id 
        self.boss_fallen_announced = False 
        
        # 1. Load and Swap the Entity & Logic
        v_path = f"data/villains/{new_villain_id}.json"
        with open(v_path, 'r') as f:
            v_data = json.load(f)
            
        self.villain = Villain(v_data, hero_count=len(self.heroes))
        self.villain_logic = get_villain_logic(self.villain.internal_id)
        self.villain.location_index = 0
        
        # 2. Reset Engine State
        self.active_pool = None
        self.log = [Col.wrap(f" 🚩 A NEW THREAT EMERGES: {self.villain.name.upper()}!", Col.YLW + Col.BOLD)]
        
        # 3. Swap Threats (Clear the old, load the new)
        threat_path = f"data/threats/{self.villain.internal_id}_threats.json"
        try:
            with open(threat_path, 'r') as f:
                threat_data = json.load(f)
            random.shuffle(threat_data)
            for i, loc in enumerate(self.locations):
                loc.threat = Threat(threat_data[i]) if i < len(threat_data) else None
        except FileNotFoundError:
            for loc in self.locations: loc.threat = None
            
        # 4. Trigger Setup Hooks for the new boss
        if hasattr(self.villain_logic, 'perform_setup'):
            self.villain_logic.perform_setup(self, self.villain)
            
    def create_threat(self, threat_id):
        v_id = self.villain.internal_id 
        threat_path = f"data/threats/{v_id}_threats.json"
        try:
            with open(threat_path, 'r') as f:
                threat_data_list = json.load(f)
            for t_data in threat_data_list:
                if t_data.get("id") == threat_id or t_data.get("id_internal") == threat_id:
                    return Threat(t_data)
        except Exception as e:
            self.log.append(Col.wrap(f" ⚠️ ERROR loading threat data: {e}", Col.YLW))
        return None

    def get_game_state(self, active_hero=None):
        return {
            "engine": self,
            "locations": self.locations,
            "villain": self.villain,
            "heroes": self.heroes,
            "missions": self.missions,
            "turn_counter": self.turn_count,
            "log": self.log,
            "hero_queue": [active_hero] if active_hero else self.heroes,
            "active_pool": getattr(self, 'active_pool', None),
            "villain_logic": getattr(self, 'villain_logic', None),
            "storyline": self.storyline
        }

    def _check_game_status(self):
        # 🚨 CHALLENGE HOOK: Plan B Alternate Win Condition
        from src.systems.challenge_system import ChallengeSystem
        if ChallengeSystem.PLAN_B in getattr(self, 'active_challenges', []):
            if (self.missions["civilians"] >= self.missions["civilians_max"] and
                self.missions["thugs"] >= self.missions["thugs_max"] and
                self.missions["threats"] >= self.missions["threats_max"]):
                
                self.game_over = True
                self.victory_status = "HEROES_WIN"
                self.victory_reason = "PLAN B EXECUTED: All critical missions achieved!"
                return
                
        # 🔌 VILLAIN HOOK: Custom Win/Loss Conditions
        if hasattr(self.villain_logic, 'check_custom_game_status'):
            if self.villain_logic.check_custom_game_status(self):
                return # The villain logic modified the state and triggered a game over

        # 🔌 NEW: MODE HOOK: Custom Win/Loss Conditions (e.g., SHIELD Mode KO rule)
        if hasattr(self.mode_handler, 'check_custom_game_status'):
            if self.mode_handler.check_custom_game_status():
                return 

        # 🛑 STANDARD DEFEAT: Plot Complete
        if self.villain.plot_max > 0 and self.villain.plot_value >= self.villain.plot_max:
            # 🔌 VILLAIN HOOK: Plot Override (e.g., Venom uses plot for something else)
            if getattr(self.villain_logic, 'plot_ends_game', True):
                self.game_over = True
                self.victory_status = "VILLAIN_WINS"
                self.loss_reason = f"PLOT COMPLETE: {self.villain.plot_name} reached {self.villain.plot_max}!"
                return

        active_heroes = [h for h in self.heroes if not getattr(h, 'is_eliminated', False)]
        if not active_heroes:
            self.game_over = True
            self.victory_status = "VILLAIN_WINS"
            self.loss_reason = "TEAM ELIMINATED: No heroes remaining."
            return

        for h in active_heroes:
            # HERO IS OUT OF CARDS (Hand AND Deck)
            if len(h.hand) == 0 and len(h.deck) == 0:
                
                # 🔌 MODE HOOK: Intercept Hero Elimination (e.g., Thanos bench swap)
                if hasattr(self.mode_handler, 'handle_hero_eliminated'):
                    if self.mode_handler.handle_hero_eliminated(self, h):
                        return # The mode intercepted the KO, the game continues!
                
                # STANDARD RULE: If anyone is out of cards, the match is lost.
                self.game_over = True
                self.victory_status = "VILLAIN_WINS"
                self.loss_reason = f"HERO ELIMINATED: {h.name} has no cards left."
                return
            
            # STANDARD KO: 0 cards in hand, but has a deck. 
            if len(h.hand) == 0 and not getattr(h, 'is_ko', False):
                from src.systems.damage_system import DamageSystem
                DamageSystem.trigger_ko(self, h)

    def _get_neutral_team_hud(self):
        """Generates a neutral S.H.I.E.L.D. Team profile with color-synced initials."""
        from src.entities.actors import Hero
        
        # 🎨 Color Sync: Match HUD initials to Hero colors
        h_colors = [Col.ORN, Col.C111, Col.GRN, Col.MAGENTA]
        initials = []
        for i, h in enumerate(self.heroes):
            color = h_colors[i % len(h_colors)]
            initials.append(Col.wrap(h.name[0].upper(), color))
        
        team_name = f"S.H.I.E.L.D. TEAM [{' '.join(initials)}]"
        
        team_hero = Hero({"internal_id": "team", "name": team_name, "deck": []})
        
        # Pull stats from the shared pool to keep HUD bars accurate
        team_hero.location_index = self.heroes[self.current_hero_index].location_index
        team_hero.deck = self.heroes[0].deck
        team_hero.hand = self.heroes[0].hand
        return team_hero

    def run_game_loop(self):
        self.setup_game()
        self.current_hero_index = 0
        
        # 🔌 INITIAL RENDER: Neutral start for S.H.I.E.L.D. protocol
        start_hero = self._get_neutral_team_hud() if getattr(self, 'is_solo_mode', False) else self.heroes[self.current_hero_index]
        BoardRenderer.render(self.get_game_state(start_hero))
        
        self.log.append(f" 🚩 MISSION START: {self.villain.name.upper()} is on the move!")
        
        turns_since_v = 99 

        while not self.game_over:
            # 🚨 THE AGGRESSIVE NEUTRAL SHIFT: Force Team HUD at the start of every cycle.
            # This intercepts Villain-triggered renders (like Spread Discord) before they can ghost a hero.
            if getattr(self, 'is_solo_mode', False):
                BoardRenderer.render(self.get_game_state(self._get_neutral_team_hud()))

            # ==========================================
            # VILLAIN PHASE
            # ==========================================
            if TurnSystem.should_villain_act(self, turns_since_v):
                # 🏎️ PRIORITY 1: Does the Villain have custom turn logic (e.g. Sinister Six)?
                if hasattr(self.villain_logic, 'execute_villain_turn'):
                    self.villain_logic.execute_villain_turn(self)
                # 🏎️ PRIORITY 2: Does the Game Mode have custom turn logic (e.g. SHIELD)?
                elif hasattr(self, 'mode_handler') and hasattr(self.mode_handler, 'execute_villain_turn'):
                    self.mode_handler.execute_villain_turn()
                # 🏎️ PRIORITY 3: Standard Villain Behavior
                else:
                    VillainSystem.execute_turn(self)
                
                self._check_game_status()
                if self.game_over:
                    if self.victory_status == "VILLAIN_WINS" and hasattr(self.mode_handler, 'handle_defeat'):
                        self.mode_handler.handle_defeat()
                        if not self.game_over:
                            turns_since_v = 99 
                            self.current_hero_index = 0
                            continue
                    if self.game_over: break
                    continue

                BoardRenderer.clear()
                # 🔌 RE-RENDER NEUTRAL: Wipe Villain phase artifacts
                display_hero = self._get_neutral_team_hud() if getattr(self, 'is_solo_mode', False) else self.heroes[self.current_hero_index]
                BoardRenderer.render(self.get_game_state(display_hero)) 
                
                # 🕒 NATIVE CLOCK: Auto-expire location-based auras at the end of the round
                from src.systems.status_system import StatusSystem
                for loc in self.locations:
                    StatusSystem.tick_all_statuses(loc)
                
                self.ui.acknowledge("\n ⚠️ VILLAIN PHASE COMPLETE. Press Enter to continue...")
                turns_since_v = 0

            # =================================
            # HERO PHASE
            # =================================
            if hasattr(self, 'mode_handler') and hasattr(self.mode_handler, 'execute_hero_turn'):
                # ShieldMode handles the switch from Team -> Specific Hero internally
                self.mode_handler.execute_hero_turn()
            else:
                active_hero = self.heroes[self.current_hero_index]
                HeroSystem.execute_turn(self, active_hero, self.current_hero_index)
            
            # --- VICTORY CHECK ---
            if hasattr(self.villain_logic, 'is_defeated'):
                villain_defeated = self.villain_logic.is_defeated(self)
            else:
                villain_defeated = getattr(self.villain, 'hp', 1) <= 0

            if villain_defeated:
                if hasattr(self.mode_handler, 'handle_victory'):
                    self.mode_handler.handle_victory()
                    if not self.game_over:
                        turns_since_v = 99 
                        self.current_hero_index = 0
                        continue
                else:
                    self.game_over = True
                    self.victory_status = "HEROES_WIN"
                if self.game_over: break
                continue 
            
            # --- DEFEAT CHECK ---
            self._check_game_status()
            if self.game_over:
                if self.victory_status == "VILLAIN_WINS" and hasattr(self.mode_handler, 'handle_defeat'):
                    self.mode_handler.handle_defeat()
                    if not self.game_over:
                        turns_since_v = 99 
                        self.current_hero_index = 0
                        continue
                if self.game_over: break
                continue

            turns_since_v += 1
            self.current_hero_index = TurnSystem.get_next_hero_index(self.current_hero_index, len(self.heroes), self)

        # --- END OF SIMULATION ---
        BoardRenderer.clear()
        end_hero = self._get_neutral_team_hud() if getattr(self, 'is_solo_mode', False) else None
        BoardRenderer.render(self.get_game_state(end_hero))

        if self.victory_status == "VILLAIN_WINS":
             print(Col.wrap(f"\n 💀 MISSION FAILED", Col.RED + Col.BOLD))
             print(Col.wrap(f" > {self.loss_reason}", Col.YLW))
             
             # 🛡️ THE DOG DOOR: Checks for custom JSON text, defaults to standard comic wail
             gloat = getattr(self.villain, 'flavor_text', {}).get("victory", "Fools! You cannot stop the Master Plan!")
             print(Col.wrap(f" 😈 {self.villain.name.upper()}: \"{gloat}\"", Col.RED))
             
        elif self.victory_status == "HEROES_WIN":
             reason = getattr(self, 'victory_reason', f"{self.villain.name.upper()} DEFEATED!")
             print(Col.wrap(f"\n 🎉 JUSTICE PREVAILS: {reason}", Col.GRN + Col.BOLD))
             
             # 🛡️ THE DOG DOOR: Checks for custom JSON text, defaults to standard comic wail
             defeat_wail = getattr(self.villain, 'flavor_text', {}).get("defeat", "Impossible! My plans are ruined!")
             print(Col.wrap(f" 💥 {self.villain.name.upper()}: \"{defeat_wail}\"", Col.GRN))
        
        # 🚨 THE UNIVERSAL HOOK: Trigger the standalone comic writer for ALL modes
        from src.ui.comic_writer import ComicWriter
        ComicWriter.display_issue_summary(self)
        
        self.ui.wait()

    def track_stat(self, hero, stat_name, amount=1):
        """Silently logs hero achievements for the MVP screen."""
        if not hero or getattr(hero, 'internal_id', 'team') == 'team': 
            return 
            
        h_id = hero.internal_id
        if getattr(self, 'match_stats', None) is None:
            self.match_stats = {}
            
        if h_id not in self.match_stats:
            # 🚨 Added "moves" to baseline, but the method is now immune to missing keys anyway
            self.match_stats[h_id] = {"damage": 0, "thugs": 0, "civs": 0, "threats": 0, "kos": 0, "moves": 0}
            
        # 🛡️ THE ARMOR: Safely initialize and increment any key, even if it's not in the baseline dictionary
        self.match_stats[h_id][stat_name] = self.match_stats[h_id].get(stat_name, 0) + amount
