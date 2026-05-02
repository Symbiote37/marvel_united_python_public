# src/systems/challenge_system.py
import random
from src.utils.helpers import Col

class ChallengeSystem:
    # 🚨 CONSTANTS
    MODERATE = "moderate_wild"  
    HARD = "hard_wild"          
    HEROIC = "heroic_wild"      
    PLAN_B = "plan_b"           
    ENDANGERED = "endangered_locations"
    SECRET_IDENTITY = "secret_identity"

    @classmethod
    def get_next_difficulty(cls, current_difficulty):
        """Returns the next difficulty tier. Returns None if already at max."""
        if not current_difficulty or current_difficulty == "standard": return cls.MODERATE
        if current_difficulty == cls.MODERATE: return cls.HARD
        if current_difficulty == cls.HARD: return cls.HEROIC
        return None

    @classmethod
    def roll_random_challenge(cls, base_difficulty=None, active_challenges=None):
        """Rolls a random challenge from the remaining pool, factoring in manual overrides."""
        if active_challenges is None:
            active_challenges = []
            
        # 1. Determine the effective difficulty (Did the player manually override it?)
        effective_diff = base_difficulty
        if cls.HEROIC in active_challenges: effective_diff = cls.HEROIC
        elif cls.HARD in active_challenges: effective_diff = cls.HARD
        elif cls.MODERATE in active_challenges: effective_diff = cls.MODERATE

        # 2. Build the possible lottery pool
        pool = [
            cls.PLAN_B,
            cls.ENDANGERED,
            cls.SECRET_IDENTITY
        ]
        
        next_diff = cls.get_next_difficulty(effective_diff)
        if next_diff:
            pool.append(next_diff)

        # 3. Filter out anything the player already selected
        available_pool = [c for c in pool if c not in active_challenges]
        
        if not available_pool:
            return None
            
        return random.choice(available_pool)

    @classmethod
    def filter_hero_deck(cls, deck, active_challenges):
        """Intercepts and filters a hero's raw deck list before the game starts."""
        filtered = []
        removed_single = False
        removed_double = False
        
        remove_single_target = cls.MODERATE in active_challenges or cls.HEROIC in active_challenges
        remove_double_target = cls.HARD in active_challenges or cls.HEROIC in active_challenges
        
        for card in deck:
            # 🚨 FIX 1: Make actions case-insensitive so "WILD" or "wild" both work
            actions = [str(a).lower() for a in card.get('actions', [])]
            
            # 🚨 FIX 2: Check for ACTUAL truthy data, ignoring empty strings like "effect_text": ""
            has_special = bool(card.get('special_id')) or bool(card.get('effect_text'))
            
            # 🎯 TARGET 1: Generic Single Wild
            if remove_single_target and not removed_single and not has_special:
                if len(actions) == 1 and actions[0] == 'wild':
                    removed_single = True
                    continue  
            
            # 🎯 TARGET 2: Generic Double Wild
            if remove_double_target and not removed_double and not has_special:
                if len(actions) == 2 and actions.count('wild') == 2:
                    removed_double = True
                    continue  
                    
            filtered.append(card)
            
        return filtered

    @classmethod
    def apply_engine_modifiers(cls, engine, active_challenges):
        """Applies state changes to the engine (like Plan B mission limits)."""
        # -- Plan B Challenge --
        if cls.PLAN_B in active_challenges:
            engine.missions["civilians_max"] = 12
            engine.missions["thugs_max"] = 12
            engine.missions["threats_max"] = 6
            engine.log.append(Col.wrap(" ⚠️ PLAN B ACTIVE: Mission thresholds increased to 12/12/6. Complete all 3 to win.", Col.PURP + Col.BOLD))
            
        # -- Endangered Locations Challenge --
        if cls.ENDANGERED in active_challenges:
            # 1. Filter for 4+ capacity locations
            valid_locs = [l for l in engine.locations if l.capacity >= 4]
            
            if len(valid_locs) < len(engine.heroes):
                valid_locs = engine.locations[:]
                
            random.shuffle(valid_locs)
            
            # 2. Tie a unique location to each active hero
            for i, hero in enumerate(engine.heroes):
                loc = valid_locs[i]
                loc.endangered_hero = hero 
                engine.log.append(Col.wrap(f" ⚠️ ENDANGERED: {hero.name} is tied to {loc.name}!", Col.YLW))

            # 3. 🚨 THE MASTER OVERRIDE: Intercept the Villain's Overflow Logic!
            original_on_overflow = getattr(engine.villain_logic, "on_overflow", None)
            
            # We add a tag to prevent infinite double-wrapping if playing multiple games in one session
            if original_on_overflow and not getattr(original_on_overflow, 'is_endangered_wrapper', False):
                def wrapped_overflow(engine_ref, villain, loc_idx, t_type):
                    # Only apply damage if the challenge is active for THIS specific match
                    if cls.ENDANGERED in getattr(engine_ref, 'active_challenges', []):
                        loc_obj = engine_ref.locations[loc_idx] if isinstance(loc_idx, int) else loc_idx
                        tied_hero = getattr(loc_obj, 'endangered_hero', None)
                        
                        if tied_hero and not getattr(tied_hero, 'is_ko', False):
                            engine_ref.log.append(Col.wrap(f" ⚠️ ENDANGERED: {tied_hero.name} takes 1 damage from the overflow at {loc_obj.name}!", Col.RED + Col.BOLD))
                            from src.systems.damage_system import DamageSystem
                            DamageSystem.deal_hero_damage(engine_ref, tied_hero, 1)
                            
                    # Pass execution back to the original villain effect
                    return original_on_overflow(engine_ref, villain, loc_idx, t_type)

                wrapped_overflow.is_endangered_wrapper = True
                engine.villain_logic.on_overflow = wrapped_overflow
               
        # -- Secret Identity Challenge --
        if cls.SECRET_IDENTITY in active_challenges:
            # 1. Place Journalists
            engine.locations[0].journalists = getattr(engine.locations[0], 'journalists', 0) + 1
            engine.locations[2].journalists = getattr(engine.locations[2], 'journalists', 0) + 1
            engine.locations[4].journalists = getattr(engine.locations[4], 'journalists', 0) + 1
            engine.log.append(Col.wrap(" 📷 SECRET IDENTITY: Journalists are watching your every move! ", Col.CYAN + Col.BOLD))

    @classmethod
    def on_action_resolved(cls, engine, hero, action_type):
        """Observer hook triggered by the ActionSystem."""
        if cls.SECRET_IDENTITY in getattr(engine, 'active_challenges', []) and action_type != "move":
            if getattr(hero, 'exposure_this_turn', False) or getattr(hero, 'is_exposed', False): 
                return
                
            loc = engine.locations[hero.location_index]
            if getattr(loc, 'journalists', 0) > 0:
                hero.exposure_this_turn = True
                hero.exposure_tokens = getattr(hero, 'exposure_tokens', 0) + 1
                engine.log.append(Col.wrap(f" 📸 FLASH! {hero.name} was photographed! (+1 Exposure) ", Col.YLW))
                
                if hero.exposure_tokens >= 3:
                    hero.is_exposed = True
                    hero.force_facedown_exposure = True
                    engine.log.append(Col.wrap(f" 🚨 IDENTITY EXPOSED! {hero.name} is swarmed by the press! ", Col.RED + Col.BOLD))
                    from src.systems.damage_system import DamageSystem
                    DamageSystem.deal_hero_damage(engine, hero, 1)

    @classmethod
    def get_challenge_heroic_options(cls, engine, hero, loc):
        """Allows active challenges to inject custom commands into the Heroic menu."""
        opts = []
        if cls.SECRET_IDENTITY in getattr(engine, 'active_challenges', []):
            
            # Scoped execution function for moving Journalists
            def execute_journalist_move(src_idx):
                def _exec(eng):
                    adj_opts = [(src_idx + 1) % 6, (src_idx - 1) % 6]
                    print(f"\n--- {Col.wrap('MOVE JOURNALIST TO', Col.CYAN)} ---")
                    for j, a_idx in enumerate(adj_opts, 1):
                        print(f" [{j}] {eng.locations[a_idx].name}")
                    
                    j_choice = eng.ui.ask_choice(" >> ", 1, 2)
                    dest_loc = eng.locations[adj_opts[j_choice - 1]]
                    
                    eng.locations[src_idx].journalists -= 1
                    dest_loc.journalists = getattr(dest_loc, 'journalists', 0) + 1
                    
                    active_h = eng.heroes[getattr(eng, 'current_hero_index', 0)]
                    eng.log.append(Col.wrap(f" 📷 {active_h.name} distracted the press, moving a Journalist to {dest_loc.name}! ", Col.CYAN))
                return _exec

            for i, loc_obj in enumerate(engine.locations):
                if getattr(loc_obj, 'journalists', 0) > 0:
                    opts.append({
                        "label": f"Move Journalist from {loc_obj.name}",
                        "id": f"move_journalist_{i}",
                        "cost": 1,
                        "execute": execute_journalist_move(i)
                    })
        return opts
