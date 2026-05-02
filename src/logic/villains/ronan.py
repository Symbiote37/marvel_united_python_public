# src/logic/villains/ronan.py

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON
from src.utils.navigation import BoardNav

class RonanLogic(BaseVillainLogic):
    """
    RONAN THE ACCUSER:
    Features: Relentless pursuit using "cw"/"ccw" directional hunting.
    Punishes KOs directly via the Plot Track and forces players to choose 
    targets for his heavy BAMs and Overflow penalties.
    """

    @staticmethod
    def handle_movement(engine, villain, card):
        """
        RONAN OVERRIDE: 
        Uses string-based movement ("cw" or "ccw") to hunt targets.
        Standard cards hunt Heroes. Kree-Law hunts empty locations.
        """
        # Accept 'movement' or legacy 'move' key
        move_val = card.get("movement", card.get("move", 0))

        if move_val == 0 or move_val == "0":
            return

        is_cw = BoardNav.parse_direction(move_val)
        sid = card.get("special_id")

        # 1. Kree-Law targets the nearest EMPTY sector
        if sid == "kree_law":
            target_idx, dist = BoardNav.find_nearest_empty_location(engine, villain.location_index, is_cw)
            flavor = "an empty sector"
            
        # 2. Standard Pursuit targets the nearest HERO
        else:
            heroes, dist = BoardNav.find_closest_hero(engine, villain.location_index, is_cw, ignore_start_loc=True)
            if heroes and dist:
                # Calculate the exact index based on distance and direction
                target_idx = (villain.location_index + dist) % 6 if is_cw else (villain.location_index - dist) % 6
                flavor = "the nearest Heroes"
            else:
                target_idx, dist = None, None

        # 3. Execute Movement
        if target_idx is not None:
            villain.location_index = target_idx
            loc_name = engine.locations[villain.location_index].name
            dir_str = "clockwise" if is_cw else "counter-clockwise"
            engine.log.append(Col.wrap(f" Ronan the Accuser moves {dir_str} to {loc_name}! ", Col.MAGENTA))
        else:
            engine.log.append(Col.wrap(" Ronan the Accuser scans the sectors, but finds no valid targets to pursue. ", Col.WHT))

    @staticmethod
    def on_bam(engine, villain):
        """
        RONAN BAM: Deals 2 damage to 1 Hero at his location.
        If multiple Heroes are present, the players must choose the target.
        """
        v_idx = villain.location_index
        if v_idx == -1: return

        heroes_present = [h for h in engine.heroes if h.location_index == v_idx and not h.is_ko]

        if not heroes_present:
            engine.log.append(Col.wrap(" 💥 Ronan slams his Universal Weapon, but no Heroes are present to take the blow! ", Col.RED))
            return

        if len(heroes_present) == 1:
            target = heroes_present[0]
            engine.log.append(Col.wrap(f" 💥 UNIVERSAL WEAPON: Ronan strikes {target.name} with crushing force! ", Col.RED + Col.BOLD))
            # Apply 2 damage (accounting for mid-damage KOs)
            target.take_damage(engine)
            if not target.is_ko: 
                target.take_damage(engine)
        else:
            # INTERACTIVE CHOICE: Multiple Heroes
            engine.log.append(Col.wrap(" 💥 UNIVERSAL WEAPON: Ronan brings the hammer down! ", Col.RED + Col.BOLD))
            print(f"\n {Col.wrap('MULTIPLE TARGETS AT ' + engine.locations[v_idx].name.upper(), Col.BOLD)}")
            for i, h in enumerate(heroes_present):
                print(f"  {i+1}: {h.name} ({len(h.hand)} Cards in Hand)")

            while True:
                try:
                    choice = engine.ui.ask_choice("  Select Hero to take 2 DMG: ", 1, len(heroes_present)) - 1
                    target = heroes_present[choice]
                    target.take_damage(engine)
                    if not target.is_ko: 
                        target.take_damage(engine)
                    break
                except (ValueError, IndexError):
                    print(Col.wrap("  Invalid selection. The Accuser demands an answer! ", Col.RED))

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        RONAN OVERRIDE: Global Overflow Penalty.
        Player must choose 1 Hero anywhere on the board to take 1 Damage.
        """
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: {location.name} is overrun by {token_type}! Ronan demands penance! ", Col.RED))

        active_heroes = [h for h in engine.heroes if not h.is_ko]
        if not active_heroes: return

        if len(active_heroes) == 1:
            target = active_heroes[0]
            engine.log.append(Col.wrap(f"   💥 {target.name} suffers the penalty of the overflow! ", Col.RED))
            target.take_damage(engine)
        else:
            # INTERACTIVE CHOICE: Global target selection
            print(f"\n {Col.wrap('OVERFLOW PENALTY (GLOBAL)', Col.BOLD)}")
            for i, h in enumerate(active_heroes):
                print(f"  {i+1}: {h.name} (Loc: {engine.locations[h.location_index].name})")

            while True:
                try:
                    choice = engine.ui.ask_choice("  Select Hero to take 1 DMG: ", 1, len(active_heroes)) - 1
                    target = active_heroes[choice]
                    engine.log.append(Col.wrap(f"   💥 {target.name} is struck by the Accuser's judgment!", Col.RED))
                    target.take_damage(engine)
                    break
                except (ValueError, IndexError):
                    print(Col.wrap("  Invalid selection.", Col.RED))

    @staticmethod
    def handle_hero_ko(engine, hero):
        """
        RONAN OVERRIDE: 
        1. Process Ronan's unique KO Tokens.
        2. Hand off to Base logic to ensure the BAM is queued!
        """
        v = engine.villain
        v.plot_value = min(v.plot_max, v.plot_value + 1)
        
        # Log the plot progress
        engine.log.append(Col.wrap(f" KO TOKENS: {v.plot_value}/{v.plot_max} ", Col.RED + Col.BOLD))

        if v.plot_value >= v.plot_max:
            engine.game_over = True
            engine.loss_reason = "THE ACCUSER HAS SPOKEN: Ronan collected 4 KO Tokens! "
            return

        # --- THE MISSING LINK ---
        # We must call the Base class version so the 'ko_bam' 
        # actually gets added to engine.queued_events.
        from src.logic.villains.base_villain import BaseVillainLogic
        BaseVillainLogic.handle_hero_ko(engine, hero)

    @staticmethod
    def resolve_special(engine, villain, card):
        """RONAN SPECIALS: Kree-Law and Cosmi-Rod."""
        sid = card.get("special_id")

        if sid == "kree_law":
            engine.log.append(Col.wrap(" 📜 KREE-LAW: Ronan summons the Kree Elite! ", Col.MAGENTA))
            # Add Thug to every location. Use TokenSystem to naturally catch any Overflows.
            from src.systems.token_system import TokenSystem
            overflow_tracker = set()
            for i in range(6):
                TokenSystem.add_token(engine, i, "thugs", overflow_tracker)

        elif sid == "cosmi_rod":
            engine.log.append(Col.wrap(" ⚡ COSMI-ROD: Energy blasts fill the sector! ", Col.MAGENTA))
            v_idx = villain.location_index
            heroes_hit = False
            for h in engine.heroes:
                if h.location_index == v_idx and not h.is_ko:
                    h.take_damage(engine)
                    engine.log.append(Col.wrap(f"       💥 {h.name} is seared by the blast! ", Col.RED))
                    heroes_hit = True

            if not heroes_hit:
                engine.log.append(Col.wrap("       ...But the sector was empty!", Col.WHT))

    @staticmethod
    def get_extra_attack_options(engine, loc, hero):
        opts = []
        if loc.threat and not loc.threat.cleared:
            req = getattr(loc.threat, 'attack_req', 0)
            current = getattr(loc.threat, 'attack_tokens', 0)
            
            if req > 0 and current < req:
                # 🚨 THE FIX: ID is "t_a", no manual execute lambda needed
                opts.append({
                    "label": f"Diffuse {loc.threat.name} (Attack)",
                    "id": "t_a"
                })
        return opts

    @staticmethod
    def get_extra_move_options(engine, loc, hero):
        opts = []
        if loc.threat and not loc.threat.cleared:
            req = getattr(loc.threat, 'move_req', 0)
            current = getattr(loc.threat, 'move_tokens', 0)
            
            if req > 0 and current < req:
                # 🚨 THE FIX: ID is "t_m", no manual execute lambda needed
                opts.append({
                    "label": f"Diffuse {loc.threat.name} (Move)",
                    "id": "t_m"
                })
        return opts
