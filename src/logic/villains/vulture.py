from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class VultureLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "STOLEN SPOILS"
        
        # Plot Max dynamically scales based on Hero count
        hero_count = len(engine.heroes)
        if hero_count <= 2:
            villain.plot_max = 9
        elif hero_count == 3:
            villain.plot_max = 7
        else:
            villain.plot_max = 5
            
        villain.plot_value = 0
        
        # Setup the "Spoils" (Crisis Tokens) at every location
        for loc in engine.locations:
            loc.crisis_tokens = 3
            
        engine.log.append(Col.wrap(" 🦅 VULTURE: 'This city owes me, and I'm collecting!' ", Col.YLW + Col.BOLD))

    @staticmethod
    def check_vulture_win(engine):
        """Checks if Vulture has stolen enough spoils to end the game."""
        if engine.villain.plot_value >= engine.villain.plot_max:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = f"THE GREAT HEIST: Vulture escaped with {engine.villain.plot_max} Spoils! "

    @staticmethod
    def steal_spoil(engine, loc_idx):
        """Helper method to handle the theft of a crisis token."""
        loc = engine.locations[loc_idx]
        if loc.crisis_tokens > 0:
            loc.crisis_tokens -= 1
            engine.villain.plot_value += 1
            engine.log.append(Col.wrap(f" 💰 HEIST: Vulture stole a Spoil from {loc.name}! (Total: {engine.villain.plot_value}/{engine.villain.plot_max}) ", Col.PURP))
            VultureLogic.check_vulture_win(engine)
        else:
            engine.log.append(Col.wrap(f" 💰 HEIST: Vulture tried to steal from {loc.name}, but it's empty! ", Col.DARK_GRAY))

    # --- DEFENSE & EVASION (ELECTROMAGNETIC WINGS) ---

    @staticmethod
    def is_wings_active(engine, villain):
        """Checks if Vulture is currently sitting on an active Wings threat."""
        loc = engine.locations[villain.location_index]
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', '') or getattr(loc.threat, 'id', '')).lower()
            if "wings" in t_id:
                return True
        return False

    @staticmethod
    def reduce_damage(engine, villain, amount, is_action):
        """Limits incoming damage to 1 if Wings are active."""
        if VultureLogic.is_wings_active(engine, villain) and amount > 1:
            engine.log.append(Col.wrap(" 🪽 DEFENSE: Electromagnetic Wings absorb the impact! ", Col.PURP))
            return 1
        return amount

    @staticmethod
    def on_damage_taken(engine, villain, amount):
        """Forces an immediate retreat if Wings are active."""
        if VultureLogic.is_wings_active(engine, villain):
            opp_idx = (villain.location_index + 3) % 6
            villain.location_index = opp_idx
            opp_name = engine.locations[opp_idx].name
            engine.log.append(Col.wrap(f" 🪽 EVASION: Vulture uses the momentum to retreat to {opp_name}! ", Col.PURP))

    # --- MAIN TURN LOGIC ---

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return

        # 1. Steal from current location
        VultureLogic.steal_spoil(engine, v_idx)
        if getattr(engine, 'game_over', False): return

        # 2. The Great Gust (Movement)
        opp_idx = (v_idx + 3) % 6
        opp_loc = engine.locations[opp_idx]

        engine.log.append(Col.wrap(" 🌪️ BAM! Vulture's wings create a massive gust, blowing Heroes away! ", Col.YLW + Col.BOLD))
        
        active_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False)]
        if not active_heroes: return

        # Prompt for a Martyr
        prompt_lines = [
            Col.wrap(f"\n VULTURE'S GUST: Move all heroes to {opp_loc.name}?", Col.CYAN),
            " Any Hero can take 2 damage to prevent this movement."
        ]
        for i, h in enumerate(active_heroes, 1):
            # Display cards in hand instead of an 'hp' attribute
            prompt_lines.append(f" [{i}] {h.name} takes 2 damage (Cards in hand: {len(h.hand)})")
        prompt_lines.append(" [0] Allow Movement\n >> ")
        
        prompt_text = "\n".join(prompt_lines)

        # 🔌 UI ADAPTER: Fully concatenated prompt ensures headless Fuzzer compatibility
        choice = engine.ui.ask_choice(prompt_text, 0, len(active_heroes))

        if choice > 0:
            martyr = active_heroes[choice - 1]
            engine.log.append(Col.wrap(f" 🛡️ {martyr.name} braces against the wind, taking 2 damage to anchor the team! ", Col.RED))
            for _ in range(2):
                martyr.take_damage(engine)
        else:
            engine.log.append(Col.wrap(f" 💨 The wind sweeps the Heroes to {opp_loc.name}! ", Col.YLW))
            for h in active_heroes:
                h.location_index = opp_idx

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Vulture's Overflow loots the affected location."""
        engine.log.append(Col.wrap(f"   ! OVERFLOW: Panic at {loc.name} due to {t_type}! ", Col.RED))
        VultureLogic.steal_spoil(engine, engine.locations.index(loc))

    # --- SPECIAL CARDS & TRIGGERS ---

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "heist_plan":
            # 1. Count Heist Plans in the Storyline
            story_cards = getattr(engine.storyline, 'cards', engine.storyline)
            heist_count = sum(
                1 for c in story_cards 
                if str(getattr(c, 'special_id', c.get('special_id', ''))).lower() == "heist_plan"
            )
            
            # 2. Execute if it's NOT the first one
            if heist_count > 1:
                engine.log.append(Col.wrap(" 🦅 HEIST PLAN: Vulture swoops down on unguarded Locations! ", Col.YLW + Col.BOLD))
                
                theft_occurred = False
                # 🚨 JULES'S O(1) OPTIMIZATION + OUR ARMOR
                guarded_locations = {h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)}
                
                for i, loc in enumerate(engine.locations):
                    # Fast O(1) lookup to check if the location is unguarded
                    if i not in guarded_locations and loc.crisis_tokens > 0:
                        theft_occurred = True
                        VultureLogic.steal_spoil(engine, i)

                if not theft_occurred:
                    engine.log.append(Col.wrap("   ...But the Heroes were guarding all the remaining Spoils! ", Col.DARK_GRAY))
                    
            else:
                engine.log.append(Col.wrap(" 🦅 HEIST PLAN: Vulture is scouting the city for unguarded loot... ", Col.DARK_GRAY))

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        t_id = (getattr(threat, 'id_internal', '') or getattr(threat, 'id', '')).lower()
        if "grenade" in t_id:
            loc = engine.locations[loc_idx]
            targets = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
            if targets:
                engine.log.append(Col.wrap(f" 💣 TRIGGER: Grenades detonate at {loc.name}!", Col.RED + Col.BOLD))
                for h in targets:
                    engine.log.append(Col.wrap(f"   🎯 {h.name} takes 2 damage!", Col.RED))
                    for _ in range(2):
                        h.take_damage(engine)

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        """Handles custom henchmen logic (Sandman vs Kraven)."""
        t_id = (getattr(threat, 'id_internal', '') or getattr(threat, 'id', '')).lower()
        
        if "sandman" in t_id:
            loc = engine.locations[loc_idx]
            targets = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
            if targets:
                engine.log.append(Col.wrap(f"   💥 BAM! Sandman strikes {loc.name}!", Col.YLW))
                for h in targets:
                    engine.log.append(Col.wrap(f"   🎯 Sandman hits {h.name}!", Col.RED))
                    h.take_damage(engine)
            else:
                engine.log.append(Col.wrap(f"   💥 BAM! Sandman finds no heroes, so he secures loot for Vulture!", Col.YLW))
                VultureLogic.steal_spoil(engine, loc_idx)
        else:
            # Kraven uses the standard rulebook heavy_dmg_single_bam
            BaseVillainLogic.apply_standard_bam_damage(engine, threat, loc_idx)

