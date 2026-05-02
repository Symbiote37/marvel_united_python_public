from src.utils.helpers import Col

class BlackPantherLocationLogic:
    @staticmethod
    def gain_wild_token(engine, hero, effect):
        if Col.prompt_y_n("🦍 GAIN ❖", effect['text']):
            hero.add_token("wild")
            engine.log.append(f" ✨ {hero.name} gained +1 ❖. ")

    @staticmethod
    def attack_at_loc(engine, hero, effect):
        if Col.prompt_y_n("🌊 IMMEDIATE ATTACK", effect['text']):
            from src.systems.action_system import ActionSystem
            engine.log.append(f" 🌊 {hero.name} launches an immediate attack! ")
            # Triggers a free targeted attack action directly at the hero's location
            ActionSystem._handle_targeted_attack(engine, hero, hero.location_index)
            return True
            