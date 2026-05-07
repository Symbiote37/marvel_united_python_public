# [Target: src/logic/villains/doctor_octopus.py]
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class DoctorOctopusLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "COLLAPSING CITY"
        villain.plot_max = 4 
        villain.plot_value = 0
        
        for loc in engine.locations:
            loc.is_destroyed = False
            loc.crisis_tokens = 0
            
        engine.log.append(Col.wrap("  DOC OCK: 'The city will crumble under my genius!'", Col.RED + Col.BOLD))

    # --- COLLAPSE MECHANICS ---

    @staticmethod
    def on_bam(engine, villain, damage=1):
        # 1. Standard damage to heroes at his location
        BaseVillainLogic.on_bam(engine, villain, damage=1)
        
        # 2. Add Crisis to his current location
        loc = engine.locations[villain.location_index]
        DoctorOctopusLogic.add_crisis(engine, loc)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        engine.log.append(Col.wrap(f"   ! OVERFLOW: Structural failure at {loc.name}!", Col.RED))
        DoctorOctopusLogic.add_crisis(engine, loc)

    @staticmethod
    def add_crisis(engine, loc):
        if getattr(loc, 'is_destroyed', False):
            return

        loc.crisis_tokens += 1
        engine.log.append(Col.wrap(f"   ⚠️ CRISIS: {loc.name} is destabilizing ({loc.crisis_tokens}/3)!", Col.YLW))
        
        if loc.crisis_tokens >= 3:
            DoctorOctopusLogic.destroy_location(engine, loc)

    @staticmethod
    def destroy_location(engine, loc):
        # Force instance-level flag
        loc.is_destroyed = True
        engine.villain.plot_value += 1

        engine.log.append(Col.wrap(f" [!!!] COLLAPSE: {loc.name} has been destroyed!", Col.RED + Col.BOLD))

        # Clear rubble & delete threats
        loc.civilians = 0; loc.thugs = 0
        if loc.threat:
            loc.threat.cleared = True
            loc.threat = None 

        # 🚨 THE FIX: Get the absolute array index, with fallback for headless deep-clones
        try:
            actual_loc_idx = engine.locations.index(loc)
        except ValueError:
            # Fallback to match by ID to prevent mismatches across clones/headless simulations
            actual_loc_idx = next((i for i, l in enumerate(engine.locations) if getattr(l, 'index', None) == getattr(loc, 'index', object())), 0)

        # Calculation: Find the actual next valid spots relative to this index
        cw_idx = DoctorOctopusLogic.get_next_valid_index(engine, actual_loc_idx, steps=1, direction=1)
        ccw_idx = DoctorOctopusLogic.get_next_valid_index(engine, actual_loc_idx, steps=1, direction=-1)
        cw_name = engine.locations[cw_idx].name
        ccw_name = engine.locations[ccw_idx].name

        # Evacuate Heroes
        for h in engine.heroes:
            if h.location_index == actual_loc_idx and not getattr(h, 'is_ko', False):
                prompt_text = (
                    f"\n {Col.wrap('🏚️ EVACUATION:', Col.RED)} {loc.name} is collapsing under {h.name}!\n"
                    f" (1) Leap clockwise to {cw_name}\n"
                    f" (2) Leap counter-clockwise to {ccw_name}\n"
                    f" Choose destination >> "
                )

                # 🚨 HEADLESS FIX: Route full prompt through UI Adapter
                choice = engine.ui.ask_choice(prompt_text, 1, 2)
                h.location_index = cw_idx if choice == 1 else ccw_idx
                engine.log.append(Col.wrap(f"   🏃 {h.name} fled to {engine.locations[h.location_index].name}!", Col.CYAN))

        # Move Villain (Automatic CW)
        if engine.villain.location_index == actual_loc_idx:
            engine.villain.location_index = cw_idx
            engine.log.append(Col.wrap(f"   🐙 Doc Ock scuttled to {cw_name}!", Col.RED))

    # --- NAVIGATION OVERRIDES ---

    @staticmethod
    def get_next_valid_index(engine, start_idx, steps=1, direction=1):
        """
        Finds the next valid location, skipping destroyed ones. 
        direction: 1 for Clockwise, -1 for Counter-Clockwise.
        """
        loc_count = len(engine.locations)
        current = start_idx
        for _ in range(steps):
            current = (current + direction) % loc_count
            attempts = 0
            while getattr(engine.locations[current], 'is_destroyed', False) and attempts < loc_count:
                current = (current + direction) % loc_count
                attempts += 1
        return current

    @staticmethod
    def handle_movement(engine, villain, card):
        """Overrides standard movement to skip destroyed locations."""
        move = card.get("move", 0)
        if isinstance(move, int) and move > 0:
            new_idx = DoctorOctopusLogic.get_next_valid_index(engine, villain.location_index, move, direction=1)
            villain.location_index = new_idx
            engine.log.append(f" 🏃 {villain.name} moves to {engine.locations[new_idx].name}.")

    # --- SPECIAL CARDS ---

    @staticmethod
    def _resolve_master_planner(engine, villain):
        engine.log.append(Col.wrap(" 🧠 MASTER PLANNER: Doc Ock exploits the city's weaknesses!", Col.PURP))
        hit_heroes = []

        for h in engine.heroes:
            if h.location_index != -1 and not getattr(h, 'is_ko', False):
                if engine.locations[h.location_index].crisis_tokens > 0:
                    hit_heroes.append(h)

        if hit_heroes:
            for h in hit_heroes:
                h.take_damage(engine)
                engine.log.append(Col.wrap(f"   💥 {h.name} caught in unstable terrain! (1 DMG)", Col.RED))
        else:
            engine.log.append(Col.wrap("   🛡️ No heroes were in unstable locations.", Col.GRN))

        loc = engine.locations[villain.location_index]
        DoctorOctopusLogic.add_crisis(engine, loc)

    @staticmethod
    def _resolve_tentacle_grasp(engine, villain):
        engine.log.append(Col.wrap(" 🦾 TENTACLE GRASP: Doc Ock drags the heroes closer!", Col.PURP))
        v_idx = villain.location_index
        loc_count = len(engine.locations)

        for h in engine.heroes:
            if h.location_index == -1 or getattr(h, 'is_ko', False) or h.location_index == v_idx:
                continue

            # Pathfinding: calculate CW vs CCW distances ignoring destroyed locations
            dist_cw = 0
            curr = h.location_index
            while curr != v_idx:
                curr = (curr + 1) % loc_count
                if not getattr(engine.locations[curr], 'is_destroyed', False): 
                    dist_cw += 1

            dist_ccw = 0
            curr = h.location_index
            while curr != v_idx:
                curr = (curr - 1) % loc_count
                if not getattr(engine.locations[curr], 'is_destroyed', False): 
                    dist_ccw += 1

            # Determine direction or prompt the player on a tie
            if dist_cw < dist_ccw:
                dir_step = 1
            elif dist_ccw < dist_cw:
                dir_step = -1
            else:
                # Player agency on equidistant drags
                cw_idx = DoctorOctopusLogic.get_next_valid_index(engine, h.location_index, steps=1, direction=1)
                ccw_idx = DoctorOctopusLogic.get_next_valid_index(engine, h.location_index, steps=1, direction=-1)
                cw_name = engine.locations[cw_idx].name
                ccw_name = engine.locations[ccw_idx].name

                prompt_text = (
                    f"\n {Col.wrap('🦾 TIE-BREAKER:', Col.PURP)} {h.name} is equidistant from Doc Ock.\n"
                    f" (1) Drag clockwise to {cw_name}\n"
                    f" (2) Drag counter-clockwise to {ccw_name}\n"
                    f" Choose direction >> "
                )

                # 🚨 HEADLESS FIX: Route full prompt through UI Adapter
                choice = engine.ui.ask_choice(prompt_text, 1, 2)
                if choice == 1:
                    dir_step = 1
                else:
                    dir_step = -1

            new_idx = DoctorOctopusLogic.get_next_valid_index(engine, h.location_index, steps=1, direction=dir_step)
            h.location_index = new_idx
            engine.log.append(Col.wrap(f"   🦾 {h.name} is dragged to {engine.locations[new_idx].name}!", Col.YLW))

        # 🚨 ROUTING FIX: Use the global broadcast so Henchmen (Vulture) trigger!
        from src.systems.event_system import EventSystem
        EventSystem.broadcast_bam(engine, full_board=True)

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")

        if sid == "master_planner":
            DoctorOctopusLogic._resolve_master_planner(engine, villain)
        elif sid == "tentacle_grasp":
            DoctorOctopusLogic._resolve_tentacle_grasp(engine, villain)

    # --- TARGETED OVERRIDES ---

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        """Custom BAM logic for the specific Sinister Six threats."""
        t_id = (getattr(threat, 'id_internal', '') or threat.id).lower()

        if t_id == "sandman":
            threat.hp += 1
            engine.log.append(Col.wrap(f" ⏳ SANDMAN: Gathers more sand! (+1 HP, now {threat.hp})", Col.YLW))
            # Deal 1 damage to all heroes in location
            BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Sandman's sandstorm", single_target=False)

        elif "vulture" in t_id:
            # 🚨 ONE SOURCE OF TRUTH: Prevent loop-chasing by locking Vulture to the engine's Storyline clock
            current_step = len(engine.storyline.cards)
            if getattr(threat, '_last_bam_step', -1) == current_step:
                return
            threat._last_bam_step = current_step

            # 1. Base Attack
            BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Vulture's swoop", single_target=True)

            # 2. Movement Logic
            moved = False
            loc_count = len(engine.locations)
            for i in range(1, loc_count): # Check the other locations dynamically
                check_idx = (loc_idx + i) % loc_count
                target_loc = engine.locations[check_idx]

                is_open = (not target_loc.threat) or getattr(target_loc.threat, 'cleared', False)

                if is_open and not getattr(target_loc, 'is_destroyed', False):
                    # Move Vulture into the slot (crushing the old cleared threat)
                    target_loc.threat = threat
                    engine.locations[loc_idx].threat = None
                    engine.log.append(Col.wrap(f" 🦅 VULTURE: Swoops to {target_loc.name}!", Col.YLW))
                    moved = True
                    break

            if not moved:
                engine.log.append(Col.wrap(f" 🦅 VULTURE: No open perches! Remains at {engine.locations[loc_idx].name}.", Col.DARK_GRAY))

        elif "mysterio" in t_id:
            # Deal 1 damage to 1 hero
            BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Mysterio's illusion", single_target=True)
            loc = engine.locations[loc_idx]

            if not getattr(loc, 'is_destroyed', False):
                engine.log.append(Col.wrap(f" 🔮 MYSTERIO (Threat): Summons a Civilian and Thug!", Col.PURP))
                from src.systems.token_system import TokenSystem

                # Create a local tracker for this specific threat resolution
                overflow_tracker = set()
                TokenSystem.add_token(engine, loc_idx, "civilians", overflow_tracker)
                TokenSystem.add_token(engine, loc_idx, "thugs", overflow_tracker)

        else:
            # Fallback for standard generic damage patterns
            BaseVillainLogic.apply_standard_bam_damage(engine, threat, loc_idx)

    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Dr. Otto Octavius relies on pure intellectual superiority \n"
                "and his mechanical appendages. He doesn't just want to defeat \n"
                "the heroes; he wants to structurally dismantle the city."
            ),
            "rules": (
                "\"Collapsing City\"\n"
                "Doc Ock places Crisis tokens to destabilize sectors. If a \n"
                "location accumulates 3 Crisis tokens, it is DESTROYED. \n"
                "All tokens are wiped, and the sector is permanently removed \n"
                "from board movement. If 4 locations collapse, the city falls \n"
                "and the mission is lost. \n\n"
                "Also, beware his 'Tentacle Grasp', which drags all heroes \n"
                "closer to him before triggering a massive BAM."
            ),
            "bam": (
                "\"Controlled Demolition\"\n"
                "He lashes out, dealing 1 damage to every hero in his sector. \n"
                "Simultaneously, his tentacles rip at the foundations, placing \n"
                "1 Crisis token on his current location."
            ),
            "overflow": (
                "\"Structural Stress\"\n"
                "When a sector is overrun, the sheer weight of the panic \n"
                "accelerates the collapse. Any overflow adds 1 Crisis token \n"
                "to that location."
            ),
            "threats": (
                "He has assembled the Sinister Six for this operation.\n"
                "- Sandman: Deals AoE damage and actually GAINS health on BAM.\n"
                "- Vulture: Hit-and-run tactics; he strikes a hero and immediately \n"
                "  relocates to an empty Threat slot.\n"
                "- Mysterio: Deals damage and floods the zone with new Civilians \n"
                "  and Thugs, accelerating Overflows.\n"
                "- Endangered Civilians: Requires 2 Heroic (★) actions to rescue."
            )
        }
