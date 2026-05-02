import os
from src.utils.helpers import Col

class DebugSystem:
    @staticmethod
    def open_menu(engine):
        if os.environ.get("DEBUG_MODE") != "1":
            return

        prompt_text = (
            Col.wrap("\n=== 🛠️ DEBUG / CHEAT MENU ===", Col.CYAN + Col.BOLD) + "\n" +
            " [1] +5 Wild Tokens (Current Hero Stash)\n" +
            " [2] Complete 2 Missions (Thugs/Civs)\n" +
            " [3] Clear All Threats\n" +
            " [0] Return to Game\n\n DEBUG > "
        )

        choice = engine.ui.ask_raw(prompt_text, ["0", "1", "2", "3"])

        if choice == "1":
            # Access current hero using the newly promoted engine attribute
            idx = getattr(engine, 'current_hero_index', 0)
            hero = engine.heroes[idx]

            # Initialization safety check
            if not hasattr(hero, 'stashed_tokens') or hero.stashed_tokens is None:
                hero.stashed_tokens = []

            for _ in range(5):
                hero.stashed_tokens.append("❖")

            engine.log.append(Col.wrap(f" 🛠️ DEBUG: Injected 5 Wilds into {hero.name}'s stash.", Col.YLW))

        elif choice == "2":
            # Force mission completion for immediate villain vulnerability
            engine.missions['thugs'] = engine.missions.get('thugs_max', 9)
            engine.missions['civilians'] = engine.missions.get('civilians_max', 9)

            engine.log.append(Col.wrap(" 🛠️ DEBUG: Missions 'Thugs' & 'Civilians' forced to MAX.", Col.YLW))

        elif choice == "3":
            # Batch clear threats
            for loc in engine.locations:
                if loc.threat:
                    loc.threat.cleared = True
                    # Update global mission counter for threats
                    engine.missions['threats'] = engine.missions.get('threats', 0) + 1

            engine.log.append(Col.wrap(" 🛠️ DEBUG: All Threats Cleared. Board is reset.", Col.YLW))

        elif choice == "0":
            return
