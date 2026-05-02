from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("rocket")
class RocketLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "rocket_master_tinkerer":
            print(f"\n--- {Col.wrap('MASTER TINKERER', Col.CYAN + Col.BOLD)} ---")
            print(" [1] Gain 1 ❖ Token")
            print(" [2] Action tokens can be used twice this turn")
            
            choice = Col.get_choice(" >> ", 1, 2)
            if choice == 1:
                hero.add_token("wild")
                engine.log.append(Col.wrap(" 🦝 MASTER TINKERER: Rocket scavenged a ❖ token!", Col.CYAN))
            else:
                from src.systems.status_system import StatusSystem
                # 🚨 Apply a generic status that the ActionSystem can check later
                StatusSystem.apply_status(hero, "double_tokens", duration=1)
                engine.log.append(Col.wrap(" 🦝 MASTER TINKERER: Rocket upgraded his gear! Tokens count twice this turn.", Col.CYAN))
            return True
            
        elif sid == "rocket_raccoon_senses":
            tokens = getattr(hero, 'stashed_tokens', [])
            
            # Auto-skip the prompt if he has no tokens to convert
            if not tokens:
                hero.add_token("wild")
                engine.log.append(Col.wrap(" 🦝 RACCOON SENSES: Rocket sniffed out a ❖ token!", Col.CYAN))
                return True
                
            print(f"\n--- {Col.wrap('RACCOON SENSES', Col.CYAN + Col.BOLD)} ---")
            print(" [1] Gain 1 ❖ Token")
            print(f" [2] Convert current tokens into ❖ Tokens ({len(tokens)} available)")
            
            choice = Col.get_choice(" >> ", 1, 2)
            if choice == 1:
                hero.add_token("wild")
                engine.log.append(Col.wrap(" 🦝 RACCOON SENSES: Rocket sniffed out a ❖ token!", Col.CYAN))
            else:
                # Convert all existing tokens to wild
                count = len(tokens)
                hero.stashed_tokens = ["wild"] * count
                engine.log.append(Col.wrap(f" 🦝 RACCOON SENSES: Rocket converted {count} token(s) into ❖ tokens!", Col.CYAN))
            return True
            
        return False
        