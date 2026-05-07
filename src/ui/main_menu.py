import sys
import time
from src.utils.helpers import Col, wait_for_user
# 🚨 FIXED: Updated the path to reflect the move to core/
from src.core.campaign_manager import CampaignManager 
from src.ui.campaign_menu import CampaignMenu
from src.ui.controllers import HybridController

class MainMenu:
    @staticmethod
    def run():
        """The primary application router."""
        while True:
            sys.stdout.write("\033c")
            sys.stdout.flush()

            print(f"\n{Col.wrap('='*50, Col.CYAN)}")
            print(Col.wrap(" 🛡️ MARVEL UNITED: TERMINAL PROTOCOL ", Col.CYAN + Col.BOLD))
            print(f"{Col.wrap('='*50, Col.CYAN)}")
            
            print("\n [1] 🌍 Campaign Mode (Ultimate S1)")
            print("\n [2] 💥 Free Play (Quick Match) ")
            print("\n [0] Exit System ")

            choice = input("\n Initialization Command >> ").strip()

            if choice == '1':
                # 🌍 LAUNCH CAMPAIGN
                cm = CampaignManager()
                
                roster = cm.state.get("unlocked_heroes", [])
                history = cm.state.get("historical_roster", [])
                
                # 🚨 THE FIX: Catch the zombie save BEFORE auto-starting a new campaign
                # If they have a history but no viable roster, force them into the Hub's Death Screen
                if len(history) > 0 and len(roster) < 2:
                    hub = CampaignMenu(cm)
                    hub.open_hub() 
                    continue # Kick back to Main Menu after the wipe completes

                # 🔌 ROSTER CHECK: Truly fresh timeline
                if not roster and not history:
                    # Starting squad for a fresh timeline
                    cm.start_new_campaign(["captain_america", "winter_soldier", "spider-man", "miles_morales"])
                
                hub = CampaignMenu(cm)
                hub.run() 
                
            elif choice == '2':
                MainMenu.launch_free_play()
            elif choice == '0':
                print(Col.wrap("\n Powering down...", Col.DARK_GRAY))
                break
            elif choice == '9':
                MainMenu.open_master_debug()

    @staticmethod
    def open_master_debug():
        """Hidden menu to inject campaign resources for testing."""
        import os
        if os.environ.get("DEBUG_MODE") != "1":
            return
            
        cm = CampaignManager()
        while True:
            sys.stdout.write("\033c")
            sys.stdout.flush()
            print(Col.wrap("\n--- 🛠️ MASTER DEBUG PROTOCOL ---", Col.PURP + Col.BOLD))
            
            state = cm.state
            print(f"\n [1] Add +5 Blue Bolts (Current: {state.get('blue_bolts', 0)})")
            print(f" [2] Add +5 Crosses    (Current: {state.get('crosses', 0)})")
            print(f" [3] Add +5 Shields    (Current: {state.get('shields', 0)})")
            print(f" [4] Add +10 Keys      (Current: {state.get('keys', 0)})")
            print(f" [5] Wipe State (Hard Reset)")
            print("\n [0] Return to Main Menu")

            cmd = input("\n Override >> ").strip()
            
            if cmd == '0': break
            elif cmd == '1': state["blue_bolts"] = state.get("blue_bolts", 0) + 5
            elif cmd == '2': state["crosses"] = state.get("crosses", 0) + 5
            elif cmd == '3': state["shields"] = state.get("shields", 0) + 5
            elif cmd == '4': state["keys"] = state.get("keys", 0) + 10
            elif cmd == '5':
                if input(Col.wrap(" Confirm Wipe? (y/n): ", Col.RED)).lower() == 'y':
                    # Explicitly reset to defaults
                    cm.state = {
                        "unlocked_heroes": [],
                        "historical_roster": [],
                        "eliminated_heroes": [],
                        "completed_nodes": [],
                        "keys": 0,
                        "trophies": 0,
                        "blue_bolts": 0,
                        "shields": 0,
                        "crosses": 0,
                        "last_lost_heroes": []
                    }
                    cm.save_state()
            
            cm.save_state()
            print(Col.wrap(" State Saved.", Col.GRN))
            time.sleep(0.5)

    @staticmethod
    def _select_location_set():
        """Prompts the user to select an expansion set for locations."""
        print(f"\n--- {Col.wrap('SELECT LOCATION SET', Col.CYAN + Col.BOLD)} ---")
        
        # 🚨 THE FIX: Thanos Battle removed, but Infinity Gauntlet locations restored
        sets = [
            {"label": "Core Box", "file": "data/locations/core_locations.json"},
            {"label": "Enter the Spider-Verse", "file": "data/locations/spider_verse_locations.json"},
            {"label": "Tales of Asgard", "file": "data/locations/asgard_locations.json"},
            {"label": "Rise of the Black Panther", "file": "data/locations/black_panther_locations.json"},
            {"label": "Guardians of the Galaxy Remix", "file": "data/locations/gotg_remix_locations.json"},
            {"label": "Infinity Gauntlet", "file": "data/locations/infinity_gauntlet_locations.json"}
        ]
        
        for i, s in enumerate(sets, 1):
            print(f" [{i}] {s['label']}")
            
        choice = Col.get_choice(" >> ", 1, len(sets))
        return sets[choice - 1]['file']

    @staticmethod
    def launch_free_play():
        """The Training Room: Quick Match using ALL available content for testing."""
        import os
        from src.core.engine import GameEngine
        
        # 🔓 THE MASTER OVERRIDE: Scan the directories directly!
        try:
            heroes = [f.replace('.json', '') for f in os.listdir("data/heroes") if f.endswith('.json')]
            all_villains = [f.replace('.json', '') for f in os.listdir("data/villains") if f.endswith('.json')]
            
            # 🚨 THE FILTER: Remove campaign-exclusive entities from Free Play
            excluded_villains = {"thanos"} 
            villains = [v for v in all_villains if v not in excluded_villains]
            
        except FileNotFoundError:
            print(Col.wrap("\n [!] FATAL: Data directories not found.", Col.RED))
            wait_for_user()
            return
            
        heroes.sort()
        villains.sort()

        while True:
            sys.stdout.write("\033c")
            sys.stdout.flush()
            print(Col.wrap("="*50, Col.CYAN))
            print(Col.wrap(" 🦾 TRAINING ROOM: DANGER ROOM PROTOCOL [UNRESTRICTED] ", Col.CYAN + Col.BOLD))
            print(Col.wrap("="*50, Col.CYAN))
            
            if not villains:
                print(Col.wrap("\n [!] No Villains unlocked yet.", Col.RED))
                wait_for_user()
                break

            # --- SELECT VILLAIN ---
            print(f"\n{Col.wrap('--- SELECT COMBAT SIMULATION ---', Col.RED)}")
            for i, v_id in enumerate(villains, 1):
                print(f" [{i}] {v_id.replace('_', ' ').title()}")
            print(" [0] Abort Simulation")
            
            v_choice = input("\n Target Selection >> ").strip()
            if v_choice == '0': break
            
            try:
                selected_v = villains[int(v_choice) - 1]
                
                # --- SELECT SQUAD ---
                print(f"\n{Col.wrap('--- ASSEMBLE TRAINING TEAM ---', Col.CYAN)}")
                
                for i in range(0, len(heroes), 2):
                    col1 = f"[{i+1}] {heroes[i].replace('_', ' ').title()}"
                    col2 = f"[{i+2}] {heroes[i+1].replace('_', ' ').title()}" if i+1 < len(heroes) else ""
                    print(f" {col1:<25} {col2}")
                
                # 🔌 NEW: Solo Mode Toggle for Danger Room
                solo_ans = input("\n Run this simulation as a Solo Player (Xavier Protocol)? (Y/N) >> ").strip().upper()
                is_solo_run = solo_ans == 'Y'

                if is_solo_run:
                    print(Col.wrap("\n 🛡️ XAVIER PROTOCOL: You must select exactly 3 heroes.", Col.CYAN))
                    min_h, max_h = 3, 3
                else:
                    min_h, max_h = 2, 4

                s_choice = input(f"\n Select {min_h}-{max_h} heroes (e.g. 1,2,5) >> ").strip()
                indices = [int(x.strip()) - 1 for x in s_choice.split(',')]
                
                if not (min_h <= len(indices) <= max_h):
                    print(Col.wrap(f" [!] Must select between {min_h} and {max_h} heroes.", Col.RED))
                    time.sleep(1)
                    continue

                selected_squad = [heroes[i] for i in indices]
                
                # 🚨 THE FIX: Auto-route locations for the Gauntlet
                if selected_v == "infinity_gauntlet":
                    selected_location_file = "data/locations/infinity_gauntlet_locations.json"
                    print(Col.wrap(f"\n 🌌 [AUTO] Location Set: Infinity Gauntlet", Col.PURP))
                else:
                    selected_location_file = MainMenu._select_location_set()

                # --- SELECT CHALLENGE ---
                from src.systems.challenge_system import ChallengeSystem
                print(f"\n{Col.wrap('--- SELECT CHALLENGE MODIFIER ---', Col.YLW)}")
                print(" [1] Standard (No Modifiers)")
                print(f" [2] Moderate (Remove 1 Generic Single Wild)")
                print(f" [3] Hard (Remove 1 Generic Double Wild)")
                print(f" [4] Heroic (Remove BOTH Generic Wilds)")
                print(f" [5] Plan B (Increase Mission Thresholds)")
                print(f" [6] Endangered Locations (Heroes tied to locations take damage on overflow)")
                print(f" [7] Secret Identity (Journalists penalize non-move actions in their location)")
                
                c_choice = input("\n Challenge Override (Default: 1) >> ").strip()
                active_challenges = []
                if c_choice == '2': active_challenges.append(ChallengeSystem.MODERATE)
                elif c_choice == '3': active_challenges.append(ChallengeSystem.HARD)
                elif c_choice == '4': active_challenges.append(ChallengeSystem.HEROIC)
                elif c_choice == '5': active_challenges.append(ChallengeSystem.PLAN_B)
                elif c_choice == '6': active_challenges.append(ChallengeSystem.ENDANGERED)
                elif c_choice == '7': active_challenges.append(ChallengeSystem.SECRET_IDENTITY)
                
                # --- LAUNCH ENGINE ---
                print(Col.wrap(f"\n 🚀 INITIATING SIMULATION: vs {selected_v.replace('_', ' ').upper()}...", Col.YLW))
                
                # 🚨 THE CO-OP ROUTER INTERCEPT 🚨
                print(Col.wrap("\n Who should S.H.I.E.L.D. control?", Col.CYAN))
                print(" Enter numbers (1, 2, 3) corresponding to the order you selected your heroes.")
                print(" Example: If you selected Captain America, Black Widow, Miles Morales.")
                print(" Entering '2, 3' means the bot plays Black Widow and Miles.")
                print(" Press Enter to play fully manual.")
                
                bot_input = input(" >> ").strip()
                bot_seats = []
                if bot_input:
                    try:
                        # Convert human-readable "1, 2" into code-readable index [0, 1]
                        bot_seats = [int(x.strip()) - 1 for x in bot_input.split(',')]
                    except ValueError:
                        print(Col.wrap(" [!] Invalid input, defaulting to Manual play.", Col.RED))
                
                # 🚨 Pass the selected location file to the engine
                game = GameEngine(location_file=selected_location_file)
                
                # Assign the Hybrid Controller
                game.ui = HybridController(game, bot_indices=bot_seats)
                
                # 🚨 Pre-load the selected heroes and villains into the engine manually 
                game.selected_heroes = selected_squad
                game.selected_villain = selected_v
                game.is_solo_mode = is_solo_run # 🔌 NEW: Pass the Solo flag explicitly!
                game.active_challenges = active_challenges
                # Run the loop
                game.run_game_loop()
                
                print(Col.wrap("\n --- SIMULATION TERMINATED ---", Col.CYAN))
                wait_for_user()
                
            except (ValueError, IndexError):
                print(Col.wrap(" [!] Invalid Command.", Col.RED))
                time.sleep(1)
