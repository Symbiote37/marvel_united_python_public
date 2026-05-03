from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("daredevil")
class DaredevilLogic:
    
    # --- SETUP PHASE (Playing the Cards) ---
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        from src.systems.status_system import StatusSystem
        
        if sid == "daredevil_radar_sense":
            StatusSystem.apply_status(hero, "radar_sense", duration=1)
            engine.log.append(Col.wrap(" 🦯 RADAR SENSE: Daredevil is tracking the environment.", Col.RED))
            return True
        elif sid == "daredevil_man_without_fear":
            StatusSystem.apply_status(hero, "man_without_fear", duration=1)
            engine.log.append(Col.wrap(" ⚖️ MAN WITHOUT FEAR: Civilians rescued will grant Move tokens.", Col.RED))
            return True
        elif sid == "daredevil_blind_justice":
            StatusSystem.apply_status(hero, "blind_justice", duration=1)
            engine.log.append(Col.wrap(" ⚖️ BLIND JUSTICE: Thugs defeated will grant Move tokens.", Col.RED))
            return True
        return False

    # --- REACTION PHASE (Listening to the Bus) ---
    @staticmethod
    def on_location_entered(engine, hero):
        from src.systems.status_system import StatusSystem
        if StatusSystem.has_status(hero, "radar_sense"):
            print(f"\n--- {Col.wrap('🦯 RADAR SENSE', Col.RED)} ---")
            print(f" {hero.name} entered {engine.locations[hero.location_index].name}! Choose a token:")
            print(" [1] ✸ (Attack)")
            print(" [2] ★ (Heroic)")
            
            # 🔌 UI ADAPTER
            choice = engine.ui.ask_choice(" >> ", 1, 2)
            token = 'attack' if choice == 1 else 'heroic'
            
            # 🚨 THE FIX: Use the engine's built-in token stash method
            hero.add_token(token)
            engine.log.append(Col.wrap(f" 🦯 Daredevil mapped the area! (+1 {ICON.get(token, token)})", Col.RED))

    @staticmethod
    def on_civilian_rescued(engine, hero):
        from src.systems.status_system import StatusSystem
        if StatusSystem.has_status(hero, "man_without_fear"):
            # 🚨 THE FIX: Use the engine's built-in token stash method
            hero.add_token('move')
            engine.log.append(Col.wrap(f" ⚖️ MAN WITHOUT FEAR: Civilian rescued! (+1 {ICON['move']})", Col.RED))

    @staticmethod
    def on_thug_defeated(engine, hero):
        from src.systems.status_system import StatusSystem
        if StatusSystem.has_status(hero, "blind_justice"):
            # 🚨 THE FIX: Use the engine's built-in token stash method
            hero.add_token('move')
            engine.log.append(Col.wrap(f" ⚖️ BLIND JUSTICE: Thug cleared! (+1 {ICON['move']})", Col.RED))
