# src/logic/heroes/miles_morales.py
from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("miles_morales")
class MilesMoralesLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")

        if sid == "miles_morales_invisibility":
            return MilesMoralesLogic._invisibility(engine, hero)
        elif sid == "miles_morales_venom_strike":
            return MilesMoralesLogic._venom_strike(engine, hero)
        elif sid == "miles_morales_web":
            return MilesMoralesLogic._web(engine, hero)
        return False

    @staticmethod
    def _invisibility(engine, hero):
        # 🚨 Hooked into the standard Invincibility protocol
        hero.is_invincible = True
        hero.invincible_deflect_msg = f"   🕸️ {hero.name} completely vanishes, dodging the attack!"
        hero.invincible_wear_off_msg = f" 👤 {hero.name}'s camouflage fades."
        engine.log.append(Col.wrap(f" 👤 INVISIBILITY: {hero.name} vanished into thin air!", Col.PURP))
        return True

    @staticmethod
    def _venom_strike(engine, hero):
        from src.systems.action_system import ActionSystem
        
        engine.log.append(Col.wrap(f" ⚡ {hero.name} unleashes a bio-electric Venom Strike!", Col.YLW))
        
        # 💥 Leverage the upgraded engine: Ask once, hit twice
        success = ActionSystem._handle_targeted_attack(engine, hero, hero.location_index, damage=2, burst_mode=True)
        
        if not success:
            engine.log.append(Col.wrap("   (Venom Strike cancelled or no valid targets)", Col.DARK_GRAY))
            
        return True

    @staticmethod
    def _web(engine, hero):
        if engine.villain.location_index == hero.location_index:
            # 🚨 Set the Stun flag for the VillainSystem to catch
            engine.villain_stunned = True 
            engine.log.append(Col.wrap(f" 🕸️ WEB: {engine.villain.name} is tangled up and will skip their next turn!", Col.GRN + Col.BOLD))
            return True
        else:
            engine.ui.acknowledge(" The Villain is not in your location.")
            return False
