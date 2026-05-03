# src/systems/token_system.py

from src.ui.board import BoardRenderer
from src.utils.helpers import ICON, Col

class TokenSystem:
    @staticmethod
    def distribute_token(engine, source_hero, token_type, targets=None):
        """
        Standardized UI-agnostic method for 'Give X token to another Hero' abilities.
        """
        # 1. Define valid recipients (usually anyone but the source who isn't KO'd)
        if targets is None:
            targets = [h for h in engine.heroes if h != source_hero and not getattr(h, 'is_ko', False)]

        if not targets:
            engine.log.append(Col.wrap(" No eligible heroes to receive the token.", Col.DARK_GRAY))
            return False

        # 2. Selection logic (Auto-pick if only one choice, else use UI Adapter)
        if len(targets) == 1:
            selected = targets[0]
        else:
            print(f"\n{Col.wrap(' SELECT RECIPIENT:', Col.CYAN)} Who receives the {token_type} token?")
            for i, h in enumerate(targets, 1):
                print(f" [{i}] {h.name}")
            
            # 🔌 UI ADAPTER
            choice = engine.ui.ask_choice(" >> ", 1, len(targets))
            selected = targets[choice - 1]

        # 3. Apply and Log
        selected.add_token(token_type)
        engine.log.append(Col.wrap(f" {selected.name} received a {ICON.get(token_type, token_type)} token from {source_hero.name}!", Col.GRN))
        return True

    @staticmethod
    def use_stashed_token(engine, hero):
        """Allows a hero to activate a stashed token and add it to the active pool."""
        from src.systems.status_system import StatusSystem
        from src.utils.helpers import ICON
        
        # 🛡️ NORMALIZER: Ensure action_tokens exists and syncs with stashed_tokens
        if not hasattr(hero, 'action_tokens'):
            hero.action_tokens = getattr(hero, 'stashed_tokens', [])
            
        # If legacy stashed_tokens exists and is somehow a different list, merge it safely
        if hasattr(hero, 'stashed_tokens') and hero.stashed_tokens is not hero.action_tokens:
            hero.action_tokens.extend(hero.stashed_tokens)
            hero.stashed_tokens.clear() # Mutate in place, don't reassign
            
        # Point both attributes to the exact same memory list (Crucial for S.H.I.E.L.D. mode)
        hero.stashed_tokens = hero.action_tokens

        if not hero.action_tokens:
            engine.ui.acknowledge(" Your stash is empty. ")
            return False

        print(Col.wrap("\n--- SELECT TOKEN TO ACTIVATE ---", Col.CYAN + Col.BOLD))
        for i, t in enumerate(hero.action_tokens):
            print(f" [{i+1}] {ICON.get(t, t)}")
        print(" [0] Cancel")
        
        # 🔌 UI ADAPTER
        choice = engine.ui.ask_choice(" >> ", 0, len(hero.action_tokens))
        
        if choice == 0: 
            return False 
        
        idx = choice - 1
        # This now safely pops from the shared S.H.I.E.L.D. pool without breaking references!
        token_val = hero.action_tokens.pop(idx) 
        
        # 🚨 THE FIX: Map both string names AND literal icons back to the action key
        mapping = {
            ICON.get('attack', '✸'): "attack", "attack": "attack",
            ICON.get('move', '➡'): "move", "move": "move",
            ICON.get('heroic', '★'): "heroic", "heroic": "heroic",
            ICON.get('wild', '❖'): "wild", "wild": "wild"
        }
        pool_key = mapping.get(token_val, "wild")
        
        multiplier = 2 if StatusSystem.has_status(hero, "double_tokens") else 1
        
        if getattr(engine, 'active_pool', None) is None:
            engine.active_pool = {}
            
        engine.active_pool[pool_key] = engine.active_pool.get(pool_key, 0) + multiplier
        
        amt_str = f" (+{multiplier})" if multiplier > 1 else ""
        engine.log.append(f" ✨ {hero.name} activated a {ICON.get(token_val, token_val)} token{amt_str}. ")
        
        # 🕸️ GENERIC HOOK: Broadcast that a token was explicitly cashed in
        if hasattr(hero, 'process_triggers'):
            hero.process_triggers("on_token_used", engine, token_type=pool_key)
        return True

    @staticmethod
    def add_token(engine, loc_idx, t_type, overflow_tracker):
        """Adds a single token to a location, respecting blockades and handling overflows."""
        loc = engine.locations[loc_idx]

        # 🛑 THE GATE: Is the location already full?
        if loc.total_figures() >= loc.capacity:
            # Only trigger the overflow event if we haven't done so this phase
            if loc_idx not in overflow_tracker:
                overflow_tracker.add(loc_idx)
                engine.log.append(Col.wrap(f"  OVERFLOW: {loc.name}", Col.RED))
                
                # Fire the villain's specific overflow punishment
                if hasattr(engine.villain, 'on_overflow'):
                    engine.villain.on_overflow(engine, loc, t_type)
                    
            return # Silently reject the token since the location is full

        # If there's room, let the VillainSystem physically place the token
        from src.systems.villain_system import VillainSystem
        thugs = 1 if t_type == "thugs" else 0
        civs = 1 if t_type == "civilians" else 0
        VillainSystem.add_figures(engine, loc_idx, thugs=thugs, civs=civs)

    @staticmethod
    def distribute_from_villain(engine, add_data):
        v_idx = engine.villain.location_index
        offsets = {"left": -1, "center": 0, "right": 1}
        overflowed_this_turn = set()
        
        for side, offset in offsets.items():
            if side in add_data:
                target_idx = (v_idx + offset) % 6
                counts = add_data[side]
                
                for _ in range(counts.get("thugs", 0)):
                    TokenSystem.add_token(engine, target_idx, "thugs", overflowed_this_turn)
                for _ in range(counts.get("civilians", 0)):
                    TokenSystem.add_token(engine, target_idx, "civilians", overflowed_this_turn)
                
                BoardRenderer.render({"engine": engine})

    @staticmethod
    def apply_heroic(engine, loc, amount=1, target_type="c", hero=None):
        from src.systems.mission_system import MissionSystem
        from src.systems.status_system import StatusSystem
        
        # 🔌 Automatically grab the active hero if none was specifically passed
        if hero is None:
            hero = engine.heroes[engine.current_hero_index]

        if target_type == "c":
            if loc.civilians > 0:
                # Calculate exactly how many were saved to prevent over-counting
                actual_rescued = min(loc.civilians, amount)
                loc.civilians -= actual_rescued
                
                # 🚨 SENSOR ADDED: Track Civilians Rescued
                if hasattr(engine, 'track_stat'):
                    engine.track_stat(hero, "civs", actual_rescued)
                
                if MissionSystem.increment_mission(engine, "civilians"):
                    engine.log.append(f" {ICON['civilian']} Civilian Rescued! ")
                    
                    # 🚨 THE CLEAN FIX: Broadcast the rescue to the Bus
                    from src.systems.special_abilities import SpecialAbilitySystem
                    SpecialAbilitySystem.trigger_event(engine, hero, "on_civilian_rescued")
                    
                    return True
        elif target_type == "t":
            loc.threat.heroic_req -= amount
            if loc.threat.heroic_req <= 0:
                loc.threat.cleared = True
                
                # 🚨 SENSOR ADDED: Track Threat Diffused
                if hasattr(engine, 'track_stat'):
                    engine.track_stat(hero, "threats", 1)
                
                diverted = False
                if hasattr(engine, 'mode_handler') and hasattr(engine.mode_handler, 'try_intercept_threat_token'):
                    diverted = engine.mode_handler.try_intercept_threat_token()
                
                if not diverted:
                    MissionSystem.increment_mission(engine, "threats")
                    
                engine.log.append(Col.wrap(f" 🛡️ THREAT DIFFUSED: {loc.threat.name}! ", Col.GRN))
                return True
                
        elif target_type == "x":
            loc.crisis_tokens -= 1
            engine.log.append(Col.wrap(f" ✨ Crisis cleared from {loc.name}! ", Col.GRN))
            return True
            
        return False

    @staticmethod
    def apply_thug_defeat(engine, loc, hero, amount=1):
        from src.systems.mission_system import MissionSystem
        from src.systems.status_system import StatusSystem
        
        if loc.thugs > 0:
            # Clamp removal to actual thugs present
            actual_removal = min(loc.thugs, amount)
            loc.thugs -= actual_removal
            engine.track_stat(hero, "thugs", actual_removal) # 🚨 SENSOR ADDED
            
            for _ in range(actual_removal):
                if MissionSystem.increment_mission(engine, "thugs"):
                    engine.log.append(f" {ICON['thug']} {hero.name} defeated a Thug. ")
                    
                    # 🚨 THE CLEAN FIX: Broadcast the defeat to the Bus
                    from src.systems.special_abilities import SpecialAbilitySystem
                    SpecialAbilitySystem.trigger_event(engine, hero, "on_thug_defeated")
                    
                    # 🕸️ GENERIC HOOK: Broadens to any registered listener (Legacy Support)
                    if hasattr(hero, 'process_triggers'):
                        hero.process_triggers("on_thug_defeat", engine)
                
            return True
        return False

    @staticmethod
    def apply_threat_token(engine, loc, token_type, amount=1):
        from src.systems.mission_system import MissionSystem
        
        if loc.threat and not loc.threat.cleared:
            if token_type == "heroic":
                loc.threat.heroic_tokens = getattr(loc.threat, 'heroic_tokens', 0) + amount
            elif token_type == "move":
                loc.threat.move_tokens = getattr(loc.threat, 'move_tokens', 0) + amount
            elif token_type == "attack":
                loc.threat.attack_tokens = getattr(loc.threat, 'attack_tokens', 0) + amount

            engine.log.append(f" ✨ {token_type.capitalize()} token applied to {loc.threat.name}. ")
            
            h_met = getattr(loc.threat, 'heroic_tokens', 0) >= getattr(loc.threat, 'heroic_req', 0)
            m_met = getattr(loc.threat, 'move_tokens', 0) >= getattr(loc.threat, 'move_req', 0)
            a_met = getattr(loc.threat, 'attack_tokens', 0) >= getattr(loc.threat, 'attack_req', 0)
            
            if h_met and m_met and a_met:
                loc.threat.cleared = True
                
                diverted = False
                if hasattr(engine, 'mode_handler'):
                    diverted = engine.mode_handler.try_intercept_threat_token()
                
                if not diverted:
                    MissionSystem.increment_mission(engine, "threats")
                
                engine.log.append(Col.wrap(f" 💥 THREAT CLEARED: {loc.threat.name}! ", Col.GRN + Col.BOLD))
                
                if hasattr(engine.villain_logic, 'on_threat_defeated'):
                    engine.villain_logic.on_threat_defeated(engine, loc.threat)
