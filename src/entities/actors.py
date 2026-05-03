# src/entities/actors.py

import random
from src.utils.helpers import Col

class Hero:
    def __init__(self, data):
        # 🛡️ THE IDENTITY BADGE
        self.internal_id = data.get('internal_id') 
        self.name = data.get('name', "Unknown Hero")

        # Deck & Hand management
        self.deck = list(data.get('deck', [])) 
        self.hand = []
        random.shuffle(self.deck)
        self.draw_cards(3)

        # State & Inventory
        self.location_index = 3 
        self.is_ko = False
        self.stashed_tokens = [] 
        self.crisis_tokens = 0 

    def draw_cards(self, count=1):
        for _ in range(count):
            if self.deck:
                self.hand.append(self.deck.pop(0))

    def play_card(self, index):
        if 0 <= index < len(self.hand):
            card = self.hand.pop(index)
            card['owner'] = self.name 
            return card
        return None

    def take_damage(self, engine, amount=1):
        """
        Signals the KO immediately but delegates the state change 
        to the Villain Logic.
        """
        from src.systems.status_system import StatusSystem

        if getattr(self, 'is_invincible', False):
            default_msg = f"   🛡️ {self.name} shrugs off the attack completely!"
            msg = getattr(self, 'invincible_deflect_msg', default_msg)
            engine.log.append(Col.wrap(msg, Col.CYAN))
            if hasattr(self, 'on_deflect'):
                self.on_deflect(engine, amount)
            return False 

        if getattr(self, 'is_ko', False):
            return False

        from src.systems.damage_system import DamageSystem
        DamageSystem.deal_hero_damage(engine, self, amount)

        if len(self.hand) == 0 and not getattr(self, 'is_ko', False):
            if StatusSystem.has_status(self, "protect_last_card"):
                engine.log.append(Col.wrap(f" 🌟 IMMORTAL: {self.name} refuses to fall! ", Col.CYAN + Col.BOLD))
                return True 

            from src.logic.registry import get_villain_logic
            logic = get_villain_logic(engine.villain.internal_id)
            if hasattr(logic, 'handle_hero_ko'):
                logic.handle_hero_ko(engine, self)

        return True

    def add_token(self, token_char):
        if self.is_ko: return 
        self.stashed_tokens.append(token_char)

    def process_triggers(self, trigger_type, engine, **kwargs):
        """
        🚨 THE FIX: Handles both innate Hero passives and Storyline card triggers.
        """
        from src.logic.registry import get_hero_logic
        import inspect
        
        # 1. Fetch logic handler via the Neutral Ground (Registry)
        logic_class = get_hero_logic(self.internal_id)
        if not logic_class:
            return

        handler = getattr(logic_class, trigger_type, None)
        if not handler:
            return

        sig = inspect.signature(handler)
        
        # 2A. Scenario A: The trigger requires a specific card in the timeline
        if 'card' in sig.parameters:
            story_cards = getattr(engine.storyline, 'cards', engine.storyline)
            for card in story_cards:
                if card.get('owner') == self.name and card.get('special_id'):
                    handler(engine, self, card, **kwargs)
                    
        # 2B. Scenario B: The trigger is an innate hero passive (like Gamora)
        else:
            handler(engine, self, **kwargs)

class Villain:
    def __init__(self, data, hero_count=2):
        self.raw_data = data 
        self.name = data['name']
        self.internal_id = data.get('internal_id', 'generic_v')

        # Health Mapping
        self.health_map = data.get('health_map', {})
        h_key = str(hero_count)
        self.max_hp = self.health_map.get(h_key, data.get('base_health', 4))
        self.hp = self.max_hp

        # Board & Deck Setup
        self.location_index = 0 
        self.plan_deck = list(data.get('master_plan', []))

        # Plot Tracking
        self.plot_name = data.get("plot_name", "")
        self.plot_value = 0
        self.plot_max = data.get("plot_max", 0) 

        random.shuffle(self.plan_deck)

    def draw_plan(self):
        if not self.plan_deck: return None
        return self.plan_deck.pop(0)

    def on_bam(self, engine):
        from src.logic.registry import get_villain_logic
        logic = get_villain_logic(self.internal_id)
        logic.on_bam(engine, self)

    def on_overflow(self, engine, location, token_type):
        from src.logic.registry import get_villain_logic
        logic = get_villain_logic(self.internal_id)
        logic.on_overflow(engine, self, location, token_type)
