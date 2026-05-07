from src.utils.helpers import Col

class InfinityGauntletLocationLogic:
    @staticmethod
    def token_for_card(engine, hero, effect):
        tokens = getattr(hero, 'action_tokens', []) + getattr(hero, 'stashed_tokens', [])
        if not tokens: return
        if Col.prompt_y_n("🍎 TOKEN FOR CARD", effect['text']):
            print("\n Select token to discard:")
            for i, t in enumerate(tokens, 1): print(f" ({i}) {t}")
            t_idx = Col.get_choice(" >> ", 1, len(tokens)) - 1
            
            if tokens[t_idx] in getattr(hero, 'action_tokens', []): 
                hero.action_tokens.remove(tokens[t_idx])
            else: 
                hero.stashed_tokens.remove(tokens[t_idx])
                
            hero.draw_cards(1)
            engine.log.append(f" 🍎 {hero.name} traded a token for 1 card.")

    @staticmethod
    def action_boost(engine, hero, effect):
        options = []
        
        # 1. Scan for Uncleared Threats
        for l in engine.locations:
            if getattr(l, 'threat', None) and not getattr(l.threat, 'cleared', False):
                options.append({
                    "type": "threat",
                    "label": f"{l.threat.name} (at {l.name})",
                    "target": l
                })
                
        # 2. Scan for Active Power-Ups (If playing Infinity Gauntlet Mode)
        pu_manager = getattr(engine.mode_handler, 'power_up_manager', None)
        active_pu = getattr(pu_manager, 'state', None) and getattr(pu_manager.state, 'active_pu_token', None)
        
        if active_pu:
            reqs = active_pu.get("req", {})
            progress = pu_manager.state.pu_progress
            for req_type, target in reqs.items():
                if req_type != "threat" and progress.get(req_type, 0) < target:
                    options.append({
                        "type": "power_up",
                        "label": f"Power-Up: {active_pu['name']} (Requires {req_type.upper()})",
                        "target_type": req_type,
                        "manager": pu_manager
                    })

        if not options: return

        # 3. Prompt the user
        if Col.prompt_y_n("🪄 SANCTUM SANCTORUM", effect['text']):
            print(Col.wrap("\n Select a target to receive a free Action token:", Col.CYAN))
            
            for i, opt in enumerate(options, 1):
                print(f" [{i}] {opt['label']}")
                
            choice = Col.get_choice(" >> ", 1, len(options)) - 1
            selected = options[choice]
            
            # 4. Route the Action into the correct mechanical pipeline
            if selected["type"] == "threat":
                target_loc = selected["target"]
                threat = target_loc.threat
                
                if getattr(threat, 'hp', 0) > 0:
                    # It's a Henchman (Requires Attack ✸)
                    from src.systems.damage_system import DamageSystem
                    DamageSystem.deal_enemy_damage(engine, threat, amount=1, flavor="Sanctum Magic")
                    engine.log.append(Col.wrap(f" 🪄 SANCTUM SANCTORUM: A free ✸ hit {threat.name}!", Col.MAGENTA))
                else:
                    # It's a Standard Threat (Can require Heroic ★, Move ➡, or Attack ✸)
                    from src.systems.token_system import TokenSystem
                    
                    unmet = []
                    if getattr(threat, 'heroic_tokens', 0) < getattr(threat, 'heroic_req', 0): unmet.append("heroic")
                    if getattr(threat, 'move_tokens', 0) < getattr(threat, 'move_req', 0): unmet.append("move")
                    if getattr(threat, 'attack_tokens', 0) < getattr(threat, 'attack_req', 0): unmet.append("attack")
                    
                    if not unmet:
                        # Failsafe fallback
                        TokenSystem.apply_threat_token(engine, target_loc, "heroic")
                    elif len(unmet) == 1:
                        # Auto-route if there is only one valid option
                        TokenSystem.apply_threat_token(engine, target_loc, unmet[0])
                    else:
                        # Prompt if the threat has mixed requirements
                        print(Col.wrap(f"\n Select requirement to fill on {threat.name}:", Col.CYAN))
                        for i, req in enumerate(unmet, 1):
                            print(f" [{i}] {req.capitalize()} Token")
                        req_choice = Col.get_choice(" >> ", 1, len(unmet)) - 1
                        TokenSystem.apply_threat_token(engine, target_loc, unmet[req_choice])
                        
                    # (Duplicate engine.log.append removed from here)

            elif selected["type"] == "power_up":
                req_type = selected["target_type"]
                mgr = selected["manager"]
                mgr.state.pu_progress[req_type] += 1
                engine.log.append(Col.wrap(f" 🪄 SANCTUM SANCTORUM: A free token was channeled into {active_pu['name']}!", Col.MAGENTA))

    @staticmethod
    def ko_for_threat(engine, hero, effect):
        """
        VORMIR: A soul for a soul.
        Rule: Must have ANOTHER hero at this location to sacrifice.
        Rule: Clears ONE uncleared threat elsewhere on the board.
        """
        loc = engine.locations[hero.location_index]
        
        # 1. FIND SACRIFICE CANDIDATES (Must be ANOTHER hero at this location)
        others = [
            h for h in engine.heroes 
            if h != hero and h.location_index == hero.location_index and not getattr(h, 'is_ko', False)
        ]
        
        # 2. FIND TARGET THREATS (Any uncleared threat on the board)
        targets = [
            l for l in engine.locations 
            if l.threat and not getattr(l.threat, 'cleared', False)
        ]
        
        # 3. STRICT GATEKEEPER: Must have a victim and a target
        if not others or not targets:
            return 

        if Col.prompt_y_n("☠️ VORMIR: A SOUL FOR A SOUL", effect['text']):
            # Step A: Choose the Sacrifice
            print("\n Select a hero to sacrifice:")
            for i, h in enumerate(others, 1):
                print(f" ({i}) {h.name}")
            
            sacrifice_idx = Col.get_choice(" >> ", 1, len(others)) - 1
            sacrifice = others[sacrifice_idx]
            
            # Step B: Choose the Target Threat
            print("\n Select Threat to eliminate:")
            for i, t_loc in enumerate(targets, 1):
                print(f" ({i}) {t_loc.threat.name} (at {t_loc.name})")
            
            target_idx = Col.get_choice(" >> ", 1, len(targets)) - 1
            target_loc = targets[target_idx]
            
            # Step C: Resolution
            from src.systems.damage_system import DamageSystem
            from src.systems.mission_system import MissionSystem
            
            # 🚨 THE LETHAL TRADE: 
            # We call trigger_ko with silent=True to bypass discard menus 
            # and immediately process the sacrifice as a 6-damage equivalent event.
            DamageSystem.trigger_ko(engine, sacrifice, silent=True)
            
            # Threat is cleared
            target_loc.threat.cleared = True
            
            # We increment the mission which handles clearing the figure from the board
            MissionSystem.increment_mission(engine, "threats")
            
            engine.log.append(Col.wrap(f" ☠️ {sacrifice.name} fell to clear {target_loc.threat.name}!", Col.RED + Col.BOLD))
            
            # Note: The BAM will be processed by the LocationSystem pulse 
            # immediately after this method returns.
            if hasattr(engine.villain_logic, 'on_threat_defeated'):
                engine.villain_logic.on_threat_defeated(engine, target_loc.threat)

    @staticmethod
    def nidavellir_forge(engine, hero, effect):
        if Col.prompt_y_n("⚒️ THE FORGE", effect['text']):
            hero.add_token("attack")
            msg = " ⚒️ Nidavellir: Gained +1 ✸."
            if hero.hand and input(" Discard 1 card for another ✸ token? (y/n): ").strip().lower() == 'y':
                print("\n Select card to discard (Bottom of Deck):")
                for i, c in enumerate(hero.hand, 1): print(f" ({i}) {Col._get_card_label(c)}")
                hero.deck.insert(0, hero.hand.pop(Col.get_choice(" >> ", 1, len(hero.hand)) - 1))
                hero.add_token("attack")
                msg = " ⚒️ Nidavellir: Forged +2 ✸!"
            engine.log.append(msg)

    @staticmethod
    def token_from_heroes(engine, hero, effect):
        others = [h for h in engine.heroes if h != hero and h.location_index == hero.location_index and not getattr(h, 'is_ko', False)]
        if not others: return
        if Col.prompt_y_n("🛡️ ALLY BOOST", effect['text']):
            for _ in range(len(others)): hero.add_token("wild")
            engine.log.append(f" 🛡️ {hero.name} gained {len(others)} ❖ token(s) from allies!")

    @staticmethod
    def discard_for_tokens(engine, hero, effect):
        if not hero.hand: return
        if Col.prompt_y_n("🪑 POWER GATHERING", effect['text']):
            print("\n Select card to discard (Bottom of Deck):")
            for i, c in enumerate(hero.hand, 1): print(f" ({i}) {Col._get_card_label(c)}")
            hero.deck.insert(0, hero.hand.pop(Col.get_choice(" >> ", 1, len(hero.hand)) - 1))
            
            hero.add_token("attack")
            hero.add_token("attack")
            engine.log.append(f" 🪑 {hero.name} discarded a card for +2 ✸!")

    @staticmethod
    def move_thanos(engine, hero, effect):
        if engine.villain.location_index == hero.location_index: return
        if Col.prompt_y_n("🪐 LURE VILLAIN", effect['text']):
            engine.villain.location_index = hero.location_index
            engine.log.append(f" 🪐 {hero.name} lured the Villain to their location!")

    @staticmethod
    def swap_the_storyline(engine, hero, effect):
        hero_cards = [(idx, c) for idx, c in enumerate(engine.storyline.cards) if 'owner' in c]
        if len(hero_cards) < 2: return
        
        if Col.prompt_y_n("🌀 ALTER TIMELINE", effect['text']):
            print("\n Select FIRST card to swap:")
            for i, (s_idx, c) in enumerate(hero_cards, 1): print(f" ({i}) {c.get('owner')}'s {Col._get_card_label(c)}")
            first = Col.get_choice(" >> ", 1, len(hero_cards)) - 1
            
            print("\n Select SECOND card to swap:")
            for i, (s_idx, c) in enumerate(hero_cards, 1):
                if i - 1 == first: continue
                print(f" ({i}) {c.get('owner')}'s {Col._get_card_label(c)}")
            second = Col.get_choice(" >> ", 1, len(hero_cards)) - 1
            
            idx1, idx2 = hero_cards[first][0], hero_cards[second][0]
            engine.storyline.cards[idx1], engine.storyline.cards[idx2] = engine.storyline.cards[idx2], engine.storyline.cards[idx1]
            engine.log.append(Col.wrap(" 🌀 Timeline altered! Two Hero cards swapped positions in the Storyline.", Col.MAGENTA))
