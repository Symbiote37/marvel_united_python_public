from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("nova")
class NovaLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "nova_i_am_the_help":
            return NovaLogic._i_am_the_help(engine, hero)
        return False

    @staticmethod
    def _i_am_the_help(engine, hero):
        from src.systems.action_system import ActionSystem
        
        loc_idx = hero.location_index
        adj_indices = [(loc_idx - 1) % 6, (loc_idx + 1) % 6]
        
        print(f"\n--- {Col.wrap('🌠 I AM THE HELP: SELECT SECTOR', Col.CYAN + Col.BOLD)} ---")
        for i, idx in enumerate(adj_indices, 1):
            print(f" [{i}] {engine.locations[idx].name}")
        print(" [0] Cancel")
        
        # 🔌 UI ADAPTER: Using the established interface hook
        choice = engine.ui.ask_choice(" >> ", 0, len(adj_indices))
        if choice == 0: return False
        
        target_idx = adj_indices[choice - 1]
        target_loc = engine.locations[target_idx]
        
        engine.log.append(Col.wrap(f" 🌠 Nova beams support to {target_loc.name}!", Col.CYAN + Col.BOLD))
        
        # 🚨 ONE SOURCE OF TRUTH: Delegate to ActionSystem for targeted resolution
        ActionSystem._handle_targeted_heroic(engine, hero, target_idx, amount=2)
        
        return True
 