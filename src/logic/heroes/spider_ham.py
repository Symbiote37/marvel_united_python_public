from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("spider-ham")
class SpiderHamLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "spider-ham_toony_web":
            return SpiderHamLogic._toony_web(engine, hero)
        elif sid == "spider-ham_toony_essence":
            return SpiderHamLogic._toony_essence(engine, hero)
        elif sid == "spider-ham_toony_weapon":
            return SpiderHamLogic._toony_weapon(engine, hero)
        return False

    @staticmethod
    def _toony_web(engine, hero):
        from src.systems.status_system import StatusSystem
        StatusSystem.apply_status(engine.villain, "negate_movement", duration=1)
        engine.log.append(f" [*] PASSIVE: {hero.name} readies a trap for the Villain!")
        return True

    @staticmethod
    def _toony_essence(engine, hero):
        hero.protect_last_card = True
        engine.log.append(Col.wrap(f" 🐷 PASSIVE: {hero.name} cannot be forced to discard their last card!", Col.CYAN))
        return True

    @staticmethod
    def _toony_weapon(engine, hero):
        print(f"\n{Col.wrap('🔨 TOONY WEAPON:', Col.CYAN)} Deal 1 damage anywhere.")
        
        # Build target list similar to standard attack logic, but ignoring location distance
        # ... (Implementation details depend on your VillainSystem targeting)
        engine.log.append(Col.wrap(f" 🔨 {hero.name} drops an anvil from the sky!", Col.CYAN))
        return True
        