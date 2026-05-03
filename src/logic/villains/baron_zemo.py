# src/logic/villains/baron_zemo.py

import random

from src.utils.navigation import BoardNav
from src.utils.helpers import Col, ICON
from src.logic.villains.base_villain import BaseVillainLogic

class ZemoLogic(BaseVillainLogic):
    @staticmethod
    def on_bam(engine, villain):
        """
        Zemo BAM: Surgical Strike + Clockwise Crisis Mark.
        Note: Following the Red Skull pattern, this does NOT call henchmen.
        The EventSystem/DamageSystem handles the 'Who' and 'When' of board triggers.
        """
        # 1. THE QUOTE (Flavor)
        quotes = [
            "An empire toppled by its enemies can rise again.",
            "I am Baron Zemo. I do not repeat my mistakes.",
            "The world is better under my leadership.",
            "Long live the Masters of Evil!"
        ]
        engine.log.append(Col.wrap(f" 👑 ZEMO: '{random.choice(quotes)}'", Col.PURP))

        v_idx = villain.location_index
        heroes_here = [h for h in engine.heroes if h.location_index == v_idx and not h.is_ko]

        # 2. SURGICAL STRIKE (The Exception: 1 Damage to ONE Hero instead of all)
        if heroes_here:
            if len(heroes_here) > 1:
                print(f"\n 🎯 {Col.wrap('ZEMO TARGETING:', Col.RED)} Choose a Hero at {engine.locations[v_idx].name} to take 1 Damage:")
                for i, h in enumerate(heroes_here, 1):
                    print(f" ({i}) {h.name}")
                try:
                    choice = int(input(" >> ") or 1) - 1
                    target = heroes_here[choice]
                except (ValueError, IndexError):
                    target = heroes_here[0]
            else:
                target = heroes_here[0]

            engine.log.append(Col.wrap(f" 💥 Zemo strikes {target.name} for 1 damage.", Col.RED))
            target.take_damage(engine, 1)

        # 3. CLOCKWISE MARK (Seasoning: Crisis Token to closest Hero NOT at his location)
        marked_hero = None
        for dist in range(1, 6):
            search_idx = (v_idx + dist) % 6
            targets_at_dist = [h for h in engine.heroes if h.location_index == search_idx and not h.is_ko]

            if targets_at_dist:
                if len(targets_at_dist) > 1:
                    print(f"\n ⚠️ {Col.wrap('ZEMO MARKING:', Col.PURP)} Closest Heroes found {dist} sectors away. Who receives the Crisis?")
                    for i, h in enumerate(targets_at_dist, 1):
                        print(f" ({i}) {h.name}")
                    try:
                        choice = int(input(" >> ") or 1) - 1
                        marked_hero = targets_at_dist[choice]
                    except (ValueError, IndexError):
                        marked_hero = targets_at_dist[0]
                else:
                    marked_hero = targets_at_dist[0]
                break # Found the closest location with active heroes

        if marked_hero:
            engine.log.append(Col.wrap(f" 🎯 Zemo marks {marked_hero.name} with a Crisis token.", Col.PURP))
            marked_hero.crisis_tokens += 1

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """Zemo Overflow: Information Breach. Marks the nearest Hero clockwise."""
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW at {location.name}!", Col.RED))
        ovr_idx = engine.locations.index(location)

        targets, dist = BoardNav.find_closest_hero(
            engine, ovr_idx, direction="cw", ignore_start_loc=False 
        )

        if targets:
            if len(targets) > 1:
                print(f"\n 🎯 {Col.wrap('ZEMO OVERFLOW TARGETING:', Col.RED)} Choose a Hero to receive the Crisis Token:")
                for i, h in enumerate(targets, 1):
                    print(f" ({i}) {h.name}")
                try:
                    choice = int(input(" >> ") or 1) - 1
                    target = targets[choice]
                except (ValueError, IndexError):
                    target = targets[0]
            else:
                target = targets[0]

            engine.log.append(Col.wrap(f" 🎯 Zemo exploits the chaos! {target.name} receives a Crisis token.", Col.PURP))
            target.crisis_tokens += 1

    @staticmethod
    def resolve_special(engine, villain, card):
        """Standard pipeline for Zemo's Master Plan specials."""
        sid = card.get("special_id")

        if sid == "thunderbolts":
            loc = engine.locations[villain.location_index]
            engine.log.append(Col.wrap(f" 🌩️ THUNDERBOLTS: Reinforcements at {loc.name}!", Col.CYAN))

            for _ in range(3):
                if (loc.thugs + loc.civilians) >= loc.capacity:
                    ZemoLogic.on_overflow(engine, villain, loc, "thugs")
                else:
                    loc.thugs += 1
                    engine.log.append(f"   + Added 1 Thug to {loc.name}.")

            engine.log.append(Col.wrap("  Thunderbolts signal the Master Plan to proceed!", Col.YLW))
            # Trigger the Standard BAM signal (which will include henchmen)
            from src.systems.event_system import EventSystem
            EventSystem.broadcast_bam(engine, full_board=True)

        elif sid == "citizen_v":
            target_idx, max_civs = BoardNav.find_densest_location(engine, villain.location_index, "civilians")
            if target_idx is not None and max_civs > 0:
                target_loc = engine.locations[target_idx]
                villain.location_index = target_idx
                engine.log.append(Col.wrap(f" 🎭 CITIZEN V: Zemo relocates to {target_loc.name} and purges all tokens!", Col.BLU))
                target_loc.thugs = 0
                target_loc.civilians = 0

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        """
        Surgical Threat Resolver:
        Handles unique token effects manually, then delegates standard damage 
        to the BaseVillainLogic patterns.
        """
        hid = getattr(threat, 'id', '')
        loc = engine.locations[loc_idx]

        # 1. HANDLE TOKEN SABOTEURS (Unique Logic)
        if hid == "fixer":
            if loc.civilians > 0:
                loc.civilians -= 1
                engine.log.append(Col.wrap(f" FIXER: Sabotaged 1 Civilian at {loc.name}. ", Col.PURP))

        elif hid == "beetle":
            if loc.thugs > 0:
                loc.thugs -= 1
                engine.log.append(Col.wrap(f" BEETLE: Cleared 1 Thug at {loc.name}. ", Col.PURP))

        # 2. DELEGATE EVERYTHING ELSE
        # This automatically handles Moonstone, Goliath, and Mimi 
        # based on the bam_id in their JSON data.
        else:
            BaseVillainLogic.resolve_threat_bam(engine, threat, loc_idx)

    @staticmethod
    def get_extra_heroic_options(engine, loc, hero):
        """Adds the 'Diplomacy' menu for susceptible Masters of Evil."""
        from src.utils.helpers import ICON
        opts = []

        # Registry for dismissal costs (Moonstone remains excluded)
        DISMISSAL_REGISTRY = {
            "fixer": 2, 
            "beetle": 2, 
            "screaming_mimi": 2, 
            "goliath": 3
        }

        if loc.threat and not loc.threat.cleared:
            cost = DISMISSAL_REGISTRY.get(loc.threat.id)
            if cost:
                opts.append({
                    "label": f"Peaceful Resolution: {loc.threat.name} ({cost} {ICON['heroic']})",
                    "id": f"zemo_dismiss_{loc.threat.id}",
                    "cost": cost, # CRITICAL: We pass the total cost to the ActionSystem
                    "execute": lambda e: ZemoLogic._execute_dismissal(e, loc)
                })
        return opts

    @staticmethod
    def _execute_dismissal(engine, loc):
        """The actual board state change (The Banker already handled the payment)"""
        from src.systems.mission_system import MissionSystem

        loc.threat.cleared = True
        MissionSystem.increment_mission(engine, "threats")
        engine.log.append(Col.wrap(f" 🕊️ DIPLOMACY: {loc.threat.name} has been outmaneuvered!", Col.GRN))
        return True
        
    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Helmut Zemo is a tactical genius who doesn't just want to \n"
                "defeat the Avengers; he wants to humiliate them. He leads \n"
                "the Masters of Evil, focusing on sabotage and disruption."
            ),
            "rules": (
                "\"Tactical Sabotage\"\n"
                "Zemo's primary weapon is the Crisis token. At the end of \n"
                "your turn, any Crisis tokens you hold MUST be used to cover \n"
                "action symbols on the card you just played. \n\n"
                "Covered symbols grant NO actions. This completely severs \n"
                "the team's communication, leaving the next hero with nothing \n"
                "to inherit for their turn."
            ),
            "bam": (
                "\"Collateral Targeting\"\n"
                "Zemo strikes with surgical precision. He deals 1 damage to \n"
                "a single hero in his sector, but the psychological impact \n"
                "ripples outward, immediately placing a Crisis token on the \n"
                "nearest hero to disrupt their upcoming turn."
            ),
            "overflow": (
                "\"Spreading Panic\"\n"
                "When a sector overruns, Zemo capitalizes on the chaos. \n"
                "The hero stationed nearest to the overflowing location is \n"
                "immediately hit with a Crisis token."
            ),
            "threats": (
                "The Masters of Evil have assembled.\n"
                "- Unified Front: While active, no Henchmen can take damage.\n"
                "- The Roster: Beetle, Fixer, Goliath, Moonstone, and Screaming Mimi.\n"
                "- Tactical Weakness: Many of these elites can bypass damage immunity \n"
                "  if you coordinate 2 to 3 Heroic (★) actions in a single turn."
            )
        }
