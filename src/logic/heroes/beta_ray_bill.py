from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("beta_ray_bill")
class BetaRayBillLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "beta_ray_bill_stormbreaker":
            # 1. Add 2 Attack actions directly to the turn's active pool
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
            
            # 2. Resolve the card draw
            drawn = 0
            if hero.deck:
                hero.hand.append(hero.deck.pop(0))
                drawn = 1
                
            engine.log.append(Col.wrap(f" ⚡ STORMBREAKER: Beta Ray Bill gains +2 ✸ and draws {drawn} card!", Col.CYAN + Col.BOLD))
            return True
            
        return False
