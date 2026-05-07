import os
import json
import sys
from collections import Counter
from src.utils.helpers import Col, wait_for_user, ICON
from src.core.engine import GameEngine

class CampaignMenu:
    def __init__(self, campaign_manager, campaign_map_file="data/ultimate_campaign_map.json"):
        self.manager = campaign_manager
        with open(campaign_map_file, 'r') as f:
            self.campaign_data = json.load(f)

    def run(self):
        """The Executive Loop: Manages the Hub -> Battle -> Resolution flow."""
        state = self.manager.state
        
        # 🚨 THE CAMPAIGN LOCK-IN: Ask once and save to state
        if "campaign_mode" not in state:
            print(Col.wrap("\n >>> INITIALIZING CAMPAIGN PROTOCOLS <<< ", Col.CYAN + Col.BOLD))
            is_solo = input(" Use S.H.I.E.L.D. Solo Protocol for this campaign? (y/n) >> ").strip().lower() == 'y'
            state["campaign_mode"] = "solo" if is_solo else "normal"
            
            if is_solo:
                diff_options = ["Easy (2 KOs)", "Medium (1 KO)", "Hard (KO = Game Over)"]
                print("\n 🛡️ S.H.I.E.L.D. DIFFICULTY: ")
                for i, opt in enumerate(diff_options, 1):
                    print(f" [{i}] {opt}")
                
                while True:
                    try:
                        choice = int(input(" Select >> ").strip())
                        if 1 <= choice <= 3:
                            state["solo_difficulty"] = choice - 1
                            break
                    except ValueError:
                        pass
                    print(Col.wrap(" [!] Invalid Selection. ", Col.RED))
            
            self.manager.save_state()

        while True:
            mission_node = self.open_hub()
            
            if mission_node is None:
                break
                
            node_data = self.campaign_data["nodes"][mission_node]
            villain_id = node_data["villain"]
            
            # 🚨 NEW: Display S.H.I.E.L.D. Intel before squad selection
            self._display_intel_report(villain_id)
            
            # 1. Assemble the Strike Team
            deployed_squad = self._select_campaign_squad()
            if not deployed_squad: 
                continue 
            
            print(Col.wrap(f"\n >>> DEPLOYING SQUAD TO: {node_data['name'].upper()} <<< ", Col.PURP + Col.BOLD))
            
            # 🚨 THE _02 CHALLENGE SEQUENCE
            active_challenges = []
            if mission_node.endswith('_02'):
                from src.systems.challenge_system import ChallengeSystem
                
                base_diff = self.manager.state.get("campaign_difficulty", None)
                next_diff = ChallengeSystem.get_next_difficulty(base_diff)
                
                print(f"\n{Col.wrap('--- ESCALATION DETECTED ---', Col.YLW)}")
                print(" This is a Boss Node. A random challenge will be applied automatically.")
                print(Col.wrap(" Optional: Would you like to lock in an ADDITIONAL challenge?", Col.CYAN))
                print(" [1] No additional challenge.")
                
                # Dynamically build the options map
                opt_idx = 2
                options_map = {}
                
                if next_diff:
                    print(f" [{opt_idx}] Difficulty Override: {next_diff.replace('_', ' ').title()}")
                    options_map[str(opt_idx)] = next_diff
                    opt_idx += 1
                
                print(f" [{opt_idx}] Plan B (Increase Mission Thresholds)")
                options_map[str(opt_idx)] = ChallengeSystem.PLAN_B
                opt_idx += 1

                print(f" [{opt_idx}] Endangered Locations (Heroes tied to locations take damage on overflow)")
                options_map[str(opt_idx)] = ChallengeSystem.ENDANGERED
                opt_idx += 1

                print(f" [{opt_idx}] Secret Identity (Journalists penalize non-move actions)")
                options_map[str(opt_idx)] = ChallengeSystem.SECRET_IDENTITY
                opt_idx += 1
                
                ans = input("\n Tactical Override >> ").strip()
                if ans in options_map:
                    selected_chal = options_map[ans]
                    active_challenges.append(selected_chal)
                    print(Col.wrap(f" > ⚠️ {selected_chal.replace('_', ' ').upper()} EXPLICITLY LOCKED IN.", Col.PURP))
                
                rolled_challenge = ChallengeSystem.roll_random_challenge(base_diff, active_challenges)
                
                if rolled_challenge:
                    active_challenges.append(rolled_challenge)
                    print(Col.wrap(f"\n ⚠️ WARNING: Unexpected complications detected.", Col.RED + Col.BOLD))
                    print(Col.wrap(f" > RANDOMLY APPLIED: {rolled_challenge.replace('_', ' ').upper()}", Col.RED))
                
                import time
                time.sleep(.5)

            # 2. Launch Game Engine
            game = GameEngine()
            game.campaign_manager = self.manager # Hand off save data
            
            # 🚨 THE FIX: Read mode directly from state, no unpacking needed
            is_solo = self.manager.state.get("campaign_mode") == "solo"
            
            # 🗺️ THE INJECTION: Extract the location set from the campaign node
            preferred_loc = node_data.get("location_set")
            
            # 🎲 THE RANDOMIZER: Pick a random set if one isn't explicitly requested
            if not preferred_loc:
                import random
                try:
                    valid_sets = [
                        f for f in os.listdir("data/locations") 
                        if f.endswith('.json') and f != "thanos_battle_locations.json"
                    ]
                    if valid_sets:
                        preferred_loc = random.choice(valid_sets)
                except FileNotFoundError:
                    pass # Engine will handle missing directories gracefully
            
            game.setup_campaign_mission(
                villain_id, 
                deployed_squad, 
                is_solo=is_solo,
                active_challenges=active_challenges,
                location_set=preferred_loc
            ) 
            game.run_game_loop()

            # 3. Post-Battle Resolution
            self._resolve_mission_results(game, mission_node, node_data, deployed_squad)

            wait_for_user()
            
    def open_hub(self):
        """Interactive Command Hub UI."""
        while True:
            sys.stdout.write("\033c")
            sys.stdout.flush()
            
            state = self.manager.state
            
            # 🚨 CAMPAIGN END STATE CHECKS
            if "infinity_gauntlet_boss" in state.get("completed_nodes", []):
                print(Col.wrap("\n 🎉 THE INFINITY GAUNTLET IS SECURED. THE UNIVERSE IS SAVED! 🎉", Col.CYAN + Col.BOLD))
                print(f" Final Score: {state.get('trophies', 0)} Trophies.")
                return None
                
            # 🚨 THE FIX: Cinematic Death Screen & Auto-Wipe
            if len(state.get("unlocked_heroes", [])) < 2:
                print(Col.wrap("\n=======================================", Col.RED))
                print(Col.wrap("   CRITICAL MISSION FAILURE", Col.RED + Col.BOLD))
                print(Col.wrap("=======================================", Col.RED))
                print(f" Trophies Collected: {state.get('trophies', 0)}")
                print(f" Nodes Cleared: {len(state.get('completed_nodes', []))}")
                print(" Earth's mightiest heroes have fallen...\n")
                
                input(Col.wrap(" Press Enter to accept your fate... ", Col.DARK_GRAY))
                self.manager.wipe_campaign()
                return None
                
            print(f"\n{Col.wrap('='*50, Col.CYAN)}")
            print(Col.wrap(f" 🌐 {self.campaign_data.get('campaign_name', 'CAMPAIGN').upper()} - COMMAND HUB ", Col.CYAN + Col.BOLD))
            print(f"{Col.wrap('='*50, Col.CYAN)}")
            
            print(f" 🗝️ Keys: {state.get('keys', 0)}  |  🏆 Trophies: {state.get('trophies', 0)}")
            print(f" ✨ Blue Bolts: {state.get('blue_bolts', 0)} | ✝️ Crosses: {state.get('crosses', 0)} ")
            print(f" 🦸 Active Roster: {len(state.get('unlocked_heroes', []))}")
            print(f"{Col.wrap('-'*50, Col.DARK_GRAY)}")
            
            print(" [1] View Tactical Map & Launch Mission")
            print(" [2] Enter the Hero Vault")
            print(" [3] View Unlocked Roster")
            print(Col.wrap(" [8] Reset Campaign (ERASE SAVE)", Col.RED))
            print(" [0] Save & Exit to Main Menu")
            
            choice = input("\n Hub Command >> ").strip().upper()
            
            if choice == '1':
                selected = self._view_map()
                if selected: return selected 
            elif choice == '2':
                self._hero_vault()
            elif choice == '3':
                self._view_roster()
            elif choice == '8':
                if self._reset_campaign(): return None
            elif choice == '0':
                self.manager.save_state()
                return None

    def _view_map(self):
        """Displays all nodes and allows mission selection."""
        print(f"\n--- {Col.wrap('TACTICAL MAP', Col.CYAN)} ---")
        
        available_nodes = {}
        completed_display = []
        available_display = []
        
        counter = 1
        
        for node_id, node_data in self.campaign_data["nodes"].items():
            is_completed = node_id in self.manager.state["completed_nodes"]
            is_unlocked = self.manager.is_node_unlocked(node_data.get("prerequisites", []))
            
            # Only process if it's actually visible on the map
            if is_completed or is_unlocked:
                
                # 🧹 Scrub the underscores and capitalize
                v_name = node_data['villain'].replace('_', ' ').title()
                
                # ⚡ Dynamic Challenge Detection
                bolt = Col.wrap(" ⚡", Col.RED) if node_id.endswith("_02") or "boss" in node_id else ""
                
                if is_completed:
                    status = Col.wrap("[✅ CLEARED]", Col.GRN)
                    completed_display.append(f"   {status} {node_data['name']} (Defeated {v_name}{bolt})")
                elif is_unlocked:
                    status = Col.wrap(f"[{counter}] AVAILABLE", Col.YLW + Col.BOLD)
                    
                    # 🎁 Parse and build the reward L-bracket (ONLY for available nodes)
                    rewards = node_data.get("rewards", {})
                    reward_icons = {
                        "keys": "🗝️", "trophies": "🏆", "blue_bolts": "✨",
                        "shields": "🛡️", "crosses": "✝️ "
                    }
                    
                    reward_parts = []
                    for r_key, icon in reward_icons.items():
                        if r_key in rewards:
                            reward_parts.append(icon * rewards[r_key])
                            
                    if "unlock_heroes" in rewards:
                        for h in rewards["unlock_heroes"]:
                            reward_parts.append(f"[{h.replace('_', ' ').title()}]")
                    
                    # Build the two-line display string
                    node_text = f" {status} : {node_data['name']} vs {v_name}{bolt}"
                    if reward_parts:
                        reward_str = " ".join(reward_parts)
                        node_text += f"\n{Col.wrap(f'      └─ {reward_str} ', Col.CYAN)}                "
                        
                    available_display.append(node_text)
                    available_nodes[str(counter)] = node_id
                    counter += 1

        # 🖨️ RENDER PHASE: Print completed first, then available
        for text in completed_display:
            print(text)
            
        if completed_display and available_display:
            print(Col.wrap("   ---", Col.DARK_GRAY)) # Visual separator
            
        for text in available_display:
            print(text)
                
        print("\n [0] Back to Hub")
        choice = input(" Select Mission to Launch >> ").strip()
        return available_nodes.get(choice)

    def _hero_vault(self):
        """The shop interface for spending keys on new heroes."""
        while True:
            print(f"\n--- {Col.wrap('THE HERO VAULT', Col.PURP)} ---")
            print(f" Available Keys: {self.manager.state['keys']} 🗝️")
            
            available_heroes = self.manager.get_available_vault_heroes(self.campaign_data)
            
            if not available_heroes:
                print(Col.wrap("\n The Vault is empty.", Col.DARK_GRAY))
                wait_for_user()
                return

            hero_keys = list(available_heroes.keys())
            for i, h_id in enumerate(hero_keys, 1):
                details = available_heroes[h_id]
                cost = details.get('cost', 1)
                display = details.get('display_name', h_id.replace('_', ' ').title())
                color = Col.GRN if self.manager.state['keys'] >= cost else Col.RED
                print(f" [{i}] {Col.wrap(display, color)} - Cost: {cost} 🗝️")

            print(" [0] Leave Vault")
            # 🔌 FIXED: Using standard input check since engine isn't initialized yet
            raw_choice = input(" Buy >> ").strip()
            if not raw_choice or raw_choice == '0': break
            
            try:
                choice = int(raw_choice)
                selected_id = hero_keys[choice - 1]
                self.manager.purchase_hero(selected_id, available_heroes[selected_id])
            except (ValueError, IndexError):
                print(Col.wrap(" [!] Invalid Selection.", Col.RED))

    def _view_roster(self):
        """Displays the active Hero roster."""
        print(f"\n{Col.wrap('--- ACTIVE HERO ROSTER ---', Col.CYAN + Col.BOLD)}")
        counts = Counter(self.manager.state['unlocked_heroes'])
        if not counts:
            print(" No heroes currently in active roster.")
        else:
            for h_id in sorted(counts.keys()):
                name = h_id.replace('_', ' ').title()
                print(f" • {name}" + (f" ({counts[h_id]}x)" if h_id == "nick_fury" else ""))

        input(f"\n{Col.wrap('Press Enter to return...', Col.DARK_GRAY)}")

    def _display_intel_report(self, villain_id):
        """Fetches and renders the S.H.I.E.L.D. dossier for the target."""
        from src.logic.registry import get_villain_logic
        logic_class = get_villain_logic(villain_id)
        
        # Clear the screen for dramatic effect
        sys.stdout.write("\033c")
        sys.stdout.flush()

        if hasattr(logic_class, 'get_intel_report'):
            intel = logic_class.get_intel_report()
            v_name = villain_id.replace('_', ' ').upper()
            
            print(Col.wrap(f"{'='*53}", Col.CYAN))
            print(Col.wrap(f" 📁 S.H.I.E.L.D. TARGET INTEL: {v_name} ", Col.CYAN + Col.BOLD))
            print(Col.wrap(f"{'='*53}", Col.CYAN))
            
            if "profile" in intel:
                print(Col.wrap("\n 👤 PROFILE: ", Col.CYAN + Col.BOLD))
                print(f" {intel['profile']}")
                
            if "rules" in intel:
                print(Col.wrap("\n ⚠️ MODUS OPERANDI (Special Rules): ", Col.YLW + Col.BOLD))
                print(f" {intel['rules']}")
                
            if "bam" in intel:
                print(Col.wrap("\n 💥 SIGNATURE STRIKE (BAM!): ", Col.RED + Col.BOLD))
                print(f" {intel['bam']}")
                
            if "overflow" in intel:
                print(Col.wrap("\n 🌊 COLLATERAL (Overflow): ", Col.PURP + Col.BOLD))
                print(f" {intel['overflow']}")
                
            if "threats" in intel:
                print(Col.wrap("\n 🦹 KNOWN THREATS: ", Col.WHT + Col.BOLD))
                print(f" {intel['threats']}")
                
            print(Col.wrap(f"\n{'='*53}", Col.CYAN))
            input(Col.wrap(" Press [ENTER] to Assemble Strike Team... ", Col.DARK_GRAY))
        else:
            print(Col.wrap(f"\n ⚠️ WARNING: No S.H.I.E.L.D. intel on record for {villain_id.upper()}. ", Col.RED))
            input(Col.wrap(" Press [ENTER] to deploy blindly... ", Col.DARK_GRAY))

    def _select_campaign_squad(self):
        """Assembles the team and confirms Protocol selection."""
        roster = self.manager.state["unlocked_heroes"]
        
        # 🚨 THE FIX: Pull directly from the locked state
        is_solo = self.manager.state.get("campaign_mode") == "solo"
        
        print(f"\n--- {Col.wrap('ASSEMBLE STRIKE TEAM', Col.CYAN)} ---")
        for i, h in enumerate(roster, 1):
            print(f" [{i}] {h.replace('_', ' ').title()}")
        print(" [0] Abort")
            
        limit_msg = "exactly 3 heroes" if is_solo else "2-4 heroes"
        while True:
            try:
                choice = input(f" Select {limit_msg} (e.g., 1,2) >> ").strip()
                if choice == '0': return None
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                
                if is_solo and len(indices) != 3:
                    print(Col.wrap(" [!] S.H.I.E.L.D. Protocol requires exactly 3 heroes. ", Col.RED))
                    continue
                if not is_solo and not (2 <= len(indices) <= 4):
                    print(Col.wrap(" [!] Standard deployment requires 2-4 heroes. ", Col.RED))
                    continue
                    
                squad = [roster[i] for i in indices]
                # 🚨 THE FIX: Just return the array
                return squad
            except: 
                print(Col.wrap(" [!] Invalid entry. ", Col.RED))

    def _resolve_mission_results(self, game, node_id, node_data, squad):
        """Processes campaign state with a Manual Mulligan/Reset option."""
        victory = getattr(game, 'victory_status', '') == 'HEROES_WIN'
        
        if victory:
            print(Col.wrap("\n 🏆 MISSION SUCCESS!", Col.GRN + Col.BOLD))
            # 🚨 THE FIX: Pass the node_name directly from the campaign data
            self.manager.complete_node(node_id, node_data.get("rewards", {}), node_name=node_data.get("name"))
            
            # 🚨 AGGREGATOR: Save stats on a Victory
            if getattr(game, 'match_stats', {}):
                self.manager.aggregate_match_stats(game.match_stats)
        else:
            print(Col.wrap("\n 💀 MISSION FAILURE", Col.RED + Col.BOLD))
            
            # 🚨 THE MANUAL MULLIGAN GATE
            print(f" {Col.wrap('[M] Mulligan', Col.CYAN)} : Reset to Hub (Squad stays safe)")
            print(f" {Col.wrap('[A] Accept Fate', Col.RED)} : Squad is M.I.A. / Use Crosses")
            
            choice = input("\n Protocol >> ").strip().upper()
            
            if choice == 'M':
                print(Col.wrap("\n ✨ MULLIGAN ACTIVATED: Squad returning to Hub...", Col.CYAN))
                print(Col.wrap(" 🗑️ Timeline branch pruned. Stats purged.", Col.DARK_GRAY))
                return # Exit without removing heroes or marking node complete

            # --- ACCEPT FATE PATH ---
            # 🚨 AGGREGATOR: Save stats because this timeline is officially locked in
            if getattr(game, 'match_stats', {}):
                self.manager.aggregate_match_stats(game.match_stats)

            crosses = self.manager.state.get("crosses", 0)
            if crosses > 0:
                print(Col.wrap(f" ✝️ CROSSES AVAILABLE: {crosses}. Use one? (y/n)", Col.CYAN))
                if input(" >> ").strip().lower() == 'y':
                    self.manager.state["crosses"] -= 1
                    print(Col.wrap("\n ✨ Cross used. Squad recovered.", Col.GRN))
                    self.manager.save_state()
                    return

            # --- PERMANENT LOSS PATH ---
            clean_names = [h.replace('_', ' ').title() for h in squad]
            print(Col.wrap(f"\n 💀 SQUAD M.I.A: {', '.join(clean_names)}", Col.RED + Col.BOLD))
            for h in squad:
                if h in self.manager.state["unlocked_heroes"]:
                    self.manager.state["unlocked_heroes"].remove(h)
                
                # 🚨 SENSOR ADDED: Mark the hero as permanently fallen in the Hall of Fame
                if "hall_of_fame" in self.manager.state and h in self.manager.state["hall_of_fame"]:
                    self.manager.state["hall_of_fame"][h]["mia"] = True

    def _reset_campaign(self):
        """Self-destruct sequence to erase the save file."""
        print(Col.wrap("\n ⚠️  WARNING: ERASE ALL CAMPAIGN PROGRESS? ⚠️", Col.RED + Col.BOLD))
        confirm = input(" Type 'OBLIVIATE' to confirm >> ").strip().upper()
        if confirm == 'OBLIVIATE':
            save_path = getattr(self.manager, 'save_file', 'data/campaign_save.json')
            if os.path.exists(save_path):
                os.remove(save_path)
            print(Col.wrap("\n 💥 Timeline Erased.", Col.YLW))
            wait_for_user()
            return True 
        return False
