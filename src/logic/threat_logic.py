# [Target: src/logic/threat_logic.py]
from src.utils.helpers import Col

class ThreatLogic:
    @staticmethod
    def resolve_sot_passives(engine, hero, location):
        """Phase 1: Start of Turn (SOT). Returns dict of state modifiers."""
        # Start by fetching unique Villain modifiers (like Rhino's Concussion)
        mods = engine.villain_logic.get_start_of_turn_modifiers(engine, hero, location)
        
        # 2. PASSIVE THREAT Check
        if not location.threat or location.threat.cleared:
            return mods

        t_id = (getattr(location.threat, 'id_internal', None) or location.threat.id).lower()
        
        if t_id == "debilitating_torture":
            engine.log.append(Col.wrap(" ⛓️ DEBILITATING TORTURE: You cannot focus on your ally's lead!", Col.RED))
            mods["ignore_prev"] = True

        elif t_id == "space_ambush":
            engine.log.append(Col.wrap(f" ⚠️ SPACE AMBUSH: {hero.name} is caught in a Kree crossfire at {location.name}! (1 DMG)", Col.RED))
            hero.take_damage(engine)

        elif t_id == "bob_hydra":
            msg = Col.wrap(f" {location.threat.name} harasses {hero.name}!", Col.YLW)
            engine.log.append(msg)
            hero.crisis_tokens = getattr(hero, 'crisis_tokens', 0) + 1

        return mods

    @staticmethod
    def resolve_eot_passives(engine, hero, location):
        """Phase 2: End of Turn (EOT). Resolves location-based and global threats."""
        
        t_id = None
        if location.threat and not location.threat.cleared:
            t_id = (getattr(location.threat, 'id_internal', None) or location.threat.id).lower()

        # 1. TOKEN HAZARDS (Crisis/Tokens)
        if t_id == "no_cover":
            engine.log.append(Col.wrap(f" 🏗️ NO COVER: {hero.name} is exposed at {location.name}! (+1 Crisis)", Col.YLW))
            hero.crisis_tokens = getattr(hero, 'crisis_tokens', 0) + 1
            
        elif t_id == "shapeshifting":
            engine.log.append(Col.wrap(f" 🦠 SHAPESHIFTING: {hero.name} is ambushed by the Symbiote at {location.name}!", Col.PURP))
            hero.crisis_tokens = getattr(hero, 'crisis_tokens', 0) + 1
            if engine.villain.internal_id == "venom":
                from src.logic.villains.venom import VenomLogic
                VenomLogic.check_assimilation(engine)

        # 2. DIRECT DAMAGE HAZARDS (EOT)
        # Includes Hidden Traps (Corvus) along with Assassination/Elemental Control
        if t_id in ["assassination_attempt", "elemental_control", "hidden_traps"]:
            msg_map = {
                "assassination_attempt": "🎯 ASSASSINATION ATTEMPT: Assassins strike",
                "elemental_control": "🔥 ELEMENTAL CONTROL: Dormammu's fire burns",
                "hidden_traps": "⚔️ HIDDEN TRAPS: Corvus's traps spring on"
            }
            engine.log.append(Col.wrap(f" {msg_map[t_id]} {hero.name} at {location.name}! (1 DMG)", Col.RED))
            hero.take_damage(engine)
            
        # Global Check: Time Army (Triggered by thugs in the current sector)
        if location.thugs > 0:
            is_army_active = any(
                l.threat and not l.threat.cleared and 
                (getattr(l.threat, 'id_internal', None) or l.threat.id).lower() == "time_army"
                for l in engine.locations
            )
            
            if is_army_active:
                alert = Col.wrap(f" ⚔️ TIME ARMY: Kang's reinforcements ambush {hero.name} at {location.name}!", Col.RED)
                engine.log.append(alert)
                print(f"\n{alert}")
                hero.take_damage(engine)

        return {}