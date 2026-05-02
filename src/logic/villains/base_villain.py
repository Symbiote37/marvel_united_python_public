from src.utils.helpers import Col

class BaseVillainLogic:
    """
    The Global Rulebook. 
    Behaviors inherited unless overridden.
    """
    BAM_PATTERNS = {
        "light_damage_bam": (1, 0, False),
        "heavy_damage_bam": (2, 0, False),
        "light_dmg_single_bam": (1, 0, True),
        "heavy_dmg_single_bam": (2, 0, True),
        "light_dmg_adj_bam": (1, 1, False),
        "heavy_dmg_adj_bam": (2, 1, False),
        "light_adj_bam": (0, 1, False)
    }
    
    CRISIS_COLOR = ""

    # --- ACTION DISCOVERY (The Menu) ---

    @staticmethod
    def get_heroic_options(engine, hero, location_override=None):
        target_idx = location_override if location_override is not None else hero.location_index
        loc = engine.locations[target_idx]
        opts = []
        if loc.civilians > 0:
            opts.append({"label": f"Rescue Civilian ({loc.civilians})", "id": "c"})
        if loc.threat and not loc.threat.cleared:
            if getattr(loc.threat, 'heroic_req', 0) > getattr(loc.threat, 'heroic_tokens', 0):
                opts.append({"label": f"Diffuse {loc.threat.name} (Heroic)", "id": "t_h"})
        return opts
        
    @staticmethod
    def get_move_options(engine, hero, location_override=None):
        target_idx = location_override if location_override is not None else hero.location_index
        loc = engine.locations[target_idx]
        opts = []
        if loc.threat and not loc.threat.cleared:
            if getattr(loc.threat, 'move_req', 0) > getattr(loc.threat, 'move_tokens', 0):
                opts.append({"label": f"Diffuse {loc.threat.name} (Move)", "id": "t_m"})
        return opts

    @staticmethod
    def get_attack_options(engine, hero, location_override=None):
        target_idx = location_override if location_override is not None else hero.location_index
        loc = engine.locations[target_idx]
        opts = []
        
        if loc.thugs > 0:
            opts.append({"label": "Attack Thug", "id": "m"})
        if loc.threat and not loc.threat.cleared:
            hp = getattr(loc.threat, 'hp', 0)
            if hp > 0:
                opts.append({"label": f"Attack {loc.threat.name}", "id": "h"})
        if target_idx == engine.villain.location_index:
            opts.append({"label": f"Attack {engine.villain.name}", "id": "v"})
            
        return opts

    # --- VILLAIN OVERRIDES ---

    @staticmethod
    def get_extra_heroic_options(engine, loc, hero):
        return []

    @staticmethod
    def get_extra_attack_options(engine, loc, hero):
        return []

    @staticmethod
    def get_extra_move_options(engine, loc, hero):
        return []

    @staticmethod
    def resolve_special_action(engine, loc, hero, action_id):
        pass
        
    @staticmethod
    def get_occupancy(engine, loc):
        return loc.total_figures()

    # --- STANDARD TRIGGERS ---

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return

        v_loc = engine.locations[v_idx]
        # 🚨 ARMOR RESTORED: getattr check
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        
        if not targets:
            engine.log.append(Col.wrap(f"   💥 BAM! {villain.name} strikes {v_loc.name} but misses!", Col.RED))
            return

        engine.log.append(Col.wrap(f"   💥 BAM! {villain.name} strikes {v_loc.name}! ", Col.RED + Col.BOLD))
        for h in targets:
            for _ in range(damage):
                h.take_damage(engine)

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        BaseVillainLogic.apply_standard_bam_damage(engine, threat, loc_idx)

    @staticmethod
    def get_start_of_turn_modifiers(engine, hero, location):
        mods = {"is_random": False, "ignore_prev": False, "label": ""}
        
        # 🚨 THE DATA-DRIVEN FIX: Read mechanical booleans directly off the Threat!
        if location.threat and not location.threat.cleared:
            if getattr(location.threat, 'ignore_prev', False):
                mods["ignore_prev"] = True
                mods["label"] = f"THREAT: {location.threat.name}"
                
            if getattr(location.threat, 'is_random', False):
                mods["is_random"] = True
                mods["label"] = f"THREAT: {location.threat.name}"
                
        return mods
        
    @staticmethod
    def apply_standard_bam_damage(engine, threat, loc_idx):
        bid = getattr(threat, 'bam_id', None)
        if not bid: return

        pattern = BaseVillainLogic.BAM_PATTERNS.get(bid, (0, 0, False))
        
        if len(pattern) == 2:
            main_dmg, adj_dmg = pattern
            single_target = False
        else:
            main_dmg, adj_dmg, single_target = pattern
        
        if main_dmg == 0 and adj_dmg == 0: return

        BaseVillainLogic._hit_sector(engine, loc_idx, main_dmg, f"{threat.name}'s strike", single_target=single_target)

        if adj_dmg > 0:
            for offset in [-1, 1]:
                adj_idx = (loc_idx + offset) % 6
                BaseVillainLogic._hit_sector(engine, adj_idx, adj_dmg, f"{threat.name}'s shockwave", single_target=False)

    @staticmethod
    def _hit_sector(engine, idx, dmg, src, single_target=False):
        if dmg <= 0 or idx == -1: return

        # 🚨 ARMOR RESTORED: getattr check
        targets = [h for h in engine.heroes if h.location_index == idx and h.location_index != -1 and not getattr(h, 'is_ko', False)]
        if not targets: return
            
        if single_target and len(targets) > 1:
            print(f"\n {Col.wrap('TARGET:', Col.YLW)} {src}")
            for i, h in enumerate(targets, 1):
                print(f" ({i}) {h.name} (Cards: {len(h.hand)})")
                
            # 🚨 HEADLESS FIX RESTORED
            choice = engine.ui.ask_choice(" Choose >> ", 1, len(targets))
            targets = [targets[choice - 1]]

        for h in targets:
            engine.log.append(Col.wrap(f"   🎯 {src} hits {h.name}!", Col.RED))
            for _ in range(dmg):
                h.take_damage(engine)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        engine.log.append(Col.wrap(f"   ! OVERFLOW: {loc.name} cap exceeded by {t_type}!", Col.RED))

    @staticmethod
    def restore_defeated_threat(engine, villain, threat_id, max_copies=6):
        active_count = 0
        for loc in engine.locations:
            if loc.threat and not loc.threat.cleared:
                t_id = (getattr(loc.threat, 'id_internal', None) or getattr(loc.threat, 'id', "")).lower()
                if t_id == threat_id: active_count += 1
                    
        if active_count >= max_copies: return False
            
        for i in range(1, 7):
            check_idx = (villain.location_index + i) % 6
            loc = engine.locations[check_idx]
            if not loc.threat or loc.threat.cleared:
                if hasattr(engine, 'create_threat'):
                    loc.threat = engine.create_threat(threat_id)
                    engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: A defeated {loc.threat.name} returns at {loc.name}!", Col.RED))
                    return True
        return False

    @staticmethod
    def handle_hero_ko(engine, hero):
        if getattr(hero, 'is_ko', False): return
        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} IS KO'D!", Col.RED + Col.BOLD))
        hero.is_ko = True 
        
        # 🔌 DECOUPLED MODE DELEGATION: Let custom modes intercept!
        if hasattr(engine, 'mode_handler') and hasattr(engine.mode_handler, 'handle_hero_ko'):
            if engine.mode_handler.handle_hero_ko(engine, hero):
                return

        if hasattr(engine, 'queued_events'):
            # 🛑 CASCADE LOCK: Prevent duplicate/infinite KO BAMs
            if not getattr(engine, 'is_resolving_ko_bam', False):
                if not any(e.get("type") == "ko_bam" for e in engine.queued_events):
                    engine.queued_events.append({"type": "ko_bam", "hero": hero})

    @staticmethod
    def resolve_special(engine, villain, card):
        pass
        
    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        pass
        
    @staticmethod
    def is_hero_alone(engine, hero):
        # 🚨 ALGORITHMIC OPTIMIZATION RESTORED: Fail-fast loop instead of sum()
        for h in engine.heroes:
            if h != hero and not getattr(h, 'is_ko', False) and h.location_index == hero.location_index:
                return False
        return True

    @staticmethod
    def add_plan_facedown(engine):
        deck = engine.villain.plan_deck 
        if deck:
            card = deck.pop(0)
            card['is_facedown'] = True 
            engine.storyline.append(card)
            engine.log.append(Col.wrap(" 🃏 Master Plan card added facedown!", Col.MAGENTA))
        else:
            engine.log.append(Col.wrap(" ⚠️ Master Plan is exhausted!", Col.RED))
            
    @staticmethod
    def handle_movement(engine, villain, card):
        move = card.get("move", 0)
        if move > 0 and getattr(villain, 'is_in_play', True):
            villain.location_index = (villain.location_index + move) % len(engine.locations)
            loc_name = engine.locations[villain.location_index].name
            engine.log.append(f" 🏃 {villain.name} moves to {loc_name}.")
            
    @staticmethod
    def on_civilians_flee(engine, loc):
        count = loc.civilians
        if count > 0:
            loc.civilians = 0
            engine.log.append(Col.wrap(f" 💨 {count} Civilians fled the scene!", Col.YLW))
