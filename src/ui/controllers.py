import random
import time
from src.ai.utility_evaluator import UtilityEvaluator
from src.utils.helpers import Col, wait_for_user

class BaseController:
    """The universal interface the GameEngine uses to ask questions."""
    def ask_choice(self, prompt_text, options_or_min, max_val=None, return_index=False): raise NotImplementedError
    def ask_raw(self, prompt_text, valid_options): raise NotImplementedError
    def ask_yes_no(self, prompt_text): raise NotImplementedError
    def wait(self): raise NotImplementedError
    def acknowledge(self, message): raise NotImplementedError
    def render_intel_dossier(self, villain_name, intel_data): raise NotImplementedError

class HumanController(BaseController):
    """Translates engine requests into terminal prompts for a human player."""
    def ask_choice(self, prompt_text, options_or_min, max_val=None, return_index=False):
        if isinstance(options_or_min, list):
            options = options_or_min
            print(prompt_text)
            for i, opt in enumerate(options, 1):
                print(f" [{i}] {opt}")
            while True:
                choice = input(" >> ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return idx if return_index else options[idx]
                except ValueError:
                    pass
                print(Col.wrap(" [X] Invalid selection. Please enter a valid number.", Col.RED))
        else:
            min_val = options_or_min
            while True:
                choice = input(prompt_text).strip()
                try:
                    val = int(choice)
                    if min_val <= val <= max_val:
                        return val
                except ValueError:
                    pass
                print(Col.wrap(f" [X] Invalid selection. Must be between {min_val} and {max_val}.", Col.RED))

    def ask_raw(self, prompt_text, valid_options):
        while True:
            choice = input(prompt_text).strip().upper()
            if choice in valid_options: return choice
            elif choice == '9': return '9' 
            print(Col.wrap(" Invalid Selection.", Col.RED))

    def ask_yes_no(self, prompt_text):
        while True:
            choice = input(prompt_text).strip().lower()
            if choice in ['y', 'yes']: return True
            if choice in ['n', 'no']: return False
            print(Col.wrap(" Please enter 'y' or 'n'.", Col.RED))

    def wait(self):
        wait_for_user()

    def acknowledge(self, message):
        print(Col.wrap(message, Col.YLW))
        input(" >> ")

    def render_intel_dossier(self, villain_name, intel_data):
        import sys
        from src.utils.helpers import Col
        
        sys.stdout.write("\033c")
        sys.stdout.flush()
        
        if not intel_data:
            print(Col.wrap(f"\n ⚠️ WARNING: No S.H.I.E.L.D. intel on record for {villain_name}.", Col.RED))
            input(Col.wrap(" Press [ENTER] to return to the battle... ", Col.DARK_GRAY))
            return

        print(Col.wrap(f"{'='*53}", Col.CYAN))
        print(Col.wrap(f" 📁 S.H.I.E.L.D. TARGET INTEL: {villain_name.upper()}", Col.CYAN + Col.BOLD))
        print(Col.wrap(f"{'='*53}", Col.CYAN))
        
        icon_map = {
            "profile": "👤",
            "rules": "⚠️",
            "bam": "💥",
            "overflow": "🌊",
            "threats": "🦹"
        }
        
        for key, content in intel_data.items():
            icon = icon_map.get(key.lower(), "🔸")
            header_title = key.replace('_', ' ').upper()
            color = Col.RED if key.lower() == "bam" else Col.CYAN
            
            print(Col.wrap(f"\n {icon} {header_title}:", color + Col.BOLD))
            print(f" {content}")
            
        print(Col.wrap(f"\n{'='*53}", Col.CYAN))
        input(Col.wrap(" Press [ENTER] to return to the battle... ", Col.DARK_GRAY))

class TacticalBotController(BaseController):
    def __init__(self, engine):
        self.engine = engine
        self.evaluator = UtilityEvaluator()
        self.last_state = None
        self.loop_count = 0
        self.is_retreating = False

    def ask_choice(self, prompt_text, options_or_min, max_val=None, return_index=False):
        # 1. CARD PLAY
        if "Play card" in prompt_text:
            hero = self.engine.heroes[self.engine.current_hero_index]
            prev_actions = self.engine.storyline.get_last_hero_actions()
            best_score, best_idx = -999, 0
            for i, card in enumerate(hero.hand):
                score = self.evaluator.score_card_play(self.engine, hero, card, prev_actions)
                if score > best_score: best_score, best_idx = score, i
            print(Col.wrap(f" 🤖 S.H.I.E.L.D. BOT selected Card {best_idx + 1}!", Col.CYAN))
            time.sleep(1.0)
            return best_idx + 1 
            
        # 1.5 DAMAGE CONTROL (Discarding)
        if "discard" in prompt_text.lower() or "lose a card" in prompt_text.lower():
            hero = self.engine.heroes[self.engine.current_hero_index]
            worst_score, worst_idx = 999, 0
            for i, card in enumerate(hero.hand):
                score = self.evaluator.score_card_play(self.engine, hero, card, [])
                if score < worst_score: worst_score, worst_idx = score, i
            print(Col.wrap(f" 🤖 BOT COMMAND: Discarding weakest card ({worst_idx + 1}) to absorb damage.", Col.RED))
            time.sleep(0.5)
            return worst_idx + 1

        # 2. LIST RESOLUTION (Targets & Locations)
        if isinstance(options_or_min, list):
            if not options_or_min: return 1 if return_index else None
            
            m_state = self.engine.missions
            cleared = sum(1 for m in ["civilians", "thugs", "threats"] if str(m_state.get(m, 0)) in ["✔", "True", "cleared"] or (isinstance(m_state.get(m, 0), int) and m_state.get(m, 0) >= m_state.get(f"{m}_max", 99)))
            boss_vulnerable = cleared >= 2

            # A. BOSS HUNTER
            if boss_vulnerable and not self.is_retreating:
                v_name = self.engine.villain.name.upper()
                for i, opt in enumerate(options_or_min):
                    if v_name in str(opt).upper():
                        return i if return_index else options_or_min[i]

            # B. TRUE GPS PATHFINDER (Heat-Seeking & Directional Logic)
            if any(k in prompt_text.lower() for k in ["move", "location", "where", "to"]):
                retreating = self.is_retreating
                if retreating: self.is_retreating = False
                
                # 🎯 TARGET IDENTIFICATION
                if boss_vulnerable:
                    target_idx = self.engine.villain.location_index
                else:
                    # Heat-seeking: Find the location with the most tokens/threats
                    hottest_idx, max_heat = 0, -1
                    for idx, loc in enumerate(self.engine.locations):
                        heat = getattr(loc, 'thugs', 0) + getattr(loc, 'civilians', 0)
                        if loc.threat and not loc.threat.cleared: heat += 2
                        if heat > max_heat: max_heat, hottest_idx = heat, idx
                    target_idx = hottest_idx
                
                best_idx, min_dist = 0, 99
                curr_idx = self.engine.heroes[self.engine.current_hero_index].location_index

                for i, opt in enumerate(options_or_min):
                    dest_idx = -1
                    for loc_i, loc in enumerate(self.engine.locations):
                        if loc.name.upper() in str(opt).upper():
                            dest_idx = loc_i
                            break
                    
                    if dest_idx != -1:
                        # 🔄 CIRCULAR DISTANCE CALCULATOR
                        # We calculate the absolute shortest path on a 6-node ring
                        cw_dist = (target_idx - dest_idx) % 6
                        ccw_dist = (dest_idx - target_idx) % 6
                        dist_to_target = min(cw_dist, ccw_dist)

                        if retreating:
                            # If retreating, we want the option that MAXIMIZES distance from Villain
                            if dist_to_target > 0: return i if return_index else options_or_min[i]
                        else:
                            # If moving toward target, pick the option that results in the smallest gap
                            if dist_to_target < min_dist:
                                min_dist = dist_to_target
                                best_idx = i
                
                return best_idx if return_index else options_or_min[best_idx]

            # C. Fallback
            idx = random.randint(0, len(options_or_min) - 1)
            return idx if return_index else options_or_min[idx]

        # 3. INTEGER RANGE / WILD TOKENS
        else:
            min_val = options_or_min
            if "SELECT TOKEN" in prompt_text.upper():
                hero = self.engine.heroes[self.engine.current_hero_index]
                tokens = getattr(hero, 'stashed_tokens', []) or getattr(hero, 'action_tokens', []) or []
                m_state = self.engine.missions
                cleared = sum(1 for m in ["civilians", "thugs", "threats"] if str(m_state.get(m, 0)) in ["✔", "True", "cleared"] or (isinstance(m_state.get(m, 0), int) and m_state.get(m, 0) >= m_state.get(f"{m}_max", 99)))
                
                if cleared >= 2 and hero.location_index == self.engine.villain.location_index:
                    for i, t in enumerate(tokens):
                        if str(t).lower() in ['w', 'wild', 'attack', 'a', '2']:
                            print(Col.wrap(" 🤖 BOT COMMAND: Auto-Selected Damage/Wild Token!", Col.CYAN))
                            return i + 1

            if min_val == 0 and max_val is not None and max_val >= 1: return 1
            return random.randint(min_val, max_val) if max_val and max_val >= min_val else min_val

    def ask_raw(self, prompt_text, valid_cmds):
        pool = getattr(self.engine, 'active_pool', None) or {}
        current_state = f"{prompt_text}_{pool.get('move',0)}_{pool.get('attack',0)}_{pool.get('heroic',0)}_{pool.get('wild',0)}"

        if current_state == getattr(self, 'last_state', None):
            self.loop_count += 1
            if self.loop_count > 3: return '0' if '0' in valid_cmds else list(valid_cmds)[0]
        else:
            self.last_state = current_state
            self.loop_count = 0

        time.sleep(0.5)

        if "U" not in valid_cmds:
            for cmd in ["1", "2", "3", "4", "5"]:
                if cmd in valid_cmds: return cmd
            return list(valid_cmds)[0]

        hero = self.engine.heroes[self.engine.current_hero_index]
        loc = self.engine.locations[hero.location_index]

        can_move = pool.get("move", 0) > 0 or pool.get("wild", 0) > 0
        can_attack = pool.get("attack", 0) > 0 or pool.get("wild", 0) > 0
        can_heroic = pool.get("heroic", 0) > 0 or pool.get("wild", 0) > 0

        # 🚨 [REMOVED "S" CHECK FROM HERE]

        has_thugs = getattr(loc, 'thugs', 0) > 0
        has_civs = getattr(loc, 'civilians', 0) > 0
        has_threat = loc.threat and not loc.threat.cleared
        has_villain = hero.location_index == self.engine.villain.location_index

        m_state = self.engine.missions
        missions_cleared = sum(1 for m in ["civilians", "thugs", "threats"] if str(m_state.get(m, 0)) in ["✔", "True", "cleared"] or (isinstance(m_state.get(m, 0), int) and m_state.get(m, 0) >= m_state.get(f"{m}_max", 99)))
        boss_vulnerable = missions_cleared >= 2

        threat_hp = getattr(loc.threat, 'hp', 0) if has_threat else 0
        threat_is_attackable = has_threat and threat_hp > 0
        threat_is_heroic = has_threat and threat_hp <= 0

        # 🚨 THE BAM RETREAT
        if has_villain and can_move:
            needs_retreat = False
            if boss_vulnerable:
                has_shield = loc.threat and not loc.threat.cleared
                if has_shield and not can_heroic: needs_retreat = True
                elif not has_shield and not can_attack: needs_retreat = True
            else:
                if not can_attack and not can_heroic: needs_retreat = True

            if needs_retreat:
                self.is_retreating = True
                print(Col.wrap(" 🤖 BOT COMMAND: Move -> Tactical Retreat! (1)", Col.CYAN))
                return "1"

        # 🚨 THE BLOODHOUND DIRECTIVE
        if boss_vulnerable:
            has_shield = loc.threat and not loc.threat.cleared
            if not has_villain and can_move: return "1"
            if has_villain and has_shield and can_heroic: return "3"
            if has_villain and can_attack: return "2"
            if has_villain: return "0"

        # 🚨 WILD TOKEN AUTO-ACTIVATION (Kill Phase)
        tokens = getattr(hero, 'stashed_tokens', []) or getattr(hero, 'action_tokens', []) or []
        if boss_vulnerable and has_villain and "T" in valid_cmds:
            if ("W" in tokens or "wild" in tokens or "attack" in tokens) and (pool.get("attack", 0) + pool.get("wild", 0)) == 0:
                print(Col.wrap(" 🤖 BOT COMMAND: Pumping Boss Damage (T)", Col.CYAN))
                return "T"

        # --- Standard Operating Procedure ---
        # 🚨 [MOVED "S" CHECK TO HERE] - Only cast specials if not actively hunting the Boss!
        if "S" in valid_cmds: return "S" 
        
        if can_attack and (has_thugs or threat_is_attackable): return "2"
        if can_heroic and (has_civs or threat_is_heroic): return "3"
        if can_move and not (has_thugs or has_civs or has_threat or has_villain): return "1"
        if can_move: return "1"
        return "0"

        # 🚨 SMART SUB-MENU ARMOR (Runs AT THE END)
        if desired_cmd not in valid_cmds:
            if boss_vulnerable and has_villain:
                for fallback in ["2", "3", "1"]: # Force Attacks/Heroics first if Wilds are prompting
                    if fallback in valid_cmds: return fallback
            else:
                for fallback in ["1", "2", "3"]:
                    if fallback in valid_cmds: return fallback
            return list(valid_cmds)[0]

        return desired_cmd
        
    def ask_yes_no(self, prompt_text):
        time.sleep(0.5)
        return True

    def wait(self): time.sleep(1.0)
    def acknowledge(self, message): time.sleep(0.5)
    def render_intel_dossier(self, villain_name, intel_data): pass

class HybridController(BaseController):
    """
    A routing controller that seamlessly delegates engine queries 
    between a human player and the S.H.I.E.L.D. bot.
    """
    def __init__(self, engine, bot_indices):
        self.engine = engine
        self.bot_indices = bot_indices  # List of integers (e.g., [1, 2] for Heroes 2 and 3)
        self.human_ui = HumanController()
        self.bot_ui = TacticalBotController(engine)

    def _get_active_ui(self):
        # Determine who is currently taking their turn
        idx = getattr(self.engine, 'current_hero_index', -1)
        
        # If the active hero is in our bot list, deploy S.H.I.E.L.D.
        if idx in self.bot_indices:
            return self.bot_ui
            
        # Default to human for their hero turns, AND for global/villain events
        return self.human_ui

    def ask_choice(self, prompt_text, options_or_min, max_val=None, return_index=False):
        return self._get_active_ui().ask_choice(prompt_text, options_or_min, max_val, return_index)

    def ask_raw(self, prompt_text, valid_options):
        return self._get_active_ui().ask_raw(prompt_text, valid_options)

    def ask_yes_no(self, prompt_text):
        return self._get_active_ui().ask_yes_no(prompt_text)

    def wait(self):
        self._get_active_ui().wait()
        
    def acknowledge(self, message):
        self._get_active_ui().acknowledge(message)

    def render_intel_dossier(self, villain_name, intel_data):
        self._get_active_ui().render_intel_dossier(villain_name, intel_data)
