from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("mantis")
class MantisLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "mantis_astral_projection":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "astral_projection", duration=1)
            engine.log.append(Col.wrap(" 🧘‍♀️ ASTRAL PROJECTION: Mantis can interact with any Location this turn!", Col.GRN))
            return True
        elif sid == "mantis_psychic_healing":
            engine.log.append(Col.wrap(" 🧠 PSYCHIC HEALING:", Col.GRN))
            # Helper to pick ally and draw 2
            return True
        elif sid == "mantis_emphatic":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(engine, "cancel_next_bam", duration=1)
            engine.log.append(Col.wrap(" 🧠 EMPATHIC: The next BAM! is cancelled!", Col.GRN))
            return True
        return False
        