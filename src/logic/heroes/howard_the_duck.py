from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("howard_the_duck")
class HowardTheDuckLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "howard_the_duck_big_freaking_gun":
            from src.systems.action_system import ActionSystem
            print(f"\n--- {Col.wrap('BFG: SELECT TARGET SECTOR', Col.YLW)} ---")
            for i, loc in enumerate(engine.locations, 1): 
                print(f" [{i}] {loc.name}")
            
            c = Col.get_choice(" >> ", 1, 6) - 1
            engine.log.append(Col.wrap(f" 🦆 BFG fired into {engine.locations[c].name}!", Col.YLW + Col.BOLD))
            
            # The card says "Deal ✸ ✸", which means two separate 1-damage strikes
            for _ in range(2): 
                ActionSystem._handle_targeted_attack(engine, hero, c)
            return True
            
        elif sid == "howard_the_duck_neutron_disintegrator":
            from src.systems.villain_system import VillainSystem
            from src.systems.damage_system import DamageSystem
            from src.logic.shield_logic import is_target_vulnerable
            
            loc_idx = hero.location_index
            loc = engine.locations[loc_idx]
            opts = []

            # Find Villains with > 1 HP
            for v in VillainSystem.get_attackable_villains_at(engine, loc_idx):
                if v["hp"] > 1:
                    opts.append({"label": f"Villain: {v['name']} (HP: {v['hp']})", "obj": v["ref"]})
            
            # Find Henchmen Threats with > 1 HP
            if loc.threat and not loc.threat.cleared and getattr(loc.threat, 'hp', 0) > 1:
                if is_target_vulnerable(engine, loc.threat)[0]:
                    opts.append({"label": f"Henchman: {loc.threat.name} (HP: {loc.threat.hp})", "obj": loc.threat})

            if not opts:
                engine.log.append(Col.wrap(" 🔫 NEUTRON DISINTEGRATOR failed: No targets with >1 HP available here.", Col.YLW))
                return True

            print(f"\n--- {Col.wrap('DISINTEGRATE TARGET TO 1 HP', Col.RED)} ---")
            for i, opt in enumerate(opts, 1):
                print(f" [{i}] {opt['label']}")
            
            choice = Col.get_choice(" >> ", 1, len(opts))
            selected = opts[choice - 1]
            target = selected["obj"]
            
            # Math: Deal damage equal to (Current HP - 1)
            dmg_to_deal = getattr(target, 'hp') - 1
            engine.log.append(Col.wrap(f" 🔫 NEUTRON DISINTEGRATOR: Blasting {selected['label'].split(':')[1].strip()} for {dmg_to_deal} damage!", Col.RED + Col.BOLD))
            
            DamageSystem.deal_enemy_damage(engine, target, amount=dmg_to_deal, flavor="disintegrated")
            
            # Apply the penalty
            engine.active_pool["attack"] = 0
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "pacifist", duration=1) 
            engine.log.append(Col.wrap(" 🦆 Howard's weapon is cooling down. He cannot attack this turn.", Col.DARK_GRAY))
            return True
            
        elif sid == "howard_the_duck_no_more_mr_nice_duck":
            from src.systems.damage_system import DamageSystem
            from src.systems.token_system import TokenSystem
            from src.systems.villain_system import VillainSystem
            
            loc = engine.locations[hero.location_index]
            engine.log.append(Col.wrap(" 🦆 NO MORE MR. NICE DUCK! 2 Damage to EVERY enemy here!", Col.RED + Col.BOLD))
            
            # 1. Vaporize Thugs (They only have 1 HP, so 2 damage is a guaranteed KO)
            # We iterate individually so the MissionSystem increments correctly for each one
            if loc.thugs > 0:
                engine.log.append(f"   💥 Blasting {loc.thugs} Thug(s)!")
                for _ in range(loc.thugs): 
                    TokenSystem.apply_thug_defeat(engine, loc, hero, amount=1)
            
            # 2. Blast Henchmen Threats
            if loc.threat and not loc.threat.cleared and getattr(loc.threat, 'hp', 0) > 0:
                DamageSystem.deal_enemy_damage(engine, loc.threat, amount=2, flavor="blasted")
                
            # 3. Blast Villains
            for v in VillainSystem.get_attackable_villains_at(engine, hero.location_index):
                DamageSystem.deal_enemy_damage(engine, v["ref"], amount=2, flavor="blasted")
                
            return True
            
        return False
