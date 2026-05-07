from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class BlackDwarfLogic(BaseVillainLogic):
    """
    BLACK DWARF: The Unstoppable Tank.
    """

    @staticmethod
    def perform_setup(engine, villain):
        # 🛡️ STATE ARMOR: Initialize mitigation tracking
        villain.dmg_ignored_this_turn = 0
        engine.log.append(Col.wrap(" 🧱 BLACK DWARF stands ready. He will not be moved. ", Col.RED))

    @staticmethod
    def reduce_damage(engine, villain, amount, is_action=False):
        """
        SUPER TOUGH: Pre-damage check. 
        """
        # 🛡️ SAFETY: Use getattr to check for the specific threat
        has_tough = any(
            loc.threat and not loc.threat.cleared and 
            (getattr(loc.threat, 'id_internal', None) or loc.threat.id) == "super_tough"
            for loc in engine.locations
        )

        if has_tough and getattr(villain, 'dmg_ignored_this_turn', 0) == 0:
            villain.dmg_ignored_this_turn = 1
            engine.log.append(Col.wrap(" 🛡️ SUPER TOUGH: The blow gets deflected! ", Col.CYAN))
            return max(0, amount - 1)
            
        return amount

    @staticmethod
    def on_bam(engine, villain, damage=1):
        """
        CHAIN HAMMER: Standard BAM + Adjacent dmg if Chain Hammer is active.
        """
        v_idx = villain.location_index
        if v_idx == -1: return

        # 1. Standard BAM (Handled by Base with our new getattr armor)
        BaseVillainLogic.on_bam(engine, villain, damage)

        # 2. Check for Chain Hammer
        has_hammer = any(
            loc.threat and not loc.threat.cleared and 
            (getattr(loc.threat, 'id_internal', None) or loc.threat.id) == "chain_hammer"
            for loc in engine.locations
        )

        if has_hammer:
            engine.log.append(Col.wrap(" ⛓️ CHAIN HAMMER: The shockwave spreads! ", Col.RED))
            for offset in [-1, 1]:
                adj_idx = (v_idx + offset) % 6
                # 🛡️ ARMOR: Using the hit_sector logic which now uses getattr
                BaseVillainLogic._hit_sector(engine, adj_idx, 1, "Chain Hammer shockwave")

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        BaseVillainLogic.on_overflow(engine, villain, loc, t_type)
        try:
            loc_idx = engine.locations.index(loc)
            BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Overflow Collapse")
        except ValueError:
            pass

    @staticmethod
    def handle_hero_ko(engine, hero):
        """KO: No BAM revenge, just Loki-style facedown pressure."""
        if getattr(hero, 'is_ko', False): return
        hero.is_ko = True
        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} IS KO'D!", Col.RED + Col.BOLD))
        BaseVillainLogic.add_plan_facedown(engine)

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        v_idx = villain.location_index

        if sid == "axe_swing":
            engine.log.append(Col.wrap(" 🪓 AXE SWING: Black Dwarf spins his massive blade!", Col.RED + Col.BOLD))
            for offset in [-1, 0, 1]:
                idx = (v_idx + offset) % 6
                BaseVillainLogic._hit_sector(engine, idx, 1, "Axe Swing")

        elif sid == "healing_factor":
            # 🛡️ SAFETY: Robust HP lookup
            max_hp = getattr(villain, 'max_hp', 10)
            if villain.hp < max_hp:
                heal_amt = min(3, max_hp - villain.hp)
                villain.hp += heal_amt
                engine.log.append(Col.wrap(f" 🧪 HEALING FACTOR: Black Dwarf recovers {heal_amt} HP!", Col.GRN))
            else:
                engine.log.append(Col.wrap(" 🧪 HEALING FACTOR: At full health! Kinetic energy released!", Col.RED))
                BaseVillainLogic._hit_sector(engine, v_idx, 1, "Healing Factor Overload")

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        if (getattr(threat, 'trigger_id', None) or threat.id) == "charge":
            engine.log.append(Col.wrap(f" 🏃 CHARGE: {threat.name} tramples the heroes!", Col.RED))
            BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Charge")

    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Cull Obsidian, aka Black Dwarf, is the heavy muscle of the \n"
                "Black Order. He is an immovable object and an unstoppable \n"
                "force, relying on impenetrable skin and sweeping area attacks."
            ),
            "rules": (
                "\"Relentless Advance\"\n"
                "Black Dwarf doesn't waste time gloating over a fallen hero. \n"
                "If he KOs a hero, he doesn't BAM; instead, he relentlessly \n"
                "accelerates his timeline by playing a Master Plan facedown.\n\n"
                "Watch out for his Master Plan specials: he can swing his axe \n"
                "in a massive arc (hitting adjacent sectors) or use his Healing \n"
                "Factor to recover health (or explode with energy if full!)."
            ),
            "bam": (
                "\"Ground Smash\"\n"
                "A massive localized strike dealing 1 damage to every hero in \n"
                "his current location. However, if his 'Chain Hammer' is active, \n"
                "the shockwave extends to hit both adjacent locations as well."
            ),
            "overflow": (
                "\"Crushing Weight\"\n"
                "When a sector is overrun with Thugs or Civilians, the sheer \n"
                "chaos causes collateral damage. Every hero in the overflowing \n"
                "location immediately takes 1 damage."
            ),
            "threats": (
                "He brings heavy weaponry and impenetrable armor to the field.\n"
                "- Super Tough: He ignores the first point of damage each turn.\n"
                "- Chain Hammer: Upgrades his BAM to hit adjacent locations.\n"
                "- Charge: Tramples heroes, dealing 1 damage when triggered."
            )
        }
