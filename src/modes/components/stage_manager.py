import json, random, os
from src.entities.actors import Villain, Hero
from src.entities.threats import Threat
from src.entities.locations import Location
from src.logic.registry import get_villain_logic
from src.utils.helpers import Col

class StageManager:
    def __init__(self, engine, state):
        self.engine, self.state = engine, state

    def prepare_campaign(self):
        children = ["proxima_midnight", "ebony_maw", "black_dwarf"]
        random.shuffle(children)
        self.state.roster = children + ["thanos"]

    def load_current_stage(self):
        """Standardized name. Forces a complete overwrite of the engine's villain state."""
        v_id = self.state.roster[self.state.stage_index]
        
        with open(f"data/villains/{v_id}.json", 'r') as f:
            v_data = json.load(f)
            
        # 🚨 THE PURGE: Creating a fresh Villain object clears old HP and state
        self.engine.villain = Villain(v_data, hero_count=len(self.engine.heroes))
        self.engine.villain.location_index = 0
        self.engine.villain_logic = get_villain_logic(v_id)
        
        # 🚨 THE FIX: Corrected method name to match the definition below
        self._load_threats(v_id)
        
        self.engine.log.append(Col.wrap(f" 🚩 STAGE {self.state.stage_index + 1}: {self.engine.villain.name.upper()}", Col.PURP + Col.BOLD))

        if hasattr(self.engine.villain_logic, 'perform_setup'):
            self.engine.villain_logic.perform_setup(self.engine, self.engine.villain)

    def _load_threats(self, v_id):
        path = f"data/threats/{v_id}_threats.json"
        if not os.path.exists(path): path = "data/threats/generic_v_threats.json"
        with open(path, 'r') as f: deck = json.load(f)
        random.shuffle(deck)
        for i, loc in enumerate(self.engine.locations):
            loc.threat = Threat(deck[i]) if i < len(deck) else None

    def filter_draft(self, count, exclude_ids=None):
        """
        Drafts heroes while excluding those in the Grave AND 
        any heroes already selected for the current squad.
        """
        if exclude_ids is None:
            exclude_ids = []

        # Combine the Dead and the Currently Selected
        total_blacklist = self.state.eliminated_heroes + exclude_ids

        print(f"\n {Col.wrap('--- THE GRAVE ---', Col.RED)}: {', '.join(self.state.eliminated_heroes) or 'Empty'}")

        hero_path = "data/heroes"
        all_files = sorted([f for f in os.listdir(hero_path) if f.endswith('.json')])

        available_files = []
        for f_name in all_files:
            # 🚨 OPTIMIZATION: Extract ID directly from filename (O(1) string slice)
            hero_id = f_name[:-5]
            if hero_id not in total_blacklist:
                available_files.append(f_name)

        return self.engine._load_from_folder(hero_path, Hero, count=count, file_subset=available_files)

    def reset_engine_for_stage(self):
        self.engine.game_over = False
        self.engine.turn_count = 0
        self.engine.storyline.cards = []
        self.engine.missions = {"civilians": 0, "civilians_max": 9, "thugs": 0, "thugs_max": 9, "threats": 0, "threats_max": 4}

    def handle_death(self, victory):
        """
        Manages the transition after a match.
        Heroes are only permanently eliminated during the Thanos Finale (Stage 4).
        """
        if victory:
            return

        # 🚨 THE FIX: Only Stage 4 (index 3) uses the 'Grave' mechanic.
        if self.state.stage_index == 3:
            for h in self.engine.heroes:
                if h.internal_id not in self.state.eliminated_heroes:
                    self.state.eliminated_heroes.append(h.internal_id)
            self.engine.log.append(Col.wrap(" 🪦 The fallen heroes have been removed from the timeline.", Col.RED))
        else:
            # Prelude failure logic (e.g., just logging the defeat)
            self.engine.log.append(Col.wrap(" ❌ The heroes retreat to recover.", Col.YLW))

    def setup_thanos_finale(self):
        """Sets up the final battle: Titan shift, Stone injection, and double-draft."""
        print(Col.wrap("\n 🫰 THE FINAL STAND: THANOS HAS ARRIVED.", Col.RED + Col.BOLD))
        
        active_count = len(self.engine.heroes)
        bench_count = active_count - 1
        
        # 1. PRIMARY & RESERVE DRAFTS
        print(f"\n Select your {active_count} primary heroes for the finale:")
        self.engine.heroes = self.filter_draft(active_count)
        
        primary_ids = [h.internal_id for h in self.engine.heroes]
        print(Col.wrap(f"\n Select {bench_count} RESERVE heroes (Primary team excluded):", Col.CYAN))
        self.state.hero_bench = self.filter_draft(bench_count, exclude_ids=primary_ids)
        
        # 2. SHIFT BATTLEFIELD TO TITAN
        try:
            with open("data/locations/thanos_battle_locations.json", 'r', encoding='utf-8') as f:
                loc_data = json.load(f)
            random.shuffle(loc_data)
            self.engine.locations = [Location(d) for d in loc_data[:6]]
            self.engine.log.append(Col.wrap(" 🌍 BATTLEFIELD SHIFT: TITAN", Col.PURP + Col.BOLD))
            for h in self.engine.heroes: h.location_index = 3
        except FileNotFoundError:
            self.engine.log.append(Col.wrap(" ⚠️ WARNING: Missing Titan locations! Using Earth.", Col.YLW))

        # 3. LOAD & INJECT INFINITY STONES
        try:
            with open("data/infinity_stones.json", "r") as f:
                stone_data = json.load(f)["infinity_stones"]
            
            for stone_name in self.state.thanos_vault:
                stone_def = next((s for s in stone_data if s["id"] == f"stone_{stone_name}"), None)
                if stone_def:
                    self.engine.villain.plan_deck.append(stone_def)
            
            random.shuffle(self.engine.villain.plan_deck)
            self.engine.log.append(Col.wrap(f" Thanos enters wielding {len(self.state.thanos_vault)} Infinity Stones!", Col.RED + Col.BOLD))
        except FileNotFoundError:
            self.engine.log.append(Col.wrap(" ⚠️ WARNING: No Infinity Stone deck found!", Col.YLW))

        # 4. RESET ENGINE
        self.reset_engine_for_stage()
        self.load_current_stage()

    def handle_thanos_ko(self, engine, fallen_hero):
        """The Stage 4 Reinforcement Logic."""
        engine.log.append(Col.wrap(f" 💀 PERMANENT KO: Thanos has utterly crushed {fallen_hero.name}!", Col.RED + Col.BOLD))
        
        fallen_idx = engine.heroes.index(fallen_hero)
        if self.state.hero_bench:
            new_hero = self.state.hero_bench.pop(0)
            new_hero.location_index = 3 
            new_hero.hand = [] # Ensure hand is clear before drawing
            new_hero.draw_cards(4)
            engine.heroes[fallen_idx] = new_hero
            engine.log.append(Col.wrap(f" ⚡ REINFORCEMENTS: {new_hero.name} joins the fight!", Col.CYAN + Col.BOLD))
        else:
            engine.heroes.pop(fallen_idx)
            engine.log.append(Col.wrap(f" ⚠️ No reinforcements left! The team is dwindling...", Col.YLW))
            if not engine.heroes:
                engine.game_over = True
                engine.victory_status = "VILLAIN_WINS"
                engine.loss_reason = "Thanos has eliminated all heroes."
                