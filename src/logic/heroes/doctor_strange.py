import random
from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("doctor_strange")
class DoctorStrangeLogic:
    @staticmethod
    def _resolve_book_of_vishanti(engine):
        deck = engine.villain.plan_deck
        if not deck:
            engine.log.append(Col.wrap(" 📖 BOOK OF VISHANTI: The timeline is already empty!", Col.RED))
            return True
            
        prompt_lines = [
            f"\n--- {Col.wrap('📖 THE BOOK OF VISHANTI', Col.MAGENTA + Col.BOLD)} ---",
            Col.wrap(" Peer into the timeline and select a Master Plan to banish:", Col.CYAN)
        ]
        
        from src.ui.board import BoardRenderer
        
        for i, p_card in enumerate(deck, 1):
            # 🚨 POINT TO THE NEW UNIVERSAL FORMATTER
            label = BoardRenderer.format_master_plan(p_card)
            desc = p_card.get('effect_text', '')
            if desc:
                desc = f" - {desc[:35]}..." if len(desc) > 35 else f" - {desc}"
            prompt_lines.append(f" [{i}] {label}{desc}")
            
        prompt_lines.append(" [0] Cancel / Do not alter the timeline")
        prompt_lines.append("\n Select a timeline to prune >> ")
        
        # 🔌 Fully concatenated prompt for the Fuzzer
        choice = engine.ui.ask_choice("\n".join(prompt_lines), 0, len(deck))
        
        if choice == 0:
            engine.log.append(Col.wrap(" 📖 BOOK OF VISHANTI: The future remains unaltered.", Col.MAGENTA))
            return True
            
        banished_card = deck.pop(choice - 1)
        random.shuffle(deck)
        
        card_name = banished_card.get('id', f"Plan #{choice}")
        engine.log.append(Col.wrap(f" 📖 BOOK OF VISHANTI: {card_name} banished from time!", Col.MAGENTA + Col.BOLD))
        engine.log.append(Col.wrap(f" 🔀 The Master Plan deck has been reshuffled.", Col.DARK_GRAY))
        
        return True

    @staticmethod
    def _resolve_cloak_of_levitation(engine, hero):
        choice = engine.ui.ask_raw(f" CLOAK: (1) ✸ Adjacent or (2) Gain ➡ action? ", {'1', '2'})
        
        if choice == '1':
            from src.systems.action_system import ActionSystem
            adj = [(hero.location_index - 1) % 6, (hero.location_index + 1) % 6]
            
            # 🔌 Concatenated prompt
            prompt = f" Choose adjacent: [1] {engine.locations[adj[0]].name} | [2] {engine.locations[adj[1]].name}\n >> "
            c = engine.ui.ask_choice(prompt, 1, 2) - 1
            ActionSystem._handle_targeted_attack(engine, hero, adj[c])
        else:
            # 🚨 THE FIX: Inject directly into the active turn pool, not the persistent inventory
            if not hasattr(engine, 'active_pool'):
                engine.active_pool = {}
            engine.active_pool["move"] = engine.active_pool.get("move", 0) + 1
            engine.log.append(" 🧥 Gained 1 ➡ action for this turn.")
        return True

    @staticmethod
    def _resolve_dimensional_portal(engine, hero):
        prompt_lines = [f"\n--- {Col.wrap('PORTAL', Col.MAGENTA)} ---"]
        loc_count = len(engine.locations)
        
        for i, loc in enumerate(engine.locations, 1): 
            prompt_lines.append(f" [{i}] {loc.name}")
        prompt_lines.append(" >> ")
        
        # 🔌 Concatenated prompt with dynamic location scaling
        c = engine.ui.ask_choice("\n".join(prompt_lines), 1, loc_count) - 1
        hero.location_index = c
        engine.log.append(Col.wrap(f" 🌀 PORTAL: Strange emerges at {engine.locations[c].name}!", Col.MAGENTA))
        return True

    @staticmethod
    def _resolve_eye_of_agamotto(engine):
        engine.log.append(Col.wrap(" 👁️ EYE OF AGAMOTTO: Time reverses... (Storyline manipulation triggered)", Col.MAGENTA))
        return True

    @staticmethod
    def _resolve_orb_of_agamotto(engine):
        engine.log.append(Col.wrap(f" 🔮 ORB OF AGAMOTTO: The future is revealed...", Col.MAGENTA))
        return True

    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "doctor_strange_book_of_vishanti":
            return DoctorStrangeLogic._resolve_book_of_vishanti(engine)
        elif sid == "doctor_strange_cloak_of_levitation":
            return DoctorStrangeLogic._resolve_cloak_of_levitation(engine, hero)
        elif sid == "doctor_strange_dimensional_portal":
            return DoctorStrangeLogic._resolve_dimensional_portal(engine, hero)
        elif sid == "doctor_strange_eye_of_agamotto":
            return DoctorStrangeLogic._resolve_eye_of_agamotto(engine)
        elif sid == "doctor_strange_orb_of_agamotto":
            return DoctorStrangeLogic._resolve_orb_of_agamotto(engine)
            
        return False

