from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("iron_man")
class IronManLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "iron_man_advanced_combat_analysis":
            return IronManLogic._distribute_tokens(engine, hero, "attack", 2)
        elif sid == "iron_man_stark_resources":
            return IronManLogic._distribute_tokens(engine, hero, "move", 2)
        return False

    @staticmethod
    def _distribute_tokens(engine, hero, token_type, amount):
        icon = ICON.get(token_type, token_type)
        engine.log.append(Col.wrap(f" 🏗️ STARK TECH: Distributing {amount} {icon} tokens...", Col.CYAN))
        
        for _ in range(amount):
            print(f"\nAward {icon} to which Hero?")
            for i, h in enumerate(engine.heroes):
                print(f" [{i+1}] {h.name}")
            
            choice = Col.get_choice(" >> ", 1, len(engine.heroes))
            target = engine.heroes[choice-1]
            target.add_token(icon)
            engine.log.append(Col.wrap(f"   🎁 {icon} awarded to {target.name}.", Col.GRN))
        return True
