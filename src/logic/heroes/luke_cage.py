from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("luke_cage")
class LukeCageLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "luke_cage_superhuman_strength": return LukeCageLogic._superhuman_strength(engine, hero)
        elif sid == "luke_cage_nigh_invulnerability": return LukeCageLogic._nigh_invulnerability(engine, hero)
        elif sid == "luke_cage_healing_factor": return LukeCageLogic._healing_factor(engine, hero)
        return False

    @staticmethod
    def _superhuman_strength(engine, hero):
        print(f"\n--- {Col.wrap('⛓️ SUPERHUMAN STRENGTH', Col.YLW)} ---")
        if input(" [1] Execute: Gain ✸ equal to hand size\n [0] Cancel\n >> ").strip() != '1': return False
        
        cards_in_hand = len(hero.hand)
        engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + cards_in_hand
        engine.log.append(Col.wrap(f" ⛓️ {hero.name} flexes his Superhuman Strength! (+{cards_in_hand} ✸)", Col.YLW))
        return True

    @staticmethod
    def _nigh_invulnerability(engine, hero):
        print(f"\n--- {Col.wrap('🛡️ NIGH-INVULNERABILITY', Col.YLW)} ---")
        if input(" [1] Execute: Draw 1, Evade damage\n [0] Cancel\n >> ").strip() != '1': return False
        
        hero.draw_cards(1)
        hero.is_invincible = True
        hero.invincible_deflect_msg = f" 🛡️ The attack bounces harmlessly off {hero.name}'s unbreakable skin!"
        hero.invincible_wear_off_msg = f" 🧍 {hero.name} lowers his guard."
        engine.log.append(Col.wrap(f" 🛡️ {hero.name} braces for impact! (Draw 1, Invincible this round)", Col.YLW))
        return True

    @staticmethod
    def _healing_factor(engine, hero):
        print(f"\n--- {Col.wrap('🩹 REGENERATIVE HEALING FACTOR', Col.GRN)} ---")
        if input(" [1] Execute: Draw 2\n [0] Cancel\n >> ").strip() != '1': return False
        
        hero.draw_cards(2)
        engine.log.append(Col.wrap(f" 🩹 {hero.name}'s Healing Factor kicks in! (Draw 2)", Col.GRN))
        return True
        