## src/systems/villain_system.py
from src.utils.helpers import Col, wait_for_user, ICON
from src.systems.turn_system import TurnSystem

class VillainSystem:
    @staticmethod
    def add_figures(engine, loc_idx, thugs=0, civs=0):
        """
        The System Gatekeeper.
        Checks for global blocks (Spymaster) then hands off to the Location.
        """
        from src.systems.status_system import StatusSystem
        loc = engine.locations[loc_idx]

        # 🛑 GATE 1: Destroyed Locations (Doctor Octopus mechanics)
        if getattr(loc, 'is_destroyed', False):
            return None

        # 🛑 GATE 2: Spymaster Block (Generic Reinforcement Block)
        if StatusSystem.has_status(loc, "block_reinforcements"): 
            engine.log.append(Col.wrap(f" 🛡️ SPYMASTER: {loc.name} is secured against reinforcements!", Col.CYAN)) 
            return 0 
            
        # Hand off the actual math and internal bouncer-logic to the Location entity
        return loc.add_figures(engine, thugs=thugs, civs=civs)

    @staticmethod
    def _check_turn_skipped(engine, forced_extra_card):
        from src.systems.status_system import StatusSystem
        if StatusSystem.has_status(engine.villain, "delay_turn") and not forced_extra_card:
            StatusSystem.decrement_status(engine.villain, "delay_turn")
            engine.log.append(Col.wrap(f" ⏳ DELAYED: {engine.villain.name}'s turn was skipped!", Col.PURP + Col.BOLD))
            engine.turn_count += 1
            return True

        if getattr(engine, 'villain_stunned', False) and not forced_extra_card:
            engine.villain_stunned = False
            engine.log.append(Col.wrap(f" [*] TANGLED: {engine.villain.name} loses their turn!", Col.GRN + Col.BOLD))
            engine.turn_count += 1
            return True

        return False

    @staticmethod
    def _modify_plan(engine, plan):
        from src.systems.status_system import StatusSystem
        plan = StatusSystem.route_draw_interception(engine, plan)
        
        if StatusSystem.has_status(engine.villain, "force_facedown_plan"):
            engine.log.append(Col.wrap(f" 🌟 PASSIVE: Master Plan played facedown!", Col.CYAN + Col.BOLD))
            for key in ['bam', 'trigger', 'add', 'movement', 'move', 'special_id']: 
                plan[key] = False if key != 'add' else {}
            plan['effect_text'] = "Nullified."
            StatusSystem.decrement_status(engine.villain, "force_facedown_plan")

        plan['owner'] = engine.villain.name
        return plan

    @staticmethod
    def _execute_plan_phases(engine, logic, plan):
        from src.systems.status_system import StatusSystem
        
        # 1. MOVEMENT (🚨 PRESERVED DELEGATION FOR DOC OCK)
        if not StatusSystem.has_status(engine.villain, "negate_movement"):
            logic.handle_movement(engine, engine.villain, plan)

        # 2. TRIGGER
        v_idx = engine.villain.location_index
        v_loc = engine.locations[v_idx]
        if plan.get("trigger") and v_loc.threat and not v_loc.threat.cleared:
            logic.resolve_trigger(engine, v_loc.threat, v_idx)
            VillainSystem.process_event_queue(engine)

        # 3. BAM!
        if plan.get("bam"):
            from src.systems.status_system import StatusSystem
            # 🚨 THE INTERCEPTOR: Catch Empathic Manipulation before it reaches the Event System
            if StatusSystem.has_status(engine, "cancel_next_bam"):
                engine.log.append(Col.wrap("\n 🛑 BAM! CANCELLED by Empathic Manipulation!", Col.GRN + Col.BOLD))
                StatusSystem.remove_status(engine, "cancel_next_bam")
            else:
                from src.systems.event_system import EventSystem
                EventSystem.broadcast_bam(engine)
            
            VillainSystem.process_event_queue(engine)

        # 4. TOKEN DISTRIBUTION
        if "add" in plan:
            from src.systems.token_system import TokenSystem
            TokenSystem.distribute_from_villain(engine, plan["add"])
            
        # 5. SPECIAL EFFECT
        if plan.get("special_id"):
            logic.resolve_special(engine, engine.villain, plan)
            VillainSystem.process_event_queue(engine)

    @staticmethod
    def execute_turn(engine, forced_extra_card=False):
        """Processes the full Villain turn sequence."""
        TurnSystem.reset_boss_defenses(engine)

        if VillainSystem._check_turn_skipped(engine, forced_extra_card):
            return

        logic = engine.villain_logic 
        plan = engine.villain.draw_plan()
        
        if not plan: 
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS" 
            engine.victory_reason = f"{engine.villain.name} has completed the Master Plan!"
            engine.loss_reason = f"{engine.villain.name} has completed the Master Plan!"
            return 

        plan = VillainSystem._modify_plan(engine, plan)
        engine.storyline.add(plan)

        if not forced_extra_card:
            engine.turn_count += 1
            engine.log = [] 
        else:
            engine.log.append(Col.wrap(" EXTRA MASTER PLAN ACTIVATED!", Col.MAGENTA))

        # 🚨 THE VILLAIN ANNOUNCER (PRESERVED)
        card_name = VillainSystem.get_plan_name(plan)
        effect = plan.get('effect_text') or plan.get('effect') or plan.get('special_text') or plan.get('text')
        
        print(f"\n{Col.wrap('=====================================================', Col.RED)}")
        print(f"{Col.wrap(f' 🃏 VILLAIN PLAYS: {card_name.upper()}', Col.RED + Col.BOLD)} ")
        if effect:
            print(Col.wrap(f"    └ {effect}", Col.YLW))
        print(f"{Col.wrap('=====================================================', Col.RED)}")
        
        engine.log.append(Col.wrap(f" 🃏 Master Plan Revealed: {card_name} ", Col.RED + Col.BOLD))
        if effect:
            engine.log.append(Col.wrap(f"    └ {effect} ", Col.DARK_GRAY))

        VillainSystem._execute_plan_phases(engine, logic, plan)
        VillainSystem.process_event_queue(engine, is_final_phase=True)

    @staticmethod
    def process_event_queue(engine, is_final_phase=False):
        deferred_events = []
        
        # ⚡ BOLT OPTIMIZATION: Define priority map and sort key ONCE outside the loop
        priority = {"overflow": 1, "ko_bam": 2, "extra_card": 3}
        sort_key = lambda e: priority.get(e["type"], 99)

        while getattr(engine, 'queued_events', []):
            # 🛑 THE SHORT-CIRCUIT: Halt all cascade triggers if the game is over!
            if getattr(engine, 'game_over', False):
                engine.queued_events.clear()
                break

            engine.queued_events.sort(key=sort_key)
            event = engine.queued_events.pop(0)
            
            if event["type"] == "extra_card" and not is_final_phase:
                deferred_events.append(event)
                continue

            if event["type"] == "overflow": 
                engine.villain_logic.on_overflow(engine, engine.villain, event["loc"], event["t_type"])
            elif event["type"] == "ko_bam":
                engine.log.append(Col.wrap(f" ☠️ {engine.villain.name} strikes while the hero is down! ", Col.RED + Col.BOLD))
                from src.systems.event_system import EventSystem
                
                # 🛑 THE SHIELD: Turn on the lock while the BAM resolves
                engine.is_resolving_ko_bam = True
                EventSystem.broadcast_bam(engine)
                engine.is_resolving_ko_bam = False
            elif event["type"] == "extra_card" and is_final_phase:
                engine.log.append(Col.wrap(f" ⏳ THE TIMELINE FRACTURES!", Col.YLW))
                VillainSystem.execute_turn(engine, forced_extra_card=True)

        if deferred_events: engine.queued_events.extend(deferred_events)

    @staticmethod
    def get_attackable_villains_at(engine, loc_idx):
        """
        Returns a list of targetable villains at a specific location.
        """
        # 🔌 DECOUPLED MODE DELEGATION
        if hasattr(engine.mode_handler, "get_attackable_villains_at"): 
            return engine.mode_handler.get_attackable_villains_at(loc_idx) 

        # 🦹 STANDARD MODE
        targets = []
        if engine.villain and engine.villain.location_index == loc_idx:
            from src.logic.shield_logic import is_target_vulnerable
            vulnerable, _ = is_target_vulnerable(engine, engine.villain)
            if vulnerable:
                targets.append({
                    "name": engine.villain.name, 
                    "hp": engine.villain.hp, 
                    "type": "standard_villain", 
                    "ref": engine.villain
                })
        return targets

    @staticmethod
    def get_plan_name(card):
        """Standardized translator utilizing existing Hero Oracle logic."""
        from src.utils.helpers import get_plan_intel
        
        # 1. Signature Moves (Catching specials missing a hardcoded 'name')
        if card.get('special_id') and not card.get('name'):
            parsed_name = card['special_id'].replace('_', ' ').title()
            if parsed_name == "Hail Hydra": return "HAIL HYDRA!"
            return parsed_name.upper()
            
        # 2. The Universal Translator (Widow/Warlock Helper)
        # This will perfectly parse generic cards into readable intel strings!
        return get_plan_intel(card)
        
    @staticmethod
    def execute_bam(engine):
        from src.systems.event_system import EventSystem
        EventSystem.broadcast_bam(engine)
