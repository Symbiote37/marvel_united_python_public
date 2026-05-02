from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("daredevil")
class DaredevilLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        from src.systems.status_system import StatusSystem
        
        if sid == "daredevil_radar_sense":
            StatusSystem.apply_status(hero, "radar_sense", duration=1)
            engine.log.append(Col.wrap(" 🦯 RADAR SENSE: Daredevil is tracking the environment.", Col.RED))
            return True
        elif sid == "daredevil_man_without_fear":
            StatusSystem.apply_status(hero, "man_without_fear", duration=1)
            engine.log.append(Col.wrap(" ⚖️ BLIND JUSTICE: Civilians rescued will grant Move tokens.", Col.RED))
            return True
        elif sid == "daredevil_blind_justice":
            StatusSystem.apply_status(hero, "blind_justice", duration=1)
            engine.log.append(Col.wrap(" ⚖️ BLIND JUSTICE: Thugs defeated will grant Move tokens.", Col.RED))
            return True
        return False
        