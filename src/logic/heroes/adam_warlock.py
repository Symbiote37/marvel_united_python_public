from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("adam_warlock")
class AdamWarlockLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "adam_warlock_quantum_magic":
            return AdamWarlockLogic._quantum_magic(engine, hero)
        elif sid == "adam_warlock_immortality":
            return AdamWarlockLogic._immortality(engine, hero)
        elif sid == "adam_warlock_avatar_of_life":
            return AdamWarlockLogic._avatar_of_life(engine, hero)
        return False

    @staticmethod
    def _quantum_magic(engine, hero):
        from src.utils.helpers import Col
        deck = engine.villain.plan_deck
        if not deck: return True
        
        num_cards = min(3, len(deck))
        top_cards = deck[:num_cards]

        print(f"\n{Col.wrap('🌌 QUANTUM MAGIC:', Col.CYAN)} Reorder the top {num_cards} cards.")
        new_order = []
        
        while len(top_cards) > 0:
            for i, c in enumerate(top_cards, 1):
                # 🕵️ SMART INTEL APPLIED HERE
                p_name = AdamWarlockLogic._get_plan_intel(c)
                print(f" [{i}] {Col.wrap(p_name, Col.RED)}")
                if c.get('effect_text'):
                    print(Col.wrap(f"     └ {c['effect_text']}", Col.DARK_GRAY))
            
            choice = Col.get_choice(" Select next card to put on top >> ", 1, len(top_cards)) - 1
            new_order.append(top_cards.pop(choice))
            
        engine.villain.plan_deck = new_order + deck[num_cards:]
        engine.log.append(Col.wrap(f" 🌌 {hero.name} peered into the future!", Col.CYAN))
        return True
        
    @staticmethod
    def _immortality(engine, hero):
        # This needs to be checked constantly by the engine as long as the card is faceup
        hero.protect_last_card = True
        engine.log.append(Col.wrap(f" 🌟 PASSIVE: {hero.name} taps into immortality.", Col.CYAN))
        return True

    @staticmethod
    def _avatar_of_life(engine, hero):
        from src.systems.status_system import StatusSystem
        from src.utils.helpers import Col
        
        # 🌟 THE UPGRADE: Pushing the universal tag instead of a hardcoded boolean
        StatusSystem.apply_status(engine.villain, "force_facedown_plan", duration=1)
        
        engine.log.append(Col.wrap(f" 🌟 PASSIVE: {hero.name} forces the next Master Plan to be facedown!", Col.CYAN))
        return True
    @staticmethod
    def _get_plan_intel(card):
        """
        Translates raw Master Plan data into a readable title for Oracle abilities.
        """
        if card.get('display_name'):
            return card.get('display_name').upper()
        
        parts = []
        m = card.get('move', 0)
        if isinstance(m, int) and m > 0:
            parts.append(f"MOVE {m}")
        elif isinstance(m, str):
            parts.append(f"MOVE {m.upper()}")
        if card.get('bam'):
            parts.append("BAM!")
        
        add_data = card.get('add', {})
        if add_data:
            # Check for reinforcement types in the data
            has_thugs = any('thugs' in zone for zone in add_data.values())
            has_civs = any('civilians' in zone for zone in add_data.values())
            
            if has_thugs and has_civs: parts.append("+ REINFORCE")
            elif has_thugs: parts.append(f"+ {ICON['thug']}S")
            elif has_civs: parts.append(f"+ {ICON['civilian']}S")

        return " | ".join(parts) if parts else "STATIONARY SCHEME"
        