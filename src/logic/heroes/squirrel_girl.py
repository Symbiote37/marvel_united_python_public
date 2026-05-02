from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("squirrel_girl")
class SquirrelGirlLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "squirrel_girl_squirrel_army":
            from src.systems.action_system import ActionSystem
            engine.log.append(Col.wrap(" 🐿️ SQUIRREL ARMY! Swarming all locations!", Col.YLW + Col.BOLD))
            for i in range(6):
                 ActionSystem._handle_targeted_attack(engine, hero, i)
            return True
        elif sid == "squirrel_girl_night_vision":
            engine.log.append(Col.wrap(" 🐿️ NIGHT VISION:", Col.YLW))
            if engine.villain.plan_deck:
                print(f" Top Plan: {engine.villain.plan_deck[0]['id']}")
                if engine.ui.ask_yes_no(" Move to bottom? (y/n): "):
                    engine.villain.plan_deck.append(engine.villain.plan_deck.pop(0))
            return True
        elif sid == "squirrel_girl_common_sense":
            count = sum(1 for c in engine.storyline.cards if c.get('owner') == hero.name and c.get('special_id'))
            engine.log.append(Col.wrap(f" 🐿️ COMMON SENSE Check: {count} Specials vs {engine.villain.hp} HP.", Col.YLW))
            if count > engine.villain.hp:
                engine.game_over = True
                engine.victory_status = "HEROES_WIN"
                engine.victory_reason = "SQUIRREL LOGIC! Squirrel Girl overwhelmed the Villain!"
            return True
        return False
        