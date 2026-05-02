from src.utils.helpers import Col, ICON

def get_action_details(engine, hero, action_type, action_id=None):
    """ 
    Standard Cost System: Handles flat cost increases for common threats.
    These are 'Global Rules' that apply regardless of the specific villain logic.
    """
    loc = engine.locations[hero.location_index]
    v_id = engine.villain.internal_id.lower()
    cost = 1
    warning = None
    
    if not loc.threat or loc.threat.cleared:
        return cost, warning

    threat_name = loc.threat.name.upper()
    tid = (getattr(loc.threat, 'id_internal', loc.threat.id) or "").lower()

    # 🏃 MOVEMENT TAXES
    if action_type == "move" and tid == "move_trap" and action_id in ["mc", "mcc"]:
        cost = 2
        warning = f" 🚫 {threat_name}: 2 {ICON['move']} required to break away!"
        
    # ✸ ATTACK TAXES
    elif action_type == "attack" and action_id == "m":
        if "chitauri" in tid:
            cost = 3
            warning = f" 🛡️ {threat_name}: Alien tech shrugs off the blow!"
        elif tid == "elite_troops":
            cost = 2
            # Thematic context for the same mechanical tax
            if v_id == "kingpin": warning = f" 🕴️ {threat_name}: Fisk's enforcers are heavily armored!"
            elif v_id == "red_skull": warning = f" 🐙 {threat_name}: Hydra fanatics fight with suicidal resolve!"
            elif v_id == "ultron": warning = f" 🤖 {threat_name}: Drones reinforced with secondary plating!"
            else: warning = f" 🛡️ {threat_name}: Elite armor requires extra force!"
            
    # ★ HEROIC TAXES
    elif action_type == "heroic" and tid == "heroic_trap" and action_id == "c":
        cost = 2
        warning = f" 🆘 {threat_name}: 2 {ICON['heroic']} required to extract civilians!"

    return cost, warning

def apply_action_modifiers(engine, hero, pool):
    """ 
    The Public Entry Point (The Axle).
    Universal dispatcher that handles one-time taxes and unique states.
    """
    # 🛡️ THE IMMUNITY GATE: Prevents infinite tax loops during action resolution
    if not hasattr(hero, 'tax_paid_this_turn'):
        hero.tax_paid_this_turn = False

    if getattr(hero, 'tax_paid_this_turn', False):
        # Even if we skip the logic, we still check Rhino's Concussion 
        # because that's an 'Active State' check, not a 'Tax'.
        _handle_rhino_concussion(engine, hero, pool)
        return # 🚨 We exit here so Power-Ups don't double-trigger during action loops!

    # 🎯 DYNAMIC CALL: Let the Villain's own Logic file handle its niche taxes
    v_logic = engine.villain_logic
    if hasattr(v_logic, 'apply_action_tax'):
        v_logic.apply_action_tax(engine, hero, pool)
        hero.tax_paid_this_turn = True

    # 3. RHINO: Concussion (Facedown Penalty)
    _handle_rhino_concussion(engine, hero, pool)

    # 🔌 THE INVISIBLE HOOK: Mode Passives (Power-Ups)
    # This only fires on the initial Phase 6 pool generation.
    mode = getattr(engine, 'mode_handler', None)
    if mode and hasattr(mode, 'apply_passives'):
        mode.apply_passives(engine, hero, pool)

def _handle_rhino_concussion(engine, hero, pool):
    """ Check if the hero is dazed. Does not count as a 'Paid Tax'. """
    last_card = engine.storyline.cards[-1] if engine.storyline.cards else None
    if last_card and last_card.get('is_facedown'):
        # Concussion provides no actions, but doesn't stop you from using stashed tokens
        engine.log.append(Col.wrap(" 😵 CONCUSSED: This turn's card provides no actions!", Col.PURP))

def apply_zemo_interference(engine, hero, card):
    """ 
    Zemo's Crisis Mechanic (Inheritance Sabotage).
    At the end of the turn, Crisis tokens cover symbols on the played card.
    The player chooses which symbols are covered, affecting the next hero's inheritance.
    """
    from src.utils.helpers import Col, ICON
    
    if getattr(engine.villain, 'internal_id', '') != 'baron_zemo':
        return 

    crisis_count = getattr(hero, 'crisis_tokens', 0)
    if crisis_count <= 0:
        return

    actions = card.get('actions', [])
    if not actions:
        return 
        
    engine.log.append(Col.wrap(f"\n --- ⚠️ CRISIS INTERFERENCE --- ", Col.RED))

    # Calculate the maximum tokens we can actually burn this turn
    symbols_to_cover = min(crisis_count, len(actions))
    
    for _ in range(symbols_to_cover):
        # If remaining symbols are identical, no choice is necessary
        if len(set(actions)) == 1:
            removed = actions.pop()
            engine.log.append(Col.wrap(f"   (Auto-covered {ICON.get(removed, removed)})", Col.DARK_GRAY))
        else:
            # 🔌 UI ADAPTER: Player choice required
            print(f"\n {Col.wrap('⚠️ CRISIS TOKEN EFFECT:', Col.RED)} You must cover a symbol on your card.")
            print(" Which symbol will you cover (forfeit for the next player)?")
            for i, act in enumerate(actions, 1):
                print(f" [{i}] {ICON.get(act, act)}")
            
            choice_idx = engine.ui.ask_choice(" >> ", 1, len(actions)) - 1
            removed = actions.pop(choice_idx)
            engine.log.append(Col.wrap(f"   (Player covered {ICON.get(removed, removed)})", Col.DARK_GRAY))
        
    hero.crisis_tokens -= symbols_to_cover
    
    engine.log.append(Col.wrap(f" ⚠️ Zemo's interference covered {symbols_to_cover} symbol(s) on {hero.name}'s card!", Col.RED + Col.BOLD))
    
    if hero.crisis_tokens > 0:
        engine.log.append(Col.wrap(f"   ( {hero.crisis_tokens} Crisis token(s) remain on {hero.name} )", Col.YLW))
    else:
        engine.log.append(Col.wrap(f"   ( {hero.name} is free of Crisis tokens! )", Col.GRN))

