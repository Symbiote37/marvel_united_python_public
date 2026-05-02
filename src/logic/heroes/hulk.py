from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("hulk")
class HulkLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        from src.systems.action_system import ActionSystem
        from src.systems.damage_system import DamageSystem
        from src.systems.mission_system import MissionSystem 
        loc = engine.locations[hero.location_index]
        v_id = engine.villain.internal_id.lower()
        
        engine.log.append(Col.wrap(f" 👊 HULK SMASH at {loc.name}! ", Col.GRN + Col.BOLD))

        # 1. Damage Thugs
        if loc.thugs > 0:
            tid = str(getattr(loc.threat, 'id_internal', loc.threat.id) or "").lower()
            is_elite = (loc.threat and not loc.threat.cleared and "elite_troops" in tid)
            
            if is_elite:
                if v_id == "kingpin":
                    msg = "   🕴️ MOB ARMOR: Fisk's enforcers brace for the impact! "
                elif v_id == "red_skull":
                    msg = "   🐙 HYDRA SHIELDS: Fanatics shrug off the blast! "
                else:
                    msg = "   🛡️ ELITE ARMOR: The shockwave dissipates against reinforced gear! "
                engine.log.append(Col.wrap(msg, Col.YLW))
            else:
                from src.systems.token_system import TokenSystem
                # 🚨 SENSOR HOOKED: Automatically clears the thugs, increments the mission, and tracks the MVP!
                TokenSystem.apply_thug_defeat(engine, loc, hero, amount=loc.thugs)

        # 2. Damage Henchman/Threat
        if loc.threat and not loc.threat.cleared and loc.threat.hp > 0:
            DamageSystem.deal_enemy_damage(engine, loc.threat, flavor="Smashed")

        # 3. Damage the Villain
        if engine.villain.location_index == hero.location_index:
            DamageSystem.deal_enemy_damage(engine, engine.villain, flavor="Hulk Smashed")

        # 4. Friendly Fire
        for other_h in engine.heroes:
            if other_h != hero and other_h.location_index == hero.location_index:
                # 🛡️ THE SHOCKWAVE FIX: Only log if the hero wasn't invulnerable/shielded
                if other_h.take_damage(engine):
                    engine.log.append(Col.wrap(f"   💥 {other_h.name} caught in the blast! ", Col.YLW))    

        # 5. Collateral Damage
        if hasattr(engine.villain_logic, 'on_civilians_flee'):
            engine.villain_logic.on_civilians_flee(engine, loc)
        
        return True
        