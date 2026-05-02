import copy
from src.utils.helpers import Col

class UndoSystem:
    _history_stack = []

    @classmethod
    def save_snapshot(cls, engine):
        """Takes a decoupled deepcopy of the pure data layer."""
        try:
            snapshot = {
                "heroes": copy.deepcopy(engine.heroes),
                "villain": copy.deepcopy(engine.villain),
                "locations": copy.deepcopy(engine.locations),
                "storyline": copy.deepcopy(engine.storyline),
                "active_pool": copy.deepcopy(getattr(engine, 'active_pool', {})),
                "queued_events": copy.deepcopy(getattr(engine, 'queued_events', [])),
                "used_specials": copy.deepcopy(getattr(engine, 'used_specials', set())),
                "missions": copy.deepcopy(engine.missions),
                "game_over": getattr(engine, 'game_over', False),
                "victory_status": getattr(engine, 'victory_status', None),
                "loss_reason": getattr(engine, 'loss_reason', ""),
                # 🚨 SENSOR ADDED: Capture the exact scoreboard at this moment in time
                "match_stats": copy.deepcopy(getattr(engine, 'match_stats', {}))
            }
            cls._history_stack.append(snapshot)
            # 🚨 THE EXPANSION: Prevent history capping during long combo turns
            if len(cls._history_stack) > 50:
                cls._history_stack.pop(0)
        except Exception as e:
            engine.log.append(Col.wrap(f" [!] System failed to save temporal anchor: {e}", Col.RED))

    @classmethod
    def restore_snapshot(cls, engine):
        """Restores the engine state to the last saved anchor."""
        if not cls._history_stack:
            engine.log.append(Col.wrap(" ⏳ TIME TRAVEL FAILED: No previous temporal anchor found.", Col.YLW))
            return False

        snapshot = cls._history_stack.pop()
        
        engine.heroes = snapshot["heroes"]
        engine.villain = snapshot["villain"]
        engine.locations = snapshot["locations"]
        engine.storyline = snapshot["storyline"]
        engine.active_pool = snapshot["active_pool"]
        engine.queued_events = snapshot["queued_events"]
        engine.missions = snapshot["missions"]
        engine.game_over = snapshot["game_over"]
        engine.victory_status = snapshot["victory_status"]
        engine.loss_reason = snapshot["loss_reason"]
        
        if "used_specials" in snapshot:
            engine.used_specials = snapshot["used_specials"] 
            
        engine.log.append(Col.wrap(" ⏳ TIMELINE RESTORED: Actions undone.", Col.MAGENTA + Col.BOLD))
        return True

    @classmethod
    def clear_history(cls):
        cls._history_stack.clear()
