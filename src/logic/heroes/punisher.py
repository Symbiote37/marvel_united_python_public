from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("punisher")
class PunisherLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        from src.systems.action_system import ActionSystem
        
        if sid == "punisher_special_ops_training":
            # 1. THE REPOSITION
            print(f"\n--- {Col.wrap('SPECIAL OPS: SELECT DESTINATION', Col.CYAN + Col.BOLD)} ---")
            for i, loc in enumerate(engine.locations, 1): 
                print(f" [{i}] {loc.name}")
            
            choice = Col.get_choice(" >> ", 1, 6)
            hero.location_index = choice - 1
            
            engine.log.append(Col.wrap(f" 🎯 SPECIAL OPS: Punisher breached {engine.locations[hero.location_index].name}!", Col.RED + Col.BOLD))

            # 2. THE ENGAGEMENT (Resolved immediately at the new location)
            for i in range(2):
                print(f"\n {Col.wrap(f'STRIKE {i+1}/2', Col.YLW)}")
                # This helper automatically prompts for Thugs/Threats/Villains at the current index
                ActionSystem._handle_targeted_attack(engine, hero, hero.location_index)
                
            return True

        elif sid == "punisher_heavy_firepower":
            print(f"\n--- {Col.wrap('HEAVY FIREPOWER: TARGET SECTOR', Col.RED)} ---")
            for i, loc in enumerate(engine.locations, 1): print(f" [{i}] {loc.name}")
            c = Col.get_choice(" >> ", 1, 6) - 1
            
            engine.log.append(Col.wrap(f" 💥 HEAVY FIREPOWER unloaded on {engine.locations[c].name} and adjacent Locations! ", Col.RED + Col.BOLD))
            for _ in range(2): ActionSystem._handle_targeted_attack(engine, hero, c) # 2 in target
            ActionSystem._handle_targeted_attack(engine, hero, (c - 1) % 6) # 1 Left
            ActionSystem._handle_targeted_attack(engine, hero, (c + 1) % 6) # 1 Right
            return True
            
        elif sid == "punisher_precision_shot":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "unreducible_damage", duration=1)
            engine.log.append(Col.wrap(f" 💀 PRECISION SHOT: Punisher takes aim. Damage cannot be reduced! ", Col.RED + Col.BOLD))
            for _ in range(4):
                ActionSystem._handle_targeted_attack(engine, hero, hero.location_index)
            return True
        return False
        