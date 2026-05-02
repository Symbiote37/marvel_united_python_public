from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("shuri")
class ShuriLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "shuri_young_engineer":
            engine.log.append(Col.wrap(f" ⚙️ YOUNG GENIUS: Shuri provides tech support!", Col.CYAN))
            
            other_heroes = [h for h in engine.heroes if h != hero and not getattr(h, 'is_ko', False)]
            if not other_heroes:
                print(Col.wrap(" ! No valid allies to assist.", Col.RED))
                return False
                
            print(f"\n--- {Col.wrap('SELECT ALLY', Col.CYAN)} ---")
            for i, h in enumerate(other_heroes, 1):
                print(f" [{i}] {h.name}")
            
            c = Col.get_choice(" >> ", 1, len(other_heroes)) - 1
            target = other_heroes[c]
            
            target.add_token("wild")
            engine.log.append(f"   🔧 {target.name} gained 1 ❖ token!")
            
            drawn = 0
            while len(target.hand) < 3 and target.deck:
                target.hand.append(target.deck.pop(0))
                drawn += 1
            if drawn > 0:
                engine.log.append(f"   🔋 {target.name} drew {drawn} card(s).")
            return True
        return False
        