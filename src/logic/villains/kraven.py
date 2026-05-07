# src/logic/villains/kraven.py
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class KravenLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "THE HUNT"
        villain.plot_max = 0 # No token limit, purely a state check
        villain.plot_value = 0

        # Initialize crisis tokens on heroes
        for h in engine.heroes:
            h.crisis_tokens = 0

        engine.log.append(Col.wrap(" 🐅 KRAVEN: 'The hunt begins. You are all prey!'", Col.RED + Col.BOLD))

    # --- KO REPLACEMENT (THE ENDLESS HUNT) ---
    @staticmethod
    def handle_hero_ko(engine, hero):
        """Kraven does not BAM on KOs. He accelerates the Master Plan."""
        if getattr(hero, 'is_ko', False):
            return

        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} HAS FALLEN!", Col.RED + Col.BOLD))
        hero.is_ko = True 

        # Win Condition Check: Are ALL heroes KO'd simultaneously?
        all_ko = all(getattr(h, 'is_ko', False) for h in engine.heroes)
        if all_ko:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "THE HUNT: Kraven has defeated all heroes simultaneously!"
            return

        # Queue an Extra Card instead of a KO BAM
        if hasattr(engine, 'queued_events'):
            engine.queued_events.append({"type": "extra_card"})
            engine.log.append(Col.wrap(" 🐅 KRAVEN'S HUNT: The scent of blood draws him faster! (+1 Master Plan)", Col.PURP))

    # --- MOVEMENT OVERRIDE ---
    @staticmethod
    def handle_movement(engine, villain, card):
        move = card.get("move", 0)

        if move == "cw":
            # Track to the nearest clockwise location with any standing hero
            curr = villain.location_index
            standing_hero_locations = {h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)}
            for i in range(1, 7):
                check_idx = (curr + i) % 6
                if check_idx in standing_hero_locations:
                    villain.location_index = check_idx
                    engine.log.append(Col.wrap(f" 🏃 KRAVEN tracks his prey to {engine.locations[check_idx].name}!", Col.PURP))
                    return

            engine.log.append(Col.wrap(" 🏃 KRAVEN finds no standing prey and waits.", Col.DARK_GRAY))
        else:
            # Standard movement for numerical values
            BaseVillainLogic.handle_movement(engine, villain, card)

    # --- SPECIAL CARDS ---
    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")

        if sid == "obstinate_hunt":
            v_idx = villain.location_index
            targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]

            if targets:
                target = targets[0]
                if len(targets) > 1:
                    print(Col.wrap(f"\n 🎯 OBSTINATE HUNT: Choose a hero at {engine.locations[v_idx].name} to take a Crisis token:", Col.PURP))
                    for i, h in enumerate(targets, 1):
                        print(f" ({i}) {h.name} (Crisis: {getattr(h, 'crisis_tokens', 0)})")
                    choice = Col.get_choice(" Choose >> ", 1, len(targets))
                    target = targets[choice - 1]

                target.crisis_tokens = getattr(target, 'crisis_tokens', 0) + 1
                engine.log.append(Col.wrap(f"   🎯 {target.name} is marked as prey! (Crisis Tokens: {target.crisis_tokens})", Col.YLW))
            else:
                engine.log.append(Col.wrap("   🛡️ No standing heroes in Kraven's Location to mark.", Col.GRN))

            # "Then BAM!"
            from src.systems.event_system import EventSystem
            EventSystem.broadcast_bam(engine)

    # --- DAMAGE APPLICATION (WITH TRAPS) ---
    @staticmethod
    def deal_kraven_damage(engine, hero, dmg, src, loc):
        """Wrapper to apply damage so we can calculate the Traps threat."""
        actual_dmg = dmg

        # 🚨 STATE ARMOR: Safely extract ID to prevent AttributeError
        t_id = (getattr(loc.threat, 'id_internal', '') or getattr(loc.threat, 'id', '')).lower() if loc.threat else ""
        if loc.threat and not loc.threat.cleared and "traps" in t_id:
            if loc.civilians == 0 and loc.thugs == 0:
                actual_dmg += 1
                engine.log.append(Col.wrap(f"   🪤 TRAP SPRUNG! {hero.name} takes +1 damage from the empty environment!", Col.YLW))

        engine.log.append(Col.wrap(f"   🎯 {src} hits {hero.name}!", Col.RED))
        for _ in range(actual_dmg):
            hero.take_damage(engine)

    # --- BAM RESOLUTION ---
    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return
        v_loc = engine.locations[v_idx]

        # 1. Standard damage to heroes at his location
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        if not targets:
            engine.log.append(Col.wrap(f"   💥 BAM! Kraven strikes {v_loc.name} but misses!", Col.RED))
        else:
            engine.log.append(Col.wrap(f"   💥 BAM! Kraven strikes {v_loc.name}!", Col.RED + Col.BOLD))
            for h in targets:
                KravenLogic.deal_kraven_damage(engine, h, damage, "Kraven's blade", v_loc)

        # 2. Crisis Damage (Across the entire board)
        marked_heroes = [h for h in engine.heroes if getattr(h, 'crisis_tokens', 0) > 0 and not getattr(h, 'is_ko', False)]
        if marked_heroes:
            target = marked_heroes[0]
            if len(marked_heroes) > 1:
                print(Col.wrap("\n ⚠️ KRAVEN'S PREY: Choose a marked hero to suffer Crisis damage:", Col.PURP))
                for i, h in enumerate(marked_heroes, 1):
                    print(f" ({i}) {h.name} ({h.crisis_tokens} Crisis Tokens)")
                choice = Col.get_choice(" Choose >> ", 1, len(marked_heroes))
                target = marked_heroes[choice - 1]

            dmg = target.crisis_tokens
            engine.log.append(Col.wrap(f"   🎯 Kraven exploits {target.name}'s weakness!", Col.RED + Col.BOLD))
            loc = engine.locations[target.location_index]
            KravenLogic.deal_kraven_damage(engine, target, dmg, "Kraven's hunt", loc)

    # --- OVERFLOW RESOLUTION ---
    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        engine.log.append(Col.wrap(f"   ! OVERFLOW: {loc.name} cap exceeded by {t_type}!", Col.RED))

        valid_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False)]
        if not valid_heroes: return

        target = valid_heroes[0]
        if len(valid_heroes) > 1:
            print(Col.wrap(f"\n ⚠️ OVERFLOW AT {loc.name}: Choose a hero to take 1 damage:", Col.PURP))
            for i, h in enumerate(valid_heroes, 1):
                print(f" ({i}) {h.name} (Cards: {len(h.hand)})")
            choice = Col.get_choice(" Choose >> ", 1, len(valid_heroes))
            target = valid_heroes[choice - 1]

        loc_hero = engine.locations[target.location_index]
        KravenLogic.deal_kraven_damage(engine, target, 1, "Overflow panic", loc_hero)

    # --- THREAT DEFENSE (DECOYS) ---
    @staticmethod
    def reduce_damage(engine, target_obj, amount, is_action=False):
        """Hook called when Kraven is attacked to calculate Decoy mitigation."""
        # Safeguard: Ensure we are only modifying damage intended for the boss
        if target_obj != engine.villain:
            return amount

        loc = engine.locations[target_obj.location_index]

        # Check if the Decoy threat is active in Kraven's CURRENT location
        # 🚨 STATE ARMOR: Safely extract ID to prevent AttributeError
        t_id = (getattr(loc.threat, 'id_internal', '') or getattr(loc.threat, 'id', '')).lower() if loc.threat else ""
        if loc.threat and not loc.threat.cleared and "decoys" in t_id:
            # Only absorb if no damage has been ignored yet this turn
            if amount > 0 and getattr(target_obj, 'dmg_ignored_this_turn', 0) == 0:
                target_obj.dmg_ignored_this_turn = 1
                engine.log.append(Col.wrap("   🎭 DECOY: Kraven's decoy absorbs the first blow this turn! ", Col.YLW))
                return amount - 1

        return amount