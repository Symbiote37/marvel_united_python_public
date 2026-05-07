# [Target: src/logic/villains/ebony_maw.py]

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col
import random

class EbonyMawLogic(BaseVillainLogic):
    """
    EBONY MAW: The Master of Whispers.
    Features: Crisis tokens that force random plays (Psychological Pressure), 
    and Genius Intellect which accelerates the Master Plan.
    """

    @staticmethod
    def handle_movement(engine, villain, card):
        """STEP 1: The Glide (Mental Scan)"""
        if card.get('special_id') == "manipulation":
            from src.utils.navigation import BoardNav
            best_idx, count = BoardNav.find_hero_concentration(
                engine, villain.location_index, ignore_start_loc=False
            )
            
            if best_idx is not None and best_idx != villain.location_index:
                villain.location_index = best_idx
                loc_name = engine.locations[best_idx].name
                engine.log.append(Col.wrap(f" 💨 MANIPULATION: Maw glides to the most minds at {loc_name}! ", Col.MAGENTA))

    @staticmethod
    def on_bam(engine, villain, damage=1):
        """STEP 3: The Psychic Invasion"""
        v_idx = villain.location_index
        if v_idx == -1: return
        
        # 🚨 ARMOR FIX: getattr for is_ko
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        if targets:
            engine.log.append(Col.wrap(f" 💥 BAM: Ebony Maw invades the minds at {engine.locations[v_idx].name}! ", Col.RED))
            for h in targets:
                h.take_damage(engine)
                h.crisis_tokens = getattr(h, 'crisis_tokens', 0) + 1
                engine.log.append(f"   [BAM] 🧠 {h.name} takes 1 Crisis token. ")

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Isolated Overflow: Only affects the specific location. """
        BaseVillainLogic.on_overflow(engine, villain, loc, t_type)
        loc_idx = engine.locations.index(loc)
        for h in engine.heroes:
            # 🚨 ARMOR FIX: getattr for is_ko
            if h.location_index == loc_idx and not getattr(h, 'is_ko', False):
                h.crisis_tokens = getattr(h, 'crisis_tokens', 0) + 1
                engine.log.append(Col.wrap(f"   [OVERFLOW] 🧠 {h.name} is overwhelmed! (+1 Crisis)", Col.YLW))

    @staticmethod
    def resolve_special(engine, villain, card):
        """STEP 5: The Payload (Whispers of Darkness)"""
        sid = card.get("special_id")
        
        if sid == "genius_intellect":
            total_crisis = sum(getattr(h, 'crisis_tokens', 0) for h in engine.heroes)
            engine.log.append(Col.wrap(f" 🧠 GENIUS INTELLECT: Maw foresees your moves! (Extra Plans: {total_crisis})", Col.MAGENTA))
            
            # 🛡️ DEFENSIVE FIX: Initialize the queue if missing and guard against 0-loops
            if total_crisis > 0:
                if not hasattr(engine, 'queued_events'): 
                    engine.queued_events = []
                
                for _ in range(total_crisis):
                    engine.queued_events.append({"type": "extra_card"})

        elif sid == "manipulation":
            v_idx = villain.location_index
            engine.log.append(Col.wrap(" 🗣️ MANIPULATION: Maw whispers dark truths... ", Col.MAGENTA))
            for h in engine.heroes:
                # 🚨 ARMOR FIX: getattr for is_ko
                if h.location_index == v_idx and not getattr(h, 'is_ko', False):
                    h.crisis_tokens = getattr(h, 'crisis_tokens', 0) + 1
                    engine.log.append(f"   [MANIPULATION] 🧠 {h.name} takes 1 Crisis token. ")

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        """STEP 2: Location-Based Triggers"""
        t_id = (getattr(threat, 'id_internal', None) or threat.id).lower()
        
        if t_id == "persuasion":
            found_hero = False
            for h in engine.heroes:
                # 🚨 ARMOR FIX: getattr for is_ko
                if h.location_index == loc_idx and not getattr(h, 'is_ko', False):
                    h.crisis_tokens = getattr(h, 'crisis_tokens', 0) + 1
                    engine.log.append(Col.wrap(f"   [PERSUASION] 🧠 {h.name} takes 1 Crisis token. ", Col.YLW))
                    found_hero = True
            
            if not found_hero:
                engine.log.append(Col.wrap("   🗣️ PERSUASION: No heroes present. Maw accelerates his plans! ", Col.MAGENTA))
                
                # Use a one-liner for the list initialization for cleanliness
                if not hasattr(engine, 'queued_events'): engine.queued_events = []
                engine.queued_events.append({"type": "extra_card"})

        elif t_id == "telekinesis":
            engine.log.append(Col.wrap(" 🌌 TELEKINESIS: Debris flies everywhere! ", Col.RED))
            for offset in [-1, 0, 1]:
                idx = (loc_idx + offset) % 6
                BaseVillainLogic._hit_sector(engine, idx, 1, "Telekinesis")

    @staticmethod
    def get_start_of_turn_modifiers(engine, hero, location):
        mods = {"is_random": False, "ignore_prev": False, "label": ""}
        
        # Psychological Pressure check
        crisis_count = getattr(hero, 'crisis_tokens', 0)
        if crisis_count > 0:
            mods["is_random"] = True
            mods["label"] = "PSYCHOLOGICAL PRESSURE"
            # Deduct the token after the effect is flagged
            hero.crisis_tokens -= 1
            engine.log.append(Col.wrap(f" 🧠 PSYCHOLOGICAL PRESSURE: Your mind fractures! ", Col.YLW))
            
        return mods
        
    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Ebony Maw is the telekinetic and telepathic mastermind of the \n"
                "Black Order. He avoids physical confrontation, preferring to \n"
                "break the minds of his enemies and turn their plans into chaos."
            ),
            "rules": (
                "\"Psychological Pressure & Genius Intellect\"\n"
                "Maw's Crisis tokens represent severe mental strain. If you start \n"
                "your turn with a Crisis token, your mind fractures: you are FORCED \n"
                "to play a card completely at random from your hand, discarding 1 \n"
                "token afterward.\n\n"
                "Do not hoard these tokens. His 'Genius Intellect' Master Plan card \n"
                "allows him to play an EXTRA Master Plan card for EVERY Crisis token \n"
                "currently on the board. This can cascade into an instant loss."
            ),
            "bam": (
                "\"Psychic Invasion\"\n"
                "Maw invades the minds of anyone too close. He deals 1 damage \n"
                "AND grants 1 Crisis token to every hero in his current location."
            ),
            "overflow": (
                "\"Mental Overload\"\n"
                "When a sector collapses into chaos, the psychic noise is deafening. \n"
                "Every hero standing in an overflowing location takes 1 Crisis token."
            ),
            "threats": (
                "His psychic constructs completely disrupt team cohesion.\n"
                "- Debilitating Torture: Amnesia. You ignore all inherited actions here.\n"
                "- Persuasion: Grants Crisis tokens to heroes. If left unattended \n"
                "  (no heroes present), it forces an extra Master Plan card play!\n"
                "- Telekinesis: Flying debris damages this and both adjacent locations."
            )
        }
