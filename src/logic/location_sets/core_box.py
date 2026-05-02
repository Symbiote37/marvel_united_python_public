# src/logic/location_sets/core_box.py

import random
from src.utils.helpers import Col

class CoreLocationLogic:
    @staticmethod
    def remove_crisis_effect(engine, hero, effect):
        if not hero.hand: return
        targets = []
        for h in engine.heroes:
            if getattr(h, 'crisis_tokens', 0) > 0: targets.append({"obj": h, "name": h.name, "type": "hero", "count": getattr(h, 'crisis_tokens', 0)})
        for l in engine.locations:
            if getattr(l, 'crisis_tokens', 0) > 0: targets.append({"obj": l, "name": l.name, "type": "loc", "count": getattr(l, 'crisis_tokens', 0)})

        if not targets: return 
        if engine.ui.ask_yes_no(f"\n 🛡️ CLEAR CRISIS: {effect['text']} (y/n): "):
            print("\n Select card to recycle (Bottom of Deck):")
 
            # 🎨 Create a dynamic color map based on current roster
            from src.ui.board import BoardRenderer
            color_map = {h.name: BoardRenderer.HERO_COLORS[i % len(BoardRenderer.HERO_COLORS)] for i, h in enumerate(engine.heroes)}
            
            for i, c in enumerate(hero.hand, 1):
                owner_raw = c.get('owner')
                owner_name = owner_raw.name if hasattr(owner_raw, 'name') else str(owner_raw) if owner_raw else ""
                
                # 🚨 THE FIX: Look up the color, and apply it instead of Col.CYAN
                c_color = color_map.get(owner_name, Col.CYAN)
                owner_display = Col.wrap(f" ({owner_name})", c_color) if owner_name and owner_name != "None" else ""
                
                print(f" ({i}) {Col._get_card_label(c)}{owner_display}")
            c_idx = engine.ui.ask_choice(" >> ", 1, len(hero.hand))
            hero.deck.insert(0, hero.hand.pop(c_idx - 1))

            print("\n Select target to clear Crisis from:")
            for i, t in enumerate(targets, 1): print(f" ({i}) {t['name']} ({t['count']} tokens)")
            selection = targets[engine.ui.ask_choice(" >> ", 1, len(targets)) - 1]
            selection['obj'].crisis_tokens -= 1
            engine.log.append(f" 🛡️ {hero.name} cleared 1 Crisis from {selection['name']}.")

    @staticmethod
    def swap_with_storyline(engine, hero, effect):
        story_cards = getattr(engine.storyline, 'cards', engine.storyline)
        is_shield_mode = hasattr(engine, 'mode_handler') and engine.mode_handler.__class__.__name__ == "ShieldMode"

        # 1. 🛡️ "YOU = THE PLAYER": Grant global access to all hero cards in the Storyline
        my_cards = []
        for c in story_cards:
            owner_raw = c.get('owner')
            if not owner_raw or owner_raw == engine.villain.name: 
                continue # Ignore Villain cards
            
            owner_name = owner_raw.name if hasattr(owner_raw, 'name') else str(owner_raw)
            
            # Solo Mode: Access ANY hero card. Standard: Access only your own.
            if is_shield_mode or owner_name == hero.name:
                my_cards.append(c)
        
        if not hero.hand or not my_cards:
            engine.log.append(Col.wrap("   (Swap cancelled: No valid cards available)", Col.DARK_GRAY))
            return

        # 🔌 UI ADAPTER: Safe prompts for both Human and Bot controllers
        if engine.ui.ask_yes_no(f"\n SWAP STORYLINE: {effect.get('text', 'Swap a card?')} (y/n): "):
            
            from src.ui.board import BoardRenderer
            color_map = {h.name: BoardRenderer.HERO_COLORS[i % len(BoardRenderer.HERO_COLORS)] for i, h in enumerate(engine.heroes)}

            # --- SELECT CARD TO TAKE ---
            print("\n Select card to TAKE from Storyline:")
            for i, c in enumerate(my_cards, 1):
                o_raw = c.get('owner')
                o_name = o_raw.name if hasattr(o_raw, 'name') else str(o_raw) if o_raw else "Unknown"
                c_color = color_map.get(o_name, Col.CYAN)
                o_display = Col.wrap(f" ({o_name})", c_color)
                print(f" [{i}] {Col._get_card_label(c)}{o_display}")
            print(" [0] Cancel")
            
            take_choice = engine.ui.ask_choice(" >> ", 0, len(my_cards))
            if take_choice == 0:
                print(Col.wrap(" Swap cancelled.", Col.YLW))
                return
            taken = my_cards[take_choice - 1]
            
            # --- SELECT CARD TO GIVE ---
            print("\n Select card to GIVE from Hand:")
            for i, c in enumerate(hero.hand, 1):
                o_raw = c.get('owner')
                o_name = o_raw.name if hasattr(o_raw, 'name') else str(o_raw) if o_raw else "Unknown"
                c_color = color_map.get(o_name, Col.CYAN)
                o_display = Col.wrap(f" ({o_name})", c_color)
                print(f" [{i}] {Col._get_card_label(c)}{o_display}")
            print(" [0] Cancel")
            
            give_choice = engine.ui.ask_choice(" >> ", 0, len(hero.hand))
            if give_choice == 0:
                print(Col.wrap(" Swap cancelled.", Col.YLW))
                return
            given = hero.hand.pop(give_choice - 1)
            
            # 2. 🦸‍♂️ CARD = HERO: Preserve the original hero's identity!
            if 'owner' not in given: 
                given['owner'] = hero if is_shield_mode else hero.name

            story_cards[story_cards.index(taken)] = given
            hero.hand.append(taken)
            engine.log.append(Col.wrap(f" 🔃 A card was swapped with the Storyline.", Col.MAGENTA))

    @staticmethod
    def pick_next_card(engine, hero, effect):
        if not hero.deck: return
        if engine.ui.ask_yes_no(f"\n 🗼 PREP DECK: {effect['text']} (y/n): "):
            print(" Select card to place on TOP of deck:")
            
            # 🎨 Create a dynamic color map based on current roster
            from src.ui.board import BoardRenderer
            color_map = {h.name: BoardRenderer.HERO_COLORS[i % len(BoardRenderer.HERO_COLORS)] for i, h in enumerate(engine.heroes)}
            
            for i, c in enumerate(hero.deck, 1):
                owner_raw = c.get('owner')
                owner_name = owner_raw.name if hasattr(owner_raw, 'name') else str(owner_raw) if owner_raw else ""
                
                # 🚨 THE FIX: Look up the color, and apply it instead of Col.CYAN
                c_color = color_map.get(owner_name, Col.CYAN)
                owner_display = Col.wrap(f" ({owner_name})", c_color) if owner_name and owner_name != "None" else ""
                
                print(f" ({i}) {Col._get_card_label(c)}{owner_display}")
            card = hero.deck.pop(engine.ui.ask_choice(" >> ", 1, len(hero.deck)) - 1)
            random.shuffle(hero.deck)
            hero.deck.insert(0, card) 
            engine.log.append(f" 🔭 {hero.name} prepped their next draw.")

    @staticmethod
    def discard_thug(engine, hero, effect):
        targets = [l for l in engine.locations if l.thugs > 0]
        if not targets: return
        if engine.ui.ask_yes_no(f"\n 🚓 DISCARD THUG: {effect['text']} (y/n): "):
            for i, l in enumerate(targets, 1): print(f" ({i}) {l.name} ({l.thugs} thugs)")
            idx = engine.ui.ask_choice(" >> ", 1, len(targets))
            targets[idx - 1].thugs -= 1
            engine.log.append(f" 🚓 A Thug was removed from {targets[idx - 1].name}.")

    @staticmethod
    def rescue_civilian(engine, hero, effect):
        loc = engine.locations[hero.location_index]
        if loc.civilians > 0:
            if engine.ui.ask_yes_no(f"\n ✨ RESCUE: {effect['text']} (y/n): "):
                from src.systems.token_system import TokenSystem
                TokenSystem.apply_heroic(engine, loc, target_type="c")

    @staticmethod
    def move_anywhere(engine, hero, effect):
        if engine.ui.ask_yes_no(f"\n 🚁 MOVE ANYWHERE: {effect['text']} (y/n): "):
            for i, l in enumerate(engine.locations, 1): print(f" ({i}) {l.name}")
            hero.location_index = engine.ui.ask_choice(" >> ", 1, len(engine.locations)) - 1
            engine.log.append(f" 🚁 {hero.name} flew to {engine.locations[hero.location_index].name}.")

    @staticmethod
    def token_swap_loc(engine, hero, effect):
        loc = engine.locations[hero.location_index]
        if loc.civilians == 0 and loc.thugs == 0: return
        if engine.ui.ask_yes_no(f"\n 🌳 MOVE TOKENS: {effect['text']} (y/n): "):
            for i in range(2): 
                if loc.civilians == 0 and loc.thugs == 0: break
                print(f" (Move {i+1}/2) {loc.civilians}C, {loc.thugs}T here.")
                t_choice = engine.ui.ask_choice(" (1) Move Civilian (2) Move Thug (0) Done >> ", 0, 2)
                if t_choice == 0: break 
                
                t_type = "civilians" if t_choice == 1 and loc.civilians > 0 else "thugs" if t_choice == 2 and loc.thugs > 0 else None
                if not t_type: continue
                
                print(" Select destination:")
                for d_idx, l in enumerate(engine.locations, 1): print(f" ({d_idx}) {l.name}")
                dest = engine.locations[engine.ui.ask_choice(" >> ", 1, len(engine.locations)) - 1]
                
                setattr(loc, t_type, getattr(loc, t_type) - 1)
                setattr(dest, t_type, getattr(dest, t_type) + 1)
                engine.log.append(f" 🌳 Moved {t_type[:-1]} to {dest.name}.")

    @staticmethod
    def heal_3(engine, hero, effect):
        if len(hero.hand) >= 3: return
        if engine.ui.ask_yes_no(f"\n 🏠 HEAL 3: {effect['text']} (y/n): "):
            drawn = 0
            while len(hero.hand) < 3 and hero.deck:
                hero.hand.append(hero.deck.pop(0)) 
                drawn += 1
            engine.log.append(f" 🏠 {hero.name} drew {drawn} card(s).")
            