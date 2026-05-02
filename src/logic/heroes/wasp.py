from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("wasp")
class WaspLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        # 🚨 Standardized IDs to match the JSON/Engine Registry
        if sid == "wasp_wings":
            return WaspLogic._wings(engine, hero)
        elif sid == "wasp_energy_projection": # Renamed from energy_projection to match card flavor
            return WaspLogic._energy_projection(engine, hero)
        elif sid == "wasp_shrink":
            return WaspLogic._shrink(engine, hero)
        return False

    @staticmethod
    def _wings(engine, hero):
        """Move self and any heroes at location to any other location."""
        others_at_loc = [h for h in engine.heroes if h.location_index == hero.location_index and h != hero]
        
        print(f"\n{Col.wrap('🐝 WINGS:', Col.CYAN)} Select a destination for your squad. ")
        for i, loc in enumerate(engine.locations):
            print(f" [{i+1}] {loc.name}")
        
        choice = Col.get_choice(" Destination >> ", 1, 6)
        dest_idx = choice - 1
        
        # Always move Janet
        hero.location_index = dest_idx
        
        # Optional move for others (The 'Taxi' service)
        for other in others_at_loc:
            confirm = input(f"   🚁 Carry {other.name} to {engine.locations[dest_idx].name}? (y/n): ").lower()
            if confirm == 'y':
                other.location_index = dest_idx
                
        engine.log.append(Col.wrap(f" 🐝 WINGS: Janet relocated the squad to {engine.locations[dest_idx].name}! ", Col.CYAN))
        return True

    @staticmethod
    def _energy_projection(engine, hero):
        from src.systems.action_system import ActionSystem
        from src.systems.damage_system import DamageSystem
        from src.systems.token_system import TokenSystem
        from src.logic.registry import get_villain_logic
        
        # 1. Fly Anywhere
        print(f"\n{Col.wrap('⚡ WASP STING:', Col.CYAN)} Fly anywhere and strike! ")
        for i, loc in enumerate(engine.locations):
            print(f" [{i+1}] {loc.name}")
        
        choice = Col.get_choice(" Target Location >> ", 1, 6)
        hero.location_index = choice - 1
        loc = engine.locations[hero.location_index]
        
        engine.log.append(Col.wrap(f" ⚡ Janet zips into {loc.name}...", Col.CYAN))

        # 2. Localized Target Acquisition (No pool deduction!)
        logic = get_villain_logic(engine.villain.internal_id)
        opts = logic.get_attack_options(engine, hero)
        opts.extend(logic.get_extra_attack_options(engine, loc, hero))
        valid_opts = [o for o in opts if ActionSystem._is_attack_target_valid(engine, loc, o)]
        
        if not valid_opts: 
            engine.log.append(Col.wrap("   ...but there's nothing there to hit!", Col.DARK_GRAY))
            return True

        print(f"\n--- {Col.wrap('SELECT STING TARGET', Col.CYAN)} ---")
        for i, o in enumerate(valid_opts, 1):
            print(f" [{i}] {o['label']}")

        t_choice = Col.get_choice(" >> ", 1, len(valid_opts))
        selected = valid_opts[t_choice-1]

        # 3. Direct Execution (Bypassing the ActionSystem's cost checks)
        if "execute" in selected: 
            selected["execute"](engine)
        else: 
            if selected["id"] == "v":
                DamageSystem.deal_enemy_damage(engine, engine.villain, is_action=False) # False, because it's a Special!
            elif selected["id"] == "h":
                DamageSystem.deal_enemy_damage(engine, loc.threat, is_action=False)
            elif selected["id"] == "m":
                TokenSystem.apply_thug_defeat(engine, loc, hero)
            else:
                logic.resolve_special_action(engine, loc, hero, selected["id"])
                
        return True

    @staticmethod
    def _shrink(engine, hero):
        """Standardized Invincibility using the Pym Particle protocol."""
        print(f"\n--- {Col.wrap('🐜 SHRINK: WASP PROTOCOL', Col.CYAN)} ---")
        print(" [1] Execute: Evade all damage until next turn")
        print(" [0] Cancel")
        
        if input(" >> ").strip() != '1':
            return False 

        # 🚨 THE GLOBAL SHIELD & CUSTOM FLAVOR
        hero.is_invincible = True
        hero.invincible_deflect_msg = f"   🐝 {hero.name} zips around the attack at micro-size!"
        hero.invincible_wear_off_msg = f" 🧍 {hero.name} returns to full size."
        
        engine.log.append(Col.wrap(f" 🤏 SHRINK: {hero.name} is too small to hit! ", Col.PURP + Col.BOLD))
        return True
