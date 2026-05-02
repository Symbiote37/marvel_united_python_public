from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("spider-woman")
class SpiderWomanLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "spider-woman_poison_blast":
            return SpiderWomanLogic._poison_blast(engine, hero)
        return False

    @staticmethod
    def _poison_blast(engine, hero):
        print(f"\n{Col.wrap('🕷️ POISON BLAST:', Col.CYAN)}")
        print(" [1] Gain ✸ ✸")
        print(" [2] Delay the next Villain turn by 1 card")
        print(" [0] Cancel")
        
        choice = Col.get_choice(" >> ", 0, 2)
        if choice == 0: return False
        
        if choice == 1:
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
            engine.log.append(Col.wrap(f" 🕷️ {hero.name} gathers venom! Gained 2 Attack tokens.", Col.CYAN))
        elif choice == 2:
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(engine.villain, "delay_turn", duration=1)
            engine.log.append(Col.wrap(f" 🕷️ {hero.name} poisons the Villain! Their next turn is delayed.", Col.PURP))
            
        return True
        