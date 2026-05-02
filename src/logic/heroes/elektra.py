from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("elektra")
class ElektraLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "elektra_master_assassin":
            return ElektraLogic._master_assassin(engine, hero)
        elif sid == "elektra_ninja_training":
            return ElektraLogic._ninja_training(engine, hero)
        elif sid == "elektra_sai":
            return ElektraLogic._sai(engine, hero)
        return False

    @staticmethod
    def _master_assassin(engine, hero):
        engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
        engine.log.append(Col.wrap(f" 🥷 PASSIVE: {hero.name} readies her blades. (+2 Attack)", Col.CYAN))
        return True

    @staticmethod
    def _ninja_training(engine, hero):
        print(f"\n{Col.wrap('🥷 NINJA TRAINING:', Col.CYAN)}")
        print(" [1] Gain ✸ ✸")
        print(" [2] Gain Invulnerability until next turn")
        print(" [0] Cancel")
        
        choice = Col.get_choice(" >> ", 0, 2)
        if choice == 0: return False
        
        if choice == 1:
            engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
            engine.log.append(Col.wrap(f" 🥷 {hero.name} chooses aggression! (+2 Attack)", Col.CYAN))
        elif choice == 2:
            hero.is_invincible = True
            hero.invincible_deflect_msg = f"   🥷 {hero.name} melts into the shadows to evade the attack!"
            hero.invincible_wear_off_msg = f" 🧍 {hero.name} emerges from the shadows."
            engine.log.append(Col.wrap(f" 🥷 {hero.name} chooses stealth! (Damage nullified)", Col.CYAN))
            
        return True

    @staticmethod
    def _sai(engine, hero):
        from src.systems.action_system import ActionSystem
        from src.utils.helpers import Col
        
        engine.log.append(Col.wrap(f" 🗡️ {hero.name} strikes outward with her sais!", Col.CYAN))
        
        # 🌟 THE SEQUENTIAL STRIKE: One target clockwise, one counter-clockwise.
        for offset in [1, -1]:
            adj_idx = (hero.location_index + offset) % 6
            ActionSystem._handle_targeted_attack(engine, hero, adj_idx)
            
        return True
