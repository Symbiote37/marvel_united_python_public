import random
from src.utils.helpers import Col

class StoneManager:
    def __init__(self, state):
        self.state = state

    def prepare_match_stones(self):
        random.shuffle(self.state.stone_pool)
        self.state.match_stones = [self.state.stone_pool.pop(0) for _ in range(min(3, len(self.state.stone_pool)))]
        self.state.cards_played = 0

    def check_milestones(self, engine):
        milestones = {6: 0, 10: 1, 12: 2}
        if self.state.cards_played in milestones:
            idx = milestones[self.state.cards_played]
            if idx < len(self.state.match_stones) and self.state.match_stones[idx]:
                stone = self.state.match_stones[idx]
                engine.log.append(Col.wrap(f"\n *** 💎 {stone.upper()} STONE REVEALED ***", Col.PURP + Col.BOLD))
                self.state.thanos_vault.append(stone)
                self.state.match_stones[idx] = None
                if len(self.state.thanos_vault) >= 6:
                    engine.game_over = True
                    engine.victory_status = "VILLAIN_WINS"
                    engine.victory_reason = "THE SNAP"

    def handle_match_end(self, victory, engine):
        if victory:
            for s in self.state.match_stones:
                if s: self.state.stone_pool.append(s)
        else:
            for s in self.state.match_stones:
                if s: 
                    self.state.thanos_vault.append(s)
                    engine.log.append(Col.wrap(f" ⚠️ Thanos acquired the {s.upper()} stone!", Col.PURP))
        self.state.match_stones = []
