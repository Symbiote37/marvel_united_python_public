from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class VenomLogic(BaseVillainLogic):
    
    # 🚨 PLOT OVERRIDE: Venom's plot reaching max does NOT instantly end the game
    plot_ends_game = False 

    @staticmethod
    def perform_setup(engine, villain):
        """Sets assimilation thresholds and initializes the 'Void' counter."""
        player_count = len(engine.heroes)
        limit = {2: 8, 3: 6, 4: 4}.get(player_count, 8)
        
        villain.plot_max = limit
        # We'll use this string to show the 'Danger Zone' in the UI
        villain.plot_name = f"SYMBIOTE ASSIMILATION (Limit: {limit}▲)"
        villain.plot_value = 0
        
        engine.log.append(Col.wrap(f" 🦠 WE ARE VENOM. Threshold: {limit} Crisis tokens per Hero.", Col.PURP + Col.BOLD))

    @staticmethod
    def sync_plot(engine):
        """Updates the UI to show highest infection and total casualties."""
        # 1. Find the highest token count among those NOT yet assimilated
        active_tokens = [h.crisis_tokens for h in engine.heroes if not getattr(h, 'is_eliminated', False)]
        
        # 🚨 THE FIX: Match the variable name to 'active_tokens'
        highest = max(active_tokens) if active_tokens else 0
        
        # 2. Count the fallen
        assimilated_count = sum(1 for h in engine.heroes if getattr(h, 'is_eliminated', False))
        total_heroes = len(engine.heroes)
        
        # 3. Update the UI Plot Label and Value
        engine.villain.plot_name = f"ASSIMILATED: {assimilated_count}/{total_heroes} | MAX INFECTION"
        engine.villain.plot_value = highest

    @staticmethod
    def check_assimilation(engine):
        """🚨 THE VOID FIX: Moves assimilated heroes to the void (-1)."""
        limit = engine.villain.plot_max
        for h in engine.heroes:
            if getattr(h, 'crisis_tokens', 0) >= limit and not getattr(h, 'is_eliminated', False):
                h.is_eliminated = True
                # 🕸️ CAPTURED: Send them to the Void.
                h.location_index = -1 
                # Keep their hand/deck intact as per the new ruling.
                engine.log.append(Col.wrap(f" ☠️ ASSIMILATED: {h.name} is pulled into the hive mind!", Col.RED + Col.BOLD))
        
        VenomLogic.sync_plot(engine)
        
        if all(getattr(h, 'is_eliminated', False) for h in engine.heroes):
            from src.systems.event_system import EventSystem
            EventSystem.trigger_defeat(engine, "ALL HEROES HAVE BEEN ASSIMILATED!")

    @staticmethod
    def handle_movement(engine, villain, card):
        move_val = card.get("move", 0)
        if move_val == "cw":
            from src.utils.navigation import BoardNav
            targets, move_dist = BoardNav.find_closest_hero(engine, villain.location_index, direction="cw", ignore_start_loc=True)
            dist = move_dist if move_dist else 0
        else:
            dist = int(move_val)

        if dist > 0:
            villain.location_index = (villain.location_index + dist) % 6
            loc_name = engine.locations[villain.location_index].name
            engine.log.append(f" 🏃 Venom slithers {dist} Locations to {loc_name}!")

    @staticmethod
    def on_bam(engine, villain):
        engine.log.append(Col.wrap(" 💥 BAM! Venom lashes out with Symbiote tendrils!", Col.PURP + Col.BOLD))
        v_idx = villain.location_index
        loc = engine.locations[v_idx]
        
        # Passive threat check: Organic Fangs
        extra_dmg = 0
        if loc.threat and not loc.threat.cleared and getattr(loc.threat, 'id_internal', '') == 'organic_fangs':
            extra_dmg = 1
            engine.log.append(Col.wrap("   ↳ Organic Fangs gnaw deeper (+1 Damage)!", Col.RED))

        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False) and not getattr(h, 'is_eliminated', False)]
        
        if not targets:
            engine.log.append("   ↳ No prey in sight.")
            return

        for h in targets:
            # 1 DMG base, 2 DMG if they are already infected
            base_dmg = 2 if getattr(h, 'crisis_tokens', 0) > 0 else 1
            total_dmg = base_dmg + extra_dmg
            
            engine.log.append(Col.wrap(f"   💥 {h.name} is struck for {total_dmg} damage!", Col.RED))
            for _ in range(total_dmg):
                h.take_damage(engine)
            
            # The infection spreads upon being struck
            h.crisis_tokens = getattr(h, 'crisis_tokens', 0) + 1
            engine.log.append(Col.wrap(f"   🦠 The Symbiote spreads! {h.name} gains 1 Crisis token.", Col.PURP))
        
        VenomLogic.check_assimilation(engine)

    @staticmethod
    def handle_hero_ko(engine, hero):
        engine.log.append(Col.wrap(f" ☠️ {hero.name} falls! Venom accelerates his assimilation.", Col.RED))
        BaseVillainLogic.add_plan_facedown(engine)

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: The streets run black with Symbiote matter at {location.name}!", Col.PURP))
        active_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False) and not getattr(h, 'is_eliminated', False)]
        
        if not active_heroes: return

        if len(active_heroes) == 1:
            target = active_heroes[0]
        else:
            print(f"\n{Col.wrap(' 🦠 OVERFLOW ASSIMILATION:', Col.PURP)} Who gains 1 Crisis token?")
            for i, h in enumerate(active_heroes):
                print(f" ({i+1}) {h.name} (▲: {getattr(h, 'crisis_tokens', 0)})")
            
            # 🚨 HEADLESS FIX
            choice = engine.ui.ask_choice(" >> ", 1, len(active_heroes)) - 1
            target = active_heroes[choice]

        target.crisis_tokens = getattr(target, 'crisis_tokens', 0) + 1
        engine.log.append(Col.wrap(f"   🦠 {target.name} gains 1 Crisis token from the Overflow!", Col.PURP))
        VenomLogic.check_assimilation(engine)

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        if sid == "entangle":
            v_idx = villain.location_index
            targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False) and not getattr(h, 'is_eliminated', False)]
            
            if targets:
                if len(targets) == 1:
                    target = targets[0]
                else:
                    print(f"\n{Col.wrap(' 🕸️ ENTANGLE:', Col.PURP)} Who gets ensnared (1 Crisis token)?")
                    for i, h in enumerate(targets):
                        print(f" ({i+1}) {h.name} (▲: {getattr(h, 'crisis_tokens', 0)})")
                    
                    # 🚨 HEADLESS FIX
                    choice = engine.ui.ask_choice(" >> ", 1, len(targets)) - 1
                    target = targets[choice]
                    
                target.crisis_tokens = getattr(target, 'crisis_tokens', 0) + 1
                engine.log.append(Col.wrap(f"   🕸️ {target.name} is entangled and gains 1 Crisis token!", Col.PURP))
                VenomLogic.check_assimilation(engine)
            else:
                engine.log.append("   ↳ No heroes at Venom's location to entangle.")
            
            from src.systems.event_system import EventSystem
            EventSystem.broadcast_bam(engine)

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        if engine.villain.location_index != loc_idx: return
        
        tid_raw = getattr(threat, 'trigger_id', None) or getattr(threat, 'id_internal', "")
        tid = tid_raw.lower()
        
        if "infect" in tid:
            active_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False) and not getattr(h, 'is_eliminated', False)]
            if not active_heroes: return
            
            engine.log.append(Col.wrap(" 🦠 INFECT: The Symbiote reaches out!", Col.PURP))
            
            if len(active_heroes) == 1:
                target = active_heroes[0]
            else:
                print(f"\n{Col.wrap(' 🦠 INFECT THREAT:', Col.PURP)} Who gains 1 Crisis token?")
                for i, h in enumerate(active_heroes):
                    print(f" ({i+1}) {h.name} (▲: {getattr(h, 'crisis_tokens', 0)})")
                
                # 🚨 HEADLESS FIX
                choice = engine.ui.ask_choice(" >> ", 1, len(active_heroes)) - 1
                target = active_heroes[choice]
                
            target.crisis_tokens = getattr(target, 'crisis_tokens', 0) + 1
            engine.log.append(Col.wrap(f"   ↳ {target.name} gains 1 Crisis token!", Col.PURP))
            VenomLogic.check_assimilation(engine)
