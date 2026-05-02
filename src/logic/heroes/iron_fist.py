from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("iron_fist")
class IronFistLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        engine.log.append(Col.wrap(" 🐉 CHI AUGMENTATION: The Iron Fist strikes!", Col.YLW + Col.BOLD))
        # Logic to split 2 damage between current and adjacent
        return True
        