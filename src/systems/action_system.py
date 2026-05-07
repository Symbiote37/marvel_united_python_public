from src.utils.helpers import ICON, Col
from src.systems.damage_system import DamageSystem
from src.systems.token_system import TokenSystem
from src.logic.shield_logic import is_target_vulnerable

class ActionSystem:
    # --- CORE DISPATCHERS ---

    @staticmethod
    def resolve_special_id(engine, hero, card):
        sid = card.get("special_id")
        if not sid: return False 
        
        from src.systems.special_abilities import SpecialAbilitySystem
        success = SpecialAbilitySystem.resolve(engine, hero, card)
        
        from src.systems.villain_system import VillainSystem
        VillainSystem.process_event_queue(engine)
        
        return success 

    @staticmethod
    def is_auto_trigger(card):
        if isinstance(card, dict):
            return card.get("auto_trigger", False)
        return False
        
    @staticmethod
    def resolve_single_action(engine, hero, action_type, pool):
        success = False
        
        if action_type == "move":
            success = ActionSystem._handle_move(engine, hero)
        elif action_type == "attack":
            success = ActionSystem._handle_attack(engine, hero)
        elif action_type == "heroic":
            success = ActionSystem._handle_heroic(engine, hero)
        elif action_type == "special":
            pass

        if not success:
            # 🔌 UI ADAPTER: Non-blocking acknowledgment
            engine.ui.acknowledge(f"  ! {action_type.capitalize()} action cancelled or insufficient symbols.")
        else:
            from src.systems.challenge_system import ChallengeSystem
            ChallengeSystem.on_action_resolved(engine, hero, action_type)
        if getattr(engine, 'game_over', False):
            return success
        
        from src.systems.villain_system import VillainSystem
        VillainSystem.process_event_queue(engine)
            
        return success

    # --- ACTION HANDLERS ---

    @staticmethod
    def _handle_move(engine, hero, free=False):
        from src.logic.modifier_logic import get_action_details
        from src.logic.registry import get_villain_logic
        loc = engine.locations[hero.location_index]
        pool = engine.active_pool
        
        idx_cw = hero.location_index
        for _ in range(6):
            idx_cw = (idx_cw + 1) % 6
            if not getattr(engine.locations[idx_cw], 'is_destroyed', False):
                break
                
        idx_ccw = hero.location_index
        for _ in range(6):
            idx_ccw = (idx_ccw - 1) % 6
            if not getattr(engine.locations[idx_ccw], 'is_destroyed', False):
                break
        
        opts = [
            {"label": f"Clockwise to {engine.locations[idx_cw].name}", "id": "mc"},
            {"label": f"Counter-Clockwise to {engine.locations[idx_ccw].name}", "id": "mcc"}
        ]

        logic = get_villain_logic(engine.villain.internal_id)
        if hasattr(logic, 'get_move_options'):
            opts.extend(logic.get_move_options(engine, hero))

        print(f"\n--- {Col.wrap('SELECT DESTINATION', Col.CYAN)} ---")
        for i, o in enumerate(opts, 1):
            print(f" [{i}] {o['label']}")
        print(" [0] Cancel")
        
        # 🔌 UI ADAPTER: Replaced Col.get_choice
        choice = engine.ui.ask_choice(" >> ", 0, len(opts))
        if choice == 0: return False
        selected = opts[choice-1]
            
        cost, warning = get_action_details(engine, hero, "move", action_id=selected.get('id'))
        
        if not free:
            if (pool.get("move", 0) + pool.get("wild", 0)) < cost:
                engine.ui.acknowledge(warning or f" ! Action costs {cost} ➡. ")
                return False
            ActionSystem.pay_bulk_cost(pool, "move", cost)

        if selected["id"] == "mc": hero.location_index = idx_cw
        elif selected["id"] == "mcc": hero.location_index = idx_ccw
        elif "execute" in selected: selected["execute"](engine)
        elif selected["id"] == "t_m":
            TokenSystem.apply_threat_token(engine, loc, "move")
        # 🚨 THE BUS BROADCAST: Radar Sense needs this!
        if selected["id"] in ["mc", "mcc"]:
            from src.systems.special_abilities import SpecialAbilitySystem
            SpecialAbilitySystem.trigger_event(engine, hero, "on_location_entered")

        # 🚨 THE FIX: Inject the mobility sensor here!
        if selected["id"] in ["mc", "mcc"]:
            if hasattr(engine, 'track_stat'):
                engine.track_stat(hero, "moves", 1)
        if selected["id"] in ["mc", "mcc"]:
            new_loc = engine.locations[hero.location_index]
            from src.systems.status_system import StatusSystem
            
            if StatusSystem.has_status(hero, "auto_rescue_civilians") and new_loc.civilians > 0:
                engine.log.append(Col.wrap(f" [*] PASSIVE: {hero.name} auto-rescues a Civilian!", Col.CYAN))
                TokenSystem.apply_heroic(engine, new_loc, amount=1, target_type="c")
                
            if StatusSystem.has_status(hero, "auto_rescue_thugs") and new_loc.thugs > 0:
                engine.log.append(Col.wrap(f" [*] PASSIVE: {hero.name} auto-defeats a Thug!", Col.CYAN))
                TokenSystem.apply_thug_defeat(engine, new_loc, hero, amount=1)

        return True

    @staticmethod
    def _handle_attack(engine, hero):
        from src.logic.modifier_logic import get_action_details
        from src.logic.registry import get_villain_logic
        from src.systems.status_system import StatusSystem
        
        loc = engine.locations[hero.location_index]
        pool = engine.active_pool
        logic = get_villain_logic(engine.villain.internal_id)
        
        opts = logic.get_attack_options(engine, hero)
        opts.extend(logic.get_extra_attack_options(engine, loc, hero))
        
        has_reach = StatusSystem.has_status(hero, "range") or getattr(hero, 'can_attack_adjacent', False)
        has_astral = StatusSystem.has_status(hero, "astral_projection")
        
        # 🚨 MANTIS ASTRAL PROJECTION FIX
        loc_indices = []
        if has_astral:
            loc_indices = [i for i in range(6) if i != hero.location_index]
        elif has_reach:
            loc_indices = [(hero.location_index - 1) % 6, (hero.location_index + 1) % 6]
            
        for adj_idx in loc_indices:
            adj_loc = engine.locations[adj_idx]
            if getattr(adj_loc, 'is_destroyed', False): continue
                
            adj_opts = logic.get_attack_options(engine, hero, location_override=adj_idx)
            for o in adj_opts:
                o['label'] = f"{o['label']} (at {adj_loc.name})"
                o['target_loc'] = adj_idx 
            opts.extend(adj_opts)

        valid_opts = [o for o in opts if ActionSystem._is_attack_target_valid(engine, loc, o)]
        
        if not valid_opts: 
            engine.ui.acknowledge(" ! No valid targets available. ")
            return False

        print(f"\n--- {Col.wrap('SELECT ATTACK TARGET', Col.CYAN + Col.BOLD)} ---")
        for i, o in enumerate(valid_opts, 1):
            print(f" [{i}] {o['label']}")
        print(" [0] Cancel")

        # 🔌 UI ADAPTER: Replaced Col.get_choice
        choice = engine.ui.ask_choice(" >> ", 0, len(valid_opts))
        if choice == 0: return False
        selected = valid_opts[choice-1]

        cost, warning = get_action_details(engine, hero, "attack", action_id=selected.get('id'))
        cost = selected.get("cost", cost)
        
        if (pool.get("attack", 0) + pool.get("wild", 0)) < cost:
            engine.ui.acknowledge(warning or f" ! Insufficient Attack symbols (Need {cost}). ")
            return False

        ActionSystem.pay_bulk_cost(pool, "attack", cost)
        
        target_loc_idx = selected.get("target_loc", hero.location_index)
        target_loc = engine.locations[target_loc_idx]

        if "execute" in selected: 
            selected["execute"](engine)
        else: 
            if selected["id"] == "v":
                DamageSystem.deal_enemy_damage(engine, engine.villain, is_action=True)
            elif selected["id"] == "h":
                DamageSystem.deal_enemy_damage(engine, target_loc.threat, is_action=True)
            elif selected["id"] == "m":
                TokenSystem.apply_thug_defeat(engine, target_loc, hero)
            elif selected["id"] == "t_a":
                TokenSystem.apply_threat_token(engine, target_loc, "attack")
            else:
                logic.resolve_special_action(engine, target_loc, hero, selected["id"])
        
        return True

    @staticmethod
    def _handle_heroic(engine, hero):
        from src.logic.modifier_logic import get_action_details
        from src.logic.registry import get_villain_logic
        loc = engine.locations[hero.location_index]
        pool = engine.active_pool
        logic = get_villain_logic(engine.villain.internal_id)

        opts = logic.get_heroic_options(engine, hero)
        opts.extend(logic.get_extra_heroic_options(engine, loc, hero))
        
        # 🚨 THE CHALLENGE HOOK: Fetch any challenge-specific heroic actions
        from src.systems.challenge_system import ChallengeSystem
        opts.extend(ChallengeSystem.get_challenge_heroic_options(engine, hero, loc))

        # 🚨 MANTIS ASTRAL PROJECTION FIX
        from src.systems.status_system import StatusSystem
        if StatusSystem.has_status(hero, "astral_projection"):
            for i in range(6):
                if i == hero.location_index: continue
                adj_loc = engine.locations[i]
                if getattr(adj_loc, 'is_destroyed', False): continue
                
                adj_opts = logic.get_heroic_options(engine, hero, location_override=i)
                if hasattr(logic, 'get_extra_heroic_options'):
                    adj_opts.extend(logic.get_extra_heroic_options(engine, adj_loc, hero))
                adj_opts.extend(ChallengeSystem.get_challenge_heroic_options(engine, hero, adj_loc))
                
                for o in adj_opts:
                    o['label'] = f"{o['label']} (at {adj_loc.name})"
                    o['target_loc'] = i
                opts.extend(adj_opts)
        
        if not opts: 
            engine.ui.acknowledge(" ! Nothing to do here. ")
            return False

        print(f"\n--- {Col.wrap('SELECT HEROIC ACTION', Col.CYAN)} ---")
        for i, o in enumerate(opts, 1):
            label = o.get('label', 'Action')
            req = f" ({o.get('cost', 1)})" if o.get('cost', 1) > 1 else ""
            print(f" [{i}] {label}{req}")
        print(" [0] Cancel")

        # 🔌 UI ADAPTER: Replaced Col.get_choice
        choice = engine.ui.ask_choice(" >> ", 0, len(opts))
        if choice == 0: return False
        selected = opts[choice-1]

        cost, warning = get_action_details(engine, hero, "heroic", action_id=selected.get('id'))
        total_required = selected.get("cost", cost)

        if (pool.get("heroic", 0) + pool.get("wild", 0)) < total_required:
            engine.ui.acknowledge(warning or f" ! Insufficient heroic symbols. ")
            return False

        ActionSystem.pay_bulk_cost(pool, "heroic", total_required)
        
        # 🚨 TARGET OVERRIDE FIX: Point resolution to the selected sector, not physical loc
        target_loc_idx = selected.get("target_loc", hero.location_index)
        target_loc = engine.locations[target_loc_idx]

        if "execute" in selected: 
            selected["execute"](engine)
        else:
            if selected["id"] == "c":
                TokenSystem.apply_heroic(engine, target_loc, target_type="c")
            elif selected["id"] == "t_h":
                TokenSystem.apply_threat_token(engine, target_loc, "heroic")
            elif selected["id"] == "x":
                TokenSystem.apply_heroic(engine, target_loc, target_type="x")
        return True

    @staticmethod
    def pay_bulk_cost(pool, action_type, total):
        remaining = total
        if pool.get(action_type, 0) > 0:
            spent = min(pool[action_type], remaining)
            pool[action_type] -= spent
            remaining -= spent
        if remaining > 0:
            pool["wild"] = max(0, pool.get("wild", 0) - remaining)

    @staticmethod
    def _is_attack_target_valid(engine, loc, opt):
        """Strict validation for attack targets, ensuring vulnerability and presence."""
        target_idx = opt.get('target_loc')
        eval_loc = engine.locations[target_idx] if target_idx is not None else loc
        oid = opt.get('id')

        # Minions/Thugs: Ensure they actually exist in the sector
        if oid == 'm': 
            return eval_loc.thugs > 0
            
        # Villain Vulnerability Gate
        if oid == 'v':
            return is_target_vulnerable(engine, engine.villain)[0]
            
        # Health-based Threats
        if oid == 'h':
            if not eval_loc.threat: return False
            return is_target_vulnerable(engine, eval_loc.threat)[0]

        # Sinister Six Token-based Weak Spots
        if oid in ['t_a', 't_h']:
            if not eval_loc.threat: return False
            # Check the 'Shotgun Seat' (shield_logic) to see if the Weak Spot is targetable
            return is_target_vulnerable(engine, eval_loc.threat)[0]

        # Sinister Six Boss-Specific Direct Attacks (atk_vulture, etc)
        if oid.startswith("atk_"):
            v_name = oid.replace("atk_", "")
            roster = getattr(engine, 'sinister_six_roster', {})
            v_data = roster.get(v_name, {})
            # Valid only if the player cleared the Weak Spot first
            return v_data.get("weak_spot_cleared", False)

        # 🚨 THE GATEKEEPER FIX: Allow custom logic overrides
        if "execute" in opt:
            return True

        return False # Fail closed to prevent 'Ghost' targets

    @staticmethod
    def _handle_targeted_attack(engine, hero, target_idx, damage=1, burst_mode=False):
        # ✅ Clean local imports grouped at the top of the method
        from src.logic.registry import get_villain_logic
        from src.systems.damage_system import DamageSystem
        from src.systems.token_system import TokenSystem
        from src.utils.helpers import Col
        
        target_loc = engine.locations[target_idx]
        logic = get_villain_logic(engine.villain.internal_id)
        
        # 🚨 THE ELITE SENSOR: Detects if Elite Thugs are present
        tid = str(getattr(target_loc.threat, 'id_internal', getattr(target_loc.threat, 'id', ''))).lower()
        is_elite = target_loc.threat and not target_loc.threat.cleared and "elite" in tid
        thug_cost = 2 if is_elite else 1
        thug_name = "Elite Thug" if is_elite else "Thug"

        remaining_dmg = damage
        hit_anything = False

        # 🌟 THE DYNAMIC LOOP: Spend down the damage pool
        while remaining_dmg > 0:
            opts = logic.get_attack_options(engine, hero, location_override=target_idx)
            opts.extend(logic.get_extra_attack_options(engine, target_loc, hero))

            for o in opts: o['target_loc'] = target_idx
            valid_opts = [o for o in opts if ActionSystem._is_attack_target_valid(engine, target_loc, o)]

            # 🚨 THE INTERCEPTOR: Dynamically filter and price options based on remaining damage pool
            display_opts = []
            for opt in valid_opts:
                if opt["id"] == "m": 
                    if not burst_mode and remaining_dmg < thug_cost: continue # Can't afford
                    opt["label"] = f"{opt['label'].replace('Thug', thug_name)} (Cost: {thug_cost} DMG)"
                    opt["cost"] = thug_cost
                else:
                    if not burst_mode and remaining_dmg < opt.get("cost", 1): continue
                    
                display_opts.append(opt)

            if not display_opts:
                if not hit_anything:
                    engine.log.append(Col.wrap(f"   (No valid targets at {target_loc.name})", Col.DARK_GRAY))
                return hit_anything

            pool_str = f" ({remaining_dmg} DMG POOL)" if remaining_dmg > 1 else ""
            print(f"\n--- {Col.wrap(f'STRIKE: {target_loc.name}{pool_str}', Col.YLW)} ---")
            for i, opt in enumerate(display_opts, 1):
                print(f" [{i}] {opt['label']}")
            print(" [0] Cancel / Finish Attack")

            choice = engine.ui.ask_choice(" >> ", 0, len(display_opts))
            if choice == 0: return hit_anything
            
            selected = display_opts[choice-1]
            hit_anything = True
            spent_dmg = selected.get("cost", 1)
            
            # 💥 RESOLUTION: Burst mode unleashes the entire remaining pool at once
            hits = remaining_dmg if burst_mode else 1
            
            if "execute" in selected: 
                for _ in range(hits): selected["execute"](engine)
            else: 
                if selected["id"] == "v":
                    for _ in range(hits):
                        if engine.villain.hp > 0: DamageSystem.deal_enemy_damage(engine, engine.villain, is_action=True)
                elif selected["id"] == "h":
                    for _ in range(hits):
                        if target_loc.threat and not target_loc.threat.cleared and target_loc.threat.hp > 0:
                            DamageSystem.deal_enemy_damage(engine, target_loc.threat, is_action=True)
                elif selected["id"] == "m":
                    TokenSystem.apply_thug_defeat(engine, target_loc, hero, amount=1)
                    
                    if burst_mode:
                        engine.log.append(Col.wrap(f"   💥 {thug_name} obliterated! ({remaining_dmg - spent_dmg} Damage Overkill) ", Col.DARK_GRAY))
                elif selected["id"] == "t_a":
                    for _ in range(hits): TokenSystem.apply_threat_token(engine, target_loc, "attack")
                else:
                    for _ in range(hits): logic.resolve_special_action(engine, target_loc, hero, selected["id"])
            
            if burst_mode:
                break # Burst mode instantly exits after the single massive strike
            else:
                remaining_dmg -= spent_dmg
            
        return hit_anything

    @staticmethod
    def _handle_targeted_heroic(engine, hero, target_idx, amount=2, burst_mode=False):
        from src.logic.registry import get_villain_logic
        from src.systems.token_system import TokenSystem
        from src.utils.helpers import Col
        
        target_loc = engine.locations[target_idx]
        logic = get_villain_logic(engine.villain.internal_id)
        
        remaining_val = amount
        hit_anything = False

        # 🚨 THE GHOST SHIFT: Temporarily move hero to evaluate the remote sector natively
        original_idx = hero.location_index
        hero.location_index = target_idx

        try:
            while remaining_val > 0:
                # 🚨 ONE SOURCE OF TRUTH: Fetch standard options directly from the logic baseline!
                opts = logic.get_heroic_options(engine, hero, location_override=target_idx)
                
                if hasattr(logic, 'get_extra_heroic_options'):
                    opts.extend(logic.get_extra_heroic_options(engine, target_loc, hero))

                # 🚨 THE INTERCEPTOR: Dynamically filter and price options based on remaining pool
                display_opts = []
                for opt in opts:
                    opt['target_loc'] = target_idx
                    if not burst_mode and remaining_val < opt.get("cost", 1): continue 
                    
                    label = opt['label']
                    cost = opt.get('cost', 1)
                    if "(Cost:" not in label:
                        opt['label'] = f"{label} (Cost: {cost} ★)"
                        
                    display_opts.append(opt)

                if not display_opts:
                    if not hit_anything:
                        engine.log.append(Col.wrap(f"   (No valid heroic targets at {target_loc.name})", Col.DARK_GRAY))
                    return hit_anything

                pool_str = f" ({remaining_val} ★ POOL)" if remaining_val > 1 else ""
                print(f"\n--- {Col.wrap(f'HEROIC ACTION: {target_loc.name}{pool_str}', Col.CYAN)} ---")
                for i, opt in enumerate(display_opts, 1):
                    print(f" [{i}] {opt['label']}")
                print(" [0] Cancel / Finish Action")

                choice = engine.ui.ask_choice(" >> ", 0, len(display_opts))
                if choice == 0: return hit_anything
                
                selected = display_opts[choice-1]
                hit_anything = True
                spent_val = selected.get("cost", 1)
                
                # 💥 RESOLUTION
                hits = remaining_val if burst_mode else 1
                
                if "execute" in selected: 
                    for _ in range(hits): selected["execute"](engine)
                else: 
                    if selected["id"] == "c":
                        for _ in range(hits): TokenSystem.apply_heroic(engine, target_loc, target_type="c")
                        if burst_mode:
                            engine.log.append(Col.wrap(f"   ✨ Rescued! ({remaining_val - spent_val} Heroic Overkill) ", Col.CYAN))
                    elif selected["id"] == "t":
                        for _ in range(hits): TokenSystem.apply_heroic(engine, target_loc, target_type="t")
                    else:
                        for _ in range(hits): 
                            if hasattr(logic, 'resolve_special_action'):
                                logic.resolve_special_action(engine, target_loc, hero, selected["id"])
                
                if burst_mode:
                    break 
                else:
                    remaining_val -= spent_val
                    
        finally:
            # 🚨 SNAP BACK
            hero.location_index = original_idx
            
        return hit_anything
