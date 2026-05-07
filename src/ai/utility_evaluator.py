# src/ai/utility_evaluator.py
from src.utils.helpers import ICON
import random

class UtilityEvaluator:
    @staticmethod
    def get_reachable_targets(engine, hero, combined_actions):
        """SPATIAL RADAR: What can the hero actually interact with this turn?"""
        moves = combined_actions.count("move") + combined_actions.count("wild")
        attacks = combined_actions.count("attack") + combined_actions.count("wild")
        heroics = combined_actions.count("heroic") + combined_actions.count("wild")

        reachable = {
            "thugs": 0, "civilians": 0, "threats": 0, "crisis": 0,
            "boss": False, "shielded_boss": False, "overflow_danger": False
        }

        curr_idx = hero.location_index
        v_idx = engine.villain.location_index

        # Calculate all unique location indices we can reach
        reachable_indices = set()
        for dist in range(moves + 1):
            reachable_indices.add((curr_idx + dist) % 6)
            reachable_indices.add((curr_idx - dist) % 6)

        for loc_idx in reachable_indices:
            loc = engine.locations[loc_idx]
            
            # Firefighter Trigger: Proactive Crowd Control (Lowered threshold from 3 to 2)
            if getattr(loc, 'thugs', 0) + getattr(loc, 'civilians', 0) >= 2:
                reachable["overflow_danger"] = True

            if attacks > 0:
                reachable["thugs"] += getattr(loc, 'thugs', 0)
                if loc_idx == v_idx:
                    reachable["boss"] = True
                    if loc.threat and not loc.threat.cleared:
                        reachable["shielded_boss"] = True

            if heroics > 0:
                blocks_h = loc.threat and getattr(loc.threat, 'blocks_heroic', False)
                if not blocks_h:
                    reachable["civilians"] += getattr(loc, 'civilians', 0)
                    
            if (attacks > 0 or heroics > 0) and loc.threat and not loc.threat.cleared:
                reachable["threats"] += 1

        return reachable

    @staticmethod
    def score_card_play(engine, hero, card, prev_actions):
        actions = card.get("actions", [])
        total_actions = actions + prev_actions
        
        # 1. PING THE RADAR
        reach = UtilityEvaluator.get_reachable_targets(engine, hero, total_actions)

        # 2. DETERMINE GAME STATE
        m_state = engine.missions
        cleared_count = 0
        distances = []
        for m_key, default_max in [("thugs", 9), ("civilians", 9), ("threats", 4)]:
            val = m_state.get(m_key, 0)
            if str(val) in ["✔", "True", "cleared"] or (isinstance(val, int) and val >= m_state.get(f"{m_key}_max", default_max)):
                cleared_count += 1
                distances.append((m_key, 0))
            else:
                distances.append((m_key, max(0, default_max - int(val))))
                
        distances.sort(key=lambda x: x[1])
        active_mission = distances[0][0] if cleared_count < 2 else None
        
        boss_vulnerable = cleared_count >= 2
        is_dying = len(hero.hand) <= 1
        score = 0

        # 🚨 CUMULATIVE STATE EVALUATION (Removing if/elif/else Paralysis)
        
        # STATE A: THE FIREFIGHTER (Always evaluate crisis response)
        if reach["overflow_danger"]:
            score += (reach["thugs"] + reach["civilians"]) * 100 
            
        if is_dying:
            moves = total_actions.count("move") + total_actions.count("wild")
            score += moves * 150 
            
        # STATE C: THE ASSASSIN (Always evaluate kill shots if vulnerable)
        if boss_vulnerable:
            if reach["boss"]:
                if reach["shielded_boss"]:
                    score += (total_actions.count("heroic") + total_actions.count("wild")) * 1000
                else:
                    score += (total_actions.count("attack") + total_actions.count("wild")) * 1000
            else:
                score += (total_actions.count("move") + total_actions.count("wild")) * 200
                
        # 🚨 STATE B: THE SPECIALIST (Omni-Grinding)
        if not boss_vulnerable:
            # Score ALL incomplete missions! Free progress is good progress.
            incomplete = [m for m, dist in distances if dist > 0]
            
            if "thugs" in incomplete:
                score += reach["thugs"] * 300
            if "civilians" in incomplete:
                score += reach["civilians"] * 300
            if "threats" in incomplete:
                score += reach["threats"] * 400

            # Reduced hoarding penalty so they don't overthink throwing a big card just to advance a mission
            if (actions.count("attack") + actions.count("wild") >= 2) and score == 0:
                score -= 250

        # Tie-breaker logic (RESTORED)
        return score + random.uniform(0.1, 0.9)
