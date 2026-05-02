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
        print(f"\n{Col.wrap('🌠 I AM THE HELP:', Col.CYAN)} Select an adjacent location to receive ★ ★.")
        
        idx_cw = (hero.location_index + 1) % 6
        idx_ccw = (hero.location_index - 1) % 6
        
        loc_cw = engine.locations[idx_cw]
        loc_ccw = engine.locations[idx_ccw]
        
        print(f" [1] {loc_cw.name} (Clockwise)")
        print(f" [2] {loc_ccw.name} (Counter-Clockwise)")
        print(" [0] Cancel")
        
        choice = Col.get_choice(" >> ", 0, 2)
        if choice == 0: return False
        
        target_loc = loc_cw if choice == 1 else loc_ccw
        
        # Inject virtual tokens into the location for the engine to use later
        target_loc.virtual_tokens = getattr(target_loc, 'virtual_tokens', {})
        target_loc.virtual_tokens["heroic"] = target_loc.virtual_tokens.get("heroic", 0) + 2
        
        engine.log.append(Col.wrap(f" 🌠 {hero.name} beams support to {target_loc.name}! (+2 Heroic available there)", Col.CYAN))
        return True
        