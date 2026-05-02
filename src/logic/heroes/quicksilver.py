from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("quicksilver")
class QuicksilverLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "quicksilver_run_to_the_rescue":
            return QuicksilverLogic._apply_speed_buff(engine, hero, "civilians")
        elif sid == "quicksilver_speed_fighting":
            return QuicksilverLogic._apply_speed_buff(engine, hero, "thugs")
        elif sid == "quicksilver_superhuman_speed":
            return QuicksilverLogic._superhuman_speed(engine, hero)
        return False

    @staticmethod
    def _apply_speed_buff(engine, hero, target_type):
        from src.systems.status_system import StatusSystem
        status_tag = f"auto_rescue_{target_type}"
        StatusSystem.apply_status(hero, status_tag, duration=1)
        
        # Select the correct terminology based on the target type
        verb = "rescue" if target_type == "civilians" else "defeat"
        target_label = "Civilians" if target_type == "civilians" else "Thugs"
        
        engine.log.append(f" [*] PASSIVE: {hero.name} will auto-{verb} {target_label} on arrival!")
        return True

    @staticmethod
    def _superhuman_speed(engine, hero):
        from src.utils.helpers import Col
        print(f"\n{Col.wrap('⚡ SUPERHUMAN SPEED:', Col.CYAN)}")
        print(" [1] Gain ➡ ➡")
        print(" [2] Delay the next Villain turn by 1 card")
        print(" [0] Cancel")
        
        choice = Col.get_choice(" >> ", 0, 2)
        if choice == 0: return False
        
        if choice == 1:
            # Restore speed-focused movement for Quicksilver
            engine.active_pool["move"] = engine.active_pool.get("move", 0) + 2
            engine.log.append(Col.wrap(f" ⚡ {hero.name} accelerates! Gained 2 Move tokens.", Col.CYAN))
        elif choice == 2:
            # 🌟 THE SYNC: Pointing Quicksilver to the universal StatusSystem
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(engine.villain, "delay_turn", duration=1)
            engine.log.append(Col.wrap(f" ⚡ {hero.name} runs circles around the Villain! Turn delayed.", Col.PURP))
            
        return True
