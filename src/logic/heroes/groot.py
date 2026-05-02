from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("groot")
class GrootLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        # Implementation of moving allies or drawing cards with allies
        return True
        