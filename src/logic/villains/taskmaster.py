# [Target: src/logic/villains/taskmaster.py]

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class TaskmasterLogic(BaseVillainLogic):
    @staticmethod
    def on_bam(engine, villain):
        BaseVillainLogic.on_bam(engine, villain)
        loc = engine.locations[villain.location_index]
        loc.crisis_tokens += 1
        engine.log.append(Col.wrap(f" 💥 BAM: Taskmaster deploys Crisis token in {loc.name}!", Col.RED))
        engine.log.append(f"Location Crisis: {loc.crisis_tokens}")
    
    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW at {location.name}!", Col.RED))
        location.crisis_tokens += 1
        engine.log.append(Col.wrap("Taskmaster adds a Crisis Token.", Col.YLW))

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        loc_idx = villain.location_index
        loc = engine.locations[loc_idx]
        
        if sid == "copycat":
            # 1. Identify Mimicry Type
            add_data = card.get("add", {}).get("center", {})
            is_heroic = "civilians" in add_data
            
            token_key = "civilians" if is_heroic else "thugs"
            symbol_type = "heroic" if is_heroic else "attack"
            icon = ICON['heroic'] if is_heroic else ICON['attack']
            
            # 2. Calculation
            count = engine.storyline.count_symbols(symbol_type, depth=2)
            
            # 3. DEPLOYMENT (The Fix: Using TokenSystem)
            if count > 0:
                from src.systems.token_system import TokenSystem
                # We provide a local tracker for this specific deployment batch
                overflow_tracker = set()
                for _ in range(count):
                    # 🚨 JULES'S OPTIMIZATION: Stop adding if the location already overflowed
                    if loc_idx in overflow_tracker: 
                        break
                    TokenSystem.add_token(engine, loc_idx, token_key, overflow_tracker)
            
            # 4. Log Update
            color = Col.YLW if count > 0 else Col.CYAN
            target_name = "Civilians" if is_heroic else "Thugs"
            msg = f" 🃏 Copycat ({icon}): Taskmaster mimics your {symbol_type}! +{count} {target_name}."
            engine.log.append(Col.wrap(msg, color))

        elif sid == "dark_schemes":
            heroes_here = [h for h in engine.heroes if h.location_index == loc_idx]
            if not heroes_here:
                loc.crisis_tokens = getattr(loc, "crisis_tokens", 0) + 1
                engine.log.append(Col.wrap(f" 🐙 Dark Schemes: No heroes in sight. Crisis token placed in {loc.name}!", Col.RED))

    @staticmethod
    def is_villain_shielded(engine, villain):
        """TASKMASTER: Shielded by Crisis tokens (Board-wide)."""
        total_crisis = sum(getattr(loc, 'crisis_tokens', 0) for loc in engine.locations)
        
        if total_crisis > 0:
            return True, f" 🛡️ TASKMASTER is mimicking your defense! ({total_crisis} Crisis tokens active)"
            
        return False, ""

    @staticmethod
    def get_extra_attack_options(engine, loc, hero):
        """Taskmaster: Remove Crisis ONLY if location is TOTALLY empty."""
        opts = []
        # UPDATED: Must be free of BOTH Thugs AND Civilians (BGG Rule)
        if getattr(loc, "crisis_tokens", 0) > 0 and loc.thugs == 0 and loc.civilians == 0:
            opts.append({
                "label": f"Tactical Breach: Remove Crisis ({ICON['attack']})",
                "id": "tm_remove_crisis_atk",
                "cost": 1,
                "execute": lambda e: TaskmasterLogic._execute_crisis_removal(e, loc, "Breach")
            })
        return opts

    @staticmethod
    def get_extra_heroic_options(engine, loc, hero):
        """Taskmaster: Remove Crisis ONLY if location is TOTALLY empty."""
        opts = []
        # UPDATED: Must be free of BOTH Thugs AND Civilians (BGG Rule)
        if getattr(loc, "crisis_tokens", 0) > 0 and loc.thugs == 0 and loc.civilians == 0:
            opts.append({
                "label": f"Analyze Weakness: Remove Crisis ({ICON['heroic']})",
                "id": "tm_remove_crisis_her",
                "cost": 1,
                "execute": lambda e: TaskmasterLogic._execute_crisis_removal(e, loc, "Analysis")
            })
        return opts

    @staticmethod
    def _execute_crisis_removal(engine, loc, method):
        """Standardized removal with explicit success return."""
        if getattr(loc, 'crisis_tokens', 0) <= 0:
            return False
            
        loc.crisis_tokens -= 1
        engine.log.append(Col.wrap(f" 🛡️ {method.upper()}: 1 Crisis token removed from {loc.name}!", Col.GRN))
        return True
        