from src.utils.helpers import Col

class TurnSystem:
    @staticmethod
    def reset_boss_defenses(engine):
        """Clears 'once-per-turn' mitigations."""
        v = engine.villain
        if hasattr(v, 'dmg_ignored_this_turn'):
            v.dmg_ignored_this_turn = 0
        if hasattr(v, 'ignored_action_this_turn'):
            v.ignored_action_this_turn = False
            
    @staticmethod
    def should_villain_act(engine, turns_since_v):
        # 🚨 THE MODULAR PACING FIX
        target_interval = engine.mode_handler.get_turn_interval()
        return turns_since_v >= target_interval

    @staticmethod
    def get_next_hero_index(current_index, hero_count, engine):
        """
        Iterates through the hero list to find the next hero NOT in the Void.
        """
        next_idx = (current_index + 1) % hero_count
        
        for _ in range(hero_count):
            target_hero = engine.heroes[next_idx]
            
            is_voided = target_hero.location_index == -1
            is_eliminated = getattr(target_hero, 'is_eliminated', False)
            
            if not is_voided and not is_eliminated:
                return next_idx
            
            next_idx = (next_idx + 1) % hero_count
            
        return next_idx
