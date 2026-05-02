# src/logic/villains/loki.py

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class LokiLogic(BaseVillainLogic):
    """
    LOKI: The God of Mischief.
    Features: Infinite HP scaling on overflow, invulnerability via Illusions, 
    and reactive damage via Master Tricksters.
    """

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """
        LOKI OVERRIDE: Boundless Regeneration.
        Each overflow grants +1 HP. There is no maximum cap.
        """
        engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: {location.name} capacity exceeded by {token_type}!", Col.RED))
        
        # Indefinite increase logic
        villain.hp += 1
        
        engine.log.append(Col.wrap(
            f" ✨ ILLUSIONARY HEALING: Loki's power grows! He is now at {villain.hp} HP! ", 
            Col.CYAN + Col.BOLD
        ))

    @staticmethod
    def handle_hero_ko(engine, hero):
        """LOKI OVERRIDE: Accelerated plot on KO."""
        # Actually call the base class to set the KO flag and queue the BAM!
        if getattr(hero, 'is_ko', False):
            return
            
        BaseVillainLogic.handle_hero_ko(engine, hero)
        
        # Now apply Loki's specific punishment
        engine.log.append(Col.wrap(f" 💀 {hero.name.upper()} FALLS FOR THE TRICK! ", Col.RED + Col.BOLD))
        LokiLogic.add_plan_facedown(engine)


    @staticmethod
    def broadcast_stance(engine):
        """Warns the player of Loki's illusionary shielding with atmospheric HUD text."""
        v = engine.villain
        is_shielded, _ = LokiLogic.is_villain_shielded(engine, v)
        
        if is_shielded:
            engine.log.append(Col.wrap(" Loki is hidden behind an Illusion! ", Col.YLW))

    @staticmethod
    def is_villain_shielded(engine, villain):
        """LOKI PROTECTION: Invulnerable if at an 'illusion' location."""
        loc = engine.locations[villain.location_index]
        if loc.threat and not loc.threat.cleared:
            # Check id_internal first, then fallback to id
            t_id = getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', None))
            
            # Use 'in' check or .startswith if your IDs have numbers (like illusion_1)
            if t_id and "illusion" in t_id:
                return True, " ✨ LOKI: You strike only at a shadow! "
        return False, ""

    @staticmethod
    def on_damage_taken(engine, villain, amount):
        """
        MASTER TRICKSTER: Damage Reflection.
        Triggered reactively when Loki takes 1+ damage.
        """
        loc = engine.locations[villain.location_index]
        
        # 1. Check if the threat exists and isn't cleared
        if loc.threat and not loc.threat.cleared:
            # 2. Use the 'in' check to catch 'master_trickster_1' or 'master_trickster_2'
            # We check both id_internal and id to be safe
            t_id = getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', ""))
            
            if t_id and "master_trickster" in t_id and amount > 0:
                engine.log.append(Col.wrap(" 🃏 MASTER TRICKSTER: Loki strikes back! ", Col.MAGENTA))
                
                for h in engine.heroes:
                    # 3. Only punish heroes at Loki's current location
                    if h.location_index == villain.location_index and not h.is_ko:
                        # Using your confirmed working method
                        h.take_damage(engine) 
                        engine.log.append(Col.wrap(f"       💥 {h.name} hit by the counter-attack! ", Col.RED))

    @staticmethod
    def resolve_threat_bam(engine, threat, location_index):
        """
        LOKI OVERRIDE: Handles Frost Giants via Base logic and allows for future unique BAMs.
        """
        t_id = getattr(threat, 'id_internal', getattr(threat, 'id', None))

        # We keep this method to allow for any 'Unique' Loki-specific BAM logic.
        # Currently, Frost Giant is 'standard' damage, so it falls back to BaseVillainLogic.
        if t_id == "frost_giant":
            # Calling the super class handles the light_damage_bam (1 DMG) logic automatically
            super(LokiLogic, LokiLogic).resolve_threat_bam(engine, threat, location_index)
        else:
            # Catch-all for any other threats using standard damage IDs
            super(LokiLogic, LokiLogic).resolve_threat_bam(engine, threat, location_index)

    @staticmethod
    def resolve_special(engine, villain, card):
        """LOKI SPECIALS: Sorcery, Spread Discord, and Master of Illusions."""
        sid = card.get("special_id")
        
        if sid in ["sorcery", "spread_discord"]:
            engine.log.append(Col.wrap(f" ✨ LOKI casts {card.get('display_name').upper()}! ", Col.MAGENTA))
            
            targets_hit = 0
            
            for h in engine.heroes:
                if h.is_ko: continue
                
                alone = LokiLogic.is_hero_alone(engine, h)
                
                # Determine if this specific hero is a target based on the card
                # Sorcery hits heroes who are alone; Spread Discord hits heroes who are NOT alone.
                is_target = (sid == "sorcery" and alone) or (sid == "spread_discord" and not alone)
                
                if is_target:
                    # Log the hit BEFORE applying the damage so the sequence reads correctly
                    engine.log.append(Col.wrap(f"       💥 {h.name} hit by the trick! ", Col.RED))
                    h.take_damage(engine)
                    targets_hit += 1

            # ACCELERATION: If the spell whiffed entirely, speed up the deck
            if targets_hit == 0:
                engine.log.append(Col.wrap(" 🌪️ The spell finds no targets, but the plot accelerates! ", Col.YLW))
                LokiLogic.add_plan_facedown(engine)

        elif sid == "master_of_illusions":
            engine.log.append(Col.wrap(" 🎭 MASTER OF ILLUSIONS: Loki vanishes into the mist! ", Col.MAGENTA))
            
            # Find nearest clockwise location with an 'illusion' threat
            found_new_home = False
            for i in range(1, 6):
                check_idx = (villain.location_index + i) % 6
                loc = engine.locations[check_idx]
                
                if loc.threat and not loc.threat.cleared:
                    t_id = getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', None))
                    if t_id == "illusion":
                        villain.location_index = check_idx
                        engine.log.append(Col.wrap(f" ✨ Loki reappears at {loc.name}, hidden by a new illusion!", Col.CYAN))
                        found_new_home = True
                        break
            
            if not found_new_home:
                engine.log.append(Col.wrap(" 💨 No Illusions remain! Loki is forced to stay put. ", Col.WHT))
