from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("groot")
class GrootLogic:
    @staticmethod
    def _tandem_attack_loop(engine, active_hero):
        """Temporarily hijacks the UI and Action System to allow a specific hero to resolve an attack."""
        from src.systems.action_system import ActionSystem
        from src.ui.board import BoardRenderer
        
        # 🚨 THE POOL SWAP: Save the main turn pool, give them a mini-pool
        original_pool = engine.active_pool
        engine.active_pool = {"move": 0, "attack": 1, "heroic": 0, "wild": 0}
        
        while sum(engine.active_pool.values()) > 0:
            BoardRenderer.render(engine.get_game_state(active_hero))
            
            print(f"\n{Col.wrap(f'--- 🌳 {active_hero.name.upper()} TANDEM ATTACK ---', Col.RED)}")
            print(f" [2] {ICON.get('attack', '✸')} Select Attack Target")
            print(" [0] Pass / Skip")
            
            cmd = engine.ui.ask_raw(f" [{active_hero.name}]> ", {'2', '0'})
            
            if cmd == '0':
                engine.log.append(Col.wrap(f" 🌳 {active_hero.name} holds their attack.", Col.DARK_GRAY))
                break
            elif cmd == '2':
                # Routes perfectly through your ActionSystem traffic controller
                ActionSystem.resolve_single_action(engine, active_hero, 'attack', engine.active_pool)
                if getattr(engine, 'game_over', False): 
                    break
        
        # 🚨 RESTORE THE TIMELINE: Give the original pool back for the rest of the turn
        engine.active_pool = original_pool

    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if not sid:
            return False

        # 1. Define valid tandem targets (alive, and not Groot)
        valid_targets = [h for h in engine.heroes if h != hero and not getattr(h, 'is_ko', False)]

        # ==========================================
        # ABILITY 1: "I Am Groot?" (Tandem Move)
        # ==========================================
        if sid == "groot_i_am_groot?":
            if not valid_targets:
                engine.log.append(Col.wrap(" 🌳 Groot looks around confused. No allies to move!", Col.DARK_GRAY))
                return True

            if len(valid_targets) == 1:
                target_hero = valid_targets[0]
            else:
                print(Col.wrap("\n SELECT HERO TO MOVE:", Col.CYAN))
                for i, h in enumerate(valid_targets, 1):
                    print(f" [{i}] {h.name} (at {engine.locations[h.location_index].name})")
                choice = engine.ui.ask_choice(" >> ", 1, len(valid_targets))
                target_hero = valid_targets[choice - 1]

            curr_idx = target_hero.location_index
            left_idx = (curr_idx - 1) % 6
            right_idx = (curr_idx + 1) % 6
            locs = [engine.locations[left_idx], engine.locations[right_idx]]

            print(Col.wrap(f"\n MOVE {target_hero.name.upper()} TO:", Col.CYAN))
            print(f" [1] Left: {locs[0].name}")
            print(f" [2] Right: {locs[1].name}")
            dir_choice = engine.ui.ask_choice(" >> ", 1, 2)
            new_loc = left_idx if dir_choice == 1 else right_idx

            target_hero.location_index = new_loc
            engine.log.append(Col.wrap(f" 🌳 I AM GROOT? Groot gently branches {target_hero.name} over to {engine.locations[new_loc].name}!", Col.GRN))
            
            if hasattr(engine, 'track_stat'):
                engine.track_stat(hero, "moves", 1)
            return True

        # ==========================================
        # ABILITY 2: "We Are Groot" (Tandem Draw)
        # ==========================================
        elif sid == "groot_we_are_groot":
            hero.draw_cards(1)
            engine.log.append(Col.wrap(f" 🌳 WE ARE GROOT: {hero.name} draws 1 card.", Col.GRN))

            if valid_targets:
                if len(valid_targets) == 1:
                    target_hero = valid_targets[0]
                else:
                    print(Col.wrap("\n SELECT HERO TO DRAW A CARD:", Col.CYAN))
                    for i, h in enumerate(valid_targets, 1):
                        print(f" [{i}] {h.name} (Hand: {len(h.hand)})")
                    choice = engine.ui.ask_choice(" >> ", 1, len(valid_targets))
                    target_hero = valid_targets[choice - 1]

                target_hero.draw_cards(1)
                engine.log.append(Col.wrap(f" 🌳 WE ARE GROOT: {target_hero.name} draws 1 card.", Col.GRN))
            return True

        # ==========================================
        # ABILITY 3: "I Am Groot!" (Tandem Attack Hijack)
        # ==========================================
        elif sid == "groot_i_am_groot!":
            
            # Phase 1: Ally Attacks
            if valid_targets:
                if len(valid_targets) == 1:
                    target_hero = valid_targets[0]
                else:
                    print(Col.wrap("\n SELECT HERO TO DEAL TANDEM DAMAGE:", Col.CYAN))
                    for i, h in enumerate(valid_targets, 1):
                        print(f" [{i}] {h.name} (at {engine.locations[h.location_index].name})")
                    choice = engine.ui.ask_choice(" >> ", 1, len(valid_targets))
                    target_hero = valid_targets[choice - 1]

                engine.log.append(Col.wrap(f" 🌳 I AM GROOT! {target_hero.name} is given an opening to strike!", Col.GRN + Col.BOLD))
                GrootLogic._tandem_attack_loop(engine, target_hero)

            # Safety check just in case the ally won the game
            if getattr(engine, 'game_over', False):
                return True

            # Phase 2: Groot Attacks
            engine.log.append(Col.wrap(f" 🌳 I AM GROOT! {hero.name} strikes out!", Col.GRN + Col.BOLD))
            GrootLogic._tandem_attack_loop(engine, hero)

            return True

        return False
