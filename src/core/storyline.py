# [Target: src/core/storyline.py]

class Storyline:
    def __init__(self):
        self.cards = [] 

    def add(self, card_data):
        self.cards.append(card_data)
        # 🚨 FIX: Removed the 12-card hard cap so the game history can expand infinitely!

    def get_last_hero_actions(self):
        """
        Ultimate Authority: Finds the most recent Hero actions in the chain.
        If the last hero card is facedown, it returns empty (blocking inheritance).
        """
        for card in reversed(self.cards):
            # 1. 🛑 THE FIREWALL: Always step over Villain/Master Plan cards
            if card.get('type') in ['villain', 'master_plan', 'threat'] or 'movement' in card or 'bam' in card:
                continue
                
            owner_raw = card.get('owner', '')
            owner_str = getattr(owner_raw, 'name', str(owner_raw)).lower()
            if "villain" in owner_str:
                continue

            # 2. 🦸‍♂️ THE IDENTITY CHECK: Is this a Hero Card?
            is_hero_card = (
                card.get('type') == 'hero' or 
                'owner' in card or 
                'actions' in card or 
                'action' in card or
                'special_id' in card
            )
            
            # 🚨 THE GHOST FIX: Stop on ANY verified hero card.
            if is_hero_card:
                if card.get('is_facedown', False):
                    return [] 
                
                # 🛡️ TYPO ARMOR: Accept both 'actions' and 'action' from JSONs
                return card.get('actions', card.get('action', []))
                
        return []

    # --- THE COMPATIBILITY LAYER ---
    def __getitem__(self, index): 
        return self.cards[index]
    
    def __len__(self): 
        return len(self.cards)
    
    def append(self, card_data): 
        self.add(card_data)

    def count_symbols(self, symbol_type, depth=2):
        """Taskmaster's 'Copycat' calculator."""
        total = 0
        for card in self.cards[-depth:]:
            actions = card.get('actions', [])
            total += actions.count(symbol_type)
            total += actions.count('wild')
        return total
