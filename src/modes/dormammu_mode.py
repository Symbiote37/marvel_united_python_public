from src.modes.base_mode import BaseMode
from src.utils.helpers import Col

class DormammuMode(BaseMode):
    """Modular logic for the Dormammu: Eternal Defense fight."""

    def perform_setup(self):
        # 1. Execute standard positioning (Villain at 0, Heroes at 3)
        super().perform_setup()

        # 2. Dormammu's Special Condition: Trim the Master Plan deck
        # Formula: 6 + (Number of Heroes * 2)
        hero_count = len(self.engine.heroes)
        target_size = 6 + (hero_count * 2)
        
        # Slice the deck to the required difficulty size
        self.engine.villain.plan_deck = self.engine.villain.plan_deck[:target_size]
        
        self.engine.log.append(Col.wrap(
            f" 🔥 DARK DIMENSION: Master Plan deck reduced to {target_size} cards for {hero_count} heroes. ", 
            Col.PURP + Col.BOLD
        ))
        