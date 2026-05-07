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
    def handle_hero_ko(engine, hero):
        """KANG OVERRIDE: Hero KO triggers an immediate Master Plan card. """
        # 🚨 THE FIX: Guard against null references from asynchronous state changes
        if not hero or getattr(hero, 'is_ko', False):
            return

        hero.is_ko = True

        engine.log.append(Col.wrap(f" 💀 {hero.name.upper()} IS KO'D! ", Col.RED + Col.BOLD))
        engine.log.append(Col.wrap(" ⏳ TIME LOOP: Kang prepares another card from the timeline! ", Col.MAGENTA))

        # 🚨 ONE SOURCE OF TRUTH: GameEngine natively guarantees queued_events exists.
        engine.queued_events.append({"type": "extra_card"})

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

    @staticmethod
    def broadcast_stance(engine):
        """Warns the player of Kang's temporal shielding. """
        v = engine.villain
        is_shielded, msg = KangLogic.is_villain_shielded(engine, v)

        if is_shielded:
            engine.log.append(Col.wrap(msg.strip(), Col.YLW))

    @staticmethod
    def is_villain_shielded(engine, villain):
        """KANG: Shielded if he is in or adjacent to a Time Hideout. """
        v_idx = villain.location_index
        if v_idx == -1: 
            return True, " ⏳ KANG is beyond time and cannot be targeted! "

        # 1. Identify all locations with an active Time Hideout
        hideout_locations = []
        for i, loc in enumerate(engine.locations):
            if loc.threat and not loc.threat.cleared:
                t_id = getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', None))
                if t_id == "time_hideout":
                    hideout_locations.append(i)

        # 2. Use the "BAM Logic" style for adjacency
        for h_idx in hideout_locations:
            # Epicenter
            if v_idx == h_idx:
                return True, " 🛡️ TIME HIDEOUT: Kang is shielded by the temporal epicenter! "

            # Neighbors (The 1-distance shockwave logic)
            adj = [(h_idx - 1) % 6, (h_idx + 1) % 6]
            if v_idx in adj:
                return True, " 🛡️ TIME HIDEOUT: Kang is shielded by a nearby temporal pocket! "

        return False, ""
