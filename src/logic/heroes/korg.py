from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("korg")
class KorgLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "korg_kronan_fighter":
            return KorgLogic._kronan_fighter(engine, hero)
        return False

    @staticmethod
    def _kronan_fighter(engine, hero):
        prompt = (
            f"\n--- {Col.wrap('🪨 KRONAN FIGHTER', Col.YLW)} ---\n"
            " [1] Execute: ✸✸ in current Location\n"
            " [2] Execute: ✸ in both adjacent Locations\n"
            " [0] Cancel\n >> "
        )
        choice = engine.ui.ask_choice(prompt, 0, 2)
        if choice == 0: return False
        
        if choice == 1:
            engine.log.append(Col.wrap(f" 🪨 {hero.name} smashes the ground! (+2 ✸)", Col.YLW))
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
            return True
            
        elif choice == 2:
            engine.log.append(Col.wrap(f" 🪨 {hero.name} swings wide!", Col.YLW))
            loc_cw = (hero.location_index + 1) % 6
            loc_ccw = (hero.location_index - 1) % 6
            
            from src.systems.damage_system import DamageSystem
            DamageSystem.apply_targeted_damage(engine, hero, loc_cw, 1, "Kronan Fighter (CW)")
            DamageSystem.apply_targeted_damage(engine, hero, loc_ccw, 1, "Kronan Fighter (CCW)")
            return True
