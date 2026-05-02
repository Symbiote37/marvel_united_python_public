from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("nebula")
class NebulaLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "draw_up_to_3":
            drawn = 0
            while len(hero.hand) < 3 and hero.deck:
                hero.hand.append(hero.deck.pop(0))
                drawn += 1
            if drawn > 0: engine.log.append(Col.wrap(f" 🦾 REGENERATION: Nebula drew {drawn} cards.", Col.CYAN))
            return True
            
        elif sid == "nebula_electroshock_batons":
            from src.systems.action_system import ActionSystem
            engine.log.append(Col.wrap(f" ⚡ ELECTROSHOCK BATONS: Nebula sweeps her flanks!", Col.CYAN))
            ActionSystem._handle_targeted_attack(engine, hero, (hero.location_index - 1) % 6)
            ActionSystem._handle_targeted_attack(engine, hero, (hero.location_index + 1) % 6)
            return True
            
        elif sid == "nebula_image_projection":
            from src.logic.locations import LocationLogic
            engine.log.append(Col.wrap(f" 💽 IMAGE PROJECTION: Nebula scrambles the timeline!", Col.MAGENTA))
            if engine.villain.plan_deck:
                burned = engine.villain.plan_deck.pop(0)
                engine.log.append(Col.wrap(f"   🔥 Master Plan card burned from the deck!", Col.MAGENTA))
            
            for h in engine.heroes:
                if not h.is_ko:
                    LocationLogic.swap_with_storyline(engine, h, {"text": f"Image Projection: {h.name}, swap a card!"})
            return True
        return False
        