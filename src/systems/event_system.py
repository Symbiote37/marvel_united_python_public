# [Target: src/systems/event_system.py]
from src.utils.helpers import Col

class EventSystem:
    @staticmethod
    def broadcast_bam(engine, full_board=True):
        """Signals a BAM! event across the game state."""
        # 🚨 Ensure this prints before ANYTHING else
        header = Col.wrap("\n*** BAM! ACTIVATED ***", Col.RED + Col.BOLD)
        if header not in engine.log: # Prevent duplicate headers in the same logic block
             engine.log.append(header)
        
        if engine.villain:
            engine.villain.on_bam(engine)
            
        # 2. Threats react clockwise (only on full board signals)
        if full_board:
            for i, loc in enumerate(engine.locations):
                if loc.threat and not loc.threat.cleared:
                    # We pass the engine so the threat can see the board/heroes
                    loc.threat.on_bam(engine, i)

    @staticmethod
    def broadcast_overflow(engine, location, token_type):
        """Signals that a specific location has exceeded capacity."""
        # Use the name (Sector 1) if it exists, otherwise calculate from index
        loc_display = location.name if location.name else f"Sector {engine.locations.index(location) + 1}"
        
        engine.log.append(Col.wrap(f" OVERFLOW: {loc_display}", Col.RED))
        
        # Pass to the villain to handle the mechanical consequence
        engine.villain.on_overflow(engine, location, token_type)
        
    @staticmethod
    def trigger_defeat(engine, reason):
        """Narrates the specific loss and flips the engine's game_over switch."""
        
        # 🚨 THE DEADBOLT 🚨
        # If the game is already over, ignore all subsequent calls to prevent log spam!
        if getattr(engine, 'game_over', False):
            return

        engine.game_over = True
        engine.victory_status = "VILLAIN_WINS"
        
        # 🚨 THE OVERRIDE 🚨
        # Save the custom reason so the core engine doesn't replace it with a generic message at the end.
        engine.loss_reason = reason
        
        # Build a high-visibility alert for the log
        alert = [
            "=====================================================",
            f" 💀 MISSION FAILED: {reason.upper()}",
            "====================================================="
        ]
        for line in alert:
            engine.log.append(Col.wrap(line, Col.RED + Col.BOLD))
