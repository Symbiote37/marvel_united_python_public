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
