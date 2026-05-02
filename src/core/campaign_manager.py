import json
import os
from src.utils.helpers import Col

class CampaignManager:
    def __init__(self, save_file="data/campaign_save.json"):
        self.save_file = save_file
        self.state = {
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
        self.load_state()

    def start_new_campaign(self, starting_squad):
        self.state["unlocked_heroes"] = starting_squad
        self.state["historical_roster"] = list(starting_squad) 
        self.state["eliminated_heroes"] = []                   
        self.state["completed_nodes"] = []
        for key in ["keys", "trophies", "blue_bolts", "shields", "crosses"]:
            self.state[key] = 0
        self.save_state()
        
        print(f"\n{Col.wrap('=== NEW CAMPAIGN INITIATED ===', Col.CYAN + Col.BOLD)}")
        print(f" Starting Squad: {', '.join([h.replace('_', ' ').title() for h in starting_squad])}")
        print(" The journey begins...\n")

    def complete_node(self, node_id, rewards, node_name=None):
        # 🛡️ STATE ARMOR: Ensure completed_nodes exists
        nodes = self.state.setdefault("completed_nodes", [])
        if node_id not in nodes:
            nodes.append(node_id)
            
        # 🚨 THE FIX: Use the thematic name if provided, otherwise fallback to ID
        display_name = node_name.upper() if node_name else node_id.upper()
        print(f"\n--- {Col.wrap('MISSION CLEARED: ' + display_name, Col.GRN + Col.BOLD)} ---")
        
        mapping = {
            "key": "keys", "keys": "keys",
            "trophy": "trophies", "trophies": "trophies",
            "blue_bolt": "blue_bolts", "blue_bolts": "blue_bolts",
            "shield": "shields", "shields": "shields",
            "cross": "crosses", "crosses": "crosses"
        }

        for r_key, s_key in mapping.items():
            if r_key in rewards:
                val = rewards[r_key]
                # 🛡️ STATE ARMOR: Ensure resource integer exists
                self.state[s_key] = self.state.get(s_key, 0) + val
                symbol = "🏆" if "troph" in r_key else "✨"
                print(f" {symbol} {s_key.replace('_', ' ').title()} Gained: {val} (Total: {self.state[s_key]})")
            
        if "unlock_heroes" in rewards: 
            for h_id in rewards["unlock_heroes"]:
                self.unlock_hero(h_id)
            
        self.save_state()

    def unlock_hero(self, hero_id):
        # 🛡️ STATE ARMOR: Ensure lists exist
        unlocked = self.state.setdefault("unlocked_heroes", [])
        history = self.state.setdefault("historical_roster", [])
        
        if hero_id == "nick_fury":
            unlocked.append(hero_id)
            print(Col.wrap(f"\n 📞 REINFORCEMENTS: Nick Fury is available for a mission! 📞", Col.GRN + Col.BOLD))
            self.save_state()
            
        elif hero_id not in unlocked:
            unlocked.append(hero_id)
            
            if hero_id not in history:
                history.append(hero_id)
                
            print(Col.wrap(f"\n 🎉 UNLOCKED NEW HERO: {hero_id.replace('_', ' ').title()}! 🎉", Col.GRN + Col.BOLD))
            self.save_state()

    def unlock_villain(self, villain_id):
        # 🛡️ STATE ARMOR: Ensure list exists
        unlocked_v = self.state.setdefault("unlocked_villains", [])
        if villain_id not in unlocked_v:
            unlocked_v.append(villain_id)
            print(Col.wrap(f"\n ⚠️ NEW VILLAIN UNLOCKED: {villain_id.replace('_', ' ').title()}! ⚠️", Col.RED + Col.BOLD))
            self.save_state()

    def get_available_vault_heroes(self, campaign_map):
        available = {}
        for tier_id, data in campaign_map.get("hero_vault", {}).items():
            if self.is_node_unlocked({"all_of": data.get("requirement", [])}):
                for h_id, details in data["heroes"].items():
                    history = self.state.get("historical_roster", self.state.get("unlocked_heroes", []))
                    if h_id not in history:
                        available[h_id] = details
        return available

    def purchase_hero(self, hero_id, details):
        cost = details.get("cost", 0)
        # 🛡️ STATE ARMOR: Safe get for keys
        keys = self.state.get("keys", 0)
        
        if keys >= cost:
            self.state["keys"] = keys - cost
            self.unlock_hero(hero_id)
            
            if "unlock_villains" in details:
                for v_id in details["unlock_villains"]:
                    self.unlock_villain(v_id)
                    
            print(Col.wrap(f" 🗝️ Transaction Complete: {cost} keys spent. ", Col.YLW))
            self.save_state()
            return True
        else:
            print(Col.wrap(" 🔒 Not enough keys! Go beat some more villains! ", Col.RED))
            return False

    def is_node_unlocked(self, prerequisites):
        # 🛡️ STATE ARMOR
        completed = self.state.setdefault("completed_nodes", [])
        
        if isinstance(prerequisites, list):
            return all(p in completed for p in prerequisites)
            
        if isinstance(prerequisites, dict):
            all_of = prerequisites.get("all_of", [])
            met_all = all(p in completed for p in all_of)
            
            any_of = prerequisites.get("any_of", [])
            met_any = any(p in completed for p in any_of) if any_of else True
                
            return met_all and met_any
            
        return True

    def use_mulligan(self):
        """Restores the last lost squad."""
        # 🛡️ STATE ARMOR: Use get() to prevent KeyError
        lost = self.state.get("last_lost_heroes", [])
        if lost:
            unlocked = self.state.setdefault("unlocked_heroes", [])
            unlocked.extend(lost)
            self.state["last_lost_heroes"] = []
            self.save_state()
            print(Col.wrap(f"\n ⏳ TIME STONE ACTIVATED: {', '.join(lost).replace('_', ' ').title()} have been restored to the timeline!", Col.GRN + Col.BOLD))
            return True
        return False
        
    def load_state(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    self.state.update(json.load(f))
            except json.JSONDecodeError:
                print(Col.wrap(" ! Warning: Campaign save file corrupted.", Col.RED))
                
    def save_state(self):
        os.makedirs(os.path.dirname(self.save_file), exist_ok=True)
        with open(self.save_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def is_game_over(self):
        """
        Checks if the campaign is in a 'Zombie' state.
        True if the campaign has a history (started) but the playable roster is empty.
        """
        history = self.state.get("historical_roster", [])
        unlocked = self.state.get("unlocked_heroes", [])
        
        return len(history) > 0 and len(unlocked) == 0

    def wipe_campaign(self):
        """Gracefully deletes the save file and resets the internal state."""
        import os # Just in case it isn't imported at the top of the file
        
        if os.path.exists(self.save_file):
            os.remove(self.save_file)
            
        # Reset the state dictionary back to default
        self.state = {
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
        print(Col.wrap("\n 💀 CAMPAIGN OVER: Roster decimated. The timeline has been reset.", Col.RED + Col.BOLD))

    def aggregate_match_stats(self, match_stats):
        if "hall_of_fame" not in self.state:
            self.state["hall_of_fame"] = {}
            
        for h_id, stats in match_stats.items():
            if h_id not in self.state["hall_of_fame"]:
                self.state["hall_of_fame"][h_id] = {
                    "damage": 0, "thugs": 0, "civs": 0, 
                    "threats": 0, "deployments": 0, "kos": 0, "mia": False
                }
            
            self.state["hall_of_fame"][h_id]["deployments"] += 1
            for k, v in stats.items():
                if k in self.state["hall_of_fame"][h_id]:
                    self.state["hall_of_fame"][h_id][k] += v
                
        self.save_state()
