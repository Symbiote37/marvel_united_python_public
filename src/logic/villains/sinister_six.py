# src/logic/villains/sinister_six.py

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class SinisterSixLogic(BaseVillainLogic):
    """
    Master logic controller for the Sinister Six game mode.
    GEOMETRY LOCK: Strictly 6 locations (% 6).
    """

    @staticmethod
    def perform_setup(engine, villain):
        """Initializes the multi-villain roster and syncs the Master Plan deck."""
        import json
        import random
        from src.entities.threats import Threat
        from src.entities.actors import Villain as VillainActor
        
        roster_names = ["kraven", "sandman", "electro", "vulture", "doctor_octopus", "mysterio"]
        initials = ["K", "S", "E", "V", "D", "M"]
        
        engine.sinister_six_roster = {}
        engine.villains = [] 
        
        # Determine starting positions and layout
        board_offset = random.randint(0, 5)
        start_positions = [0, 0, 1, 1, 5, 5]
        random.shuffle(start_positions)
        
        target_hp = getattr(villain, 'hp', len(engine.heroes))

        try:
            with open("data/threats/sinister_six_threats.json", 'r') as f:
                threat_data = json.load(f)
        except FileNotFoundError:
            threat_data = []
            
        for i in range(6):
            v_idx = (i + board_offset) % 6
            v_id = roster_names[v_idx]
            
            # 1. Setup the Logic Roster Data
            engine.sinister_six_roster[v_id] = {
                "loc": start_positions[v_idx],
                "initials": initials[v_idx],
                "defeated": False,
                "internal_id": v_id,
                "hp": target_hp,
                "max_hp": target_hp,
                "weak_spot_cleared": False
            }

            # 2. Setup the Physical UI Actors for the HUD/Map rendering
            new_v = VillainActor({
                "name": v_id.replace('_', ' ').title(),
                "internal_id": v_id,
                "hp": target_hp
            })
            new_v.location_index = start_positions[v_idx]
            engine.villains.append(new_v)

            # 3. Setup the Weak Spot Threats
            t_data = next((t for t in threat_data if t.get("id_internal") == f"weak_spot_{v_id}"), None)
            if t_data:
                engine.locations[i].threat = Threat(t_data)
                engine.locations[i].threat.villain_owner = v_id

        # 4. 🎴 THE DECK SYNC: Hand the master plan cards to the new lead actor
        master_deck = villain.plan_deck
        engine.villain = engine.villains[0]
        engine.villain.plan_deck = master_deck

        for h in engine.heroes:
            h.location_index = 3

        engine.log.append(Col.wrap(" 🚩 SINISTER SIX MODE: The Hive Mind is active! ", Col.YLW))

        # 🔌 THE UI GRAFT: Override Mode Handler methods with Sinister Six HUD logic
        if hasattr(engine, 'mode_handler'):
            mode = engine.mode_handler
            mode.render_center_dashboard = lambda: SinisterSixLogic.render_center_dashboard(engine)
            mode.get_location_presence = lambda loc_idx: SinisterSixLogic.get_location_presence(engine, loc_idx)
            mode.is_eot_blocked = lambda loc_idx: SinisterSixLogic.is_eot_blocked(engine, loc_idx)
            mode.get_turn_interval = lambda: 2

    @staticmethod
    def execute_villain_turn(engine, forced_extra_card=False):
        """Custom Sinister Six turn rotation logic for multi-villain activation."""
        from src.systems.villain_system import VillainSystem
        from src.systems.turn_system import TurnSystem
        from src.systems.token_system import TokenSystem

        TurnSystem.reset_boss_defenses(engine)
        plan = engine.villain.draw_plan()
        if not plan:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "TIME EXPIRED: The Six completed their Master Plan!"
            return

        engine.storyline.add(plan)
        engine.turn_count += 1
        engine.log = []

        order = plan.get("villain_order", [])
        is_all = plan.get("special_id") == "return_of_sinister_six"
        
        # Identify which villains act this turn (Max 2 unless Special Plan)
        active_names = [v for v in order if not engine.sinister_six_roster[v]["defeated"]]
        if not is_all: 
            active_names = active_names[:2]

        for i, v_name in enumerate(active_names):
            v_data = engine.sinister_six_roster[v_name]
            display_name = v_name.replace('_', ' ').title()
            
            # Update logical position
            v_data["loc"] = (v_data["loc"] + plan.get("move", 0)) % 6
            loc = engine.locations[v_data["loc"]]
            
            # Sync Physical Actor Position
            for actor in engine.villains:
                if actor.internal_id == v_name:
                    actor.location_index = v_data["loc"]

            engine.log.append(Col.wrap(f" 🏃 {display_name} stalks into {loc.name}. ", Col.CYAN))
            
            if plan.get("bam"):
                SinisterSixLogic.on_bam(engine, v_data)
            
            tracker = set()
            if i == 0 or is_all:
                TokenSystem.add_token(engine, v_data["loc"], "thugs", tracker)
            if i == 1 or is_all:
                TokenSystem.add_token(engine, v_data["loc"], "civilians", tracker)
            
            VillainSystem.process_event_queue(engine)
            if getattr(engine, 'game_over', False): 
                break

    @staticmethod
    def render_center_dashboard(engine):
        roster = getattr(engine, 'sinister_six_roster', {})
        if not roster: return []
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

    @staticmethod
    def get_location_presence(engine, loc_idx):
        icons = ""
        roster = getattr(engine, 'sinister_six_roster', {})
        for name, data in roster.items():
            if data["loc"] == loc_idx and not data["defeated"]:
                icons += Col.wrap(data["initials"], Col.RED + Col.BOLD)
        return icons

    @staticmethod
    def is_eot_blocked(engine, loc_idx):
        roster = getattr(engine, 'sinister_six_roster', {})
        return any(v["loc"] == loc_idx and not v["defeated"] 
                  for v in roster.values())

    @staticmethod
    def _bam_doctor_octopus(engine, v_data, loc_idx, loc):
        loc.crisis_tokens = getattr(loc, 'crisis_tokens', 0) + 1
        engine.log.append(Col.wrap(" 🐙 Doctor Octopus deploys a crisis token!", Col.YLW))
        hit_anyone = False
        for h in engine.heroes:
            if h.location_index == loc_idx and not getattr(h, 'is_ko', False):
                if "crisis" in getattr(h, 'stashed_tokens', []):
                    h.take_damage(engine)
                    hit_anyone = True
        if hit_anyone:
            engine.log.append(Col.wrap("   🎯 Doctor Octopus's tentacles strike the vulnerable!", Col.RED))

    @staticmethod
    def _bam_mysterio(engine, v_data, loc_idx, loc):
        hit_anyone = False
        for h in engine.heroes:
            if h.location_index == loc_idx and not getattr(h, 'is_ko', False):
                if not hasattr(h, 'stashed_tokens'): h.stashed_tokens = []
                h.stashed_tokens.append("crisis")
                hit_anyone = True
        if hit_anyone:
            engine.log.append(Col.wrap(" 🔮 Mysterio clouds their minds! (+1 Crisis to Heroes)", Col.PURP))

    @staticmethod
    def _bam_kraven(engine, v_data, loc_idx, loc):
        target = None
        heroes_by_loc = {}
        for h in engine.heroes:
            if not getattr(h, 'is_ko', False):
                heroes_by_loc.setdefault(h.location_index, []).append(h)

        for offset in range(6):
            check_idx = (loc_idx + offset) % 6
            heroes_here = heroes_by_loc.get(check_idx, [])
            if len(heroes_here) == 1:
                target = heroes_here[0]
                break
        
        if target:
            engine.log.append(Col.wrap(f" 🦁 Kraven ambushes a lone prey!", Col.RED))
            for _ in range(2): target.take_damage(engine)
        else:
            from src.systems.token_system import TokenSystem
            tracker = set()
            for _ in range(2):
                TokenSystem.add_token(engine, loc_idx, "civilians", tracker)
            engine.log.append(Col.wrap(" 🦁 Kraven finds no prey and baits a trap!", Col.YLW))

    @staticmethod
    def _bam_sandman(engine, v_data, loc_idx, loc):
        if v_data.get("defeated", False): return
        v_data["hp"] = v_data.get("hp", 0) + 1
        v_data["max_hp"] = v_data.get("max_hp", 0) + 1
        engine.log.append(Col.wrap(" ⏳ Sandman hardens his form and gains 1 HP! ", Col.YLW))
        
        for h in engine.heroes:
            if h.location_index == loc_idx and not getattr(h, 'is_ko', False):
                h.take_damage(engine)

    @staticmethod
    def _bam_electro(engine, v_data, loc_idx, loc):
        engine.log.append(Col.wrap(" ⚡ Electro releases a massive shockwave! ", Col.YLW))
        for offset in [-1, 1]:
            adj_idx = (loc_idx + offset) % 6
            for h in engine.heroes:
                if h.location_index == adj_idx and not getattr(h, 'is_ko', False):
                    h.take_damage(engine)

    @staticmethod
    def _bam_vulture(engine, v_data, loc_idx, loc):
        civs = getattr(loc, 'civilians', 0)
        thugs = getattr(loc, 'thugs', 0)
        if civs > 0 or thugs > 0:
            v_data['stashed_civs'] = v_data.get('stashed_civs', 0) + civs
            v_data['stashed_thugs'] = v_data.get('stashed_thugs', 0) + thugs
            loc.civilians = 0
            loc.thugs = 0
            engine.log.append(Col.wrap(f" 🦅 Vulture snatches {civs} Civilians and {thugs} Thugs! ", Col.YLW))

    @staticmethod
    def on_bam(engine, v_input):
        """Routes the BAM effect to the specific active villain using a clean dispatch."""
        
        # 🚨 THE SHIELD: Preserving our dynamic input parsing and roster sync!
        roster = getattr(engine, 'sinister_six_roster', None)
        if roster is None:
            roster = getattr(getattr(engine, 'mode_handler', None), 'sinister_six_roster', {})

        if hasattr(v_input, 'internal_id'):
            v_id = v_input.internal_id
            v_data = roster.get(v_id, {})
        elif isinstance(v_input, dict):
            v_data = v_input
            v_id = v_data.get("internal_id")
        else:
            return 

        if not v_id or not v_data: 
            return

        loc_idx = v_data.get("loc")
        loc = engine.locations[loc_idx]

        # 🎯 THE PR PAYLOAD: Clean dictionary dispatch
        dispatch = {
            "doctor_octopus": SinisterSixLogic._bam_doctor_octopus,
            "mysterio": SinisterSixLogic._bam_mysterio,
            "kraven": SinisterSixLogic._bam_kraven,
            "sandman": SinisterSixLogic._bam_sandman,
            "electro": SinisterSixLogic._bam_electro,
            "vulture": SinisterSixLogic._bam_vulture,
        }

        handler = dispatch.get(v_id)
        if handler:
            handler(engine, v_data, loc_idx, loc)

    @staticmethod
    def on_overflow(engine, villain, loc, token_type):
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: The Six gain momentum from {loc.name}! ", Col.RED + Col.BOLD))
        SinisterSixLogic._accelerate_plot(engine)

    @staticmethod
    def handle_hero_ko(engine, hero):
        if getattr(hero, 'is_ko', False): return
        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} IS KO'D! ", Col.RED + Col.BOLD))
        hero.is_ko = True 
        engine.log.append(Col.wrap(" 💀 SPECIAL KO: The Six capitalize on the fallen hero! ", Col.RED))
        SinisterSixLogic._accelerate_plot(engine)

    @staticmethod
    def _accelerate_plot(engine):
        deck = engine.villain.plan_deck 
        if deck:
            card = deck.pop(0)
            card['is_facedown'] = True 
            engine.storyline.cards.append(card)
            engine.log.append(Col.wrap(" 📉 A Master Plan card was added facedown! ", Col.MAGENTA))
        else:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "TIME EXPIRED: The Six have executed their Master Plan! "

    @staticmethod
    def get_start_of_turn_modifiers(engine, hero, location):
        stashed = getattr(hero, 'stashed_tokens', [])
        if "crisis" in stashed:
            mysterio_data = engine.sinister_six_roster.get("mysterio")
            if mysterio_data and not mysterio_data.get("defeated", False):
                stashed.remove("crisis")
                engine.log.append(Col.wrap(f" 🔮 {hero.name} discards a Crisis token due to Mysterio's illusions! ", Col.PURP))
                return {"is_random": True, "ignore_prev": False, "label": "Mysterio's Illusion"}
        return {"is_random": False, "ignore_prev": False, "label": ""}

    @staticmethod
    def reduce_damage(engine, target_obj, amount, is_action):
        if getattr(target_obj, 'villain_owner', '') == "vulture":
            v_data = engine.sinister_six_roster.get("vulture")
            if v_data and not v_data.get("defeated", False):
                stashed_c = v_data.get("stashed_civs", 0)
                stashed_t = v_data.get("stashed_thugs", 0)
                if stashed_c > 0 or stashed_t > 0:
                    loc_idx = v_data.get("loc", 0)
                    loc = engine.locations[loc_idx]
                    loc.civilians += stashed_c
                    loc.thugs += stashed_t
                    v_data["stashed_civs"] = 0
                    v_data["stashed_thugs"] = 0
                    engine.log.append(Col.wrap(f" 🦅 Vulture uses his captives as a shield! ({stashed_c} Civs and {stashed_t} Thugs dropped at {loc.name}) ", Col.RED))
                    engine.log.append(Col.wrap(" 🛡️ Vulture escapes unscathed! ", Col.YLW))
                    if loc.total_figures() > loc.capacity:
                         if not hasattr(engine, 'queued_events'): engine.queued_events = []
                         engine.queued_events.append({"type": "overflow", "loc": loc, "t_type": "Captives"})
                    return 0 
        return amount

    @staticmethod
    def on_threat_defeated(engine, threat):
        v_owner_id = getattr(threat, 'villain_owner', None)
        if v_owner_id and v_owner_id in engine.sinister_six_roster:
            v_data = engine.sinister_six_roster[v_owner_id]
            v_data["weak_spot_cleared"] = True
            display_name = v_owner_id.replace('_', ' ').title()
            engine.log.append(Col.wrap(f" 🔓 SHIELDS DOWN! {display_name} is now vulnerable to attacks! ", Col.GRN + Col.BOLD))

    @staticmethod
    def get_attack_options(engine, hero):
        opts = []
        target_indices = [hero.location_index]
        if getattr(hero, 'can_attack_adjacent', False):
            target_indices.append((hero.location_index + 1) % 6)
            target_indices.append((hero.location_index - 1) % 6)
        target_indices = list(set(target_indices))
        for loc_idx in target_indices:
            loc = engine.locations[loc_idx]
            loc_label = f" in {loc.name}" if loc_idx != hero.location_index else ""
            if getattr(loc, 'thugs', 0) > 0:
                opts.append({"label": f"Attack Thug{loc_label}", "id": "m", "target_loc": loc_idx})
            if loc.threat and not loc.threat.cleared:
                if getattr(loc.threat, 'attack_req', 0) > getattr(loc.threat, 'attack_tokens', 0):
                    opts.append({"label": f"Diffuse {loc.threat.name} (Attack){loc_label}", "id": "t_a", "target_loc": loc_idx})
                elif getattr(loc.threat, 'hp', 0) > 0:
                    opts.append({"label": f"Attack {loc.threat.name}{loc_label}", "id": "h", "target_loc": loc_idx})
            for v_name, v_data in engine.sinister_six_roster.items():
                if v_data.get("loc") == loc_idx and not v_data.get("defeated", False):
                    if v_data.get("weak_spot_cleared", False):
                        display_name = v_name.replace('_', ' ').title()
                        opts.append({"label": f"Attack {display_name} (HP: {v_data.get('hp', 0)}){loc_label}", "id": f"atk_{v_name}", "target_loc": loc_idx})
        return opts

    @staticmethod
    def resolve_special_action(engine, loc, hero, action_id):
        if action_id.startswith("atk_"):
            v_name = action_id.replace("atk_", "")
            v_data = engine.sinister_six_roster.get(v_name)
            if not v_data or v_data.get("defeated", False): return
            if v_name == "vulture":
                stashed_c = v_data.get("stashed_civs", 0)
                stashed_t = v_data.get("stashed_thugs", 0)
                if stashed_c > 0 or stashed_t > 0:
                    loc.civilians += stashed_c
                    loc.thugs += stashed_t
                    v_data["stashed_civs"] = 0
                    v_data["stashed_thugs"] = 0
                    engine.log.append(Col.wrap(f" 🦅 Vulture uses his captives as a shield! ({stashed_c} Civs and {stashed_t} Thugs dropped at {loc.name})", Col.RED))
                    engine.log.append(Col.wrap(" 🛡️ Vulture escapes unscathed!", Col.YLW))
                    if loc.total_figures() > loc.capacity:
                         if not hasattr(engine, 'queued_events'): engine.queued_events = []
                         engine.queued_events.append({"type": "overflow", "loc": loc, "t_type": "Captives"})
                    return 
            v_data["hp"] -= 1
            display_name = v_name.replace('_', ' ').title()
            if v_data["hp"] <= 0:
                v_data["defeated"] = True
                engine.log.append(Col.wrap(f" 💀 {display_name.upper()} ELIMINATED! ", Col.RED + Col.BOLD))
                if all(v.get("defeated", False) for v in engine.sinister_six_roster.values()):
                    engine.game_over = True
                    engine.victory_status = "HEROES_WIN"
                    engine.victory_reason = "The Sinister Six have been dismantled!"
            else:
                engine.log.append(Col.wrap(f"   💥 {display_name} takes 1 damage! ({v_data.get('hp', 0)} HP left)", Col.RED))
