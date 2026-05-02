# src/modes/shield_mode.py
import random
from src.modes.base_mode import BaseMode
from src.systems.villain_system import VillainSystem
from src.utils.helpers import Col
from src.ui.board import BoardRenderer

class ShieldMode(BaseMode):
    def __init__(self, engine): 
        super().__init__(engine)
        self.shared_hand = []
        self.shared_deck = []
        self.shared_tokens = [] 
        self.ko_limit = 0
        self.recovering_from_ko = False
        self.override_draw = True  # 🛡️ THE ARCHITECTURAL FLAG
        
    def perform_setup(self):
        """The Deck Synthesis Protocol"""
        super().perform_setup()
        
        diff_options = [
            "Easy (2 KOs allowed)", 
            "Medium (1 KO allowed)", 
            "Hard (KO = Game Over)"
        ]
        choice_idx = self.engine.ui.ask_choice("\n 🛡️ S.H.I.E.L.D. PROTOCOL ACTIVATED. Select Difficulty:", diff_options, return_index=True)
        
        if choice_idx == 0: self.ko_limit = 2
        elif choice_idx == 1: self.ko_limit = 1
        else: self.ko_limit = 0
            
        self.engine.log.append(Col.wrap(f" > S.H.I.E.L.D. Difficulty Locked: {self.ko_limit} Team KOs Allowed", Col.CYAN + Col.BOLD))
        
        # Merge decks, hands, and tokens
        for hero in self.engine.heroes:
            for card in hero.deck + hero.hand:
                card['owner'] = hero
            self.shared_deck.extend(hero.deck + hero.hand)
            
        random.shuffle(self.shared_deck)
        
        # 🚨 THE MAGIC LINK: Bind the heroes to the shared pool.
        for hero in self.engine.heroes:
            hero.deck = self.shared_deck
            hero.hand = self.shared_hand
            hero.stashed_tokens = self.shared_tokens
            hero.action_tokens = self.shared_tokens  
            
        self.draw_shared_cards(5)

    def draw_shared_cards(self, count=1, limit=None):
        for _ in range(count):
            if self.shared_deck:
                if limit and len(self.shared_hand) >= limit: break
                self.shared_hand.append(self.shared_deck.pop(0))

    def check_custom_game_status(self):
        """Hijacks the engine's state check to handle S.H.I.E.L.D. KOs seamlessly."""
        # 1. Total Wipe
        if len(self.shared_hand) == 0 and len(self.shared_deck) == 0:
            self.engine.game_over = True
            self.engine.victory_status = "VILLAIN_WINS"
            self.engine.loss_reason = "TACTICAL WIPEOUT: No cards remaining in S.H.I.E.L.D. reserves."
            return True
            
        # 2. Team KO Event
        if len(self.shared_hand) == 0 and not self.recovering_from_ko:
            if self.ko_limit > 0:
                self.ko_limit -= 1
                self.engine.log.append(Col.wrap(f" 💀 TEAM KO! Hand exhausted. {self.ko_limit} recoveries remaining.", Col.RED + Col.BOLD))
                
                # Mute the standard engine cascades by declaring them KO'd early
                for h in self.engine.heroes: h.is_ko = True
                    
                self.engine.log.append(Col.wrap(" 💥 The Villain capitalizes on the downed heroes!", Col.YLW))
                VillainSystem.execute_bam(self.engine)
                
                self.recovering_from_ko = True
                return False 
            else:
                self.engine.game_over = True
                self.engine.victory_status = "VILLAIN_WINS"
                self.engine.loss_reason = "TEAM ELIMINATED: S.H.I.E.L.D. ran out of recovery options."
                return True
                
        return False

    def handle_hero_eliminated(self, engine, hero):
        return True # Mutes the engine's default game over trigger

    def handle_mission_complete(self, mission_id):
        if mission_id == "threats": 
             self.engine.log.append(Col.wrap(" 🎉 TACTICAL ADVANTAGE: Team draws 3 cards!", Col.GRN))
             self.draw_shared_cards(3)

    def execute_hero_turn(self):
        from src.systems.hero_system import HeroSystem
        
        # 🚨 TEMPORAL ANOMALY FIX: Resync all references before the turn starts.
        # This reconnects the shared pool if an Undo severed the memory links!
        for h in self.engine.heroes:
            h.deck = self.shared_deck
            h.hand = self.shared_hand
            h.stashed_tokens = getattr(self, 'shared_tokens', [])
            h.action_tokens = getattr(self, 'shared_tokens', [])

        # 🎨 HERO COLOR SYNC: Mapping names to HUD initial colors
        h_colors = [Col.ORN, Col.C111, Col.GRN, Col.MAGENTA]
        color_map = {self.engine.heroes[i].name: h_colors[i % len(h_colors)] for i in range(len(self.engine.heroes))}

        if self.recovering_from_ko:
            self.engine.log.append(Col.wrap(" 🛡️ S.H.I.E.L.D. RECOVERS! Drawing up to 5 cards.", Col.CYAN))
            for h in self.engine.heroes: h.is_ko = False
            self.draw_shared_cards(5, limit=5)
            self.recovering_from_ko = False
            
        # 🚨 THE DRAW SYNC: Guaranteed 5+1 hand size
        if self.shared_deck:
            self.draw_shared_cards(1)

        if not self.shared_hand: return

        # 📊 INHERITANCE TRACKER
        prev_actions = self.engine.storyline.get_last_hero_actions()
        inherited_display = ""
        if prev_actions:
            icon_map = {"move": "➡", "attack": "✸", "heroic": "★", "wild": "❖"}
            p = [f"{icon_map.get(k, k)}:{prev_actions.count(k)}" for k in ["move", "attack", "heroic", "wild"] if prev_actions.count(k) > 0]
            if p: inherited_display = f" | INHERITED: {' '.join(p)}"

        # 🚨 SCREEN FLUSH: Clear Villain phase artifacts
        BoardRenderer.render(self.engine.get_game_state(self.engine.heroes[0]))

        # 🖥️ S.H.I.E.L.D. TACTICAL DEPLOYMENT MENU
        print(f"\n{Col.wrap(f'--- S.H.I.E.L.D. TACTICAL COMMAND{inherited_display} ---', Col.CYAN + Col.BOLD)}")
        print(f"{Col.wrap('HAND:', Col.BOLD)}")
        
        icon_map = {"attack": "✸", "heroic": "★", "move": "➡", "wild": "❖", "double_wild": "❖ ❖"}
        
        for i, card in enumerate(self.shared_hand, 1):
            owner = card.get('owner', self.engine.heroes[0])
            owner_name = owner.name if hasattr(owner, 'name') else str(owner)
            
            c_color = color_map.get(owner_name, Col.WHT)
            
            # 🚨 THE PARADOX FIX: Broadcast the Crisis state directly into the deployment menu
            crisis_warn = ""
            if getattr(owner, 'crisis_tokens', 0) > 0:
                crisis_warn = Col.wrap(" ⚠️ [CRISIS: RANDOMIZED]", Col.RED + Col.BOLD)
                
            owner_display = Col.wrap(f"({owner_name})", c_color) + crisis_warn
            
            actions = card.get('actions', [])
            symbols = " ".join([icon_map.get(a.lower(), a.upper()) for a in actions])
            
            c_name = card.get('name', '').replace('Action Card', '').strip()
            c_name_display = f" {c_name}" if c_name and "(" not in c_name else ""
            
            print(f" {i}: [{symbols}]{c_name_display} {owner_display}")
            
            effect = card.get('effect_text') or card.get('effect') or card.get('special_text') or card.get('text')
            if effect:
                print(Col.wrap(f"    └ {effect}", Col.DARK_GRAY))

        # --- THE INTERCEPTOR: Select and deploy ---
        choice_idx = self.engine.ui.ask_choice("\nDeploy hero via card >> ", 1, len(self.shared_hand)) - 1
        played_card = self.shared_hand[choice_idx]
        
        # 🛡️ RE-LINKER: Handle String vs Object owners
        owner_raw = played_card.get('owner', self.engine.heroes[0])
        owner_name = owner_raw.name if hasattr(owner_raw, 'name') else str(owner_raw)
        active_hero = next((h for h in self.engine.heroes if h.name == owner_name), self.engine.heroes[0])

        self.engine.log.append(Col.wrap(f" 📡 COMM LINK OPEN: {active_hero.name} deployed!", Col.GRN))

        original_ask = self.engine.ui.ask_choice
        def single_use_ask(*args, **kwargs):
            self.engine.ui.ask_choice = original_ask 
            if played_card in self.shared_hand:
                return self.shared_hand.index(played_card) + 1
            return 1
            
        self.engine.ui.ask_choice = single_use_ask 
        self.engine.current_hero_index = self.engine.heroes.index(active_hero)

        # Execute the turn normally.
        HeroSystem.execute_turn(self.engine, active_hero, self.engine.current_hero_index)

    def handle_hero_ko(self, engine, hero):
        """
        🛑 INTERCEPTOR: Tells the base engine that S.H.I.E.L.D. Mode 
        is handling the KOs via check_custom_game_status. 
        Prevents standard KO BAMs from queuing.
        """
        return True 
