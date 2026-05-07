from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class ElectroLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "CITY-WIDE BLACKOUT"
        villain.plot_max = 6
        villain.plot_value = 0
        
        # 🚨 THE FIX: Replace 'dematerialized_until' with a Storyline tracker
        villain.demat_target_storyline = 0 
        
        for loc in engine.locations:
            loc.crisis_tokens = 0
            
        engine.log.append(Col.wrap(" ⚡ ELECTRO: 'I'll fry this whole city!'", Col.YLW + Col.BOLD))

    # --- VULNERABILITY OVERRIDE ---

    @staticmethod
    def is_villain_shielded(engine, villain):
        """
        Checks the literal length of the physical Storyline to see if enough
        Hero cards have been played since he dematerialized.
        """
        # 🚨 ONE SOURCE OF TRUTH: The engine dictates Storyline is an object with a .cards list.
        actual_length = len(engine.storyline.cards)
        if getattr(villain, 'demat_target_storyline', 0) > actual_length:
            cards_needed = villain.demat_target_storyline - actual_length
            return True, f" ⚡ INVULNERABLE: Electro is pure static! (Needs {cards_needed} more cards in Storyline)"
            
        return False, ""

    # --- THE POWER GRID (CRISIS TOKENS) ---

    @staticmethod
    def add_crisis_cascade(engine, start_idx):
        """Cascades clockwise until it finds an open location."""
        # 🛡️ SAFETY 1: Wrap the incoming index immediately
        # This prevents an IndexError if start_idx is 6 or higher
        current_idx = start_idx % 6
        target_idx = -1 

        for i in range(6):
            check_idx = (current_idx + i) % 6
            if getattr(engine.locations[check_idx], 'crisis_tokens', 0) == 0:
                target_idx = check_idx
                break
        
        # ⚡ RESOLUTION
        if target_idx != -1:
            loc = engine.locations[target_idx]
            loc.crisis_tokens = 1
            engine.log.append(Col.wrap(f"   ⚡ SURGE: {loc.name} is electrified!", Col.YLW))
        else:
            # 🛡️ SAFETY 2: If the grid is totally full, don't crash, just log it.
            # The Plot Tracker check below will handle the Game Over.
            engine.log.append(Col.wrap(f"   ⚡ TOTAL SURGE: The grid is fully overloaded!", Col.RED))

        # Update Plot and Check Win Condition
        ElectroLogic.update_plot_tracker(engine)
        
        if engine.villain.plot_value >= 6:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "CITY-WIDE BLACKOUT: Electro has overloaded the entire power grid!"


    @staticmethod
    def update_plot_tracker(engine):
        engine.villain.plot_value = sum(1 for l in engine.locations if l.crisis_tokens > 0)

    @staticmethod
    def on_crisis_cleared(engine, loc):
        """Hook called when a Hero uses a heroic token to clear a crisis."""
        ElectroLogic.update_plot_tracker(engine)

    # --- DAMAGE APPLICATION (WITH HIGH VOLTAGE) ---

    @staticmethod
    def deal_electro_damage(engine, hero, dmg, src):
        """Wrapper to apply damage so we can calculate the High Voltage threat."""
        loc = engine.locations[hero.location_index]
        actual_dmg = dmg
        
        t_id = (getattr(loc.threat, 'id_internal', '') or getattr(loc.threat, 'id', '')).lower()
        if loc.threat and not loc.threat.cleared and "high_voltage" in t_id:
            actual_dmg += 1
            engine.log.append(Col.wrap(f"   ⚠️ HIGH VOLTAGE! {hero.name} takes +1 damage from the electrified environment!", Col.YLW))
            
        engine.log.append(Col.wrap(f"   🎯 {src} hits {hero.name}!", Col.RED))
        for _ in range(actual_dmg):
            hero.take_damage(engine)

    # --- MAIN TURN LOGIC ---

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return

        # Target Across (Index + 3) and its neighbors (+1, -1)
        target_idx = (v_idx + 3) % 6
        adj_1 = (target_idx + 1) % 6
        adj_2 = (target_idx - 1) % 6
        
        hit_zones = {target_idx, adj_1, adj_2}
        
        target_name = engine.locations[target_idx].name
        engine.log.append(Col.wrap(f"   💥 BAM! Electro fires a massive arc across the city at {target_name}!", Col.YLW + Col.BOLD))
        
        hit_anyone = False
        for idx in hit_zones:
            targets = [h for h in engine.heroes if h.location_index == idx and not getattr(h, 'is_ko', False)]
            for h in targets:
                hit_anyone = True
                ElectroLogic.deal_electro_damage(engine, h, damage, "Electro's chain-lightning")
                
        if not hit_anyone:
            engine.log.append(Col.wrap("   ⚡ The lightning strikes nothing but pavement!", Col.DARK_GRAY))

    @staticmethod
    def handle_hero_ko(engine, hero):
        """Electro does not BAM on KOs. He electrifies the fallen hero's location."""
        if getattr(hero, 'is_ko', False):
            return

        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} HAS FALLEN!", Col.RED + Col.BOLD))
        hero.is_ko = True 
        
        # Override the KO BAM with a Crisis Token cascade
        engine.log.append(Col.wrap(" ⚡ ELECTRO'S REVENGE: A power surge strikes the fallen hero's location!", Col.YLW))
        ElectroLogic.add_crisis_cascade(engine, hero.location_index)
        
    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        # 👔 Find the actual list position (0-5)
        try:
            idx = engine.locations.index(location)
            ElectroLogic.add_crisis_cascade(engine, idx)
        except ValueError:
            # Emergency fallback to start at the Helicarrier
            ElectroLogic.add_crisis_cascade(engine, 0) 

   # --- SPECIAL CARDS ---

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "blackout":
            engine.log.append(Col.wrap(" 🔌 BLACKOUT: A massive surge hits the local grid!", Col.YLW))
            ElectroLogic.add_crisis_cascade(engine, villain.location_index)
            
        elif sid == "dematerialize":
            active_heroes = len([h for h in engine.heroes if not getattr(h, "is_ko", False)])
            
            # 🚨 ONE SOURCE OF TRUTH: Lock the target using .cards
            villain.demat_target_storyline = len(engine.storyline.cards) + active_heroes
            
            engine.log.append(Col.wrap(
                f" 🌌 DEMATERIALIZE: Electro turns into static! (Invulnerable for {active_heroes} Hero Hero cards)", 
                Col.PURP + Col.BOLD
            ))

    # --- THREAT TRIGGERS ---

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        t_id = (getattr(threat, 'id_internal', '') or threat.id).lower()
        
        if "overpowered" in t_id:
            engine.log.append(Col.wrap(f" ⚡ OVERPOWERED: Electro absorbs raw energy! (+1 Master Plan)", Col.YLW))
            if hasattr(engine, 'queued_events'):
                engine.queued_events.append({"type": "extra_card"})
                
        elif "recharge" in t_id:
            engine.villain.hp += 3
            engine.log.append(Col.wrap(f" 🔋 RECHARGE: Electro regains 3 Health! (Now {engine.villain.hp} HP)", Col.GRN))
            
    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Max Dillon, a.k.a. Electro, is living lightning. He doesn't \n"
                "just want to defeat you; he wants to fry the entire city's \n"
                "power grid until everything goes dark."
            ),
            "rules": (
                "\"City-Wide Blackout & Static Form\"\n"
                "Electro overloads the grid using Crisis tokens. If a token \n"
                "is placed on a location that already has one, the surge \n"
                "cascades clockwise until it finds an empty node. If all 6 \n"
                "locations are electrified, the grid collapses and you lose.\n\n"
                "KOs do not trigger a Revenge BAM; instead, they strike the \n"
                "fallen hero's location with a Crisis token. Also, beware his \n"
                "ability to 'Dematerialize', making him utterly invulnerable \n"
                "until every active hero cycles a card!"
            ),
            "bam": (
                "\"Arc Lightning\"\n"
                "He fires a massive electrical arc across the city. His BAM \n"
                "hits the sector EXACTLY OPPOSITE to him, as well as the two \n"
                "sectors adjacent to that target zone. Strangely, standing \n"
                "close to him might be the safest place."
            ),
            "overflow": (
                "\"Grid Overload\"\n"
                "When a sector is overrun, the local grid blows out. Any \n"
                "overflow places 1 Crisis token at that location (cascading \n"
                "clockwise if it is already electrified)."
            ),
            "threats": (
                "He has weaponized the city's infrastructure against you.\n"
                "- High Voltage: Environmental hazard; you take +1 damage here.\n"
                "- Overpowered: Absorbs raw energy to play an EXTRA Master Plan.\n"
                "- Recharge: Restores 3 HP to Electro (and can even exceed his \n"
                "  starting health!)."
            )
        }
