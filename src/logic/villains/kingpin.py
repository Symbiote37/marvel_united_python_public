import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class KingpinLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "CRIMINAL EMPIRE"
        villain.plot_max = 6
        villain.plot_value = 0
        
        # 1. Randomized Plan Tokens
        tokens = [1, 2, 3, 4, 5, 6]
        random.shuffle(tokens)
        for i, loc in enumerate(engine.locations):
            loc.plan_token = tokens[i]
            
            # 👔 THE CORRUPTION: Immediate C to T conversion for Elite Troops
            if loc.threat and not loc.threat.cleared:
                if "elite_troops" in str(loc.threat.id_internal).lower():
                    if loc.civilians > 0:
                        engine.log.append(Col.wrap(f" 👔 CORRUPTION: Civilians at {loc.name} turned into Thugs! ", Col.RED))
                        loc.thugs += loc.civilians
                        loc.civilians = 0
            
        engine.log.append(Col.wrap(" 👔 KINGPIN: 'Business is about to pick up.' ", Col.WHT + Col.BOLD))
        engine.log.append(Col.wrap(" 📦 6 Plan Tokens have been scattered across the city. ", Col.DARK_GRAY))

    @staticmethod
    def handle_movement(engine, villain, card):
        """
        Overrides movement to handle Kingpin's 'Advance the Plan' routing.
        Wilson Fisk doesn't move randomly; he moves toward his next criminal objective.
        """
        sid = card.get("special_id")
        
        if sid == "advance_plan":
            # 1. SCAN: Find the lowest numbered Plan token currently on the board
            target_loc = None
            lowest_val = 99
            
            for loc in engine.locations:
                token_val = getattr(loc, 'plan_token', None)
                if token_val is not None and token_val < lowest_val:
                    lowest_val = token_val
                    target_loc = loc
            
            if target_loc:
                # 2. POSITION: Move Kingpin directly to the target location
                v_idx = engine.locations.index(target_loc)
                villain.location_index = v_idx
                
                # 3. CONSUME: Discard the token and advance the Villainous Plot
                target_loc.plan_token = None
                villain.plot_value += 1
                
                # 🚨 UI SYNC: Ensure the Plot tracker in the header updates immediately
                engine.villain.plot_value = villain.plot_value 
                
                engine.log.append(Col.wrap(f" 🏃 ADVANCE: Kingpin moves to {target_loc.name} to complete Plan #{lowest_val}! ", Col.YLW))
                engine.log.append(Col.wrap(f"  PLOT: {villain.plot_name} {villain.plot_value}/6 ", Col.PURP))
                
                # 4. WIN CHECK: If Plan #6 is completed, the Empire is consolidated
                if villain.plot_value >= villain.plot_max:
                    engine.game_over = True
                    engine.victory_status = "VILLAIN_WINS"
                    engine.loss_reason = "CRIMINAL EMPIRE: Kingpin has successfully consolidated his power! "
            else:
                engine.log.append(Col.wrap(" 🏃 ADVANCE: No Plan tokens remain. Kingpin holds his ground. ", Col.DARK_GRAY))
        
        else:
            # Standard Move (1-5): Use the rulebook's standard clockwise movement
            BaseVillainLogic.handle_movement(engine, villain, card)

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        loc = engine.locations[v_idx]
        
        engine.log.append(Col.wrap(f" 💥 BAM! Kingpin exerts his influence at {loc.name}! ", Col.YLW))
        
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        if targets:
            for h in targets:
                engine.log.append(Col.wrap(f"   🎯 Kingpin crushes {h.name}!", Col.RED))
                h.take_damage(engine)
        else:
            engine.log.append(Col.wrap("   💨 No heroes were present to feel his weight. ", Col.DARK_GRAY))

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Overflow causes damage to heroes at the location."""
        engine.log.append(Col.wrap(f" 🚨 OVERFLOW at {loc.name}! ", Col.RED))
        targets = [h for h in engine.heroes if h.location_index == engine.locations.index(loc) and not getattr(h, 'is_ko', False)]
        for h in targets:
            engine.log.append(Col.wrap(f"   🎯 Backlash hits {h.name}! ", Col.RED))
            h.take_damage(engine)

    @staticmethod
    def handle_hero_ko(engine, hero):
        """KO accelerates the Master Plan."""
        if getattr(hero, 'is_ko', False): return
        hero.is_ko = True
        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} HAS FALLEN! ", Col.RED + Col.BOLD))
        engine.log.append(Col.wrap(" 👔 OPPORTUNITY: Kingpin presses his advantage! ", Col.YLW))
        if hasattr(engine, 'queued_events'):
            engine.queued_events.append({"type": "extra_card"})

    # --- THREAT LOGIC ---

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        t_id = (getattr(threat, 'id_internal', '') or getattr(threat, 'id', '')).lower()
        
        if t_id == "bullseye":
            engine.log.append(Col.wrap(" 🎯 BAM! Bullseye takes aim from his nest! ", Col.RED))
            # Targets: This loc + adjacent
            affected_indices = [loc_idx, (loc_idx - 1) % 6, (loc_idx + 1) % 6]
            
            for idx in affected_indices:
                loc = engine.locations[idx]
                heroes = [h for h in engine.heroes if h.location_index == idx and not getattr(h, 'is_ko', False)]
                
                if heroes:
                    for h in heroes:
                        engine.log.append(Col.wrap(f"   🎯 Snipe hits {h.name} at {loc.name}! ", Col.RED))
                        h.take_damage(engine)
                else:
                    # Discard 1 Civ if no heroes
                    if loc.civilians > 0:
                        loc.civilians -= 1
                        engine.log.append(Col.wrap(f"   💀 Bullseye picks off a civilian at {loc.name}! ", Col.DARK_GRAY))
        else:
            BaseVillainLogic.apply_standard_bam_damage(engine, threat, loc_idx)

    # --- MISSION INTERCEPTION ---

    @staticmethod
    def can_increment_mission(engine, mission_type):
        """
        Passive check for 'Connections' and 'Secrets'.
        Also serves as a 'Corruption Sweep' for Elite Troops.
        """
        # 👔 THE CORRUPTION SWEEP
        # We scan every location. If Elite Troops are present, any C becomes a T.
        for loc in engine.locations:
            if loc.threat and not loc.threat.cleared:
                if "elite_troops" in str(loc.threat.id_internal).lower():
                    if loc.civilians > 0:
                        engine.log.append(Col.wrap(f" 👔 CORRUPTION: Civilians at {loc.name} turned into Thugs! ", Col.RED))
                        loc.thugs += loc.civilians
                        loc.civilians = 0

        # MISSION BLOCKING LOGIC
        if mission_type == "thugs":
            if any(l.threat and not l.threat.cleared and "connections" in str(l.threat.id_internal).lower() for l in engine.locations):
                engine.log.append(Col.wrap(" ⛓️ CONNECTIONS: Fisk's lawyers ensure these Thugs disappear. ", Col.DARK_GRAY))
                return False
        
        if mission_type == "civilians":
            if any(l.threat and not l.threat.cleared and "secrets" in str(l.threat.id_internal).lower() for l in engine.locations):
                engine.log.append(Col.wrap(" 🤫 SECRETS: Kingpin silences the witnesses. ", Col.DARK_GRAY))
                return False
                
        return True
