from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("captain_marvel")
class CaptainMarvelLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        from src.systems.action_system import ActionSystem
        
        # 1. Sector Selection (Current vs Adjacent)
        loc_idx = hero.location_index
        adj_indices = [(loc_idx - 1) % 6, (loc_idx + 1) % 6]
        valid_adj = [i for i in adj_indices if not getattr(engine.locations[i], 'is_destroyed', False)]
        
        if not valid_adj:
            print(Col.wrap(" ! No adjacent sectors found for Photon Blast.", Col.RED))
            return False

        print(f"\n--- {Col.wrap('PHOTON BLAST: SELECT SECTOR', Col.CYAN + Col.BOLD)} ---")
        for i, idx in enumerate(valid_adj, 1):
            print(f" [{i}] {engine.locations[idx].name}")
        print(" [0] Cancel")
        
        # 🔌 UI ADAPTER: Updated to use your new interface hook
        choice = engine.ui.ask_choice(" >> ", 0, len(valid_adj))
        if choice == 0: return False
        
        target_idx = valid_adj[choice - 1]
        target_loc = engine.locations[target_idx]

        engine.log.append(Col.wrap(f" ✨ PHOTON BLAST focused on {target_loc.name}!", Col.CYAN + Col.BOLD))

        # 🚨 ONE SOURCE OF TRUTH: The core engine natively handles the 2-damage split pool!
        ActionSystem._handle_targeted_attack(engine, hero, target_idx, damage=2, burst_mode=False)
        
        return True
