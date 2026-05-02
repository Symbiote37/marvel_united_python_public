from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("jessica_jones")
class JessicaJonesLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "jessica_jones_expert_detective": return JessicaJonesLogic._expert_detective(engine, hero)
        elif sid == "jessica_jones_private_investigator": return JessicaJonesLogic._private_investigator(engine, hero)
        return False

    @staticmethod
    def _expert_detective(engine, hero):
        print(f"\n--- {Col.wrap('🕵️‍♀️ EXPERT DETECTIVE', Col.PURP)} ---")
        if input(" [1] Execute: Peek Master Plan, gain ❖ equal to Move\n [0] Cancel\n >> ").strip() != '1': return False
        
        if engine.villain.plan_deck:
            top_card = engine.villain.plan_deck[0]
            m_val = top_card.get("move", top_card.get("movement", 0))
            if not hasattr(hero, 'action_tokens'): hero.action_tokens = []
            for _ in range(m_val): hero.action_tokens.append("wild")
            engine.log.append(Col.wrap(f" 🕵️‍♀️ {hero.name} deduces the Villain's plan! (Gained {m_val} {ICON['wild']})", Col.PURP))
        return True

    @staticmethod
    def _private_investigator(engine, hero):
        print(f"\n--- {Col.wrap('🕵️‍♀️ PRIVATE INVESTIGATOR', Col.PURP)} ---")
        if engine.villain.plan_deck:
            from src.systems.villain_system import VillainSystem
            top_name = VillainSystem.get_plan_name(engine.villain.plan_deck[0])
            print(Col.wrap(f"\n 👁️ Intel Gathered: The next Master Plan is '{top_name}'", Col.CYAN))
            
        for i, loc in enumerate(engine.locations):
            marker = " (Current)" if i == hero.location_index else ""
            print(f" [{i+1}] Move to {loc.name}{marker}")
        print(" [0] Cancel")
        
        choice = Col.get_choice(" >> ", 0, 6)
        if choice == 0: return False
        
        loc_idx = choice - 1
        hero.location_index = loc_idx
        engine.log.append(Col.wrap(f" 🕵️‍♀️ {hero.name} relocates to {engine.locations[loc_idx].name} to investigate.", Col.CYAN))
        return True
        