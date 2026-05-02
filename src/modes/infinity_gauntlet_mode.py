from src.modes.base_mode import BaseMode
from src.modes.components.gauntlet_state import GauntletState
from src.modes.components.power_up_manager import PowerUpManager
from src.modes.components.stone_manager import StoneManager
from src.modes.components.stage_manager import StageManager
from src.modes.components.gauntlet_ui import GauntletUI
import random

class InfinityGauntletMode(BaseMode):
    """
    Orchestrator for the Infinity Gauntlet campaign. 
    Delegates logic to specialized components while managing the engine lifecycle.
    """

    STONE_ICONS = {
        "power": "🟣", "space": "🔵", "reality": "🔴",
        "soul": "🟠", "time": "🟢", "mind": "🟡"
    }

    def perform_setup(self):
        """Initializes components and prepares the initial campaign state."""
        super().perform_setup()
        
        # 1. Component Initialization
        self.state = GauntletState()
        self.power_ups = PowerUpManager(self.state)
        self.stones = StoneManager(self.state)
        self.stages = StageManager(self.engine, self.state)
        
        # 🎲 2. THE QUEUE: Randomize 3 Children, end with Thanos
        children = ["proxima_midnight", "ebony_maw", "corvus_glaive", "black_dwarf"]
        random.shuffle(children)
        self.state.campaign_roster = children[:3] + ["thanos"]
        
        # 3. Campaign Setup
        self.power_ups.initialize_pool()
        self.stages.prepare_campaign()
        
        # 4. Initial Stage Loading
        self.stages.load_current_stage()
        self._prepare_round()

    def _prepare_round(self):
        """Delegates match-specific setup based on the current stage."""
        if self.state.stage_index < 3:
            # Prelude setup: Stones and Power-Up slots
            self.stones.prepare_match_stones()
            self.power_ups.prepare_match_slots(self.engine)
        else:
            # Finale setup: Battlefield shift and reserve draft
            self.stages.setup_thanos_finale()

    def execute_villain_turn(self, forced_extra_card=False):
        """Mediates between standard villain turn logic and campaign milestones."""
        super().execute_villain_turn(forced_extra_card)
        
        if self.state.stage_index < 3 and not self.engine.game_over:
            self.state.cards_played += 1
            self.stones.check_milestones(self.engine)

    def handle_victory(self):
        """Orchestrates successful match completion."""
        self.power_ups.evaluate_stage_end(self.engine, victory=True)
        self.stones.handle_match_end(victory=True, engine=self.engine)
        self._transition_stage()

    def handle_defeat(self):
        """Orchestrates failed match completion with campaign-level consequences."""
        self.power_ups.evaluate_stage_end(self.engine, victory=False)
        self.stones.handle_match_end(victory=False, engine=self.engine)
        self.stages.handle_death(victory=False)
        self._transition_stage()

    def handle_hero_eliminated(self, engine, hero):
        """
        Intercepts permanent hero elimination (deck/hand empty) to prevent a Game Over 
        if there are reserve heroes available during the finale.
        """
        # We only intercept during the Stage 4 Finale
        if self.state.stage_index == 3:
            engine.log.append(Col.wrap(f" 💀 {hero.name.upper()} IS EXHAUSTED AND ELIMINATED!", Col.RED + Col.BOLD))
            
            # 1. Increment Thanos's plot (KO Counter)
            engine.villain.plot_value += 1
            
            # 2. Check if this KO triggers the Snap
            if engine.villain.plot_value >= getattr(engine, 'starting_hero_count', 2):
                from src.systems.event_system import EventSystem
                EventSystem.trigger_defeat(engine, "THE SNAP: Thanos has eliminated the primary resistance!")
                return True # We intercepted it, the EventSystem will handle the Game Over sequence.

            # 3. Swap in a Reserve Hero
            if hasattr(engine, 'standby_heroes') and engine.standby_heroes:
                new_hero = engine.standby_heroes.pop(0)
                new_hero.location_index = hero.location_index
                
                # Replace the fallen hero in the engine's active roster
                idx = engine.heroes.index(hero)
                engine.heroes[idx] = new_hero
                
                engine.log.append(Col.wrap(f" 🛡️ REINFORCEMENTS: {new_hero.name} steps up to replace {hero.name}!", Col.GRN))
                return True # We successfully intercepted the Game Over! The match continues.
            else:
                engine.log.append(Col.wrap(" ⚠️ No heroes left on standby!", Col.RED))
                return False # No reserves left. Return False so the Engine triggers a standard Game Over.
                
        # If we aren't fighting Thanos, let the engine kill the team normally.
        return False 
        
    def _transition_stage(self):
        """Evaluates campaign-wide game-over conditions or progresses to the next stage."""
        # 1. Check for the Snap (Total Campaign Loss)
        if len(self.state.thanos_vault) >= 6:
            self.engine.game_over = True
            self.engine.victory_status = "VILLAIN_WINS"
            self.engine.loss_reason = "THE SNAP: Thanos collected all 6 Infinity Stones!"
            return

        # 2. Check for Campaign Completion (Beat Thanos)
        if self.state.stage_index == 3:
            self.engine.game_over = True
            return

        # 🚨 THE RESUSCITATION: If we lost the match, revive the engine for the next stage!
        self.engine.game_over = False 
        
        # 3. Progress Stage & Swap Boss
        self.state.stage_index += 1
        next_boss = self.state.campaign_roster[self.state.stage_index]
        self.engine.hot_swap_villain(next_boss)
        
        self.stages.reset_engine_for_stage()
        
        # 4. Draft next squad if applicable
        if self.state.stage_index < 3:
            self.engine.heroes = self.stages.filter_draft(len(self.engine.heroes))
            
        self._prepare_round()

    def get_custom_commands(self, engine, hero, pool):
        """Delegates turn-based custom commands to the Power-Up component."""
        return self.power_ups.get_deposit_commands(pool)

    def handle_custom_command(self, engine, hero, cmd, pool):
        """Delegates command execution to the Power-Up component."""
        if cmd == 'P':
            return self.power_ups.handle_deposit(engine, hero, pool)
        return False

    def try_intercept_threat_token(self):
        """Delegates threat token diversion to the Power-Up component."""
        return self.power_ups.intercept_threat(self.engine)

    def apply_passives(self, engine, hero, pool):
        """Delegates arsenal rewards to the Power-Up component."""
        self.power_ups.apply_passives(engine, hero, pool)

    def render_center_dashboard(self):
        """Delegates HUD rendering to the UI component."""
        return GauntletUI.render_dashboard(self.state, self.engine, self.STONE_ICONS)
