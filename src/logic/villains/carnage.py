# [Target: src/logic/villains/carnage.py]
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class CarnageLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "SPAWN TRACK"
        villain.plot_max = 10
        villain.plot_value = 0
        engine.log.append(Col.wrap(" 🩸 CARNAGE: 'I am the ultimate freedom!'", Col.RED + Col.BOLD))

    @staticmethod
    def handle_movement(engine, villain, card):
        """Supports standard integer moves and Carnage's 'cw' (Clockwise) cards."""
        move = card.get("move", 0)
        if move == "cw":
            move = 1

        if isinstance(move, int) and move > 0:
            villain.location_index = (villain.location_index + move) % 6
            loc_name = engine.locations[villain.location_index].name
            engine.log.append(f" 🏃 {villain.name} moves to {loc_name}.")

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return
        loc = engine.locations[v_idx]

        engine.log.append(Col.wrap(f" 🔪 CARNAGE BAM: Chaos at {loc.name}!", Col.RED))

        # 1. Infection: Direct conversion between Location properties
        if loc.civilians > 0:
            loc.civilians -= 1
            loc.infected += 1
            engine.log.append(Col.wrap(f"   ⚠️ A Civilian has been INFECTED! {ICON['infected']}", Col.YLW))

        # 2. Damage: Hits current location via Base Logic
        BaseVillainLogic.on_bam(engine, villain, damage=damage)

    @staticmethod
    def handle_hero_ko(engine, hero):
        """Carnage advances Plot when a Hero falls."""
        engine.villain.plot_value += 1
        engine.log.append(Col.wrap("   📈 SPAWN TRACK advances from Hero KO!", Col.RED))
        BaseVillainLogic.handle_hero_ko(engine, hero)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """
        🚨 REFINED OVERFLOW: Only infected Δ advance the Spawn Track.
        Healthy civilians and Thugs are discarded with no penalty.
        """
        if loc.infected > 0:
            count = loc.infected
            loc.infected = 0 # Accountability: Souls consumed
            villain.plot_value += count
            engine.log.append(Col.wrap(f" 🩸 SPAWN OVERFLOW: {count} civilians consumed!", Col.RED + Col.BOLD))

        # If no infected are present, the overflow is ignored. 
        # No plot advance, no log entry.

    @staticmethod
    def resolve_special(engine, villain, card):
        if card.get("special_id") == "spawn_of_evil":
            # 1. Move to densest healthy sector
            target_idx = 0
            max_c = -1
            for i, loc in enumerate(engine.locations):
                if loc.civilians > max_c:
                    max_c = loc.civilians
                    target_idx = i

            villain.location_index = target_idx
            engine.log.append(Col.wrap(f" 🏃 Carnage moves to the densest Location: {engine.locations[target_idx].name}!", Col.RED))

            # 2. Effect: Add 1 C to every Location (Now using standard capacity check)
            for loc in engine.locations:
                if not loc.is_full:
                    loc.civilians += 1
                else:
                    CarnageLogic.on_overflow(engine, villain, loc, "civilians")

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        t_id = (getattr(threat, 'id_internal', None) or getattr(threat, 'id', "")).lower()

        if t_id == "carnage_offspring":
            loc = engine.locations[loc_idx]
            # 1. Infect
            if loc.civilians > 0:
                loc.civilians -= 1
                loc.infected += 1
                engine.log.append(Col.wrap(f"   ⚠️ {threat.name} at {loc.name} infects a Civilian!", Col.YLW))

            # 2. Spawn (Using standard capacity check)
            if not loc.is_full:
                loc.civilians += 1
            else:
                CarnageLogic.on_overflow(engine, engine.villain, loc, "civilians")

            # 3. Damage
            BaseVillainLogic._hit_sector(engine, loc_idx, 1, f"{threat.name}'s frenzy")
        else:
            BaseVillainLogic.resolve_threat_bam(engine, threat, loc_idx)

    @staticmethod
    def get_heroic_options(engine, hero):
        """Injects the 'Rescue Infected' option."""
        loc = engine.locations[hero.location_index]
        opts = BaseVillainLogic.get_heroic_options(engine, hero)

        if loc.infected > 0:
            opts.append({
                "label": f"Rescue Infected ({loc.infected})",
                "id": "ci",
                "execute": lambda e: CarnageLogic._execute_infected_rescue(e, loc)
            })

        # Apply Heroic Trap cost penalties
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', None) or getattr(loc.threat, 'id', "")).lower()
            if t_id == "heroic_trap":
                for opt in opts:
                    if opt['id'] in ['c', 'ci']:
                        opt['cost'] = 2
                        opt['label'] += " [COST: 2★]"
        return opts

    @staticmethod
    def _execute_infected_rescue(engine, loc):
        from src.systems.mission_system import MissionSystem
        loc.infected -= 1
        MissionSystem.increment_mission(engine, "civilians")
        engine.log.append(Col.wrap(f" 💉 Infected Civilian Rescued! {ICON['infected']}", Col.GRN))
        return True

    @staticmethod
    def on_civilians_flee(engine, loc):
        """Carnage override: Everyone runs (Infected + Healthy)."""
        total = loc.civilians + loc.infected
        if total > 0:
            loc.civilians = 0
            loc.infected = 0
            engine.log.append(Col.wrap(f" 💨 {total} inhabitants fled the scene!", Col.YLW))
            
    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Cletus Kasady and the Carnage symbiote are a match made in \n"
                "hell. He doesn't just kill; he spreads a parasitic infection \n"
                "that turns the city's population into fuel for his 'Spawn Track'."
            ),
            "rules": (
                "\"The Spawn Track\"\n"
                "Carnage is playing for a total victory condition. Every time \n"
                "a hero is KO'd, or an infected civilian is consumed by an \n"
                "overflow, his Spawn Track advances. If it reaches 10, the \n"
                "symbiote takeover is complete and the mission is lost."
            ),
            "bam": (
                "\"Contagion Strike\"\n"
                "Carnage deals 1 damage to every hero in his sector. More \n"
                "dangerously, he infects the local population. Healthy \n"
                "civilians are converted into Infected units (marked with \n"
                "Crisis tokens), setting them up for his harvest."
            ),
            "overflow": (
                "\"The Harvest\"\n"
                "Normal overflows are manageable, but a Carnage overflow is \n"
                "lethal. If a location overflows, all INFECTED civilians \n"
                "there are consumed, each one advancing the Spawn Track by 1. \n"
                "Keep the locations clear or keep them healthy."
            ),
            "threats": (
                "His offspring and ambush tactics make rescue nearly impossible.\n"
                "- Carnage Offspring: These entities infect, spawn, and attack \n"
                "  simultaneously during a BAM.\n"
                "- Symbiote Ambush: Thick webbing and chaos mean it takes \n"
                "  double the Heroic effort (2 ★) to rescue any civilian."
            )
        }
