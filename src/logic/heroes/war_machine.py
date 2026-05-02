from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("war_machine")
class WarMachineLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "war_machine_beam_weapon": return WarMachineLogic._fire_weapon(engine, hero, 1, "Beam Weapon")
        elif sid == "war_machine_rocket_launcher": return WarMachineLogic._fire_weapon(engine, hero, 2, "Rocket Launcher")
        elif sid == "war_machine_strafing_gun": return WarMachineLogic._strafing_gun(engine, hero)
        return False

    @staticmethod
    def _fire_weapon(engine, hero, dmg, name):
        loc_cw = (hero.location_index + 1) % 6
        loc_ccw = (hero.location_index - 1) % 6
        
        prompt = (
            f"\n--- {Col.wrap(f'🚀 {name.upper()}', Col.RED)} ---\n"
            f" [1] Target: {engine.locations[loc_cw].name} (Clockwise)\n"
            f" [2] Target: {engine.locations[loc_ccw].name} (Counter-Clockwise)\n"
            " [0] Cancel\n >> "
        )
        
        choice = engine.ui.ask_choice(prompt, 0, 2)
        if choice == 0: return False
        
        target_idx = loc_cw if choice == 1 else loc_ccw
        engine.log.append(Col.wrap(f" 💥 {hero.name} fires a {name} at {engine.locations[target_idx].name}!", Col.RED))
        
        from src.systems.damage_system import DamageSystem
        return DamageSystem.apply_targeted_damage(engine, hero, target_idx, dmg, name)

    @staticmethod
    def _strafing_gun(engine, hero):
        print(f"\n--- {Col.wrap('🔫 STRAFING GUN', Col.CYAN)} ---")
        if engine.ui.ask_raw(" [1] Execute: Gain ✸✸ and ➡\n [0] Cancel\n >> ", {'0', '1'}) != '1': return False
        
        engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
        engine.active_pool["move"] = engine.active_pool.get("move", 0) + 1
        engine.log.append(Col.wrap(f" 🔫 {hero.name} spins up the Strafing Gun! (+2 ✸, +1 ➡)", Col.CYAN))
        return True
        