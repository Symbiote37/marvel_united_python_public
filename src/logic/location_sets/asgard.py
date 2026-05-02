from src.utils.helpers import Col

class AsgardLocationLogic:
    @staticmethod
    def move_all_heroes(engine, hero, effect):
        others = [h for h in engine.heroes if h != hero and h.location_index != hero.location_index and not getattr(h, 'is_ko', False)]
        if not others: return
        if Col.prompt_y_n("👁️ CALL HEROES", effect['text']):
            moved = 0
            for ally in others:
                # Sub-prompt for individual allies
                if input(f" Move {ally.name} here? (y/n): ").strip().lower() == 'y':
                    ally.location_index = hero.location_index
                    moved += 1
            if moved > 0: engine.log.append(f" 👁️ Called {moved} Hero(es) to {engine.locations[hero.location_index].name}! ")

    @staticmethod
    def swap_out_hand(engine, hero, effect):
        if not hero.hand: return
        if Col.prompt_y_n("⚔️ REFRESH HAND", effect['text']):
            count = Col.get_choice(f" How many cards to discard? (0-{len(hero.hand)}) >> ", 0, len(hero.hand))
            if count == 0: return
            
            for _ in range(count):
                print("\n Select card to discard:")
                for i, c in enumerate(hero.hand, 1): print(f" ({i}) {Col._get_card_label(c)}")
                hero.deck.insert(0, hero.hand.pop(Col.get_choice(" >> ", 1, len(hero.hand)) - 1))
            
            hero.draw_cards(count)
            engine.log.append(f" ⚔️ {hero.name} cycled {count} card(s). ")

    @staticmethod
    def add_civilian_thug(engine, hero, effect):
        if Col.prompt_y_n("🏰 ADD TOKENS", effect['text']):
            from src.systems.token_system import TokenSystem
            for i in range(2):
                t_choice = Col.get_choice(f"\n (Token {i+1}/2) Add: [1] Civilian [2] Thug [0] Done >> ", 0, 2)
                if t_choice == 0: break
                
                t_type = "civilians" if t_choice == 1 else "thugs"
                print(" Select destination:")
                for d_idx, l in enumerate(engine.locations, 1): print(f" ({d_idx}) {l.name}")
                dest = Col.get_choice(" >> ", 1, 6) - 1
                
                TokenSystem.add_token(engine, dest, t_type, set())
                engine.log.append(f" 🏰 Added 1 {t_type[:-1].capitalize()} to {engine.locations[dest].name}. ")

    @staticmethod
    def throne_room_move(engine, hero, effect):
        others = [h for h in engine.heroes if h != hero and not getattr(h, 'is_ko', False)]
        if not others: return
        if Col.prompt_y_n("👑 MOVE ALLY", effect['text']):
            print("\n Select Hero to move:")
            for i, h in enumerate(others, 1): print(f" ({i}) {h.name}")
            target = others[Col.get_choice(" >> ", 1, len(others)) - 1]
            
            cw, ccw = (target.location_index + 1) % 6, (target.location_index - 1) % 6
            print(f"\n [1] Clockwise: {engine.locations[cw].name} | [2] Counter-Clockwise: {engine.locations[ccw].name}")
            target.location_index = cw if Col.get_choice(" >> ", 1, 2) == 1 else ccw
            engine.log.append(f" 👑 {target.name} shifted to an adjacent location. ")

    @staticmethod
    def bifrost_bridge_move(engine, hero, effect):
        others = [h for h in engine.heroes if h != hero and h.location_index == hero.location_index and not getattr(h, 'is_ko', False)]
        if not others: return
        if Col.prompt_y_n("🌈 BIFROST WARP", effect['text']):
            print(" Select destination for all Heroes here:")
            for d_idx, l in enumerate(engine.locations, 1): print(f" ({d_idx}) {l.name}")
            dest = Col.get_choice(" >> ", 1, 6) - 1
            
            for ally in others: ally.location_index = dest
            hero.location_index = dest
            engine.log.append(f" 🌈 The team warped to {engine.locations[dest].name}! ")
