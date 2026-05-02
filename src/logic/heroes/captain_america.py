# src/logic/heroes/captain_america.py

from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("captain_america")
class CaptainAmericaLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        others = [h for h in engine.heroes if h != hero]
        if not others: 
            print(Col.wrap(" No teammates nearby to lead.", Col.RED))
            return False

        print(f"\n{Col.wrap('🛡️ LEADERSHIP:', Col.CYAN)} Award a Wild Token to a teammate. ")
        for i, h in enumerate(others):
            print(f" {i+1}: {h.name}")
        
        choice = Col.get_choice("Select Hero (0 to cancel): ", 0, len(others))
        if choice == 0: return False

        target = others[choice - 1]
        if not hasattr(target, 'stashed_tokens'):
            target.stashed_tokens = []
            
        wild_icon = ICON.get('wild', '❖')
        target.stashed_tokens.append(wild_icon)
        
        engine.log.append(Col.wrap(f" 🛡️ {hero.name} awarded a {wild_icon} to {target.name}!", Col.GRN))
        return True
        