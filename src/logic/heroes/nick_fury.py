from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("nick_fury")
class NickFuryLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        if card.get("special_id") == "nick_fury_director_of_shield":
            return NickFuryLogic._director_of_shield(engine, hero, card)
        return False

    @staticmethod
    def _director_of_shield(engine, hero, card):
        acts = []
        if "➡" in card.get("effect_text", ""): acts = ["move", "move"]
        elif "★" in card.get("effect_text", ""): acts = ["heroic", "heroic"]
        elif "✸" in card.get("effect_text", ""): acts = ["attack", "attack"]
        
        print(f"\n--- {Col.wrap('🛡️ DIRECTOR OF S.H.I.E.L.D.', Col.CYAN)} ---")
        
        alive_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False) and h != hero]
        if not alive_heroes:
            engine.log.append(Col.wrap(" 🛡️ No other heroes available to command!", Col.YLW))
            return False

        for i, h in enumerate(alive_heroes, 1):
            print(f" [{i}] Command {h.name}")
        print(" [0] Cancel")
        
        choice = engine.ui.ask_choice(" >> ", 0, len(alive_heroes))
        if choice == 0: return False
        
        target_hero = alive_heroes[choice-1]
        engine.log.append(Col.wrap(f" 🛡️ {hero.name} barks orders! {target_hero.name} leaps into action!", Col.CYAN))
        
        mini_pool = {"move": 0, "attack": 0, "heroic": 0, "wild": 0}
        for a in acts: mini_pool[a] += 1
        
        from src.systems.action_system import ActionSystem
        from src.ui.board import BoardRenderer
        
        # 🚨 THE POOL SWAP: Temporarily hijack the engine's active pool
        original_pool = engine.active_pool
        engine.active_pool = mini_pool
        
        # --- THE REVISED MINI-TURN LOOP ---
        while sum(engine.active_pool.values()) > 0:
            BoardRenderer.render(engine.get_game_state(target_hero))
            
            pool_display = " ".join([f"{ICON[k]}:{v}" for k, v in mini_pool.items() if v > 0])
            print(f"\n{Col.wrap(f'{target_hero.name.upper()} COMMAND POOL:', Col.RED)} {pool_display if pool_display else 'None'}")
            
            # Use the standard 1/2/3/0 commands
            commands = [f"(1) {ICON['move']}", f"(2) {ICON['attack']}", f"(3) {ICON['heroic']}", "(0) End Command"]
            print(f"\nCOMMANDS: {' | '.join(commands)}")
            
            cmd = engine.ui.ask_raw(f" [{target_hero.name}]> ", {'1', '2', '3', '0'}).upper()
            
            if cmd == '0':
                break
            elif cmd in ['1', '2', '3']:
                action_type = {'1': 'move', '2': 'attack', '3': 'heroic'}[cmd]
                
                # Check funds before dispatching
                if mini_pool.get(action_type, 0) > 0 or mini_pool.get('wild', 0) > 0:
                    ActionSystem.resolve_single_action(engine, target_hero, action_type, mini_pool)
                    if getattr(engine, 'game_over', False): return True
                else:
                    print(Col.wrap(f" No {action_type.capitalize()} available in the Command Pool! ", Col.RED))
        
        engine.log.append(Col.wrap(f" 🛡️ {target_hero.name} finishes their orders, returning control to {hero.name}.", Col.CYAN))
        return True
