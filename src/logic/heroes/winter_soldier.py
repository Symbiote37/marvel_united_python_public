from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("winter_soldier")
class WinterSoldierLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        # Expert Assassin: Simple, brutal efficiency.
        icon = ICON.get("attack", "✸")
        for _ in range(2):
            hero.add_token(icon)
            
        engine.log.append(Col.wrap(f" 🦾 EXPERT ASSASSIN: {hero.name} prepped 2 {icon} tokens.", Col.RED))
        return True
        