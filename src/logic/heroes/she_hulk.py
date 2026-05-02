from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("she-hulk")
class SheHulkLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "she-hulk_transformation":
            return SheHulkLogic._transformation(engine, hero)
        return False

    @staticmethod
    def _transformation(engine, hero):
        story = engine.storyline.cards
        
        # Count how many Transformations are currently on the table
        count = sum(1 for c in story if c.get("name") == "Transformation" and not c.get("is_facedown"))
        
        # The Math: 1 base ✸ + 1 bonus ✸ per Transformation
        gained_attack = count + 1
        
        engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + gained_attack
        engine.log.append(Col.wrap(f" 🟩 {hero.name} taps into her rage! (Found {count}x Transformation: +{gained_attack} ✸)", Col.GRN))
        
        return True
