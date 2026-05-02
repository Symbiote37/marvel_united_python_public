# src/logic/heroes/spider_man.py
from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("spider-man")
class SpiderManLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        from src.systems.token_system import TokenSystem
        from src.systems.mission_system import MissionSystem
        
        sid = card.get("special_id")
        loc = engine.locations[hero.location_index]

        if sid == "spider-man_great_power":
            # 1. Grant the raw potential to the active pool
            if getattr(engine, 'active_pool', None) is None:
                engine.active_pool = {}
            
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 3
            
            # 2. Store the tracking state safely on the Storyline card itself
            card['thug_charges'] = 3
            
            engine.log.append(Col.wrap(" 🕸️ GREAT POWER: 3 Attack actions granted!", Col.BLU))
            engine.log.append(Col.wrap("   (Bonus Heroic tokens will trigger on the next 3 Thug defeats)", Col.DARK_GRAY))
            return True

        elif sid == "spider-man_great_responsibility":
            # NOTE: Keeping this as an immediate resolution per current design, 
            # unless you'd like this to grant Heroic actions and reward Attack tokens similarly.
            engine.log.append(Col.wrap(" 🕸️ GREAT RESPONSIBILITY: Getting them to safety!", Col.BLU))
            reward_count = 0
            for _ in range(3):
                if loc.civilians > 0:
                    if MissionSystem.increment_mission(engine, "civilians"):
                        loc.civilians -= 1
                        reward_count += 1
                        engine.log.append(f" {ICON['civilian']} Citizen rescued!")
            
            if reward_count > 0:
                for _ in range(reward_count):
                    hero.add_token("attack")
                engine.log.append(Col.wrap(f"   💥 Focus: Gained {reward_count} {ICON['attack']} tokens!", Col.GRN))
            return True

        elif sid == "spider-man_webslinging":
            hero.add_token("move")
            hero.add_token("move")
            engine.log.append(Col.wrap(f" 🕸️ WEBSLINGING: {hero.name} gained 2 {ICON['move']} tokens.", Col.CYAN))
            return True
            
        return False

    # 📡 THE EVENT LISTENER: Automatically found and triggered by actors.py
    @staticmethod
    def on_thug_defeat(engine, hero, card):
        if card.get("special_id") == "spider-man_great_power":
            charges = card.get('thug_charges', 0)
            if charges > 0:
                hero.add_token("heroic")
                engine.log.append(Col.wrap(f"   💥 Momentum: {hero.name} gained 1 {ICON['heroic']} token!", Col.GRN))
                card['thug_charges'] -= 1
