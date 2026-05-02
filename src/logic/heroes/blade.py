from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("blade")
class BladeLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "blade_blood_bath":
            loc = engine.locations[hero.location_index]
            thugs = loc.thugs
            if thugs > 0:
                from src.systems.action_system import ActionSystem
                from src.systems.token_system import TokenSystem
                engine.log.append(Col.wrap(f" 🩸 BLOOD BATH: Blade clears out {loc.name}!", Col.RED + Col.BOLD))
                for _ in range(thugs):
                    TokenSystem.apply_thug_defeat(engine, loc, hero)
            else:
                engine.log.append(Col.wrap(" 🩸 No Thugs here for a Blood Bath.", Col.YLW))
            return True
            
        elif sid == "blade_hunter_skills":
            # This requires a modifier hook in apply_action_modifiers
            engine.log.append(Col.wrap(" 🦇 HUNTER SKILLS: Blade focuses his attacks!", Col.RED))
            # Temporary flag for ActionSystem to handle doubling against single targets
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "blade_hunter", duration=1)
            return True
            
        elif sid == "blade_vampiric_healing":
            if hero.deck:
                hero.hand.append(hero.deck.pop(0))
                engine.log.append(Col.wrap(" 🩸 VAMPIRIC HEALING: Blade recovers 1 card.", Col.RED))
            return True
        return False
        