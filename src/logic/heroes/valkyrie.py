from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("valkyrie")
class ValkyrieLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "valkyrie_warsong":
            return ValkyrieLogic._warsong(engine, hero)
        return False

    @staticmethod
    def _warsong(engine, hero):
        print(f"\n--- {Col.wrap('🐎 WARSONG', Col.CYAN)} ---")
        for i, loc in enumerate(engine.locations):
            marker = " (Current)" if i == hero.location_index else ""
            print(f" [{i+1}] Move to {loc.name}{marker}")
        print(" [0] Cancel")
        
        choice = Col.get_choice(" >> ", 0, 6)
        if choice == 0: return False
        
        loc_idx = choice - 1
        hero.location_index = loc_idx
        engine.log.append(Col.wrap(f" 🐎 {hero.name} rides her winged steed to {engine.locations[loc_idx].name}!", Col.CYAN))
        return True
        