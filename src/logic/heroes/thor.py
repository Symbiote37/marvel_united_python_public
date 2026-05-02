# src/logic/heroes/thor.py
from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("thor")
class ThorLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        """The 'Front Door' router."""
        sid = card.get("special_id")
        
        if sid == "thor_mjolnir":
            return ThorLogic._mjolnir(engine, hero)
            
        return False

    @staticmethod
    def _mjolnir(engine, hero):
        from src.systems.action_system import ActionSystem
        from src.utils.helpers import Col
        
        engine.log.append(Col.wrap(f" ⚡ {hero.name} hurls Mjolnir with thunderous force!", Col.RED + Col.BOLD))
        
        # 🚨 ONE SOURCE OF TRUTH: The core engine natively handles the 3-damage burst and overkill!
        return ActionSystem._handle_targeted_attack(engine, hero, hero.location_index, damage=3, burst_mode=True)
