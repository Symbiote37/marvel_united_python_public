import sys
from src.utils.helpers import Col, ICON

class DamageSystem:
    @staticmethod
    def _check_nullification_gate(engine, hero):
        from src.systems.status_system import StatusSystem
        
        is_invulnerable = StatusSystem.has_status(hero, "invulnerable") or getattr(hero, 'is_invincible', False)
        is_evading = StatusSystem.has_status(hero, "evade")

        if is_invulnerable or is_evading:
            if is_evading:
                engine.log.append(Col.wrap(f" [EVASION] {hero.name} dodges the attack!", Col.CYAN))
                
                # 🔌 HEADLESS FIX for Evasion Reposition
                prompt_lines = [f"\n--- {Col.wrap('EVASION REPOSITION', Col.CYAN + Col.BOLD)} ---"]
                for i, loc in enumerate(engine.locations, 1):
                    prompt_lines.append(f" [{i}] {loc.name}")
                prompt_lines.append(" >> ")
                
                c = engine.ui.ask_choice("\n".join(prompt_lines), 1, len(engine.locations)) - 1
                hero.location_index = c
            else:
                custom_msg = getattr(hero, 'invincible_deflect_msg', f" [SHIELD] {hero.name} is protected!")
                engine.log.append(Col.wrap(custom_msg, Col.CYAN))
                
                # Martial Artist is quarantined. Silent pass-through.
                source = getattr(hero, 'deflection_source', None)
                if source == "hawkeye_martial_artist" or "redirects" in custom_msg:
                    pass 
                
            return True # Damage was nullified
        return False

    @staticmethod
    def _check_bodyguard(engine, hero, amount):
        from src.systems.status_system import StatusSystem
        for ally in engine.heroes:
            if ally != hero and ally.location_index == hero.location_index and StatusSystem.has_status(ally, "bodyguard"):
                if engine.ui.ask_yes_no(f"\n 🛡️ {ally.name} is guarding! Take the hit for {hero.name}?"):
                    engine.log.append(Col.wrap(f" 🛡️ BODYGUARD: {ally.name} intercepts the attack!", Col.YLW))
                    return True, DamageSystem.deal_hero_damage(engine, ally, amount)
        return False, False

    @staticmethod
    def _apply_damage_reduction(engine, hero, amount):
        from src.systems.status_system import StatusSystem
        if amount > 0 and StatusSystem.has_status(hero, "prevent_next_damage"):
            StatusSystem.decrement_status(hero, "prevent_next_damage")
            engine.log.append(Col.wrap(f" ✨ PROTECTED: Psionic Field absorbed 1 damage for {hero.name}!", Col.MAGENTA))
            amount -= 1
        return amount

    @staticmethod
    def _process_discard_loop(engine, hero, amount):
        from src.systems.status_system import StatusSystem
        for i in range(amount):
            if len(hero.hand) == 1 and StatusSystem.has_status(hero, "protect_last_card"):
                engine.log.append(Col.wrap(f" 🌟 PROTECTED: {hero.name}'s immortality triggers!", Col.CYAN + Col.BOLD))
                return True 

            if not hero.hand: return True 
            
            has_shield = False
            manager = getattr(engine, 'campaign_manager', None)
            if manager and manager.state.get('shields', 0) > 0: has_shield = True

            # 🔌 CONCATENATED HEADLESS MENU
            prompt_lines = [f"\n{Col.wrap(f' !!! DAMAGE ({i+1}/{amount}): {hero.name} must choose a card to lose !!!', Col.RED)}"]
            for idx, card in enumerate(hero.hand, 1):
                icons = " ".join([ICON.get(a, a) for a in card.get('actions', [])])
                prompt_lines.append(f" {idx}: [{icons}] {card.get('name', '')}")
            
            valid_options = [str(x) for x in range(1, len(hero.hand) + 1)]
            if has_shield: valid_options.append('h')
                
            prompt = f" Choose card (1-{len(hero.hand)})"
            if has_shield: prompt += f" or {Col.wrap('[h]', Col.CYAN)} for Shield"
            prompt_lines.append(f"{prompt}: ")
            
            # 🔌 UI ADAPTER: Passed positionally to avoid parameter naming mismatches across controllers
            choice_input = engine.ui.ask_raw("\n".join(prompt_lines), valid_options).strip().lower()

            if choice_input == 'h' and has_shield:
                manager.state['shields'] -= 1
                engine.log.append(Col.wrap(f" 🛡️ SHIELD USED: {hero.name} absorbed 1 damage!", Col.CYAN))
                manager.save_state()
            else:
                idx = int(choice_input)
                card = hero.hand.pop(idx - 1)
                hero.deck.append(card)
                engine.log.append(f"   💥 {hero.name} lost card to damage.")

        return False

    @staticmethod
    def deal_hero_damage(engine, hero, amount):
        """
        Processes damage to a hero. 
        Includes checks for Invulnerability, Evade, Bodyguard, and Shields.
        """
        # 1. THE NULLIFICATION GATE (Invulnerability & Evasion)
        if DamageSystem._check_nullification_gate(engine, hero):
            return False

        # 2. 🛡️ UNIVERSAL BODYGUARD CHECK
        rerouted, result = DamageSystem._check_bodyguard(engine, hero, amount)
        if rerouted:
            return result

        # 3. ⚛️ SCARLET WITCH: PSIONIC FIELD HOOK
        amount = DamageSystem._apply_damage_reduction(engine, hero, amount)
        if amount <= 0:
            return False

        # 4. STATE CHECK
        if getattr(hero, 'is_ko', False) or not hero.hand:
            return False

        # 5. DISCARD LOOP
        return DamageSystem._process_discard_loop(engine, hero, amount)

    @staticmethod
    def trigger_ko(engine, hero, silent=False):
        if getattr(hero, 'is_ko', False): return
        if silent:
            while hero.hand: hero.deck.insert(0, hero.hand.pop())        
        # 2. STATE UPDATE
        hero.is_ko = True
        
        # 🚨 SENSOR ADDED: Track the KO for the MVP screen
        if hasattr(engine, 'track_stat'):
            engine.track_stat(hero, "kos", 1)
        
        is_shield_mode = hasattr(engine, 'mode_handler') and engine.mode_handler.__class__.__name__ == "ShieldMode"
        if is_shield_mode: return

        engine.log.append(Col.wrap(f" 💀 {hero.name.upper()} IS KO'D!", Col.RED + Col.BOLD))
        if not hasattr(engine, 'queued_events'): engine.queued_events = []
        engine.queued_events.append({"type": "ko_bam", "hero": hero})
        
        from src.logic.registry import get_villain_logic
        logic = get_villain_logic(engine.villain.internal_id)
        if hasattr(logic, 'handle_hero_ko'): logic.handle_hero_ko(engine, hero)

    @staticmethod
    def deal_enemy_damage(engine, target_obj, amount=1, flavor=None, is_action=False):
        from src.logic.shield_logic import is_target_vulnerable
        from src.systems.mission_system import MissionSystem 
        
        vulnerable, shield_msg = is_target_vulnerable(engine, target_obj)
        if not vulnerable:
            engine.log.append(Col.wrap(shield_msg, Col.YLW))
            return False

        final_damage = amount
        if hasattr(engine.villain_logic, 'reduce_damage'):
            final_damage = engine.villain_logic.reduce_damage(engine, target_obj, amount, is_action)
        
        if final_damage <= 0: return True 

        target_obj.hp -= final_damage
        if target_obj == engine.villain and hasattr(engine.villain_logic, 'on_damage_taken'):
            engine.villain_logic.on_damage_taken(engine, target_obj, amount)
            
        if target_obj.hp <= 0:
            if getattr(target_obj, 'is_defeated_signal_fired', False): return True
            target_obj.is_defeated_signal_fired = True
            status = Col.wrap(f" 💀 DEFEATED: {target_obj.name}! ", Col.RED + Col.BOLD)
            engine.log.append(status) 

            if not hasattr(target_obj, 'plan_deck'): 
                target_obj.cleared = True
                MissionSystem.increment_mission(engine, "threats")
            else:
                engine.game_over = True
                engine.victory_status = "HEROES_WIN"
        else:
            verb = flavor if flavor else "damaged"
            engine.log.append(f"   💥 {target_obj.name} {verb}! ({target_obj.hp} HP left)")

        return True

    @staticmethod
    def apply_targeted_damage(engine, hero, loc_idx, amount, flavor):
        from src.systems.action_system import ActionSystem
        from src.systems.damage_system import DamageSystem
        from src.systems.token_system import TokenSystem
        from src.systems.villain_system import VillainSystem
        loc = engine.locations[loc_idx]
        opts = []

        for vt in VillainSystem.get_attackable_villains_at(engine, loc_idx):
            opts.append({"label": f"Villain: {vt['name']} (HP: {vt['hp']})", "data": vt, "type": "v"})
        if loc.threat and not loc.threat.cleared and getattr(loc.threat, 'hp', 0) > 0:
            opts.append({"label": f"Henchman: {loc.threat.name}", "obj": loc.threat, "type": "h"})
        if loc.thugs > 0:
            opts.append({"label": "A single Thug", "obj": None, "type": "t"})

        if not opts:
            engine.log.append(Col.wrap(f"   ! No valid targets for {flavor} in {loc.name}.", Col.YLW))
            return True 

        # ⚡ THE AUTO-TARGET REFLEX (Preserved)
        if len(opts) == 1:
            sel = opts[0]
            engine.log.append(Col.wrap(f" ⚡ Reflex Strike auto-targets {sel['label'].split(':')[0]}!", Col.CYAN))
        else:
            if flavor == "Martial Artist Counter":
                engine.log.append(Col.wrap(f" ⏳ REFLEXES: {hero.name} scans the room for a counter-attack target!", Col.MAGENTA))
                
            # 🔌 CONCATENATED HEADLESS MENU
            prompt_lines = [f"\n--- {Col.wrap(f'SELECT TARGET FOR {flavor.upper()} ({amount} DMG)', Col.RED)} ---"]
            for i, opt in enumerate(opts, 1): 
                prompt_lines.append(f" [{i}] {opt['label']}")
            prompt_lines.append(" >> ")
            
            choice = engine.ui.ask_choice("\n".join(prompt_lines), 1, len(opts))
            sel = opts[choice-1]
        
        if sel["type"] == "v":
            engine.track_stat(hero, "damage", amount) # 🚨 SENSOR ADDED
            v_info = sel["data"]
            if v_info["type"] == "ss_villain":
                v_info["ref"]["hp"] -= amount
                engine.log.append(Col.wrap(f" 💥 {hero.name} hit {v_info['name']} for {amount} damage!", Col.RED + Col.BOLD))
                if v_info["ref"]["hp"] <= 0:
                    v_info["ref"]["defeated"] = True
                    engine.log.append(Col.wrap(f" 💀 {v_info['name'].upper()} ELIMINATED!", Col.RED + Col.BOLD))
            else:
                DamageSystem.deal_enemy_damage(engine, v_info["ref"], amount=amount, flavor=flavor, is_action=True)
        elif sel["type"] == "h":
            engine.track_stat(hero, "damage", amount) # 🚨 SENSOR ADDED
            DamageSystem.deal_enemy_damage(engine, sel["obj"], amount=amount, flavor=flavor, is_action=True)
            if getattr(sel["obj"], 'hp', 1) <= 0:
                engine.track_stat(hero, "threats", 1) 
        elif sel["type"] == "t":
            TokenSystem.apply_thug_defeat(engine, loc, hero, amount=min(amount, loc.thugs))
        return True
