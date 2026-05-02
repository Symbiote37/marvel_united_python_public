# src/logic/shield_logic.py

def is_target_vulnerable(engine, target_obj):
    """
    The Gatekeeper: Determines if a Villain or Henchman is currently damageable.
    Checks Missions first, then special Villain shielding, then Henchmen auras.
    """
    
    # 1. THE VILLAIN GATE
    if hasattr(target_obj, 'plan_deck'): 
        # 🚨 THE DARK DIMENSION EXCEPTION
        if engine.villain.internal_id == "dormammu":
            return False, f" 🛡️ {target_obj.name.upper()} is IMMUNE to physical damage! "

        # A. Universal Mission Check (Must complete 2/3)
        completed = 0
        for key in ['civilians', 'thugs', 'threats']:
            current = engine.missions.get(key, 0)
            target = engine.missions.get(f"{key}_max", 9)
            if current >= target:
                completed += 1
        
        if completed < 2:
            return False, f" 🛡️ {target_obj.name.upper()} is INVULNERABLE! (Missions: {completed}/2) "
        
        # B. Threat-Based Invulnerability (Loki Illusions / Time Paradox / etc.)
        logic = engine.villain_logic
        if hasattr(logic, "is_villain_shielded"):
            is_shielded, message = logic.is_villain_shielded(engine, target_obj)
            if is_shielded:
                return False, message
        
        return True, ""
    
    # 2. THE HENCHMEN GATE (Team-Based Shielding)
    else:
        # Check all locations for an uncleared 'Masters of Evil' style threat
        moe_active = any(
            loc.threat and not loc.threat.cleared and 
            getattr(loc.threat, 'id_internal', loc.threat.id) == "masters_of_evil" 
            for loc in engine.locations
        )

        if moe_active:
            # The 'Masters of Evil' card itself is never protected by its own rule
            target_id = getattr(target_obj, 'id_internal', getattr(target_obj, 'id', None))
            if target_id != "masters_of_evil":
                return False, f"   🛡️ {target_obj.name.upper()} protected by the Masters of Evil!"

    return True, ""
