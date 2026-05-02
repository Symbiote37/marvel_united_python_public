# src/logic/villains/proxima_midnight.py
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class ProximaMidnightLogic(BaseVillainLogic):
    """
    PROXIMA MIDNIGHT: The Obsidian Hunter.
    Focus: The Slaughter Track. She wins by discarding Civilians or through 
    overwhelming force (BAM/Overflow).
    """
    @staticmethod
    def perform_setup(engine, villain):
        # Tracking the 'Action Parry' for Masterful Fighter
        villain.ignored_action_this_turn = False
        engine.log.append(Col.wrap(" 🔱 PROXIMA MIDNIGHT begins the Obsidian Hunt... ", Col.RED))
        
    @staticmethod
    def broadcast_stance(engine):
        """Warns the player if Proxima's parry is actively protecting her this turn."""
        v = engine.villain
        loc = engine.locations[v.location_index]
        
        has_guard = False
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', None) or loc.threat.id).lower()
            if t_id == "masterful_fighter":
                has_guard = True
                
        # Only warn if the threat is active AND she hasn't parried yet this turn
        if has_guard and not getattr(v, 'ignored_action_this_turn', False):
            engine.log.append(Col.wrap("Proxima is in a Masterful stance! ", Col.YLW))
            
    @staticmethod
    def on_bam(engine, villain):
        """
        BAM: 1 Damage to all heroes at location.
        Discards all Civilians at location.
        Track +1 (Base) + Discarded Civilians.
        """
        v_idx = villain.location_index
        if v_idx == -1: return

        # 1. Damage Heroes (The Norm)
        BaseVillainLogic.on_bam(engine, villain)
        
        # 2. Civilian Massacre
        loc = engine.locations[v_idx]
        count = loc.civilians
        if count > 0:
            loc.civilians = 0
            engine.log.append(f"   🩸 {count} Civilians were slaughtered in the BAM!")
        
        # 3. Advance Slaughter Track
        ProximaMidnightLogic.advance_slaughter(engine, 1 + count, "BAM Strike")

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        Refined Proxima Overflow:
        Thugs: Everyone at Proxima's location takes 1 DMG.
        Civilians: The Track increases by the amount that overflowed.
        """
        if token_type == "thugs":
            engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: Thugs are swarming at {location.name}!", Col.RED))
            v_idx = villain.location_index
            for h in engine.heroes:
                if h.location_index == v_idx and not h.is_ko:
                    h.take_damage(engine)
                    engine.log.append(f"   💥 {h.name} is caught in the mob around Proxima!")
        
        elif token_type == "civilians":
            # If the engine tries to add 1 civilian and fails, that's +1 kill
            ProximaMidnightLogic.advance_slaughter(engine, 1, f"Overflow at {location.name}")

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "hunting_spear":
            ProximaMidnightLogic._resolve_purge(engine, [villain.location_index], "Hunting Spear")
        elif sid == "cleansing":
            v_idx = villain.location_index
            adj = [(v_idx - 1) % 6, (v_idx + 1) % 6]
            ProximaMidnightLogic._resolve_purge(engine, adj, "Cleansing")

    @staticmethod
    def _resolve_purge(engine, indices, flavor):
        """Common logic for Hunting Spear and Cleansing."""
        for idx in indices:
            loc = engine.locations[idx]
            if loc.civilians <= 0: continue
            
            engine.log.append(Col.wrap(f" 🔱 {flavor.upper()} sweeping {loc.name}!", Col.MAGENTA))
            
            # Identify local heroes who can actually intervene
            local_heroes = [h for h in engine.heroes if h.location_index == idx and not h.is_ko]
            
            if not local_heroes:
                count = loc.civilians
                loc.civilians = 0
                engine.log.append(f"   💀 No heroes at {loc.name} to intervene. {count} souls lost.")
                ProximaMidnightLogic.advance_slaughter(engine, count, flavor)
                continue

            # HEROES PRESENT: Interactive choice
            saved = 0
            while loc.civilians > 0 and local_heroes:
                print(f"\n {Col.wrap(loc.name.upper(), Col.BOLD)}: {loc.civilians} Civilians targeted!")
                print(f" (D) Discard 1 Card to save 1 Civilian | (S) Let them fall")
                choice = input(" >> ").upper().strip()
                
                if choice == 'D':
                    for i, h in enumerate(local_heroes):
                        print(f"  {i+1}: {h.name} ({len(h.hand)} Cards in Hand)")
                    
                    try:
                        h_idx = int(input("  Who protects them? ")) - 1
                        protector = local_heroes[h_idx]
                        protector.take_damage(engine)
                        saved += 1
                        loc.civilians -= 1 # They stay at the location
                        
                        # Remove if hero is now KO'd
                        if protector.is_ko: 
                            local_heroes.remove(protector)
                    except (ValueError, IndexError):
                        break
                else:
                    break 

            remaining = loc.civilians
            if remaining > 0:
                loc.civilians = 0
                ProximaMidnightLogic.advance_slaughter(engine, remaining, flavor)

    @staticmethod
    def advance_slaughter(engine, amount, reason):
        v = engine.villain
        v.plot_value = min(v.plot_max, v.plot_value + amount)
        
        engine.log.append(Col.wrap(
            f" 📈 {v.plot_name} +{amount} ({reason}) -> {v.plot_value}/{v.plot_max} ", 
            Col.RED + Col.BOLD
        ))
        
        if v.plot_value >= v.plot_max:
            engine.game_over = True
            engine.loss_reason = f"THE SLAUGHTER COMPLETE: {v.plot_name} reached {v.plot_max}!"

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        tid = getattr(threat, 'trigger_id', None) or threat.id
        
        if tid == "tactical_support":
            for h in engine.heroes:
                if h.location_index == loc_idx and not h.is_ko:
                    h.take_damage(engine)
                    engine.log.append(Col.wrap(f"   🎯 TACTICAL SUPPORT: {h.name} hit by the barrage!", Col.RED))

    # FIXED: Re-indented to sit inside the class
    @staticmethod
    def reduce_damage(engine, villain, amount, is_action=False):
        # 1. Non-actions (Hulk Smash) bypass the guard
        if not is_action:
            return amount

        loc = engine.locations[villain.location_index]
        
        # 2. Check for Masterful Fighter threat
        has_guard = False
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', None) or loc.threat.id).lower()
            if t_id == "masterful_fighter":
                has_guard = True

        # 3. Use the flag (which is reset by TurnSystem every villain turn)
        if has_guard and not getattr(villain, 'ignored_action_this_turn', False):
            villain.ignored_action_this_turn = True
            engine.log.append(Col.wrap(" 🛡️ MASTERFUL FIGHTER: Proxima parries the Attack Action!", Col.YLW))
            return 0 
            
        return amount
