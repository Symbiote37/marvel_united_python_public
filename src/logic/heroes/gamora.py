from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("gamora")
class GamoraLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "gamora_deadliest_in_the_galaxy":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "deadliest_woman", duration=1)
            engine.log.append(Col.wrap(" 🗡️ DEADLIEST IN THE GALAXY: Spent attack/wild tokens will grant bonus attacks!", Col.GRN))
            return True
        return False
        