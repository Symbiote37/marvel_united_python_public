from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("black_widow")
class BlackWidowLogic:
    @staticmethod
    def get_card_description(card):
        """Translates raw Master Plan data into a readable title. """
        if card.get('display_name'):
            return card.get('display_name').upper()
        
        # Build a description for 'Standard' cards
        parts = []
        
        # 1. Movement
        m = card.get('move', 0)
        if isinstance(m, int) and m > 0:
            parts.append(f"MOVE {m}")
        elif isinstance(m, str):
            parts.append(f"MOVE {m.upper()}")
        
        # 2. BAM Status
        if card.get('bam'):
            parts.append("BAM! ")
            
        # 3. Reinforcements (The 'Add' dictionary)
        add_data = card.get('add', {})
        if add_data:
            # Check if we're adding Thugs or Civilians anywhere
            has_thugs = any('thugs' in zone for zone in add_data.values())
            has_civs = any('civilians' in zone for zone in add_data.values())
            
            if has_thugs and has_civs: parts.append("+ REINFORCE")
            elif has_thugs: parts.append(f"+ {ICON['thug']}S")
            elif has_civs: parts.append(f"+ {ICON['civilian']}S")

        return " | ".join(parts) if parts else "STATIONARY SCHEME"

    @staticmethod
    def resolve_special(engine, hero, card):
        if not engine.villain.plan_deck:
            return False

        top_card = engine.villain.plan_deck[0]
        
        # 🕵️ THE INTEL UPGRADE: Use the new descriptor
        p_name = BlackWidowLogic.get_card_description(top_card)
        
        print(f"\n{Col.wrap('🕵️ INTERROGATE:', Col.CYAN)} Next move uncovered. ")
        print(f" Intelligence: {Col.wrap(p_name, Col.RED + Col.BOLD)}")
        
        # Optionally show the full effect text if it exists
        if top_card.get('effect_text'):
            print(f" Detail: {top_card['effect_text']}")

        print("\n 1. Leave it on top")
        print(" 2. Move it to the bottom of the deck")
        
        choice = Col.get_choice(" >> ", 1, 2)
        
        if choice == 2:
            card_to_move = engine.villain.plan_deck.pop(0)
            engine.villain.plan_deck.append(card_to_move)
            engine.log.append(Col.wrap(f" 🕵️ {hero.name} buried the Villain's plan: {p_name}! ", Col.GRN))
        else:
            engine.log.append(Col.wrap(f" 🕵️ {hero.name} confirmed the next threat. ", Col.CYAN))
            
        return True
