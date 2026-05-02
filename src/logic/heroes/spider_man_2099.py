from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("spider-man_2099")
class SpiderMan2099Logic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "spider-man_2099_lyla_assistance":
            from src.systems.action_system import ActionSystem
            print(f"\n--- {Col.wrap('LYLA: SELECT HEROIC SECTOR', Col.CYAN)} ---")
            for i, loc in enumerate(engine.locations, 1): print(f" [{i}] {loc.name}")
            c = Col.get_choice(" >> ", 1, 6) - 1
            
            engine.log.append(Col.wrap(f" 💻 LYLA ASSISTANCE: 2099 triggers a Heroic Action remotely!", Col.CYAN))
            # Temporarily trick the action system into using this location
            original_loc = hero.location_index
            hero.location_index = c
            engine.active_pool["heroic"] = engine.active_pool.get("heroic", 0) + 1
            ActionSystem._handle_heroic(engine, hero)
            hero.location_index = original_loc # Revert
            return True
            
        elif sid == "invulnerability":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "invulnerable", duration=1)
            engine.log.append(Col.wrap(" 🕸️ ENHANCED SENSES: 2099 is invulnerable until his next turn!", Col.BLU))
            return True
            
        elif sid == "spider-man_2099_claws":
            from src.systems.action_system import ActionSystem
            from src.systems.status_system import StatusSystem
            
            # 🚨 THE FIX: Change add_status back to apply_status
            StatusSystem.apply_status(hero, "unreducible_damage", duration=1)
            
            engine.log.append(Col.wrap(" 🩸 CLAWS: 2099 strikes with paralyzing venom!", Col.BLU))
            ActionSystem._handle_targeted_attack(engine, hero, hero.location_index, hits=2)
            return True        