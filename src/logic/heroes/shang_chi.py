from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("shang_chi")
class ShangChiLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "shang_chi_master_martial_artist":
            story_cards = getattr(engine.storyline, 'cards', [])
            # Find the previous hero card
            prev_hero_card = next((c for c in reversed(story_cards[:-1]) if not c.get('is_villain')), None)
            
            if prev_hero_card:
                attacks = prev_hero_card.get('actions', []).count('attack')
                if attacks > 0:
                    engine.log.append(Col.wrap(f" 🥋 MASTER MARTIAL ARTIST: Shang Chi doubles the {attacks} ✸ from the previous card! ", Col.CYAN))
                    engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + attacks
                else:
                    engine.log.append(Col.wrap(" 🥋 Shang Chi finds no attacks to double. ", Col.YLW))
            return True
        return False
        