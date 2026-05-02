from src.utils.helpers import Col, ICON
from src.logic.shield_logic import is_target_vulnerable

class GotGLocationLogic:
    @staticmethod
    def gain_2_tokens(engine, hero, effect):
        # Combines active and stashed tokens for the trade menu
        tokens = getattr(hero, 'action_tokens', []) + getattr(hero, 'stashed_tokens', [])
        if not tokens: return
        
        if Col.prompt_y_n("💀 TRADE TOKENS", effect['text']):
            print("\n Select token to discard:")
            for i, t in enumerate(tokens, 1): 
                print(f" ({i}) {ICON.get(t, t)}")
            
            t_idx = Col.get_choice(" >> ", 1, len(tokens)) - 1
            chosen_token = tokens[t_idx]
            
            if chosen_token in getattr(hero, 'action_tokens', []): 
                hero.action_tokens.remove(chosen_token)
            else: 
                hero.stashed_tokens.remove(chosen_token)
                
            print("\n Select 2 tokens to gain ([1] ➡ Move, [2] ✸ Attack, [3] ★ Heroic):")
            tok_map = {1: "move", 2: "attack", 3: "heroic"}
            for _ in range(2): 
                hero.add_token(tok_map[Col.get_choice(" >> ", 1, 3)])
            
            engine.log.append(f" 💀 {hero.name} traded 1 token for 2 new ones.")

    @staticmethod
    def kyla_threat_token(engine, hero, effect):
        if not hero.hand: return
        threat_locs = [l for l in engine.locations if l.threat and not l.threat.cleared]
        if not threat_locs: return
        
        if Col.prompt_y_n("🪐 SABOTAGE THREAT", effect['text']):
            # 1. DISCARD PHASE
            print("\n Select card to discard (Bottom of Deck):")
            for i, c in enumerate(hero.hand, 1):
                icons = "".join([ICON.get(a, a) for a in c.get('actions', [])])
                print(f" ({i}) [{icons}] {c.get('name', 'Card')}")
            
            hero.deck.insert(0, hero.hand.pop(Col.get_choice(" >> ", 1, len(hero.hand)) - 1))
            
            # 2. TARGET SELECTION
            print("\n Select Threat to place token on:")
            for i, l in enumerate(threat_locs, 1): 
                print(f" ({i}) {l.threat.name} (at {l.name})")
            
            target_loc = threat_locs[Col.get_choice(" >> ", 1, len(threat_locs)) - 1]
            threat = target_loc.threat

            # 3. THE SMART SCANNER
            # Tapping into requirement logic to identify valid options
            is_vulnerable, _ = is_target_vulnerable(engine, threat)
            valid_types = []

            if is_vulnerable:
                # 1. Henchman HP (Attack only)
                if getattr(threat, 'hp', 0) > 0 or getattr(threat, 'health', 0) > 0:
                    valid_types.append("attack")
                
                # 2. Requirement-based (Attack, Move, or Heroic)
                if getattr(threat, 'attack_req', 0) > getattr(threat, 'attack_tokens', 0):
                    if "attack" not in valid_types: valid_types.append("attack")
                    
                if getattr(threat, 'move_req', 0) > getattr(threat, 'move_tokens', 0):
                    valid_types.append("move")
                    
                if getattr(threat, 'heroic_req', 0) > getattr(threat, 'heroic_tokens', 0):
                    valid_types.append("heroic")

            # 4. RESOLUTION
            final_choice = None
            if len(valid_types) == 0:
                # Default fallback for simple non-attribute threats
                final_choice = "heroic"
            elif len(valid_types) == 1:
                # AUTO-APPLY: Only one logical requirement exists
                final_choice = valid_types[0]
                engine.log.append(f" 🪐 SABOTAGE: Automatically applied {final_choice.capitalize()} to {threat.name}.")
            else:
                # COMBO: User chooses which lock to pick
                print(f"\n--- {Col.wrap('COMBO THREAT DETECTED', Col.YLW)} ---")
                for i, t in enumerate(valid_types, 1):
                    print(f" [{i}] {ICON.get(t, t)} {t.capitalize()}")
                final_choice = valid_types[Col.get_choice(" >> ", 1, len(valid_types)) - 1]

            # 5. EXECUTION
            from src.systems.token_system import TokenSystem
            if final_choice == "attack" and (getattr(threat, 'hp', 0) > 0 or getattr(threat, 'health', 0) > 0):
                from src.systems.damage_system import DamageSystem
                DamageSystem.deal_enemy_damage(engine, threat, amount=1, flavor="Sabotaged")
            else:
                TokenSystem.apply_threat_token(engine, target_loc, final_choice)
            
            return True
        return False
