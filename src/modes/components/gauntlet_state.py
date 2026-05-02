class GauntletState:
    def __init__(self):
        # Campaign Meta
        self.stage_index = 0
        self.roster = []
        self.eliminated_heroes = []  # 🪦 The Grave (internal_ids)
        
        # Arsenal & Pools
        self.power_up_pool = []
        self.acquired_power_ups = []
        self.hero_bench = []
        
        # The Vault
        self.thanos_vault = []
        self.stone_pool = ["power", "space", "reality", "soul", "time", "mind"]
        
        # Match-Specific (Reset every stage)
        self.match_stones = []
        self.cards_played = 0
        self.active_pu_token = None
        self.active_pu_mission = None
        self.pu_progress = {"attack": 0, "move": 0, "heroic": 0, "threat": 0}
