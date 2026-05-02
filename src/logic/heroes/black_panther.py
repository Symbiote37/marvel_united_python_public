from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("black_panther")
class BlackPantherLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "black_panther_panther_habit":
            # Just adds the symbols printed on the card text to the active pool
            symbols = []
            if "★ ✸" in card.get("effect_text"):
                engine.active_pool["heroic"] = engine.active_pool.get("heroic", 0) + 1
                engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 1
                symbols = ["★", "✸"]
            elif "➡ ✸" in card.get("effect_text"):
                engine.active_pool["move"] = engine.active_pool.get("move", 0) + 1
                engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 1
                symbols = ["➡", "✸"]
            elif "➡ ★" in card.get("effect_text"):
                engine.active_pool["move"] = engine.active_pool.get("move", 0) + 1
                engine.active_pool["heroic"] = engine.active_pool.get("heroic", 0) + 1
                symbols = ["➡", "★"]
            
            from src.utils.helpers import Col
            engine.log.append(Col.wrap(f" 🐾 PANTHER HABIT: T'Challa adapts his stance! (+{' '.join(symbols)})", Col.CYAN))
            return True
        return False
        