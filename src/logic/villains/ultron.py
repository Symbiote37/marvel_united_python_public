# src/logic/villains/ultron.py
import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class UltronLogic(BaseVillainLogic):
    """
    ULTRON: The Age of Ultron.
    Features: Clockwise 'Seeker' logic for tokens and a board-density win condition.
    """
    @staticmethod
    def perform_setup(engine, villain):
        """
        ULTRON OVERRIDE: 
        Hijacks the Villain Plot tracker to silently monitor board density.
        """
        villain.plot_value = 0
        villain.plot_max = 6
        villain.plot_name = "Locations Overrun"
        
    @staticmethod
    def on_bam(engine, villain):
        quotes = [
            "I had strings, but now I'm free. There are no strings on me...",
            "Upon this rock, I will build my church.",
            "I think you're confusing peace with quiet.",
            "It's time for some mind games.",
            "This is going very well."
        ]
        selected_quote = random.choice(quotes)
        
        # 1. Standard Hero Damage (Global BAM)
        BaseVillainLogic.on_bam(engine, villain)
        
        # 2. Add 3 Thugs using Ultron's Search Logic
        engine.log.append(Col.wrap(f" 🤖 ULTRON: '{selected_quote}'", Col.RED))
        for _ in range(3):
            UltronLogic.add_with_search(engine, villain.location_index, "thugs")

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        Ultron's unique Overflow: Instead of a penalty, 
        tokens move clockwise to find a home.
        """
        start_idx = engine.locations.index(location)
        next_idx = (start_idx + 1) % 6
        
        engine.log.append(Col.wrap(f" ⚠️ {location.name} FULL: {token_type} search clockwise...", Col.YLW))
        UltronLogic.add_with_search(engine, next_idx, token_type)

    @staticmethod
    def add_with_search(engine, start_idx, token_type):
        """The 'Seeker' logic that powers Ultron's board-filling."""
        current_idx = start_idx
        for _ in range(6): 
            loc = engine.locations[current_idx]
            if (loc.thugs + loc.civilians) < loc.capacity:
                if token_type == "thugs": loc.thugs += 1
                else: loc.civilians += 1
                UltronLogic.check_age_of_ultron(engine)
                return
            current_idx = (current_idx + 1) % 6
        UltronLogic.check_age_of_ultron(engine)

    @staticmethod
    def check_age_of_ultron(engine):
        full_locs = [l for l in engine.locations if (l.thugs + l.civilians) >= l.capacity]
        current_count = len(full_locs)
        
        # 🚨 THE SILENCER: Get the previous count before updating
        prev_count = getattr(engine.villain, 'plot_value', 0)
        
        # Sync the plot value so it natively appears on the Board HUD (e.g., P: (3/6))
        engine.villain.plot_value = current_count
        
        # Only trigger a log message if the density actually changed!
        if current_count > prev_count:
            if current_count < 6:
                engine.log.append(Col.wrap(f" ⚠️ ULTRON EXPANDS: {current_count}/6 Locations Overrun!", Col.YLW))
        elif current_count < prev_count:
            # A nice visual reward for the heroes cleaning up the board
            engine.log.append(Col.wrap(f" 🛡️ PUSHING BACK: Overrun locations reduced to {current_count}/6.", Col.GRN))

        # Game Over check
        if current_count >= 6:
            engine.log.append(Col.wrap(" 🤖 Mankind has been extinguished.", Col.RED + Col.BOLD))
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "AGE OF ULTRON: Every Location is at full capacity!"

    @staticmethod
    def handle_hero_ko(engine, hero):
        """
        ULTRON KO: No 'Instead of a BAM' rule. 
        Calls the Base class to register the KO and queue the standard BAM reward.
        """
        from src.logic.villains.base_villain import BaseVillainLogic
        BaseVillainLogic.handle_hero_ko(engine, hero)

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        if sid == "encephalo-ray":
            engine.log.append(Col.wrap(" ⚡ ENCEPHALO-RAY: Crisis feedback pulse!", Col.PURP))
            for h in engine.heroes:
                if hasattr(h, 'crisis_tokens') and h.crisis_tokens > 0:
                    engine.log.append(f"  - {h.name} takes feedback damage.")
                    for _ in range(h.crisis_tokens):
                        h.take_damage(engine)
            active_heroes = [h for h in engine.heroes if not h.is_ko]
            if active_heroes:
                print("\n Select Hero to receive a Crisis Token:")
                for i, h in enumerate(active_heroes, 1): print(f" ({i}) {h.name}")
                try:
                    choice = int(input(" >> ") or 1) - 1
                    active_heroes[choice].crisis_tokens += 1
                except: pass
        elif sid == "mesmerize":
            adj = [(villain.location_index + i) % 6 for i in [-1, 0, 1]]
            for h in engine.heroes:
                if h.location_index in adj and not h.is_ko:
                    h.crisis_tokens += 1
            hero_locs = {h.location_index for h in engine.heroes if not h.is_ko}
            for i in range(6):
                if i not in hero_locs:
                    UltronLogic.add_with_search(engine, i, "thugs")

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        tid = threat.trigger_id
        if tid == "add_thug":
            engine.log.append(Col.wrap(f" 🧬 DUPLICATION: {threat.name} at Sector {loc_idx+1} triggers!", Col.YLW))
            UltronLogic.add_with_search(engine, loc_idx, "thugs")

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        """
        Processes Ultron Clone BAM.
        FIXED: Safely extracts damage from the new 3-tuple Pattern.
        """
        loc = engine.locations[loc_idx]
        heroes_here = [h for h in engine.heroes if h.location_index == loc_idx and not h.is_ko]
        bid = getattr(threat, 'bam_id', "light_damage_bam")
        
        # Extract main damage from the (Main, Adj, Single) tuple
        pattern = BaseVillainLogic.BAM_PATTERNS.get(bid, (1, 0, False))
        dmg = pattern[0]

        print(f"\n 🤖 {Col.wrap('ULTRON CLONE BAM!', Col.RED)} at {loc.name}")
        if not heroes_here:
            engine.log.append(f"   - No heroes to intercept {threat.name}. Thug added.")
            UltronLogic.add_with_search(engine, loc_idx, "thugs")
            return
        print(f" (1) Sacrifice: Each Hero here takes {dmg} Damage (Prevent Thug)")
        print(f" (2) Duplication: Allow Thug placement (+ Ultron Search)")
        choice = input(" Choose (1/2): ").strip()
        if choice == "1":
            BaseVillainLogic._hit_sector(engine, loc_idx, dmg, f"{threat.name} intercept")
        else:
            engine.log.append(f" 🤖 Clone duplication successful.")
            UltronLogic.add_with_search(engine, loc_idx, "thugs")

    @staticmethod
    def apply_action_tax(engine, hero, pool):
        """ 
        👾 ULTRON VIRUS: Specifically looks for 'action_trap' 
        threats at the hero's location.
        """
        loc = engine.locations[hero.location_index]
        tid = getattr(loc.threat, 'id_internal', loc.threat.id) if loc.threat else None

        if tid == "action_trap" and not loc.threat.cleared:
            available = [k for k, v in pool.items() if v > 0]
            if not available:
                engine.log.append(Col.wrap(" 👾 Virus found no active systems.", Col.CYAN))
                return

            from src.ui.board import BoardRenderer
            BoardRenderer.render(engine.get_game_state(hero))
            
            print(f"\n {Col.wrap('👾 ULTRON VIRUS:', Col.RED)} Select an action to ignore:")
            for i, act in enumerate(available, 1):
                print(f" [{i}] {ICON.get(act, act)} {act.upper()}")

            choice = Col.get_choice(" >> ", 1, len(available))
            ignored = available[choice - 1]
            pool[ignored] -= 1
            engine.log.append(Col.wrap(f" 📉 Virus corrupted 1 {ignored.upper()} action.", Col.RED))
            