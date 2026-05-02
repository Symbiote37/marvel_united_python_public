import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class GreenGoblinLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "OSCORP TAKEOVER"
        villain.plot_max = 6 
        villain.plot_value = 0
        villain.hostages = 0
        villain.formulas_active = 0
        
        villain.threat_pool = []
        for loc in engine.locations:
            if loc.threat:
                loc.threat.cleared = False
                villain.threat_pool.append(loc.threat)
                loc.threat = None
                
        random.shuffle(villain.threat_pool)
        engine.log.append(Col.wrap(" 🎃 GREEN GOBLIN: 'Out, am I?!'", Col.RED + Col.BOLD))

    @staticmethod
    def reduce_damage(engine, target_obj, amount, is_action=False):
        if target_obj != engine.villain:
            return amount

        if getattr(target_obj, 'hostages', 0) > 0:
            engine.log.append(Col.wrap("   🛡️ HOSTAGE SHIELD: Goblin uses a civilian to block the attack! ", Col.YLW))
            return 0
            
        loc = engine.locations[target_obj.location_index]
        # 🛡️ STATE ARMOR
        t_id = (getattr(loc.threat, 'id_internal', None) or getattr(loc.threat, 'id', '') or '').lower()
        has_civ_shield = loc.threat and not loc.threat.cleared and "civilian_shield" in t_id
        if has_civ_shield and getattr(loc, 'civilians', 0) > 0:
            engine.log.append(Col.wrap(f"   🛡️ CIVILIAN SHIELD: The crowd protects Goblin! (0 DMG)", Col.YLW))
            return 0

        return amount

    @staticmethod
    def get_extra_heroic_options(engine, loc, hero):
        opts = []
        if hero.location_index == engine.villain.location_index and getattr(engine.villain, 'hostages', 0) > 0:
            opts.append({
                "label": "Rescue Hostage", 
                "id": "rescue_hostage",
                "cost": 2,
                "execute": lambda e: GreenGoblinLogic.execute_hostage_rescue(e, hero)
            })
        return opts

    @staticmethod
    def execute_hostage_rescue(engine, hero):
        # 🚨 DECOUPLING FIX: Use MissionSystem
        from src.systems.mission_system import MissionSystem
        
        engine.villain.hostages -= 1
        MissionSystem.increment_mission(engine, "civilians")
        engine.log.append(Col.wrap(f"   🦸 {hero.name} rescued a hostage from Goblin's glider! ", Col.CYAN))
        return True

    @staticmethod
    def draw_and_place_threat(engine, start_idx):
        villain = engine.villain
        if not villain.threat_pool:
            return 
            
        target_idx = -1
        for i in range(1, 7):
            check_idx = (start_idx + i) % 6
            loc = engine.locations[check_idx]
            if not loc.threat or loc.threat.cleared:
                target_idx = check_idx
                break
                
        if target_idx != -1:
            target_loc = engine.locations[target_idx]
            new_threat = villain.threat_pool.pop(0)
            
            if hasattr(new_threat, 'hp_max'):
                new_threat.hp = new_threat.hp_max
            elif hasattr(new_threat, 'base_hp'):
                new_threat.hp = new_threat.base_hp
                
            new_threat.cleared = False
            new_threat.just_placed_this_turn = engine.turn_count 
            
            target_loc.threat = new_threat
            engine.log.append(Col.wrap(f"   🎃 THREAT DEPLOYED: {new_threat.name} appears at {target_loc.name}!", Col.PURP))
            
            t_id = (getattr(new_threat, 'id_internal', None) or getattr(new_threat, 'id', '') or '').lower()
            t_name = (getattr(new_threat, 'name', '') or '').lower()
            
            if "elite_troops" in t_id or "corporate thugs" in t_name:
                from src.systems.token_system import TokenSystem
                TokenSystem.add_token(engine, target_idx, "thugs", set())
                
            active_threats = sum(1 for l in engine.locations if l.threat and not l.threat.cleared)
            engine.villain.plot_value = active_threats
            if active_threats >= 6:
                engine.game_over = True
                engine.victory_status = "VILLAIN_WINS"
                engine.loss_reason = "OSCORP TAKEOVER: Green Goblin controls all locations!"

    @staticmethod
    def on_threat_defeated(engine, threat):
        threat.cleared = True
        engine.villain.threat_pool.append(threat)
        random.shuffle(engine.villain.threat_pool)
        
        active_threats = sum(1 for l in engine.locations if l.threat and not l.threat.cleared)
        engine.villain.plot_value = active_threats

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return

        v_loc = engine.locations[v_idx]
        # 🛡️ STATE ARMOR
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        
        total_dmg = damage + getattr(villain, 'formulas_active', 0)
        
        if not targets:
            engine.log.append(Col.wrap(f"   💥 BAM! Goblin bombs {v_loc.name} but misses!", Col.RED))
        else:
            engine.log.append(Col.wrap(f"   💥 BAM! Goblin bombs {v_loc.name}! ({total_dmg} DMG)", Col.RED + Col.BOLD))
            for h in targets:
                engine.log.append(Col.wrap(f"   🎯 Pumpkin Bomb hits {h.name}!", Col.RED))
                for _ in range(total_dmg):
                    h.take_damage(engine)
                    
        GreenGoblinLogic.draw_and_place_threat(engine, v_idx)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        engine.log.append(Col.wrap(f"   ! OVERFLOW: Panic at {loc.name}!", Col.RED))
        try:
            idx = engine.locations.index(loc)
            GreenGoblinLogic.draw_and_place_threat(engine, idx)
        except ValueError:
            pass

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "goblin_formula":
            villain.formulas_active = getattr(villain, 'formulas_active', 0) + 1
            villain.hp += 1
            engine.log.append(Col.wrap(f"   🧪 GOBLIN FORMULA: +1 Max HP (Now {villain.hp}) and +1 BAM Damage!", Col.GRN))
            
        elif sid == "kidnap":
            loc = engine.locations[villain.location_index]
            if getattr(loc, 'civilians', 0) > 0:
                loc.civilians -= 1
                villain.hostages = getattr(villain, 'hostages', 0) + 1
                engine.log.append(Col.wrap(f"   🎃 KIDNAP: Goblin snatches a Civilian! (Hostages: {villain.hostages}) ", Col.PURP))

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        if getattr(threat, 'just_placed_this_turn', -1) == engine.turn_count:
            return
            
        t_id = (getattr(threat, 'id_internal', '') or threat.id).lower()

        if "electro" in t_id:
            engine.log.append(Col.wrap(f" ⚡ ELECTRO: Discharges!", Col.YLW))
            for offset in [-1, 1]:
                adj_idx = (loc_idx + offset) % 6
                BaseVillainLogic._hit_sector(engine, adj_idx, 1, "Electro's lightning", single_target=False)

        elif "kraven" in t_id:
            moved = False
            for i in range(1, 7):
                check_idx = (loc_idx + i) % 6
                target_loc = engine.locations[check_idx]
                
                has_heroes = any(h.location_index == check_idx and not getattr(h, 'is_ko', False) for h in engine.heroes)
                is_open = (not target_loc.threat) or getattr(target_loc.threat, 'cleared', False)
                
                if has_heroes and is_open:
                    target_loc.threat = threat
                    engine.locations[loc_idx].threat = None
                    engine.log.append(Col.wrap(f" 🐅 KRAVEN (Threat): Tracks prey to {target_loc.name}!", Col.YLW))
                    BaseVillainLogic._hit_sector(engine, check_idx, 1, "Kraven's strike", single_target=False)
                    moved = True
                    break
            
            if not moved:
                engine.log.append(Col.wrap(f" 🐅 KRAVEN (Threat): Cornered! Strikes his current location.", Col.YLW))
                BaseVillainLogic._hit_sector(engine, loc_idx, 1, "Kraven's strike", single_target=False)

        elif "lizard" in t_id:
            # 🛡️ STATE ARMOR
            targets = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
            if not targets: return
            
            engine.log.append(Col.wrap(f" 🦎 LIZARD: Thrashing attack! (2 DMG total)", Col.YLW))
            
            if len(targets) == 1:
                BaseVillainLogic._hit_sector(engine, loc_idx, 2, "Lizard's tail", single_target=False)
            else:
                for dmg_point in range(2):
                    print(Col.wrap(f"\n 🦎 LIZARD DAMAGE ({dmg_point+1}/2): Choose who takes the hit:", Col.YLW))
                    for i, h in enumerate(targets, 1):
                        print(f" ({i}) {h.name} (Cards: {len(h.hand)})")
                    
                    # 🚨 HEADLESS FIX
                    choice = engine.ui.ask_choice(" Choose >> ", 1, len(targets))
                    target = targets[choice - 1]
                    
                    engine.log.append(Col.wrap(f"   🎯 Lizard slashes {target.name}!", Col.RED))
                    target.take_damage(engine)
        else:
            BaseVillainLogic.apply_standard_bam_damage(engine, threat, loc_idx)
