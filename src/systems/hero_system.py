import sys
import random
from src.utils.helpers import Col, ICON
from src.ui.board import BoardRenderer
from src.systems.event_system import EventSystem
from src.systems.location_system import LocationSystem
from src.logic.threat_logic import ThreatLogic

class HeroSystem:
    @staticmethod
    def execute_turn(engine, hero, hero_idx):
        h_colors = BoardRenderer.HERO_COLORS
        h_color = h_colors[hero_idx % len(h_colors)]
        current_loc = engine.locations[hero.location_index]
        hero.tax_paid_this_turn = False

        # --- PHASE 1: STATE CAPTURE & PASSIVES ---
        is_protected, was_ko_at_start, sot_mods = HeroSystem._phase1_passives(
            engine, hero, current_loc
        )

        # --- PHASE 2: RECOVERY GATE ---
        if not HeroSystem._phase2_recovery(engine, hero, is_protected, was_ko_at_start):
            return

        # --- PHASE 3: TURN INITIALIZATION ---
        prev_actions = HeroSystem._phase3_initialization(
            engine, hero, h_color, sot_mods
        )

        # --- PHASE 4: DRAW PHASE ---
        HeroSystem._phase4_draw(engine, hero, was_ko_at_start)

        # --- PHASE 5: CARD SELECTION ---
        played = HeroSystem._phase5_card_selection(engine, hero, sot_mods)

        # --- PHASE 6: POOL RESOLUTION & COMMAND LOOP ---
        should_continue = HeroSystem._phase6_pool_resolution_and_commands(
            engine, hero, hero_idx, played, prev_actions
        )
        if not should_continue:
            return

        # --- PHASE 7: END OF TURN ---
        HeroSystem._phase7_end_of_turn(engine, hero, played)

    @staticmethod
    def _phase1_passives(engine, hero, current_loc):
        from src.systems.status_system import StatusSystem

        if StatusSystem.has_status(hero, "evade"):
            StatusSystem.remove_status(hero, "evade")
            engine.log.append(Col.wrap(f" 🧍 {hero.name}'s evasion effect wears off.", Col.DARK_GRAY))
            
        # 🚨 SECRET IDENTITY: Reset turn exposure tracker
        hero.exposure_this_turn = False

        is_protected = StatusSystem.has_status(hero, "protect_last_card")
        was_ko_at_start = hero.is_ko or (len(hero.hand) == 0 and not is_protected)

        sot_mods = ThreatLogic.resolve_sot_passives(engine, hero, current_loc)

        if getattr(hero, "is_invincible", False):
            hero.is_invincible = False
            default_msg = f" 🛡️ {hero.name}'s invincibility has worn off. "
            msg = getattr(hero, "invincible_wear_off_msg", default_msg)
            engine.log.append(Col.wrap(msg if msg.endswith(" ") else msg + " ", Col.CYAN))
            if hasattr(hero, "invincible_deflect_msg"): delattr(hero, "invincible_deflect_msg")
            if hasattr(hero, "invincible_wear_off_msg"): delattr(hero, "invincible_wear_off_msg")
            if hasattr(hero, "on_deflect"): delattr(hero, "on_deflect")

        return is_protected, was_ko_at_start, sot_mods

    @staticmethod
    def _phase2_recovery(engine, hero, is_protected, was_ko_at_start):
        if hero.is_ko or (len(hero.hand) == 0 and not is_protected):
            if was_ko_at_start:
                if not hero.deck and not hero.hand:
                    EventSystem.trigger_defeat(engine, f"{hero.name} has no cards left to recover! ")
                    return False

                hero.is_ko = False
                needed = 4 - len(hero.hand)
                if needed > 0:
                    hero.draw_cards(needed)
                engine.log.append(Col.wrap(f" ✅ {hero.name} stands back up and resupplies! ", Col.GRN))
                engine.ui.wait() 
            else:
                engine.log.append(Col.wrap(f" 💀 {hero.name} was KO'd and must skip their turn! ", Col.RED))
                return False
        return True

    @staticmethod
    def _phase3_initialization(engine, hero, h_color, sot_mods):
        from src.systems.turn_system import TurnSystem

        inherited_display = ""
        prev_actions = (
            [] if sot_mods.get("ignore_prev") else engine.storyline.get_last_hero_actions()
        )
        if prev_actions:
            p = [f"{ICON[k]}:{prev_actions.count(k)}" for k in ["move", "attack", "heroic", "wild"] if prev_actions.count(k) > 0]
            if p:
                inherited_display = f" | INHERITED: {' '.join(p)} "

        engine.log = [f"▶ {Col.wrap(hero.name.upper(), h_color)}'S TURN{inherited_display} "]
        TurnSystem.reset_boss_defenses(engine)
        if hasattr(engine.villain_logic, "broadcast_stance"):
            engine.villain_logic.broadcast_stance(engine)

        return prev_actions

    @staticmethod
    def _phase4_draw(engine, hero, was_ko_at_start):
        # 🚨 RESTORED: Respect the Mode Handler's draw override
        override_draw = getattr(engine.mode_handler, 'override_draw', False)
        if not was_ko_at_start and hero.deck and not override_draw:
            hero.draw_cards(1)

    @staticmethod
    def _phase5_card_selection(engine, hero, sot_mods):
        from src.systems.status_system import StatusSystem

        if sot_mods.get("is_random"):
            choice = random.randint(0, len(hero.hand) - 1)
        else:
            BoardRenderer.render(engine.get_game_state(hero))
            print(f"\n{Col.wrap('HAND:', Col.BOLD)}")
            for i, card in enumerate(hero.hand, 1):
                icons = " ".join([ICON.get(a, a) for a in card.get("actions", [])])
                print(f" {i}: [{icons}] {card.get('name', '')} ")
                if card.get("effect_text"):
                    print(Col.wrap(f"    └ {card['effect_text']}", Col.DARK_GRAY))

            # 🚨 RESTORED: UI Adapter ask_choice
            choice = engine.ui.ask_choice("\nPlay card >> ", 1, len(hero.hand)) - 1

        played = hero.play_card(choice)
        played["owner"] = hero.name

        if len(hero.hand) == 0 and not getattr(hero, "is_ko", False):
            if not StatusSystem.has_status(hero, "protect_last_card"):
                if hasattr(engine.villain_logic, "handle_hero_ko"):
                    engine.villain_logic.handle_hero_ko(engine, hero)
            else:
                engine.log.append(Col.wrap(f" 🌟 IMMORTAL: {hero.name} is out of cards but refuses to fall! ", Col.CYAN))

        # 🚨 RESTORED: Secret Identity Challenge Logic
        if getattr(hero, 'force_facedown_exposure', False):
            played['is_facedown'] = True
            played['actions'] = [] 
            engine.log.append(Col.wrap(f" 📷 EXPOSED! {hero.name} must play their card facedown to dodge the press. ", Col.RED + Col.BOLD))
            hero.force_facedown_exposure = False
            
        if sot_mods.get("is_facedown"):
            played["is_facedown"] = True
            played["actions"] = []
            engine.log.append(Col.wrap(f" 🃏 {hero.name} is dazed; card played facedown. ", Col.PURP))

        return played

    @staticmethod
    def _phase6_pool_resolution_and_commands(engine, hero, hero_idx, played, prev_actions):
        from src.systems.action_system import ActionSystem
        from src.logic.modifier_logic import apply_action_modifiers
        from src.systems.challenge_system import ChallengeSystem
        from src.systems.undo_system import UndoSystem

        card_actions = played.get("actions", [])
        pool = {k: card_actions.count(k) + prev_actions.count(k) for k in ["move", "attack", "heroic", "wild"]}
        engine.storyline.add(played)
        if hasattr(engine.villain_logic, "on_card_played"):
            engine.villain_logic.on_card_played(engine)

        apply_action_modifiers(engine, hero, pool)
        engine.active_pool = pool
        engine.used_specials = set() # 🚨 Attached to engine for UndoSystem

        sid = played.get("special_id")
        is_secret_identity = ChallengeSystem.SECRET_IDENTITY in getattr(engine, 'active_challenges', [])
        
        # 🚨 RESTORED: The Valve
        if sid and ActionSystem.is_auto_trigger(played) and not is_secret_identity:
            if not played.get("is_facedown"):
                if ActionSystem.resolve_special_id(engine, hero, played):
                    engine.used_specials.add(sid)

        # 🚨 RESTORED: Baseline Anchor drop
        UndoSystem.clear_history()       
        UndoSystem.save_snapshot(engine)

        # --- COMMAND LOOP ---
        while True:
            # 🚨 RESTORED: Kill Switch
            engine._check_game_status()
            if getattr(engine, 'game_over', False):
                return False
                
            # 🚨 RESTORED: Stale reference sync
            hero = engine.heroes[hero_idx]
            
            played = engine.storyline.cards[-1]
            sid = played.get("special_id")
            pool = engine.active_pool
            used_specials = getattr(engine, 'used_specials', set()) 
            
            BoardRenderer.render(engine.get_game_state(hero))

            tokens = getattr(hero, "stashed_tokens", []) or getattr(hero, "action_tokens", []) or []
            pool_display = " ".join([f"{ICON[k]}:{v}" for k, v in pool.items() if v > 0])
            token_display = " ".join([ICON.get(t, t) for t in tokens])

            print(f"\n{Col.wrap('ACTIVE POOL:', Col.YLW)} {pool_display if pool_display else 'None'} ")
            if tokens:
                print(f"{Col.wrap('STASHED TOKENS:', Col.CYAN)} [ {token_display} ] ")

            valid_cmds = {"0", "1", "2", "3", "U"}
            commands = [f"(1) {ICON['move']}", f"(2) {ICON['attack']}", f"(3) {ICON['heroic']}"]
            
            if tokens:
                commands.append(f"(T) Tokens")
                valid_cmds.add("T")

            custom_cmds = engine.mode_handler.get_custom_commands(engine, hero, pool)
            commands.extend(custom_cmds)
            if custom_cmds:
                valid_cmds.add("P")

            camp_mgr = getattr(engine, "campaign_manager", None)
            has_bolts = camp_mgr and camp_mgr.state.get("blue_bolts", 0) > 0
            if has_bolts:
                commands.append(Col.wrap(f" (B) Blue Bolt ({camp_mgr.state['blue_bolts']})", Col.CYAN))
                valid_cmds.add("B")

            is_auto = played.get("auto_trigger", False)
            
            # 🚨 RESTORED: Secret Identity auto-trigger block bypass
            if sid and sid not in used_specials and (not is_auto or is_secret_identity):
                if not played.get("is_facedown"):
                    commands.append(Col.wrap(f" (S) {played.get('name', 'SPECIAL').upper()}", Col.CYAN))
                    valid_cmds.add("S")
                else:
                    commands.append(Col.wrap(f" (S) [DISABLED]", Col.WHT))

            # 🚨 RESTORED: Undo command
            commands.append(Col.wrap(" (U) Undo Action", Col.MAGENTA))
            commands.append("(0) End Turn")
            print(f"\nCOMMANDS: {' | '.join(commands)}")

            cmd = engine.ui.ask_raw("\n> ", valid_cmds)

            if cmd == "0":
                break
                
            # 🚨 RESTORED: Temporal mechanics
            elif cmd == 'U':
                if UndoSystem.restore_snapshot(engine):
                    pool = engine.active_pool 
                    if not UndoSystem._history_stack:
                        UndoSystem.save_snapshot(engine)
                continue
                
            elif cmd == "P":
                UndoSystem.save_snapshot(engine)
                if engine.mode_handler.handle_custom_command(engine, hero, cmd, pool):
                    continue
                    
            elif cmd == "B" and has_bolts:
                UndoSystem.save_snapshot(engine)
                from src.systems.campaign_system import CampaignSystem
                if CampaignSystem.use_blue_bolt(engine, hero):
                    pass
                    
            elif cmd == "9":
                from src.systems.debug_system import DebugSystem
                DebugSystem.open_menu(engine)
                pool = engine.active_pool
                
            elif cmd == "S" and sid and sid not in used_specials and not played.get("is_facedown"):
                UndoSystem.save_snapshot(engine)
                if ActionSystem.resolve_special_id(engine, hero, played):
                    if not played.get("repeatable", False):
                        used_specials.add(sid)
                    engine.ui.wait()
                else:
                    UndoSystem._history_stack.pop()
                    print(Col.wrap(" Special action cancelled. ", Col.YLW))
                    
            elif cmd == "T":
                UndoSystem.save_snapshot(engine)
                from src.systems.token_system import TokenSystem
                if TokenSystem.use_stashed_token(engine, hero):
                    pass

            elif cmd in ["1", "2", "3"]:
                action_type = {"1": "move", "2": "attack", "3": "heroic"}[cmd]
                if pool[action_type] > 0 or pool.get("wild", 0) > 0:
                    UndoSystem.save_snapshot(engine)
                    ActionSystem.resolve_single_action(engine, hero, action_type, pool)
                else:
                    print(Col.wrap(f" No {action_type.capitalize()} available! ", Col.RED))
                    engine.ui.wait()

        return True

    @staticmethod
    def _phase7_end_of_turn(engine, hero, played):
        from src.logic.modifier_logic import apply_zemo_interference

        apply_zemo_interference(engine, hero, played)
        ThreatLogic.resolve_eot_passives(engine, hero, engine.locations[hero.location_index])
        LocationSystem.resolve_end_of_turn(engine, hero)
