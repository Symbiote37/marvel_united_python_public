from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col
from src.utils.navigation import BoardNav

class HelaLogic(BaseVillainLogic):
    """
    HELA: The Goddess of Death.
    Features: Starts out of play (Banished), protected by Fenris Wolf, 
    and raises armies while inflicting multi-token Threats.
    """

    @staticmethod
    def perform_setup(engine, villain):
        """
        HELA OVERRIDE: Banishment.
        """
        import random
        deck = getattr(villain, 'plan_deck', [])
        if not deck: return

        banished_card = next((c for c in deck if c.get("special_id") == "banished"), None)
        if banished_card:
            deck.remove(banished_card)
            random.shuffle(deck)
            deck.insert(0, banished_card)
        else:
            random.shuffle(deck)

        villain.is_in_play = False
        villain.location_index = -1
        engine.log.append(Col.wrap(" 🌌 HELA is banished... but her influence seeps into the realm.", Col.MAGENTA))

    @staticmethod
    def check_custom_game_status(engine):
        """
        HELA'S VILLAINOUS PLOT:
        If all heroes are KO'd at the same time, Hela wins instantly.
        """
        # Check if every active hero on the board is currently KO'd
        all_ko = all(getattr(h, 'is_ko', False) for h in engine.heroes if not getattr(h, 'is_eliminated', False))
        
        if all_ko:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "VILLAINOUS PLOT: Hela has claimed all souls! All heroes are KO'd simultaneously."
            return True # Signals the engine to halt immediately
            
        return False

    @staticmethod
    def broadcast_stance(engine):
        v = engine.villain
        if not getattr(v, 'is_in_play', False):
            return
            
        is_shielded, _ = HelaLogic.is_villain_shielded(engine, v)
        if is_shielded:
            engine.log.append(Col.wrap(" Fenris Wolf stands guard! Hela cannot be harmed!", Col.YLW))

    @staticmethod
    def is_villain_shielded(engine, villain):
        """HELA PROTECTION: Invulnerable if Fenris Wolf is in play."""
        for loc in engine.locations:
            if loc.threat and not loc.threat.cleared:
                t_id = (getattr(loc.threat, 'id_internal', None) or getattr(loc.threat, 'id', "")).lower()
                if t_id == "fenris_wolf":
                    return True, " 🛡️ HELA: Fenris Wolf stands guard! She cannot be harmed! "
        return False, ""

    @staticmethod
    def on_bam(engine, villain, damage=1):
        """
        HELA OVERRIDE: Manifestation.
        """
        if not getattr(villain, 'is_in_play', False):
            villain.is_in_play = True
            
            # 🚨 THE FIX: Hela manifests directly at the hero with the most cards
            max_cards = -1
            target_hero = None
            
            for h in engine.heroes:
                if getattr(h, 'is_ko', False): continue
                
                hand_size = len(getattr(h, 'hand', []))
                if hand_size > max_cards:
                    max_cards = hand_size
                    target_hero = h
                    
            if target_hero:
                villain.location_index = target_hero.location_index
            else:
                villain.location_index = 0 # Absolute fallback if everyone is KO'd
                
            loc_name = engine.locations[villain.location_index].name
            engine.log.append(Col.wrap(f" 💥 HELA manifests from the Hel-realm directly at {loc_name}! ", Col.MAGENTA + Col.BOLD))
            
        # Standard BAM logic (Now armored via BaseVillainLogic)
        BaseVillainLogic.on_bam(engine, villain, damage)

    @staticmethod
    def resolve_threat_bam(engine, threat, location_index):
        t_id = (getattr(threat, 'id_internal', None) or getattr(threat, 'id', "")).lower()

        if "necroswords" in t_id:
            loc = engine.locations[location_index]
            dmg = 2 if getattr(loc, 'thugs', 0) > 0 else 1
            
            # 🚨 THE ANTI-SPAM CHECK: Only log and strike if a conscious hero is actually present
            targets = [h for h in engine.heroes if h.location_index == location_index and not getattr(h, 'is_ko', False)]
            if targets:
                engine.log.append(Col.wrap(f" ⚔️ NECROSWORDS strikes at {loc.name}! ", Col.RED))
                BaseVillainLogic._hit_sector(engine, location_index, dmg, "Necroswords", single_target=True)
            
        else:
            BaseVillainLogic.resolve_threat_bam(engine, threat, location_index)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        fenris_threat = None
        for l in engine.locations:
            if l.threat and not l.threat.cleared:
                t_id = (getattr(l.threat, 'id_internal', None) or getattr(l.threat, 'id', "")).lower()
                if t_id == "fenris_wolf":
                    fenris_threat = l.threat
                    break
                    
        if fenris_threat:
            fenris_threat.hp = getattr(fenris_threat, 'hp', 0) + 1
            engine.log.append(Col.wrap(f" ⚠️ OVERFLOW: Fenris Wolf feeds! He gains +1 HP! (Total: {fenris_threat.hp})", Col.RED + Col.BOLD))
        else:
            success = BaseVillainLogic.restore_defeated_threat(engine, villain, "necroswords", max_copies=5)
            if not success:
                engine.log.append(Col.wrap(" ⚠️ OVERFLOW: Hela attempts to summon a Necrosword, but none are defeated!", Col.YLW))

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "banished":
            engine.log.append(Col.wrap(" 🌌 The prophecy of Hela's return begins to unfold... ", Col.MAGENTA))
            
        elif sid == "raise_undead_army":
            engine.log.append(Col.wrap(" 💀 RAISE UNDEAD ARMY: Hela summons her forces! ", Col.MAGENTA))
            
            from src.systems.token_system import TokenSystem
            
            # 🚨 THE FIX: One Source of Truth. TokenSystem natively handles the capacity check, 
            # discards the excess, and uses the tracker to enforce a max of 1 overflow per location!
            overflow_tracker = set()
            for i in range(len(engine.locations)):
                for _ in range(2):
                    TokenSystem.add_token(engine, i, "thugs", overflow_tracker)
                
            fenris_exists = False
            for loc in engine.locations:
                if loc.threat and not loc.threat.cleared:
                    t_id = (getattr(loc.threat, 'id_internal', None) or getattr(loc.threat, 'id', "")).lower()
                    if t_id == "fenris_wolf":
                        fenris_exists = True
                        break

    @staticmethod
    def handle_movement(engine, villain, card):
        """HELA OVERRIDE: Predatory Movement."""
        if not getattr(villain, 'is_in_play', False) or card.get("special_id"):
            return

        from src.utils.navigation import BoardNav
        
        max_cards = -1
        target_hero = None
        target_dist = 999
        
        for h in engine.heroes:
            # 🚨 ARMOR FIX: Safely check KO status
            if getattr(h, 'is_ko', False): continue
            
            hand_size = len(getattr(h, 'hand', []))
            dist = BoardNav.get_distance(villain.location_index, h.location_index, direction="cw")
            
            if hand_size > max_cards:
                max_cards = hand_size
                target_hero = h
                target_dist = dist
            elif hand_size == max_cards:
                if dist < target_dist:
                    target_hero = h
                    target_dist = dist
                    
        if target_hero:
            villain.location_index = target_hero.location_index
            loc_name = engine.locations[villain.location_index].name
            engine.log.append(Col.wrap(f" 💨 HELA senses a powerful soul! She teleports to {loc_name} to confront {target_hero.name}!", Col.MAGENTA))
