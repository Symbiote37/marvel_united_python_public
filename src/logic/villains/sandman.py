from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class SandmanLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "GROWING SANDSTORM (HP)"
        # His max HP is dynamic based on player count, but 20 is the hard loss limit
        villain.plot_max = 20 

        # 🚨 THE FIX: Sync immediately on load so it doesn't start at 0
        villain.plot_value = villain.hp 

        engine.log.append(Col.wrap("  SANDMAN: 'You can't punch a sandstorm!' ", Col.YLW + Col.BOLD))

    @staticmethod
    def check_sandman_win(engine):
        """Helper to check if Sandman has reached critical mass."""
        # Sync the visual plot tracker to his current HP for UI purposes
        engine.villain.plot_value = engine.villain.hp

        if engine.villain.plot_value >= 20:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "UNSTOPPABLE FORCE: Sandman grew too massive and buried the city in sand! "

    # --- DAMAGE SYNC ---

    @staticmethod
    def on_damage_taken(engine, villain, amount):
        """Hook called by ActionSystem whenever Sandman takes a hit."""
        # Instantly sync the visual plot tracker downward
        villain.plot_value = villain.hp

    # --- VULNERABILITY OVERRIDE ---

    @staticmethod
    def is_villain_shielded(engine, villain):
        """
        Bulletproof check for Sandman's 'Harder' invulnerability state.
        Safely scans both the storyline and the board ignoring case sensitivity.
        """
        # 1. Safely pull cards (handles lists or custom storyline objects)
        story_cards = getattr(engine.storyline, 'cards', engine.storyline)
        harder_played = False

        for card in story_cards:
            # Safely extract identifiers from dicts or objects
            if isinstance(card, dict):
                sid = str(card.get('special_id', card.get('display_name', ''))).lower()
            else:
                sid = str(getattr(card, 'special_id', getattr(card, 'display_name', ''))).lower()

            if 'harder' in sid:
                harder_played = True
                break

        # 2. If 'Harder' was played, aggressively check for active Sandstorms
        if harder_played:
            for loc in engine.locations:
                if loc.threat and not getattr(loc.threat, 'cleared', False):
                    # Force lowercase to avoid "Sandstorm" != "sandstorm" bugs
                    t_id = str(getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', ''))).lower()
                    t_name = str(getattr(loc.threat, 'name', '')).lower()

                    if 'sandstorm' in t_id or 'sandstorm' in t_name:
                        return True, " 🌪️ INVULNERABLE: The sandstorm protects him! Clear the Sandstorm threats first! "

        return False, ""


    # --- MAIN TURN LOGIC ---

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return

        # 1. Gain Mass
        villain.hp += 2
        engine.log.append(Col.wrap(f" 🏜️ GROWING THREAT: Sandman gathers more sand! (+2 HP, Now {villain.hp}) ", Col.YLW + Col.BOLD))
        SandmanLogic.check_sandman_win(engine)
        if getattr(engine, 'game_over', False): return

        # 2. Strike Location
        loc = engine.locations[v_idx]
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]

        engine.log.append(Col.wrap(f"   💥 BAM! Sandman blasts {loc.name} with coarse sand! ", Col.YLW))

        hit_anyone = False
        for h in targets:
            hit_anyone = True
            engine.log.append(Col.wrap(f"   🎯 Sandman hits {h.name}! ", Col.RED))
            h.take_damage(engine)

        if not hit_anyone:
            engine.log.append(Col.wrap("   💨 The sand blows harmlessly through the empty streets. ", Col.DARK_GRAY))

        # (Note: Henchmen BAMs for Doc Ock & Electro are handled automatically by BaseVillainLogic via EventSystem)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Overflows directly feed Sandman's health."""
        engine.log.append(Col.wrap(f"   ! OVERFLOW: Sand piles up at {loc.name} due to {t_type}! ", Col.RED))
        villain.hp += 2
        engine.log.append(Col.wrap(f" 🏜️ ABSORPTION: Sandman gains 2 Health! (Now {villain.hp} HP) ", Col.YLW + Col.BOLD))
        SandmanLogic.check_sandman_win(engine)

    @staticmethod
    def handle_hero_ko(engine, hero):
        """Sandman doesn't BAM on KO, he accelerates his Master Plan."""
        if getattr(hero, 'is_ko', False): return

        engine.log.append(Col.wrap(f" [!!!] {hero.name.upper()} HAS FALLEN! ", Col.RED + Col.BOLD))
        hero.is_ko = True 

        engine.log.append(Col.wrap(" 🏜️ SANDMAN SWARMS: He uses the opening to accelerate his plans! ", Col.YLW))
        if hasattr(engine, 'queued_events'):
            engine.queued_events.append({"type": "extra_card"})

    # --- MOVEMENT OVERRIDE ---

    @staticmethod
    def handle_movement(engine, villain, card):
        """
        Overrides standard movement for the Better, Faster, Stronger suite.
        Searches clockwise for the target condition and moves there before the effect fires.
        """
        sid = card.get("special_id")
        start_idx = villain.location_index

        if sid == "stronger":
            # Target: Nearest location with an uncleared Threat
            for i in range(6): # Includes current location (i=0)
                check_idx = (start_idx + i) % 6
                loc = engine.locations[check_idx]
                if loc.threat and not loc.threat.cleared:
                    if check_idx != start_idx:
                        villain.location_index = check_idx
                        engine.log.append(f" 🏃 Sandman surges to {loc.name} seeking power!")
                    return
            engine.log.append(" 🏃 Sandman searches for a threat but finds none.")

        elif sid == "faster":
            # Target: Nearest location WITH Heroes
            for i in range(6): 
                check_idx = (start_idx + i) % 6
                targets = [h for h in engine.heroes if h.location_index == check_idx and not getattr(h, 'is_ko', False)]
                if targets:
                    if check_idx != start_idx:
                        villain.location_index = check_idx
                        engine.log.append(f" 🏃 Sandman surges to {engine.locations[check_idx].name} hunting Heroes!")
                    return
            engine.log.append(" 🏃 Sandman searches for Heroes but finds none.")

        elif sid == "better":
            # Target: Nearest location WITHOUT Heroes
            for i in range(6): 
                check_idx = (start_idx + i) % 6
                targets = [h for h in engine.heroes if h.location_index == check_idx and not getattr(h, 'is_ko', False)]
                if not targets:
                    if check_idx != start_idx:
                        villain.location_index = check_idx
                        engine.log.append(f" 🏃 Sandman flows into the empty streets of {engine.locations[check_idx].name}!")
                    return
            engine.log.append(" 🏃 Sandman tries to isolate himself, but Heroes are everywhere.")

        else:
            # If it's not a special move, use the standard rulebook movement
            BaseVillainLogic.handle_movement(engine, villain, card)

    # --- SPECIAL CARDS ---

    @staticmethod
    def _resolve_better(engine, v_idx):
        engine.log.append(Col.wrap(" 🏜️ BETTER: Sandman sweeps his arms, striking adjacent sectors! ", Col.YLW))
        hit_anyone = False
        for offset in [-1, 1]:
            adj_idx = (v_idx + offset) % 6
            adj_loc = engine.locations[adj_idx]
            targets = [h for h in engine.heroes if h.location_index == adj_idx and not getattr(h, 'is_ko', False)]
            for h in targets:
                hit_anyone = True
                engine.log.append(Col.wrap(f"   🎯 Sand blast hits {h.name} at {adj_loc.name}! ", Col.RED))
                h.take_damage(engine)
        if not hit_anyone:
            engine.log.append(Col.wrap("   💨 The sand misses everyone. ", Col.DARK_GRAY))

    @staticmethod
    def _resolve_faster(engine, v_idx):
        engine.log.append(Col.wrap("  FASTER: A concentrated sand twister forms! ", Col.YLW))
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        
        if targets:
            # 1 damage base, PLUS 1 damage for each OTHER hero
            dmg = len(targets) 
            
            # ⚡ FIXED INDENTATION: Aligned all logic levels
            if len(targets) > 1:
                # 🔌 UI ADAPTER: Standardized prompt sequence
                print(Col.wrap(f"\n TARGET FOR 'FASTER' (Incoming Damage: {dmg}):", Col.YLW))
                for i, h in enumerate(targets, 1):
                    print(f" [{i}] {h.name} (HP: {h.hp}) ")
                
                choice = engine.ui.ask_choice(" Choose >> ", 1, len(targets))
                target = targets[choice - 1]
            else:
                # If only 1 hero is there, they take it automatically
                target = targets[0]
            
            engine.log.append(Col.wrap(f"   🎯 The twister hits {target.name} for {dmg} damage! ", Col.RED))
            
            # 🚨 SAFELY APPLY DAMAGE: Check KO status before each hit
            for _ in range(dmg):
                if not getattr(target, 'is_ko', False):
                    target.take_damage(engine)
        else:
            engine.log.append(Col.wrap("   💨 The twister spins out harmlessly. ", Col.DARK_GRAY))

    @staticmethod
    def _resolve_harder(engine):
        engine.log.append(Col.wrap(" 🛡️ HARDER: Sandman reinforces his body into impenetrable earth! ", Col.YLW + Col.BOLD))
        # The actual invulnerability is checked dynamically in `is_villain_shielded`

    @staticmethod
    def _resolve_stronger(engine, v_idx):
        engine.log.append(Col.wrap(" 💪 STRONGER: Sandman drains energy from the local threat! ", Col.YLW))
        loc = engine.locations[v_idx]
        if loc.threat and not loc.threat.cleared:
            # Sum up and clear all action tokens on the threat
            tokens_removed = (
                getattr(loc.threat, 'heroic_tokens', 0) +
                getattr(loc.threat, 'attack_tokens', 0) +
                getattr(loc.threat, 'move_tokens', 0)
            )

            if tokens_removed > 0:
                loc.threat.heroic_tokens = 0
                loc.threat.attack_tokens = 0
                loc.threat.move_tokens = 0
                engine.log.append(Col.wrap(f"   ! {tokens_removed} tokens swept away from {loc.threat.name}! ", Col.RED))

                targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
                for h in targets:
                    engine.log.append(Col.wrap(f"   🎯 {h.name} takes {tokens_removed} damage from the backlash! ", Col.RED))
                    for _ in range(tokens_removed):
                        h.take_damage(engine)
            else:
                engine.log.append(Col.wrap("   ...But there were no tokens to absorb. ", Col.DARK_GRAY))
        else:
            engine.log.append(Col.wrap("   ...But there was no threat to absorb. ", Col.DARK_GRAY))

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        v_idx = villain.location_index

        if sid == "better":
            SandmanLogic._resolve_better(engine, v_idx)
        elif sid == "faster":
            SandmanLogic._resolve_faster(engine, v_idx)
        elif sid == "harder":
            SandmanLogic._resolve_harder(engine)
        elif sid == "stronger":
            SandmanLogic._resolve_stronger(engine, v_idx)

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        """Intercepts threat BAMs to handle Electro's conditional chain-lightning."""
        t_id = (getattr(threat, 'id_internal', '') or getattr(threat, 'id', '')).lower()

        if t_id == "electro":
            loc = engine.locations[loc_idx]
            targets = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]

            if targets:
                engine.log.append(Col.wrap(f"   💥 BAM! Electro zaps {loc.name}! ", Col.YLW))
                for h in targets:
                    engine.log.append(Col.wrap(f"   🎯 Electro hits {h.name}! ", Col.RED))
                    h.take_damage(engine)
            else:
                engine.log.append(Col.wrap(f"   💥 BAM! Electro's lightning chains to adjacent sectors! ", Col.YLW))
                for offset in [-1, 1]:
                    adj_idx = (loc_idx + offset) % 6
                    # Use the standard sector hit so it safely ignores "The Void" (Location -1)
                    BaseVillainLogic._hit_sector(engine, adj_idx, 1, "Electro's chained lightning")
        else:
            # Let Doc Ock use the standard light_dmg_single_bam
            BaseVillainLogic.apply_standard_bam_damage(engine, threat, loc_idx)
