# src/logic/villains/kang.py

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col
from src.systems.token_system import TokenSystem

class KangLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        """
        KANG SETUP: 
        Ensure we capture his maximum health at the start of the game 
        so Time Paradox knows exactly what 'full HP' means!
        """
        villain.max_hp = villain.hp
        
    @staticmethod
    def on_bam(engine, villain):
        """
        KANG BAM: 
        - Out-of-Play: Thug Incursion (every location).
        - In-Play: 2 DMG at epicenter, 1 DMG adjacent.
        """
        # --- MODE A: OUT OF PLAY (Beyond Time) ---
        if villain.location_index == -1:
            engine.log.append(Col.wrap(" ⏳ KANG IS BEYOND TIME: Thugs invade every sector! ", Col.YLW))
            overflow_tracker = set()
            for i in range(len(engine.locations)):
                TokenSystem.add_token(engine, i, "thugs", overflow_tracker)
            return

        # --- MODE B: IN PLAY (Temporal Epicenter) ---
        # 1. Primary Blast: 2 DMG at current location
        from src.logic.villains.base_villain import BaseVillainLogic
        BaseVillainLogic.on_bam(engine, villain, damage=2)
        
        # 2. Secondary Shockwave: 1 DMG to Adjacent
        v_idx = villain.location_index
        adj = [(v_idx - 1) % 6, (v_idx + 1) % 6]
        
        engine.log.append(Col.wrap(" ⚡ TEMPORAL SHOCKWAVE expands! ", Col.RED))
        for h in engine.heroes:
            # 🛡️ STATE ARMOR: Standard KO check only.
            if not getattr(h, 'is_ko', False) and h.location_index in adj:
                h.take_damage(engine)
                engine.log.append(Col.wrap(f"       💥 {h.name} hit by the shockwave! (1 DMG)", Col.RED))

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        KANG OVERFLOW: Temporal Anomaly.
        Adds a Crisis token directly to the location, shutting down its End of Turn effect.
        """
        engine.log.append(Col.wrap(f" ⚠️ TEMPORAL ANOMALY: Overflow at {location.name}! A Crisis Token appears.", Col.PURP))
        location.crisis_tokens = getattr(location, 'crisis_tokens', 0) + 1

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "time_master":
            # Mode 1: On board -> Vanish
            if villain.location_index != -1:
                engine.log.append(Col.wrap(" 🌀 TIME MASTER: Kang vanishes into the timestream! ", Col.MAGENTA + Col.BOLD))
                villain.location_index = -1
            
            # Mode 2: Out of play -> Re-appear
            else:
                # Identify Target (Most Heroes). 
                # Since heroes aren't banished here, we don't need location != -1
                loc_counts = [0] * 6
                for h in engine.heroes:
                    if not getattr(h, 'is_ko', False):
                        loc_counts[h.location_index] += 1
                
                target_idx = loc_counts.index(max(loc_counts))
                villain.location_index = target_idx
                
                engine.log.append(Col.wrap(f" ⏳ TIME MASTER: Kang re-emerges at {engine.locations[target_idx].name.upper()}! ", Col.MAGENTA + Col.BOLD))

                # Paradox Restoration
                has_paradox = any(
                    l.threat and not l.threat.cleared and 
                    getattr(l.threat, 'id_internal', getattr(l.threat, 'id', '')) == "time_paradox" 
                    for l in engine.locations
                )
                
                if has_paradox:
                    # 🚨 THE FIX: Use the safely cached max_hp from setup
                    starting_hp = getattr(villain, 'max_hp', villain.hp)
                    
                    if villain.hp < starting_hp:
                        villain.hp = starting_hp
                        engine.log.append(Col.wrap(f"       ⚠️ PARADOX: The timeline resets! Kang restored to {villain.hp} HP. ", Col.CYAN))

                # Final BAM pulse
                KangLogic.on_bam(engine, villain)

                # Final BAM pulse
                KangLogic.on_bam(engine, villain)
