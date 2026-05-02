from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("venom")
class VenomLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "venom_symbiote_enhancement":
            engine.active_pool["move"] = engine.active_pool.get("move", 0) + 1
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 1
            engine.log.append(Col.wrap(" 🕷️ SYMBIOTE ENHANCEMENT: (+➡ +✸)", Col.BLU))
            return True
        elif sid == "venom_tracking":
            print(f"\n--- {Col.wrap('TRACKING: SELECT DESTINATION', Col.CYAN)} ---")
            for i, loc in enumerate(engine.locations, 1): print(f" [{i}] {loc.name}")
            c = Col.get_choice(" >> ", 1, 6) - 1
            hero.location_index = c
            engine.log.append(Col.wrap(f" 🕷️ TRACKING: Venom hunted down {engine.locations[c].name}! (+✸)", Col.BLU))
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 1
            return True
        return False
        