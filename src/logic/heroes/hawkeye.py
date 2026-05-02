# --- JARVIS TROJAN HORSE: FORCE MODULE RELOAD ---
import sys
import importlib
if 'src.systems.damage_system' in sys.modules:
    importlib.reload(sys.modules['src.systems.damage_system'])
# ------------------------------------------------

from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("hawkeye")
class HawkeyeLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "hawkeye_master_marksman": return HawkeyeLogic._master_marksman(engine, hero, card)
        elif sid == "hawkeye_longshot": return HawkeyeLogic._longshot(engine, hero)
        elif sid == "hawkeye_martial_artist": return HawkeyeLogic._martial_artist(engine, hero)
        return False

    @staticmethod
    def _master_marksman(engine, hero, card):
        from src.utils.helpers import Col, ICON
        
        story = engine.storyline.cards
        
        # 1. Initialize cache if it's the first time they pressed (S) this turn
        if not hasattr(hero, 'marksman_cache'):
            available_actions = []
            
            # A. Grab the current card's native symbols (the last card added)
            current_card = story[-1]
            if not current_card.get("is_facedown") and not current_card.get("is_villain"):
                available_actions.extend(current_card.get("actions", []))
                
            # B. Safely find the inherited card (skipping any Villain cards)
            for card in reversed(story[:-1]):
                if not card.get("is_villain"):
                    if not card.get("is_facedown"):
                        available_actions.extend(card.get("actions", []))
                    break # Stop looking once we find the previous hero's card
                
            if not available_actions:
                engine.log.append(Col.wrap(f" 🏹 {hero.name} has no Storyline symbols to convert. ", Col.CYAN))
                card["repeatable"] = False 
                return False
                
            counts = {}
            for a in available_actions:
                counts[a] = counts.get(a, 0) + 1
                
            hero.marksman_cache = {
                'available': counts, 
                'converted': {k: 0 for k in counts.keys()}
            }
            
        cache = hero.marksman_cache
        
        # 2. Build list of currently eligible options
        # Must have remaining capacity to convert AND actual tokens in the pool
        options = []
        for action, max_count in cache['available'].items():
            converted_already = cache['converted'].get(action, 0)
            in_pool = engine.active_pool.get(action, 0)
            
            available = min(max_count - converted_already, in_pool)
            if available > 0:
                options.append((action, available))
                
        if not options:
            engine.log.append(Col.wrap(f" 🏹 {hero.name} has no eligible Storyline symbols left to convert.", Col.YLW))
            delattr(hero, 'marksman_cache')
            card["repeatable"] = False
            return False

        # 3. Tactical Selection Menu
        print(f"\n--- {Col.wrap(' 🏹 MASTER MARKSMAN ', Col.CYAN)}---")
        print(" Select a Storyline symbol to convert into ✸ ✸ :")
        
        for i, (act, avail) in enumerate(options, 1):
            icon_str = ICON.get(act, f"[{act.upper()}]")
            print(f" [{i}] {icon_str} (Available: {avail})")
            
        cancel_idx = len(options) + 1
        print(f" [{cancel_idx}] Cancel")
        
        # Jules's UI Adapter sync
        choice_idx = engine.ui.ask_choice(" >> ", 1, cancel_idx)
        
        if choice_idx == cancel_idx:
            print(Col.wrap("   Conversion cancelled. ", Col.DARK_GRAY))
            return False
            
        # 4. Execute the Conversion
        chosen_action, _ = options[choice_idx - 1]
        
        engine.active_pool[chosen_action] -= 1
        engine.active_pool["attack"] = engine.active_pool.get("attack", 0) + 2
        cache['converted'][chosen_action] += 1
        
        icon_str = ICON.get(chosen_action, f"[{chosen_action.upper()}]")
        engine.log.append(Col.wrap(f" 🏹 {hero.name} converted 1 {icon_str} into ✸ ✸! ", Col.CYAN))
        
        # 5. Check for Exhaustion
        total_remaining = sum(
            min(count - cache['converted'].get(act, 0), engine.active_pool.get(act, 0))
            for act, count in cache['available'].items()
        )
        
        # If tokens remain, keep the menu open. If empty, shut it down.
        if total_remaining > 0:
            card["repeatable"] = True
        else:
            delattr(hero, 'marksman_cache')
            card["repeatable"] = False 
            
        return True

    @staticmethod
    def _longshot(engine, hero):
        print(f"\n--- {Col.wrap('🏹 LONGSHOT', Col.RED)} ---")
        if engine.ui.ask_raw(" [1] Execute: 2 DMG in Opposite Location\n [0] Cancel\n >> ", {'0', '1'}) != '1': return False
        
        target_loc_idx = (hero.location_index + 3) % 6
        engine.log.append(Col.wrap(f" 🏹 {hero.name} fires a Longshot at {engine.locations[target_loc_idx].name}!", Col.CYAN))
        
        from src.systems.damage_system import DamageSystem
        return DamageSystem.apply_targeted_damage(engine, hero, target_loc_idx, 2, "Longshot")

    @staticmethod
    def _martial_artist(engine, hero):
        print(f"\n--- {Col.wrap('🥋 MARTIAL ARTIST', Col.CYAN)} ---")
        if engine.ui.ask_raw(" [1] Execute: Redirect damage this round\n [0] Cancel\n >> ", {'0', '1'}) != '1': return False

        hero.is_invincible = True
        hero.invincible_deflect_msg = f" 🥋 {hero.name} redirects the attack into an enemy!"
        hero.invincible_wear_off_msg = f" 🥋 {hero.name} drops his guard."
        
        from src.systems.damage_system import DamageSystem
        hero.on_deflect = lambda eng, amt: DamageSystem.apply_targeted_damage(eng, hero, hero.location_index, amt, "Martial Artist Counter")
        engine.log.append(Col.wrap(f" 🥋 {hero.name} prepares to redirect incoming damage!", Col.CYAN))
        return True
