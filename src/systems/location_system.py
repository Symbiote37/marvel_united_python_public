# src/systems/location_system.py
from src.utils.helpers import Col, wait_for_user
from src.logic.locations import LocationLogic

class LocationSystem:
    @staticmethod
    def resolve_end_of_turn(engine, hero):
        loc_idx = hero.location_index
        loc = engine.locations[loc_idx]
        
        if engine.mode_handler.is_eot_blocked(loc_idx):
            return

        # Trigger logic if threat is cleared (Standard Boon)
        # Note: You can add bypass_logic here if you want Vormir to work while uncleared
        if loc.threat_cleared and loc.end_effect:
            from src.logic.locations import LocationLogic
            LocationLogic.resolve(engine, hero, loc.end_effect)
            
            # 🚨 THE SIGNAL BOOSTER: Pulse the event queue!
            # This is where the Villain sees the 'ko_bam' and reacts.
            from src.systems.villain_system import VillainSystem
            VillainSystem.process_event_queue(engine)
            
            from src.ui.board import BoardRenderer
            BoardRenderer.render(engine.get_game_state(hero))
