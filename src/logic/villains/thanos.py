# [Target: src/logic/villains/thanos.py]
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class ThanosLogic(BaseVillainLogic):
    """
    THANOS: The Mad Titan.
    Features: Hero Replacement on KO, Multi-sector BAMs, and 
    Civilian-to-Thug conversion on Overflows.
    """

    @staticmethod
    def on_bam(engine, villain):
        """
        THANOS BAM: 
        2 Damage to all Heroes at location. 
        1 Damage to all Heroes at adjacent locations.
        """
        v_idx = villain.location_index
        if v_idx == -1: return

        engine.log.append(Col.wrap(" 💥 INFINITY GAUNTLET: Thanos unleashes a cosmic surge!", Col.RED + Col.BOLD))

        # 1. Primary Location (2 Damage)
        BaseVillainLogic._hit_sector(engine, v_idx, 2, "Infinity Surge")

        # 2. Adjacent Locations (1 Damage)
        for offset in [-1, 1]:
            adj_idx = (v_idx + offset) % 6
            BaseVillainLogic._hit_sector(engine, adj_idx, 1, "Gauntlet Shockwave")

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        THANOS OVERFLOW: 
        1. If a Thug can't be added, convert 1 Civilian to a Thug.
        2. If no Civilians exist, queue another Master Plan card.
        """
        if token_type == "thugs":
            if location.civilians > 0:
                location.civilians -= 1
                location.thugs += 1
                engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: Thanos recruits a local at {location.name}! (C ➡ T)", Col.YLW))
                return
        
        # If we reach here, it's either a Civilian overflow or no conversion was possible
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: The destruction at {location.name} fuels the Titan's resolve!", Col.RED))
        
        if not hasattr(engine, 'queued_events'): engine.queued_events = []
        engine.queued_events.append({"type": "extra_card"})


# [Target: src/logic/villains/thanos.py]

    @staticmethod
    def handle_hero_ko(engine, hero):
        """
        THANOS KO RULE:
        1. Increment the Villainous Plot (KO Counter).
        2. Check for game loss (Original Hero Count).
        3. Replace the KO'd hero with a Standby hero.
        """
        v = engine.villain
        v.plot_value += 1
        
        engine.log.append(Col.wrap(f" 💀 {hero.name.upper()} HAS FALLEN!", Col.RED + Col.BOLD))
        engine.log.append(Col.wrap(f" VILLAINOUS PLOT: {v.plot_value}/{getattr(engine, 'starting_hero_count', 2)}", Col.RED))

        # Check Win Condition (Routed through EventSystem for the cinematic banner)
        if v.plot_value >= getattr(engine, 'starting_hero_count', 2):
            from src.systems.event_system import EventSystem
            EventSystem.trigger_defeat(engine, "THE SNAP: Thanos has eliminated the primary resistance!")
            return

        # Replace Hero from Standby Pool
        if hasattr(engine, 'standby_heroes') and engine.standby_heroes:
            new_hero = engine.standby_heroes.pop(0)
            # Transfer location to the replacement
            new_hero.location_index = hero.location_index
            
            # Replace in the active hero list
            idx = engine.heroes.index(hero)
            engine.heroes[idx] = new_hero
            
            engine.log.append(Col.wrap(f" 🛡️ REINFORCEMENTS: {new_hero.name} enters the fray!", Col.GRN))
        else:
            engine.log.append(Col.wrap(" ⚠️ No heroes left on standby!", Col.RED))

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "thanos_mercy":
            engine.log.append(Col.wrap(" ⚖️ THANOS' MERCY: Balancing the sectors...", Col.PURP))
            for offset in [-1, 0, 1]:
                idx = (villain.location_index + offset) % 6
                loc = engine.locations[idx]
                if loc.civilians > 0:
                    loc.civilians -= 1
                    engine.log.append(f"   - Discarded 1 Civilian from {loc.name}.")

        elif sid == "mad_titan":
            engine.log.append(Col.wrap(" ⚡ MAD TITAN: Thanos regenerates and strikes!", Col.RED))
            # Heal up to 5
            old_hp = villain.hp
            villain.hp = min(villain.max_hp, villain.hp + 5)
            engine.log.append(f"   - Thanos healed {villain.hp - old_hp} HP.")
            # Damage at location
            BaseVillainLogic._hit_sector(engine, villain.location_index, 1, "Titan's Wrath")

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        tid = threat.trigger_id
        
        if tid == "corvus_glaive":
            engine.log.append(Col.wrap(" ⚔️ CORVUS GLAIVE: Summoning the vanguard!", Col.YLW))
            from src.systems.token_system import TokenSystem
            
            # --- THE MISSING LINK ---
            # We initialize a set here to track overflows for this specific trigger.
            # This prevents infinite loops if one overflow causes another!
            overflow_tracker = set()
            
            for _ in range(2):
                # Now passing the 4th required argument
                TokenSystem.add_token(engine, loc_idx, "thugs", overflow_tracker)
        
        elif tid == "ebony_maw":
            engine.log.append(Col.wrap(" 🗣️ EBONY MAW: 'Hear me and rejoice!'", Col.CYAN))
            # Maw triggers another card after current one finishes
            if not hasattr(engine, 'queued_events'): engine.queued_events = []
            engine.queued_events.append({"type": "extra_card"})

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        bid = getattr(threat, 'bam_id', "")
        
        if bid == "proxima_midnight":
            loc = engine.locations[loc_idx]
            if loc.civilians > 0:
                engine.log.append(Col.wrap(f" 🔱 PROXIMA MIDNIGHT: Purging {loc.name} of life!", Col.RED))
                loc.civilians = 0
            else:
                engine.log.append(Col.wrap(" 🔱 PROXIMA MIDNIGHT: Hunting the weak...", Col.RED))
                # Target 1 hero anywhere (Player Choice)
                targets = [h for h in engine.heroes if not h.is_ko]
                if targets:
                    print("\n Select a Hero to take 1 Damage from Proxima:")
                    for i, h in enumerate(targets, 1): print(f" ({i}) {h.name}")
                    try:
                        choice = int(input(" >> ") or 1) - 1
                        targets[choice].take_damage(engine)
                    except: targets[0].take_damage(engine)
        else:
            BaseVillainLogic.resolve_threat_bam(engine, threat, loc_idx)
            