from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("falcon")
class FalconLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "falcon_air_strike": 
            return FalconLogic._air_strike(engine, hero)
        return False

    @staticmethod
    def _air_strike(engine, hero):
        prompt_lines = [f"\n--- {Col.wrap('🦅 AIR STRIKE', Col.CYAN)} ---"]
        for i, loc in enumerate(engine.locations):
            marker = " (Current)" if i == hero.location_index else ""
            prompt_lines.append(f" [{i+1}] Move to {loc.name}{marker} and deal 1 ✸")
        prompt_lines.append(" [0] Cancel\n >> ")
        
        choice = engine.ui.ask_choice("\n".join(prompt_lines), 0, 6)
        if choice == 0: return False
        
        loc_idx = choice - 1
        hero.location_index = loc_idx
        engine.log.append(Col.wrap(f" 🦅 {hero.name} swoops into {engine.locations[loc_idx].name} for an Air Strike!", Col.CYAN))
        
        from src.systems.damage_system import DamageSystem
        return DamageSystem.apply_targeted_damage(engine, hero, loc_idx, 1, "Air Strike")
