from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("star-lord")
class StarLordLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "star-lord_problem_solver":
            other_heroes = [h for h in engine.heroes if h != hero and not getattr(h, 'is_ko', False)]
            if not other_heroes: return False
            
            print(f"\n--- {Col.wrap('PROBLEM SOLVER: SELECT ALLY', Col.CYAN)} ---")
            for i, h in enumerate(other_heroes, 1): print(f" [{i}] {h.name}")
            c = Col.get_choice(" >> ", 1, len(other_heroes)) - 1
            target = other_heroes[c]
            
            print(f"\n--- {Col.wrap('SELECT TOKEN', Col.CYAN)} ---")
            tokens = ["move", "attack", "heroic"]
            for i, t in enumerate(tokens, 1): print(f" [{i}] {ICON.get(t)}")
            t_choice = Col.get_choice(" >> ", 1, 3) - 1
            
            target.add_token(tokens[t_choice])
            engine.log.append(Col.wrap(f" 🎧 PROBLEM SOLVER: Star-Lord tossed a {ICON.get(tokens[t_choice])} to {target.name}!", Col.CYAN))
            return True
        return False
        