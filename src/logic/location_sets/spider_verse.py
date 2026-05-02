from src.utils.helpers import Col

class SpiderVerseLocationLogic:
    @staticmethod
    def gain_move_token(engine, hero, effect):
        if Col.prompt_y_n("🧪 GAIN ➡", effect['text']):
            hero.add_token("move")
            engine.log.append(f" 🧪 {hero.name} gained +1 ➡.")

    @staticmethod
    def gain_heroic_token(engine, hero, effect):
        if Col.prompt_y_n("🏫 GAIN ★", effect['text']):
            hero.add_token("heroic")
            engine.log.append(f" 🏫 {hero.name} gained +1 ★.")

    @staticmethod
    def gain_attack_token(engine, hero, effect):
        if Col.prompt_y_n("🔬 GAIN ✸", effect['text']):
            hero.add_token("attack")
            engine.log.append(f" 🔬 {hero.name} gained +1 ✸.")

    @staticmethod
    def heal_1(engine, hero, effect):
        if len(hero.hand) in [1, 2]:
            if Col.prompt_y_n("✨ HEAL 1", effect['text']):
                hero.draw_cards(1)
                engine.log.append(f" ✨ {hero.name} recovered 1 card.")

    @staticmethod
    def reveal_plan(engine, hero, effect):
        if not engine.villain.plan_deck: return
        if Col.prompt_y_n("📰 REVEAL PLAN", effect['text']):
            top = engine.villain.plan_deck[0]
            
            # --- Local Translation Logic ---
            if top.get('display_name'):
                desc = top.get('display_name').upper()
            else:
                parts = []
                # 1. Movement
                m = top.get('move', 0)
                if m > 0: parts.append(f"MOVE {m}")
                # 2. BAM
                if top.get('bam'): parts.append("BAM!")
                # 3. Reinforcements
                add_data = top.get('add', {})
                if add_data:
                    from src.utils.helpers import ICON
                    has_thugs = any('thugs' in zone for zone in add_data.values())
                    has_civs = any('civilians' in zone for zone in add_data.values())
                    if has_thugs and has_civs: parts.append("+ REINFORCE")
                    elif has_thugs: parts.append(f"+ {ICON['thug']}S")
                    elif has_civs: parts.append(f"+ {ICON['civilian']}S")
                desc = " | ".join(parts) if parts else "STATIONARY SCHEME"

            # Display the "Headline"
            print(f"\n {Col.wrap('📰 DAILY BUGLE EXCLUSIVE:', Col.CYAN + Col.BOLD)} Intel gathered!")
            print(f" Headline: {Col.wrap(desc, Col.RED + Col.BOLD)}")
            
            if top.get('effect_text'):
                print(f" Details: {top['effect_text']}")

            # Sub-prompt unique to this effect
            if input("\n Move to bottom of deck? (y/n): ").strip().lower() == 'y':
                engine.villain.plan_deck.append(engine.villain.plan_deck.pop(0))
                engine.log.append(f" 📰 {hero.name} buried the Villain's plan: {desc}")
            else:
                engine.log.append(f" 📰 {hero.name} confirmed the next threat: {desc}")

    @staticmethod
    def rescue_1_c(engine, hero, effect):
        if Col.prompt_y_n("🌉 RESCUE + SPAWN", effect['text']):
            from src.systems.token_system import TokenSystem
            print("\n Select destination to ADD 1 Civilian:")
            for d_idx, l in enumerate(engine.locations, 1): print(f" ({d_idx}) {l.name}")
            dest = Col.get_choice(" >> ", 1, 6) - 1
            TokenSystem.add_token(engine, dest, "civilians", set())
            
            loc = engine.locations[hero.location_index]
            if loc.civilians > 0:
                TokenSystem.apply_heroic(engine, loc, target_type="c")
            engine.log.append(f" 🌉 Added 1 C to {engine.locations[dest].name} and rescued 1 C locally.")
