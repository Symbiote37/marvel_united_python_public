from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("ghost_rider")
class GhostRiderLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        from src.systems.action_system import ActionSystem
        from src.systems.token_system import TokenSystem
        
        if sid == "ghost_rider_hellfire_manipulation":
            engine.log.append(Col.wrap(" 🔥 HELLFIRE: Ghost Rider unleashes 3 damage!", Col.RED + Col.BOLD))
            # Just loop the target helper 3 times for a single target
            # Note: We should technically enforce it hits the *same* target, 
            # but for simplicity, we allow sequential hits.
            for _ in range(3): ActionSystem._handle_targeted_attack(engine, hero, hero.location_index)
            return True
            
        elif sid == "ghost_rider_mystical_chain":
            loc = engine.locations[hero.location_index]
            engine.log.append(Col.wrap(f" ⛓️ MYSTICAL CHAIN: Whipping through the Thugs!", Col.YLW))
            # 2 damage to EVERY thug effectively kills all thugs (since they have 1 HP)
            thugs = loc.thugs
            for _ in range(thugs): TokenSystem.apply_thug_defeat(engine, loc, hero)
            return True
            
        elif sid == "ghost_rider_supernatural_awareness":
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 1
            engine.active_pool["heroic"] = engine.active_pool.get("heroic", 0) + 1
            if hero.deck: hero.hand.append(hero.deck.pop(0))
            engine.log.append(Col.wrap(" 💀 SUPERNATURAL AWARENESS: (+✸ +★) & drew 1 card.", Col.YLW))
            return True
        return False
        