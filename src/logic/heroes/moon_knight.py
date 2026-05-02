import random
from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("moon_knight")
class MoonKnightLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "moon_knight_khonshu_power":
            count = sum(1 for c in engine.storyline.cards if c.get('owner') == hero.name and c.get('special_id'))
            engine.log.append(Col.wrap(f" 🌙 KHONSHU'S POWER: The moon grants {count} Wilds!", Col.CYAN))
            engine.active_pool["wild"] = engine.active_pool.get("wild", 0) + count
            return True
            
        elif sid == "moon_knight_suit":
            from src.systems.status_system import StatusSystem
            # 🚨 Updated to use the generic 'evade' status
            StatusSystem.apply_status(hero, "evade", duration=1)
            engine.log.append(Col.wrap(" 🌙 MOON KNIGHT'S SUIT: Prepared to evade into the shadows!", Col.CYAN))
            return True
            
        elif sid == "moon_knight_": # Dissociative Identity Disorder
            engine.log.append(Col.wrap(" 🎭 DISSOCIATIVE IDENTITY: A new persona takes control!", Col.MAGENTA))
            hero.deck.extend(hero.hand)
            hero.hand.clear()
            random.shuffle(hero.deck)
            hero.draw_cards(3)
            return True
        return False
