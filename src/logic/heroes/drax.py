from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("drax")
class DraxLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "drax_revenge":
            from src.systems.action_system import ActionSystem
            engine.log.append(Col.wrap(" 🗡️ REVENGE: Drax seeks a target!", Col.GRN + Col.BOLD))
            
            curr = hero.location_index
            for _ in range(6):
                curr = (curr + 1) % 6
                loc = engine.locations[curr]
                
                # Check for enemies
                has_enemies = loc.thugs > 0
                if not has_enemies and loc.threat and not loc.threat.cleared and getattr(loc.threat, 'hp', 0) > 0:
                     from src.logic.shield_logic import is_target_vulnerable
                     if is_target_vulnerable(engine, loc.threat)[0]: has_enemies = True
                
                if not has_enemies:
                    from src.systems.villain_system import VillainSystem
                    if VillainSystem.get_attackable_villains_at(engine, curr): has_enemies = True
                
                if has_enemies:
                    hero.location_index = curr
                    engine.log.append(f"   Drax moved to {loc.name}!")
                    ActionSystem._handle_targeted_attack(engine, hero, curr)
                    return True
            
            engine.log.append("   But there were no enemies left to fight!")
            return True
        return False
        