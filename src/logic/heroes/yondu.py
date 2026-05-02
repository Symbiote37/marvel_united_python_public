from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("yondu")
class YonduLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "yondu_turncoat":
            return YonduLogic._turncoat(engine, hero, card)
        elif sid == "yondu_yaka_arrow_flurry":
            return YonduLogic._yaka_arrow_flurry(engine, hero, card)
        elif sid == "yondu_yaka_arrow_whirlwind":
            return YonduLogic._yaka_arrow_whirlwind(engine, hero, card)
        return False

    @staticmethod
    def _turncoat(engine, hero, card):
        loc = engine.locations[hero.location_index]
        
        if loc.civilians == 0 and loc.thugs == 0:
            print(Col.wrap(" ! No figures in this location to swap.", Col.YLW))
            return False

        print(f"\n--- {Col.wrap('TURNCOAT', Col.CYAN)} ---")
        print(f" This will swap {loc.civilians} Civilians and {loc.thugs} Thugs at {loc.name}.")
        
        while True:
            choice = input(f" Use this effect? ({Col.wrap('y/n', Col.YLW)}): ").lower().strip()
            if choice == 'y':
                # Direct state manipulation
                loc.civilians, loc.thugs = loc.thugs, loc.civilians
                engine.log.append(Col.wrap(f" 🔄 TURNCOAT: Yondu swapped the figures at {loc.name}!", Col.CYAN))
                return True
            elif choice == 'n':
                return False
            print(Col.wrap(" ! Invalid input. Enter 'y' or 'n'.", Col.RED))

    @staticmethod
    def _yaka_arrow_flurry(engine, hero, card):
        from src.systems.action_system import ActionSystem
        from src.systems.token_system import TokenSystem
        
        loc_idx = hero.location_index
        # Current, Left, Right
        sectors = [loc_idx, (loc_idx - 1) % 6, (loc_idx + 1) % 6]
        valid_sectors = [i for i in sectors if not getattr(engine.locations[i], 'is_destroyed', False)]

        engine.log.append(Col.wrap(f" 🏹 YAKA ARROW FLURRY: The arrow darts across the board!", Col.MAGENTA + Col.BOLD))
        
        # 🌟 THE FLURRY LOOP: 3 Separate Strikes
        for strike in range(3):
            print(f"\n--- {Col.wrap(f'FLURRY: STRIKE {strike+1}/3', Col.YLW)} ---")
            for i, idx in enumerate(valid_sectors, 1):
                print(f" [{i}] {engine.locations[idx].name}")
            print(" [0] Stop Flurry Early")
            
            choice = Col.get_choice(" >> ", 0, len(valid_sectors))
            if choice == 0: 
                break
                
            target_idx = valid_sectors[choice - 1]
            
            # Delegate to our Universal Targeting Helper
            ActionSystem._handle_targeted_attack(engine, hero, target_idx)

        return True

    @staticmethod
    def _yaka_arrow_whirlwind(engine, hero, card):
        from src.systems.action_system import ActionSystem
        from src.systems.token_system import TokenSystem
        
        engine.log.append(Col.wrap(f" 🌪️ YAKA WHIRLWIND: The arrow tears a path clockwise!", Col.MAGENTA + Col.BOLD))
        
        curr_idx = hero.location_index
        thugs_defeated = 0
        
        # Safely loop a maximum of 6 times to prevent infinite loops on a fully populated board
        for _ in range(6):
            loc = engine.locations[curr_idx]
            
            # Stop condition: Destroyed location or 0 Thugs
            if getattr(loc, 'is_destroyed', False) or loc.thugs <= 0:
                break
                
            # Defeat exactly 1 Thug
            if TokenSystem.apply_thug_defeat(engine, loc, hero):
                thugs_defeated += 1
                
            # Move to the next clockwise location
            curr_idx = (curr_idx + 1) % 6
            
        if thugs_defeated == 0:
            engine.log.append(Col.wrap("   ...but there were no Thugs at Yondu's starting location.", Col.YLW))
        else:
            engine.log.append(f"   💥 The Yaka Arrow took down {thugs_defeated} Thug(s) before returning!")
            
        return True
        