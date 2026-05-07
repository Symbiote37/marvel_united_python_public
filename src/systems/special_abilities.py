from src.utils.helpers import Col

class SpecialAbilitySystem:
    # 🚥 THE BUS: Starts empty, filled automatically by @register tags
    HERO_LOGIC_MAP = {}

    @classmethod
    def register(cls, hero_id):
        """
        The Automated Switchboard:
        1. Adds the hero to the map.
        2. Automatically triggers 'initialize()' if it exists.
        """
        def wrapper(logic_class):
            cls.HERO_LOGIC_MAP[hero_id] = logic_class
            
            # 🔌 AUTO-PLUG:
            # If the hero has a Villain-Phase listener (like Luck), 
            # it registers itself immediately.
            if hasattr(logic_class, "initialize"):
                logic_class.initialize()
                
            return logic_class
        return wrapper
    
    @staticmethod
    def resolve(engine, hero, card):
        sid = card.get("special_id")
        if not sid: 
            return False

        flavor_name = card.get("name", "Ability").upper()

        # ==========================================
        # 1. UNIVERSAL ABILITIES (The Interceptor)
        # ==========================================

        if sid == "invulnerability":
            hero.is_invincible = True 
            hero.invincible_deflect_msg = f"   🛡️ {hero.name} easily evaded the attack using {flavor_name}!"
            hero.invincible_wear_off_msg = f" 🧍 {hero.name}'s {flavor_name} wears off."
            engine.log.append(Col.wrap(f" 🛡️ PASSIVE: {hero.name} activated {flavor_name}. Damage nullified this round.", Col.CYAN + Col.BOLD))
            return True
            
        elif sid == "draw_up_to_3":
            needed = 3 - len(hero.hand)
            if needed > 0:
                actual_drawn = min(needed, len(hero.deck))
                if actual_drawn > 0:
                    hero.draw_cards(actual_drawn)
                    engine.log.append(Col.wrap(f" 🔋 PASSIVE: {flavor_name} triggered! {hero.name} drew {actual_drawn} card(s).", Col.CYAN))
                else:
                    engine.log.append(Col.wrap(f" 🔋 PASSIVE: {flavor_name} triggered, but deck is empty!", Col.RED))
            else:
                engine.log.append(Col.wrap(f" 🔋 PASSIVE: {flavor_name} triggered, but hand is already full.", Col.DARK_GRAY))
            return True

        # ==========================================
        # 2. HERO-SPECIFIC ABILITIES (The Router)
        # ==========================================
        
        logic_class = SpecialAbilitySystem.HERO_LOGIC_MAP.get(hero.internal_id)
        if logic_class and hasattr(logic_class, "resolve_special"):
            return logic_class.resolve_special(engine, hero, card)
        
        return False

    @staticmethod
    def initialize_interceptors(engine):
        for logic_class in SpecialAbilitySystem.HERO_LOGIC_MAP.values():
            if hasattr(logic_class, 'initialize'):
                logic_class.initialize()

    @classmethod
    def trigger_event(cls, engine, hero, event_name, **kwargs):
        """The Radio Tower: Shouts events to the hero logic brain."""
        h_id = (getattr(hero, 'internal_id', '')).replace("-", "_").lower()
        logic_class = cls.HERO_LOGIC_MAP.get(h_id)
        
        if logic_class and hasattr(logic_class, event_name):
            getattr(logic_class, event_name)(engine, hero, **kwargs)

    @staticmethod
    def swap_with_storyline(engine, hero, prompt_context=None):
        """Universal utility for swapping a card from a hero's hand with one in the storyline."""
        from src.utils.helpers import Col, ICON
        from src.ui.board import BoardRenderer
        
        if not hero.hand:
            engine.log.append(Col.wrap(f" ⚠️ {hero.name} has no cards in hand to swap!", Col.YLW))
            return False

        story_cards = getattr(engine.storyline, 'cards', engine.storyline)
        is_shield_mode = hasattr(engine, 'mode_handler') and engine.mode_handler.__class__.__name__ == "ShieldMode"
        
        # 1. 🛡️ "YOU = THE PLAYER": Grant global access to all hero cards in the Storyline
        eligible_indices = []
        for i, card in enumerate(story_cards):
            owner_raw = card.get('owner')
            if not owner_raw or owner_raw == engine.villain.name: 
                continue # Ignore Villain cards
            
            owner_name = owner_raw.name if hasattr(owner_raw, 'name') else str(owner_raw)
            
            if is_shield_mode or owner_name == hero.name:
                eligible_indices.append(i)

        if not eligible_indices:
            engine.log.append(Col.wrap(f" ⚠️ {hero.name} has no valid faceup cards in the Storyline to swap!", Col.YLW))
            return False

        color_map = {h.name: BoardRenderer.HERO_COLORS[i % len(BoardRenderer.HERO_COLORS)] for i, h in enumerate(engine.heroes)}
        header_text = prompt_context.get("text", f"SWAP WITH STORYLINE: {hero.name}") if prompt_context else f"SWAP WITH STORYLINE: {hero.name}"
        
        if not engine.ui.ask_yes_no(f"\n {Col.wrap(header_text, Col.MAGENTA)} (y/n): "):
            print(Col.wrap(" Swap cancelled.", Col.YLW))
            return False

        # --- SELECT CARD TO TAKE ---
        print(Col.wrap(f"\n Select card to TAKE from Storyline:", Col.CYAN))
        for opt_num, s_idx in enumerate(eligible_indices, 1):
            s_card = story_cards[s_idx]
            o_raw = s_card.get('owner')
            o_name = o_raw.name if hasattr(o_raw, 'name') else str(o_raw) if o_raw else "Unknown"
            c_color = color_map.get(o_name, Col.CYAN)
            o_display = Col.wrap(f" ({o_name})", c_color)
            
            actions = " ".join([ICON.get(a, a) for a in s_card.get('actions', [])])
            name_str = f" - {s_card['name']}" if 'name' in s_card else ""
            print(f" [{opt_num}] [{actions}]{name_str}{o_display}")
        print(" [0] Cancel")
        
        story_choice = engine.ui.ask_choice(" >> ", 0, len(eligible_indices))
        if story_choice == 0:
            print(Col.wrap(" Swap cancelled.", Col.YLW))
            return False
        target_story_idx = eligible_indices[story_choice - 1]
        taken = story_cards[target_story_idx]

        # --- SELECT CARD TO GIVE ---
        print(Col.wrap(f"\n Select card to GIVE from Hand:", Col.CYAN))
        for i, c in enumerate(hero.hand, 1):
            o_raw = c.get('owner')
            o_name = o_raw.name if hasattr(o_raw, 'name') else str(o_raw) if o_raw else "Unknown"
            c_color = color_map.get(o_name, Col.CYAN)
            o_display = Col.wrap(f" ({o_name})", c_color)
            
            actions = " ".join([ICON.get(a, a) for a in c.get('actions', [])])
            name_str = f" - {c['name']}" if 'name' in c else ""
            print(f" [{i}] [{actions}]{name_str}{o_display}")
        print(" [0] Cancel")
        
        hand_choice = engine.ui.ask_choice(" >> ", 0, len(hero.hand))
        if hand_choice == 0:
            print(Col.wrap(" Swap cancelled.", Col.YLW))
            return False
        given = hero.hand.pop(hand_choice - 1)
        
        # 2. 🦸‍♂️ CARD = HERO: Preserve the original hero's identity!
        if 'owner' not in given: 
            given['owner'] = hero if is_shield_mode else hero.name

        story_cards[target_story_idx] = given
        hero.hand.append(taken)
        
        engine.log.append(Col.wrap(f" 🔀 REALITY WARPED: A card was swapped with the Storyline.", Col.MAGENTA + Col.BOLD))
        return True

# Move the import to the absolute bottom, unindented
import src.logic.heroes