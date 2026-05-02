import json
import random
from src.utils.helpers import Col, ICON

class PowerUpManager:
    def __init__(self, state):
        self.state = state

    def initialize_pool(self):
        """Loads the tech tree from data/power_ups.json."""
        try:
            with open("data/power_ups.json", "r") as f:
                self.state.power_up_pool = json.load(f)["power_ups"]
            random.shuffle(self.state.power_up_pool)
        except FileNotFoundError:
            self.state.power_up_pool = []

    def prepare_match_slots(self, engine):
        """Standardized name. Sets up Action and Mission slots for the prelude."""
        if len(self.state.power_up_pool) >= 2:
            self.state.active_pu_token = self.state.power_up_pool.pop(0)
            self.state.active_pu_mission = self.state.power_up_pool.pop(0)
            self.state.pu_progress = {k: 0 for k in self.state.pu_progress}
            
            engine.log.append(Col.wrap(" AVAILABLE POWER-UPS:", Col.CYAN))
            engine.log.append(f"   [ACTIONS] {self.state.active_pu_token['effect_text']}")
            engine.log.append(f"   [MISSION] {self.state.active_pu_mission['effect_text']}")

    def get_deposit_commands(self, pool):
        """
        Only shows (P) Power-Up if the hero has a symbol 
        that is SPECIFICALLY needed by an unmet requirement.
        """
        if self.state.stage_index >= 3 or not getattr(self.state, 'active_pu_token', None): 
            return []
            
        reqs = self.state.active_pu_token.get("req", {})
        
        for t_type, target in reqs.items():
            if t_type == "threat":
                continue # Threats are handled via interception, not the P menu
                
            current = self.state.pu_progress.get(t_type, 0)
            
            # Only trigger if THIS specific type is unmet 
            # AND the hero has that specific symbol (or a wild).
            if current < target:
                if pool.get(t_type, 0) > 0 or pool.get("wild", 0) > 0:
                    return [Col.wrap(" (P) Power-Up", Col.PURP)]
                    
        return []

    def handle_deposit(self, engine, hero, pool):
        """
        Refined menu that only displays unmet requirements 
        the hero can actually satisfy.
        """
        reqs = self.state.active_pu_token.get("req", {})
        print(Col.wrap("\n--- DEPOSIT TO POWER-UP ---", Col.CYAN))
        
        options = {}
        idx = 1
        
        # Filter the menu to ONLY show unmet reqs 
        # that the hero has symbols for in their pool.
        for t_type, target in reqs.items():
            current = self.state.pu_progress.get(t_type, 0)
            if t_type != "threat" and current < target:
                if pool.get(t_type, 0) > 0 or pool.get("wild", 0) > 0:
                    print(f" [{idx}] Deposit {t_type.upper()} ({current}/{target})")
                    options[str(idx)] = t_type
                    idx += 1
        
        if not options:
            print(Col.wrap(" No eligible symbols for unmet requirements.", Col.RED))
            return True # Returns to command loop

        print(" [0] Cancel")
        choice = input(" >> ").strip()
        
        if choice in options:
            t_type = options[choice]
            if pool.get(t_type, 0) > 0: 
                pool[t_type] -= 1
            else: 
                pool["wild"] -= 1
                
            self.state.pu_progress[t_type] += 1
            engine.log.append(Col.wrap(f" {hero.name} contributed to {self.state.active_pu_token['name']}! ({self.state.pu_progress[t_type]}/{reqs[t_type]})", Col.GRN))
            return True
            
        return False

    def intercept_threat(self, engine):
        """Allows diverting a diffused threat to the power-up."""
        if self.state.stage_index >= 3 or not getattr(self.state, 'active_pu_token', None): 
            return False
        reqs = self.state.active_pu_token.get("req", {})
        if "threat" in reqs and self.state.pu_progress["threat"] < reqs["threat"]:
            print(Col.wrap(f"\n THREAT DIFFUSED! Apply to Power-Up? (1:Yes / 2:Mission)", Col.CYAN))
            if input(" >> ").strip() == '1':
                self.state.pu_progress["threat"] += 1
                engine.log.append(Col.wrap(f" Threat Token applied to Power-Up!", Col.GRN))
                return True
        return False

    def evaluate_stage_end(self, engine, victory):
        """Checks if requirements were met to secure the cards for the Arsenal."""
        if not self.state.active_pu_token: return
        
        # 1. Action Slot Check
        if victory and all(self.state.pu_progress[k] >= v for k, v in self.state.active_pu_token["req"].items()):
            self.state.acquired_power_ups.append(self.state.active_pu_token)
            engine.log.append(Col.wrap(f" 🔓 SECURED: {self.state.active_pu_token['name']}", Col.GRN + Col.BOLD))
        else:
            self.state.power_up_pool.append(self.state.active_pu_token)

        # 2. Mission Slot (M3) Check
        # We check if Civilians, Thugs, AND Threats are all marked as complete
        missions_complete = all(engine.missions[k] >= engine.missions[f"{k}_max"] for k in ["civilians", "thugs", "threats"])
        
        if victory and missions_complete:
            self.state.acquired_power_ups.append(self.state.active_pu_mission)
            engine.log.append(Col.wrap(f" 🔓 SECURED: {self.state.active_pu_mission['name']}", Col.GRN + Col.BOLD))
        else:
            self.state.power_up_pool.append(self.state.active_pu_mission)
            
        random.shuffle(self.state.power_up_pool)
        self.state.active_pu_token = self.state.active_pu_mission = None

    def apply_passives(self, engine, hero, pool):
        """Calculates and injects Arsenal bonuses into the Hero's turn."""
        if not self.state.acquired_power_ups: return
        played = engine.storyline.cards[-1] if engine.storyline.cards else {}
        prev_actions = engine.storyline.get_last_hero_actions() or []
        card_actions = played.get('actions', [])
        
        base = {
            "attack": card_actions.count("attack") + prev_actions.count("attack"),
            "move": card_actions.count("move") + prev_actions.count("move"),
            "heroic": card_actions.count("heroic") + prev_actions.count("heroic")
        }

        for pu in self.state.acquired_power_ups:
            pid = pu["id"]
            amount, t_type = 0, ""
            if pid == "pu_heroic_1" and base["move"] >= 2: amount, t_type = base["move"]//2, "heroic"
            elif pid == "pu_heroic_2" and base["attack"] >= 2: amount, t_type = base["attack"]//2, "heroic"
            elif pid == "pu_attack_1" and base["move"] >= 2: amount, t_type = base["move"]//2, "attack"
            elif pid == "pu_attack_2" and base["heroic"] >= 2: amount, t_type = base["heroic"]//2, "attack"
            elif pid == "pu_move_1" and base["attack"] >= 2: amount, t_type = base["attack"]//2, "move"
            elif pid == "pu_move_2" and base["heroic"] >= 2: amount, t_type = base["heroic"]//2, "move"
            elif pid == "pu_wild_1": amount, t_type = min(base.values()), "wild"

            if amount > 0:
                pool[t_type] = pool.get(t_type, 0) + amount
                engine.log.append(Col.wrap(f" 🌟 {pu['name'].upper()}: +{amount} {ICON.get(t_type, t_type)}!", Col.GRN + Col.BOLD))
