# src/logic/locations.py
from src.utils.helpers import Col

# Import your modular location sets
from src.logic.location_sets.core_box import CoreLocationLogic
from src.logic.location_sets.spider_verse import SpiderVerseLocationLogic
from src.logic.location_sets.asgard import AsgardLocationLogic
from src.logic.location_sets.black_panther import BlackPantherLocationLogic
from src.logic.location_sets.gotg_remix import GotGLocationLogic
from src.logic.location_sets.infinity_gauntlet import InfinityGauntletLocationLogic

class LocationLogic:
    # Map the logic keys from your JSONs to their specific classes
    LOCATION_MAP = {
        # Core Box
        "remove_crisis_effect": CoreLocationLogic,
        "swap_with_storyline": CoreLocationLogic,
        "token_swap_loc": CoreLocationLogic,
        "heal_3": CoreLocationLogic,
        "rescue_civilian": CoreLocationLogic,
        "pick_next_card": CoreLocationLogic,
        "move_anywhere": CoreLocationLogic,
        "discard_thug": CoreLocationLogic,
        
        # Spider-Verse
        "gain_move_token": SpiderVerseLocationLogic,
        "gain_heroic_token": SpiderVerseLocationLogic,
        "gain_attack_token": SpiderVerseLocationLogic,
        "heal_1": SpiderVerseLocationLogic,
        "reveal_plan": SpiderVerseLocationLogic,
        "rescue_1_c": SpiderVerseLocationLogic,

        # Tales of Asgard
        "move_all_heroes": AsgardLocationLogic,
        "swap_out_hand": AsgardLocationLogic,
        "add_civilian_thug": AsgardLocationLogic,
        "throne_room_move": AsgardLocationLogic,
        "bifrost_bridge_move": AsgardLocationLogic,

        # Black Panther
        "gain_wild_token": BlackPantherLocationLogic,
        "attack_at_loc": BlackPantherLocationLogic,

        # GotG Remix
        "gain_2_tokens": GotGLocationLogic,
        "kyla_threat_token": GotGLocationLogic,

        # Infinity Gauntlet & Thanos
        "token_for_card": InfinityGauntletLocationLogic,
        "action_boost": InfinityGauntletLocationLogic,
        "ko_for_threat": InfinityGauntletLocationLogic,
        "nidavellir_forge": InfinityGauntletLocationLogic,
        "token_from_heroes": InfinityGauntletLocationLogic,
        "discard_for_tokens": InfinityGauntletLocationLogic,
        "move_thanos": InfinityGauntletLocationLogic,
        "swap_the_storyline": InfinityGauntletLocationLogic
    }

    @staticmethod
    def resolve(engine, hero, effect):
        """Entry point for all location end-of-turn benefits."""
        if not effect: return
        
        # 1. KO Check
        if getattr(hero, 'is_ko', False): 
            return

        # 2. THE STASIS GATE
        loc = engine.locations[hero.location_index]
        if getattr(loc, 'crisis_tokens', 0) > 0:
            villain_id = getattr(engine.villain, 'internal_id', '')
            
            if villain_id == "kang":
                engine.log.append(Col.wrap(f" [!] {loc.name} is in Temporal Stasis! Effect disabled.", Col.MAGENTA))
                return 
            elif villain_id == "electro":
                engine.log.append(Col.wrap(f" [!] {loc.name} is Blacked Out! Effect disabled.", Col.DARK_GRAY))
                return

        # 3. Dynamic Logic Execution via Map
        key = effect.get("logic_key")
        logic_class = LocationLogic.LOCATION_MAP.get(key)
        
        if logic_class and hasattr(logic_class, key):
            method = getattr(logic_class, key)
            method(engine, hero, effect)
        else:
            print(f"{Col.wrap('!', Col.RED)} No logic implemented for key: {key}")
