# [Target: src/logic/villains/rhino.py]
import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON
from src.utils.navigation import BoardNav

class RhinoLogic(BaseVillainLogic):
    """
    RHINO: The Unstoppable Rampage.
    Features: Movement-scaling damage, Hero-shifting, and Crisis-induced facedown plays.
    """

    @staticmethod
    def perform_setup(engine, villain):
        """Forces Card ID 1 to the top of the Master Plan deck."""
        import random
        deck = getattr(villain, 'plan_deck', [])
        if not deck: return

        first_card = next((c for c in deck if c.get('id') == 1), None)
        if first_card:
            deck.remove(first_card)
            # 🚨 THE HELA PATTERN: Explicitly shuffle the remaining cards to guarantee randomness
            random.shuffle(deck)
            deck.insert(0, first_card)
        else:
            random.shuffle(deck)
            
        engine.log.append(Col.wrap(" 🦏 RAMPAGE BEGINS: Rhino is bracing for a charge!", Col.YLW))

    @staticmethod
    def handle_movement(engine, villain, card):
        """Calculates distance moved and stores it for the upcoming BAM."""
        move_val = card.get("move", 0)
        dist = 0

        if move_val == "cw":
            # Check if all conscious heroes are standing directly in front of him
            active_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False)]
            heroes_away = [h for h in active_heroes if h.location_index != villain.location_index]
            
            if active_heroes and not heroes_away:
                # THE LAP RULE: Everyone is here! Full 6-sector charge for maximum damage.
                dist = 6
            else:
                # Standard logic: find the nearest hero clockwise
                targets, move_dist = BoardNav.find_closest_hero(engine, villain.location_index, direction="cw", ignore_start_loc=True)
                dist = move_dist if move_dist else 0
        else:
            dist = int(move_val)

        if dist > 0:
            # Mathematical modulo ensures dist 6 lands him exactly where he started
            villain.location_index = (villain.location_index + dist) % 6
            loc_name = engine.locations[villain.location_index].name
            
            if dist == 6:
                engine.log.append(Col.wrap(f" 🏃 Rhino runs a massive lap to build momentum, returning to {loc_name}!", Col.YLW))
            else:
                engine.log.append(f" 🏃 Rhino charges through {dist} Locations to {loc_name}!")
        
        # Store distance for the BAM phase
        villain.last_move_dist = dist


    @staticmethod
    def on_bam(engine, villain):
        """BAM: Damage = Distance Moved. Also shifts hit heroes 1 sector CW."""
        v_idx = villain.location_index
        damage = getattr(villain, 'last_move_dist', 0)
        
        # 🚨 ARMOR FIX: getattr for list comprehension
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        
        if not targets:
            engine.log.append(Col.wrap(" 💥 Rhino slams into the scenery, but no heroes were in the way!", Col.WHT))
            return

        engine.log.append(Col.wrap(f" 💥 IMPACT: Rhino hits for {damage} damage and knocks heroes back!", Col.RED + Col.BOLD))
        
        for h in targets:
            # Capture state before damage is processed
            was_invincible = getattr(h, 'is_invincible', False)
            
            for _ in range(damage):
                h.take_damage(engine)
            
            # Only apply knockback if they actually took the hit
            if damage > 0 and not was_invincible:
                h.location_index = (h.location_index + 1) % 6
                new_loc = engine.locations[h.location_index].name
                engine.log.append(f"   🌪️ {h.name} is sent flying to {new_loc}!")
            elif damage > 0 and was_invincible:
                engine.log.append(Col.wrap(f"   🛡️ {h.name} anchors down and absorbs the charge!", Col.CYAN))

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Overflow acceleration: Plays a Master Plan card facedown."""
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: The chaos at {loc.name} accelerates Rhino's rampage!", Col.RED))
        BaseVillainLogic.add_plan_facedown(engine)

    @staticmethod
    def get_start_of_turn_modifiers(engine, hero, location):
        """
        RHINO: The Concussion Rule.
        Checks for Crisis tokens, clears them, and flags the turn for a facedown play.
        """
        mods = {"is_random": False, "ignore_prev": False, "label": "", "is_facedown": False}
        
        if getattr(hero, 'crisis_tokens', 0) > 0:
            mods["is_facedown"] = True
            mods["label"] = "CONCUSSED"
            
            # Clear tokens as the penalty is being 'paid' this turn
            hero.crisis_tokens = 0
            engine.log.append(Col.wrap(f" 😵 {hero.name.upper()} is Concussed! Card must be played facedown.", Col.PURP))
            
        return mods
        
    @staticmethod
    def handle_hero_ko(engine, hero):
        """RHINO EXCEPTION: No Revenge BAM. Instead, daze the hero with a Crisis Token."""
        
        # 1. Gatekeeper: Prevent double-triggers
        if getattr(hero, 'is_ko', False):
            return

        # 2. Officially mark the KO so the engine knows it's handled
        hero.is_ko = True
        
        # 3. Print the standard KO announcement
        engine.log.append(Col.wrap(f" 💀 {hero.name.upper()} IS KO'D!", Col.RED + Col.BOLD))

        # 4. Apply Rhino's specific penalty (Crisis Token instead of BAM)
        hero.crisis_tokens = getattr(hero, 'crisis_tokens', 0) + 1
        engine.log.append(Col.wrap(f" 😵 DAZED: {hero.name} is too rattled to focus!", Col.PURP))
        
    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Aleksei Sytsevich is a walking battering ram. He relies \n"
                "on pure kinetic energy and sheer mass. The longer his \n"
                "runway, the more devastating the impact."
            ),
            "rules": (
                "\"Concussive Blows\"\n"
                "Rhino doesn't follow up on a downed target like other \n"
                "threats. If he KOs a hero, he leaves them severely \n"
                "disoriented, granting a Crisis token instead of a BAM.\n\n"
                "If you start your turn with a Crisis token, you must play \n"
                "your action card FACEDOWN (blind) before discarding it."
            ),
            "bam": (
                "\"Momentum Strike\"\n"
                "Rhino deals damage to everyone in his sector equal to \n"
                "the number of locations he just crossed. Any hero who \n"
                "takes damage is violently launched one location clockwise."
            ),
            "overflow": (
                "\"Accelerated Chaos\"\n"
                "If a sector overruns with unplaceable tokens, the panic \n"
                "provides him cover. For every overflowing location, one \n"
                "Master Plan card is immediately played facedown."
            ),
            "threats": (
                "Expect Mercenaries and barricades.\n"
                "- Open Field: Taking damage here grants a Crisis token.\n"
                "- No Cover: Ending your turn here grants a Crisis token."
            )
        }
