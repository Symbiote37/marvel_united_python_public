# src/logic/heroes/ms_marvel.py
from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("ms_marvel")
@SpecialAbilitySystem.register("ms-marvel") # Safety net for hyphenated IDs
class MsMarvelLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id", "").replace("-", "_")
        if sid == "ms_marvel_elongation": return MsMarvelLogic._elongation(engine, hero)
        elif sid == "ms_marvel_morphogenetics": return MsMarvelLogic._morphogenetics(engine, hero)
        elif sid == "ms_marvel_appearance_alteration": return MsMarvelLogic._appearance_alteration(engine, hero)
        return False

    @staticmethod
    def _elongation(engine, hero):
        from src.systems.status_system import StatusSystem
        
        print(f"\n--- {Col.wrap('🤜 ELONGATION', Col.YLW)} ---")
        print(" [1] Execute: Attacks reach adjacent locations")
        print(" [0] Cancel")
        
        # 🔌 UI ADAPTER
        if engine.ui.ask_choice(" >> ", 0, 1) != 1: return False
        
        # 🚨 THE FIX: Use the StatusSystem to apply a temporary duration
        # The engine checks for "range" and will auto-remove it at the end of the turn
        StatusSystem.apply_status(hero, "range", duration=1) 
        
        engine.log.append(Col.wrap(f" 🤜 {hero.name} stretches out! (Attacks can target adjacent locations)", Col.YLW))
        return True

    @staticmethod
    def _morphogenetics(engine, hero):
        is_shield_mode = hasattr(engine, 'mode_handler') and engine.mode_handler.__class__.__name__ == "ShieldMode"
        
        # 1. 🛡️ "YOU = THE PLAYER": Use the global ActionSystem ownership logic
        eligible_indices = []
        for idx, c in enumerate(engine.storyline.cards):
            owner_raw = c.get('owner')
            if not owner_raw or owner_raw == engine.villain.name:
                continue # Ignore Villain/Master Plan cards
                
            owner_name = owner_raw.name if hasattr(owner_raw, 'name') else str(owner_raw)
            
            # Solo Mode: Access ANY hero card. Standard: Access only your own.
            if is_shield_mode or owner_name == hero.name:
                # Prevent self-swap of the current Morphogenetics card!
                if c.get("special_id") != "ms_marvel_morphogenetics":
                    eligible_indices.append(idx)
                    
        # 2. Determine maximum possible swaps
        max_swaps = min(len(hero.hand), len(eligible_indices))
        
        if max_swaps == 0:
            engine.log.append(Col.wrap(f" 🧬 {hero.name}'s Morphogenetics fizzled! (No valid cards available to swap)", Col.YLW))
            return False
            
        print(f"\n--- {Col.wrap('🧬 MORPHOGENETICS', Col.PURP)} ---")
        print(f" How many cards would you like to swap? (0 to {max_swaps})")
        num_swaps = engine.ui.ask_choice(" >> ", 0, max_swaps)
        
        if num_swaps == 0:
            return False
            
        from src.ui.board import BoardRenderer
        color_map = {h.name: BoardRenderer.HERO_COLORS[i % len(BoardRenderer.HERO_COLORS)] for i, h in enumerate(engine.heroes)}
            
        # 3. Execute the swaps via a selection loop
        for _ in range(num_swaps):
            # A. Pick from Hand
            print(f"\n--- {Col.wrap('HAND SELECTION', Col.CYAN)} ---")
            for i, c in enumerate(hero.hand):
                actions_str = ", ".join([a.upper() for a in c.get('actions', [])])
                print(f" [{i+1}] {c.get('name', 'Action Card')} [{actions_str}]")
            h_choice = engine.ui.ask_choice(" Swap out >> ", 1, len(hero.hand)) - 1
            hand_card = hero.hand.pop(h_choice) 
            
            # B. Pick from Storyline
            print(f"\n--- {Col.wrap('STORYLINE SELECTION', Col.CYAN)} ---")
            for i, sl_idx in enumerate(eligible_indices):
                c = engine.storyline.cards[sl_idx]
                
                o_raw = c.get('owner')
                o_name = o_raw.name if hasattr(o_raw, 'name') else str(o_raw) if o_raw else "Unknown"
                c_color = color_map.get(o_name, Col.CYAN)
                o_display = Col.wrap(f" ({o_name})", c_color)
                
                actions_str = ", ".join([a.upper() for a in c.get('actions', [])])
                print(f" [{i+1}] {c.get('name', 'Action Card')} [{actions_str}]{o_display}")
                
            sl_choice = engine.ui.ask_choice(" Pull in >> ", 1, len(eligible_indices)) - 1
            actual_sl_idx = eligible_indices.pop(sl_choice)
            sl_card = engine.storyline.cards[actual_sl_idx]
            
            # C. Execute Swap (Preserving the original hero's identity rule)
            if 'owner' not in hand_card: 
                hand_card['owner'] = hero if is_shield_mode else hero.name
            hand_card['type'] = 'hero'
            
            hero.hand.append(sl_card)
            engine.storyline.cards[actual_sl_idx] = hand_card
            
        card_word = "card" if num_swaps == 1 else "cards"
        engine.log.append(Col.wrap(f" 🧬 {hero.name} alters her molecular structure! (Swapped {num_swaps} {card_word} with the Storyline)", Col.PURP))
        return True

    @staticmethod
    def _appearance_alteration(engine, hero):
        print(f"\n--- {Col.wrap('👤 APPEARANCE ALTERATION', Col.PURP)} ---")
        print(" [1] Execute: Convert all active symbols to ❖")
        print(" [0] Cancel")
        
        if engine.ui.ask_choice(" >> ", 0, 1) != 1: return False
        
        total = sum(engine.active_pool.values())
        engine.active_pool = {"move": 0, "attack": 0, "heroic": 0, "wild": total}
        
        # Safely get the icon if the dictionary doesn't have it defined exactly
        wild_icon = ICON.get('wild', '❖')
        engine.log.append(Col.wrap(f" 👤 {hero.name} shifts form! (All pool symbols converted to {wild_icon})", Col.PURP))
        return True
