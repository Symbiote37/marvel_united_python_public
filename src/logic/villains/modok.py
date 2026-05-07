# [Target: src/logic/villains/modok.py]
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class ModokLogic(BaseVillainLogic):
    """
    M.O.D.O.K. (Mental Organism Designed Only for Killing)
    Core Gimmick: Flips Hero cards facedown from the start of the Storyline.
    """

    @staticmethod
    def perform_setup(engine, villain):
        """
        M.O.D.O.K.'S MASTER PLAN SETUP:
        1. 'Preparation' card forced to the top.
        2. 'Psionic Powers' threat banished from the Heroes' starting location.
        3. Mental Domination track initialized.
        """
        from src.utils.helpers import Col

        # 1. Force Card ID 9 ("Preparation") to the top
        deck = villain.plan_deck
        prep_card = next((c for c in deck if c.get('id') == 9), None)
        if prep_card:
            deck.remove(prep_card)
            deck.insert(0, prep_card)
        
        # 2. Prevent 'Psionic Powers' from bricking the starting zone
        if engine.heroes:
            h_start = engine.heroes[0].location_index
            for i, loc in enumerate(engine.locations):
                if loc.threat and getattr(loc.threat, 'id_internal', '') == 'psionic_powers':
                    if i == h_start:
                        # Swap it one sector clockwise
                        swap_idx = (i + 1) % 6
                        loc.threat, engine.locations[swap_idx].threat = engine.locations[swap_idx].threat, loc.threat
                        break

        # 3. Initialize the dynamic plot
        villain.plot_name = "MENTAL DOMINATION"
        villain.plot_value = 0
        villain.plot_max = 0
        villain.faceup_hero_indices = []
        engine.log.append(Col.wrap(" 🧠 M.O.D.O.K.: 'My grand design begins!'", Col.MAGENTA + Col.BOLD))
        
        # Sync the tracker before Turn 1 begins
        ModokLogic.update_plot_tracker(engine)

    @staticmethod
    def flip_hero_cards(engine, count):
        """
        Targeted logic to flip Hero cards starting from the oldest.
        """
        if count <= 0: return

        flipped_this_time = 0
        villain = engine.villain
        
        if not hasattr(villain, 'faceup_hero_indices'):
            # Fallback for safety, though it should be initialized in setup
            ModokLogic.update_plot_tracker(engine)

        while count > 0 and villain.faceup_hero_indices:
            idx = villain.faceup_hero_indices.pop(0)
            
            # Verify direct assignment to the root list element
            engine.storyline.cards[idx]['is_facedown'] = True
            engine.storyline.cards[idx]['actions'] = []
            
            flipped_this_time += 1
            villain.plot_value += 1
            count -= 1

        if flipped_this_time > 0:
            engine.log.append(Col.wrap(f" 🧠 M.O.D.O.K. wiped {flipped_this_time} Hero card(s) from the Storyline!", Col.MAGENTA + Col.BOLD))
        
        ModokLogic._check_defeat(engine)

    @staticmethod
    def update_plot_tracker(engine):
        """
        Maintains the Mental Domination track.
        Optimized to use cached values.
        """
        if engine.villain.plot_max == 0:
            engine.villain.plot_max = 99
        
        ModokLogic._check_defeat(engine)

    # --- STANDARD HOOKS ---

