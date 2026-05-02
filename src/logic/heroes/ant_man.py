# src/logic/heroes/ant_man.py
from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("ant-man")
class AntManLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        """ 
        The standardized 'Front Door' for Ant-Man's special abilities.
        """
        sid = card.get("special_id")
        
        if sid == "ant-man_grow":
            return AntManLogic._grow(engine, hero)
        elif sid == "ant-man_quantum_leap":
            # 🚨 THE FIX: Pass the card so we can swap it in memory
            return AntManLogic._quantum_leap(engine, hero, card)
            
        return False

    @staticmethod
    def _grow(engine, hero):
        from src.systems.action_system import ActionSystem
        
        engine.log.append(Col.wrap(f" 🧱 GIANT-MAN PROTOCOL: {hero.name} grows to massive size!", Col.RED))

        # 1. The Coupled Move
        # The player MUST complete this move phase to unlock the attack.
        if not ActionSystem._handle_move(engine, hero, free=True):
            return False

        # 2. THEN attack x3 against one target
        success = ActionSystem._handle_targeted_attack(engine, hero, hero.location_index, damage=3, burst_mode=True)
        
        if not success:
            engine.log.append(Col.wrap("   (Stomp cancelled or no valid targets)", Col.DARK_GRAY))
            
        return True 

    @staticmethod
    def _quantum_leap(engine, hero, card):
        from src.systems.action_system import ActionSystem
        import copy
        
        # 1. Find all valid Ant-Man cards currently in the storyline
        valid_cards = []
        for i, c in enumerate(engine.storyline.cards):
            # 🚨 THE FIX: Exclude the current card and any facedown cards!
            if c.get("owner") == hero.name and c is not card and not c.get("is_facedown"):
                valid_cards.append((i, c))
                
        if not valid_cards:
            engine.log.append(Col.wrap(" ! No previous cards in Storyline to swap. ", Col.RED))
            return False
            
        # 2. Build the UI prompt options
        options = []
        for _, c in valid_cards:
            actions_list = c.get('actions', [])
            actions_str = " ".join([ICON.get(a, f"[{a}]") for a in actions_list]) if actions_list else "None"
            special_str = f" | Special: {c.get('special_id').replace('_', ' ').title()}" if c.get('special_id') else ""
            options.append(f"{actions_str}{special_str}")
            
        # 3. Ask the player to choose
        choice_idx = engine.ui.ask_choice(Col.wrap(f"\n ⚛️ QUANTUM LEAP: Select a timeline to jump to: ", Col.CYAN), options, return_index=True)

        
        if choice_idx is None:
            engine.log.append(Col.wrap("   (Quantum Leap aborted)", Col.DARK_GRAY))
            return False
            
        storyline_idx, chosen_card = valid_cards[choice_idx]
        
        engine.log.append(Col.wrap(f" ⚛️ QUANTUM Leap: {hero.name} jumped to a new timeline! ", Col.CYAN))
        
        # 4. Perform the Swap
        # Slot the Quantum Leap card into the old Storyline position
        engine.storyline.cards[storyline_idx] = copy.deepcopy(card)
        
        # Add the chosen card's actions to the active pool
        for icon in chosen_card.get('actions', []):
            engine.active_pool[icon] = engine.active_pool.get(icon, 0) + 1
            
        # 🚨 THE FIX: Only trigger instantly if it is an auto-trigger (like Shrink)
        if chosen_card.get('special_id') and ActionSystem.is_auto_trigger(chosen_card):
            ActionSystem.resolve_special_id(engine, hero, chosen_card)
            
        # Mutate the current card in memory so it acts like the chosen card going forward
        card.clear()
        card.update(chosen_card)
        
        return True
