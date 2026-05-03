from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("gamora")
class GamoraLogic:
    
    @staticmethod
    def resolve_special(engine, hero, card):
        """Triggered when Gamora actually plays her Special Card into the Storyline."""
        sid = card.get("special_id", "")
        
        # Check for her specific card ID (Swap this string if yours is named differently!)
        if sid == "gamora_deadliest_in_the_galaxy":
            from src.systems.status_system import StatusSystem
            
            # Apply the buff for 1 turn using your existing StatusSystem
            StatusSystem.apply_status(hero, "deadliest_woman", duration=1)
            
            engine.log.append(Col.wrap(f" ⚔️ {hero.name.upper()} is primed for lethal strikes this turn!", Col.PURP))
            return True
            
        return False

    @staticmethod
    def on_token_used(engine, hero, **kwargs):
        """Listens for the generic broadcast from the TokenSystem."""
        from src.systems.status_system import StatusSystem
        
        token_type = kwargs.get("token_type")
        
        # Check if she spent an Attack OR Wild token AND has the buff active
        if token_type in ["attack", "wild"] and StatusSystem.has_status(hero, "deadliest_woman"):
            engine.log.append(Col.wrap(f" ⚔️ THE DEADLIEST WOMAN: {hero.name} launches a bonus strike!", Col.PURP + Col.BOLD))
            
            # Always inject an attack symbol, even if the trigger was a wild token
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 1

            # Consume the status so it only fires once per sequence
            StatusSystem.decrement_status(hero, "deadliest_woman")