# [Target: src/logic/villains/modok.py]

    @staticmethod
    def on_bam(engine, villain):
        """
        M.O.D.O.K. BAM: Flips 1 card, +1 for each faceup Consciousness Transferral.
        Ignores a Consciousness Transferral played on the current turn.
        """
        engine.log.append(Col.wrap(" 💥 BAM! M.O.D.O.K.: 'My intellect is absolute!'", Col.MAGENTA + Col.BOLD))
        
        flip_count = 1
        
        # Identify the card currently being resolved (the absolute last card in the Storyline)
        active_card = engine.storyline.cards[-1] if engine.storyline.cards else None

        # Check for ongoing Master Plan effects
        for card in engine.storyline.cards:
            if card.get('special_id') == 'consciousness_transferral' and not card.get('is_facedown'):
                
                # 🚨 STATE ARMOR: Do not let the card buff its own initial BAM, but allow Threat BAMs!
                if not card.get("_initial_bam_resolved"):
                    card["_initial_bam_resolved"] = True
                    if card is active_card:
                        continue
                    
                flip_count += 1
                engine.log.append(Col.wrap("   ↳ Consciousness Transferral amplifies the effect!", Col.CYAN))
                
        ModokLogic.flip_hero_cards(engine, flip_count)

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        OVERFLOW: Flip 1 card per overflow.
        """
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: M.O.D.O.K.'s calculations expand at {location.name}!", Col.RED))
        ModokLogic.flip_hero_cards(engine, 1)

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "preparation":
            engine.log.append(Col.wrap(" ⚙️ PREPARATION: M.O.D.O.K. targets the resistance directly.", Col.CYAN))
            if engine.heroes:
                villain.location_index = engine.heroes[0].location_index
                
        elif sid == "super_genius_intelligence":
            engine.log.append(Col.wrap(" ⏱️ SUPER-GENIUS INTELLIGENCE: The timeline accelerates!", Col.CYAN))
            if hasattr(engine, 'queued_events'):
                engine.queued_events.append({"type": "extra_card"})

    # --- THREAT LOGIC ---

    @staticmethod
    def get_start_of_turn_modifiers(engine, hero, location):
        """ Catch Psionic Powers before the Hero plays a card. """
        if location.threat and not location.threat.cleared:
            if getattr(location.threat, 'id_internal', '') == 'psionic_powers':
                return {"is_facedown": True, "label": "PSIONIC POWERS"}
        return BaseVillainLogic.get_start_of_turn_modifiers(engine, hero, location)

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        tid = getattr(threat, 'bam_id', getattr(threat, 'id_internal', "")).lower()
        
        # Helper: Get symbols from last 2 Hero cards (optimized backward scan)
        def get_recent_symbols(symbol_key):
            count = 0
            found_heroes = 0
            for c in reversed(engine.storyline.cards):
                if c.get('owner') and c['owner'] != engine.villain.name:
                    if not c.get('is_facedown'):
                        count += c.get('actions', []).count(symbol_key)
                    found_heroes += 1
                    if found_heroes >= 2:
                        break
            return count

        if "chameleon" in tid:
            dmg = get_recent_symbols("attack")
            engine.log.append(Col.wrap(f" 🦎 CHAMELEON: Mimicking combat patterns! (Dealing {dmg} DMG)", Col.YLW))
            BaseVillainLogic._hit_sector(engine, loc_idx, dmg, "Chameleon Strike", single_target=True)
            
        elif "spot" in tid:
            flips = get_recent_symbols("heroic")
            engine.log.append(Col.wrap(f" ⚫ SPOT: Disrupting heroism! (Flipping {flips} cards)", Col.YLW))
            ModokLogic.flip_hero_cards(engine, flips)
            
        elif "living_laser" in tid or "light_damage_bam" in tid:
            engine.log.append(Col.wrap(" ⚡ LIVING LASER: Sweeping the sector!", Col.YLW))
            heroes_here = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
            if heroes_here:
                BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Laser Sweep", single_target=False)
            else:
                engine.log.append("   ↳ Sector empty. Flipping 1 Hero card instead!")
                ModokLogic.flip_hero_cards(engine, 1)
        else:
            BaseVillainLogic.resolve_threat_bam(engine, threat, loc_idx)

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        if engine.villain.location_index != loc_idx:
            return
            
        tid = (getattr(threat, 'trigger_id', None) or getattr(threat, 'id_internal', None) or getattr(threat, 'id', None) or "").lower()

        if tid == "technopathy":
            heroes_here = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
            if heroes_here:
                engine.log.append(Col.wrap(" ⚙️ TECHNOPATHY: M.O.D.O.K. hacks your gear!", Col.MAGENTA))
                for h in heroes_here:
                    tokens = getattr(h, 'action_tokens', [])
                    if not tokens:
                        engine.log.append(f"   {h.name} has no tokens to discard! (Penalty: Flip 2 cards)")
                        ModokLogic.flip_hero_cards(engine, 2)
                    else:
                        print(f"\n{Col.wrap(' ⚙️ TECHNOPATHY HACK:', Col.MAGENTA)} {h.name}, your gear is compromised!")
                        print(f" You have {len(tokens)} token(s): {tokens}")
                        print(" (1) Discard All Tokens")
                        print(" (2) Keep Tokens (Penalty: Flip 2 Hero cards)")
                        choice = Col.get_choice(" >> ", 1, 2)
                        
                        if choice == 1:
                            h.action_tokens = []
                            engine.log.append(f"   {h.name} purged their systems and lost all tokens.")
                        else:
                            engine.log.append(f"   {h.name} bypassed the hack! (Penalty: Flip 2 cards)")
                            ModokLogic.flip_hero_cards(engine, 2)
                            
        elif tid == "energy_projection":
            engine.log.append(Col.wrap(" ⚡ ENERGY PROJECTION: A psionic blast disrupts the timeline!", Col.MAGENTA))
            ModokLogic.flip_hero_cards(engine, 1)

    @staticmethod
    def _check_defeat(engine):
        """Centralized win/loss check using cached tracker values."""
        villain = engine.villain
        flipped = villain.plot_value

        # Re-derive total from cached faceup indices to ensure absolute sync
        total = flipped + len(getattr(villain, 'faceup_hero_indices', []))
        villain.plot_max = total if total > 0 else 99

        if total > 0 and flipped >= total:
            # 🚨 THE FIX: Set flags silently instead of using EventSystem. 
            # The core engine will read these and print the single, unified failure screen.
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "MENTAL DOMINATION: M.O.D.O.K. has erased the Heroes' minds!"
            villain.plot_max = 999

    @staticmethod
    def on_card_played(engine):
        """
        Triggered dynamically by HeroSystem whenever a new card is added to the Storyline.
        Ensures the denominator (plot_max) expands immediately.
        """
        villain = engine.villain
        idx = len(engine.storyline.cards) - 1
        card = engine.storyline.cards[idx]

        # Verify it is a Hero card (Owner filter)
        is_hero_card = card.get('owner') and card['owner'] != villain.name
        if not is_hero_card:
            return

        if card.get('is_facedown'):
            villain.plot_value += 1
        else:
            if not hasattr(villain, 'faceup_hero_indices'):
                villain.faceup_hero_indices = []
            villain.faceup_hero_indices.append(idx)

        ModokLogic._check_defeat(engine)