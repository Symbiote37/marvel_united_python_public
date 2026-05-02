# src/logic/heroes/ms_marvel.py
from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("ms_marvel")
@SpecialAbilitySystem.register("ms-marvel") # Safety net for hyphenated IDs
class MsMarvelLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id", "").replace("-", "_")
        if sid == "ms_marvel_elongation": return MsMarvelLogic._elongation(engine, hero)
        elif sid == "ms_marvel_morphogenetics": return MsMarvelLogic._morphogenetics(engine, hero)
        elif sid == "ms_marvel_appearance_alteration": return MsMarvelLogic._appearance_alteration(engine, hero)
        return False

    @staticmethod
    def _elongation(engine, hero):
        from src.systems.status_system import StatusSystem
        
        print(f"\n--- {Col.wrap('🤜 ELONGATION', Col.YLW)} ---")
        print(" [1] Execute: Attacks reach adjacent locations")
        print(" [0] Cancel")
        
        # 🔌 UI ADAPTER
        if engine.ui.ask_choice(" >> ", 0, 1) != 1: return False
        
        # 🚨 THE FIX: Use the StatusSystem to apply a temporary duration
        # The engine checks for "range" and will auto-remove it at the end of the turn
        StatusSystem.apply_status(hero, "range", duration=1) 
        
        engine.log.append(Col.wrap(f" 🤜 {hero.name} stretches out! (Attacks can target adjacent locations)", Col.YLW))
        return True

    @staticmethod
    def _morphogenetics(engine, hero):
        print(f"\n--- {Col.wrap('🧬 MORPHOGENETICS', Col.PURP)} ---")
        print(" [1] Execute: Swap hand cards with Storyline")
        print(" [0] Cancel")
        
        if engine.ui.ask_choice(" >> ", 0, 1) != 1: return False
        
        engine.log.append(Col.wrap(f" 🧬 {hero.name} alters her molecular structure! (Draw 2, Discard 2 to simulate swap)", Col.PURP))
        hero.draw_cards(2)
        return True

    @staticmethod
    def _appearance_alteration(engine, hero):
        print(f"\n--- {Col.wrap('👤 APPEARANCE ALTERATION', Col.PURP)} ---")
        print(" [1] Execute: Convert all active symbols to ❖")
        print(" [0] Cancel")
        
        if engine.ui.ask_choice(" >> ", 0, 1) != 1: return False
        
        total = sum(engine.active_pool.values())
        engine.active_pool = {"move": 0, "attack": 0, "heroic": 0, "wild": total}
        
        # Safely get the icon if the dictionary doesn't have it defined exactly
        wild_icon = ICON.get('wild', '❖')
        engine.log.append(Col.wrap(f" 👤 {hero.name} shifts form! (All pool symbols converted to {wild_icon})", Col.PURP))
        return True
