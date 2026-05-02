from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("america_chavez")
class AmericaChavezLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "america_chavez_star_portal":
            return AmericaChavezLogic._star_portal(engine, hero)
        elif sid == "america_chavez_energy_infusion":
            return AmericaChavezLogic._energy_infusion(engine, hero)
        return False

    @staticmethod
    def _star_portal(engine, hero):
        engine.active_pool["wild"] = engine.active_pool.get("wild", 0) + 2
        engine.log.append(Col.wrap(f" ⭐ STAR PORTAL: {hero.name} opens a Star Portal! (+2 ❖) ", Col.CYAN))
        return True

    @staticmethod
    def _energy_infusion(engine, hero):
        engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
        engine.log.append(Col.wrap(f" ⭐ ENERGY INFUSION: {hero.name} surges with cosmic energy! (+2 ✸) ", Col.CYAN))
        return True
        