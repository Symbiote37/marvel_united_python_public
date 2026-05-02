from src.utils.helpers import Col

class MissionSystem:
    @staticmethod
    def increment_mission(engine, key):
        """
        Standardized mission progress with Villain Interception check.
        Returns True if the progress was accepted, False if blocked by the Villain.
        """
        # 👔 PRIORITY 1: Check with Villain logic FIRST.
        if hasattr(engine.villain_logic, 'can_increment_mission'):
            if not engine.villain_logic.can_increment_mission(engine, key):
                return False # 🚨 BLOCK SIGNAL: Trigger flavor text and exit

        # 1. Early exit if the mission is already capped
        already_complete = (engine.missions[key] >= engine.missions[f"{key}_max"])
        if already_complete:
            return True 

        # 2. Proceed with increment
        engine.missions[key] = min(engine.missions[f"{key}_max"], engine.missions[key] + 1)
        
        # 3. Handle completion triggers
        if engine.missions[key] == engine.missions[f"{key}_max"]:
            engine.log.append(Col.wrap(f" 🎉 MISSION COMPLETE: {key.upper()}! ", Col.GRN + Col.BOLD))
            
            completed_count = sum(
                1 for m in ["civilians", "thugs", "threats"] 
                if engine.missions.get(m, 0) >= engine.missions.get(f"{m}_max", 99)
            )
            
            if completed_count == 1:
                engine.log.append(Col.wrap(" ⚡ The Villain feels the pressure! (Master Plan acceleration active)", Col.YLW))
            elif completed_count == 2:
                engine.log.append(Col.wrap(" 🔓 VULNERABLE: The Villain can now be attacked! ", Col.GRN))
            elif completed_count == 3:
                engine.log.append(Col.wrap(" 🃏 REINFORCEMENTS: All Heroes draw 1 card immediately! ", Col.CYAN + Col.BOLD))
                for h in engine.heroes:
                    if not getattr(h, 'is_ko', False):
                        h.draw_cards(1)
                        
        return True
        