# src/logic/villains/corvus_glaive.py
import collections

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class CorvusGlaiveLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "KO TOKENS"
        villain.plot_max = len(engine.heroes)
        villain.plot_value = 0
        engine.log.append(Col.wrap(" 🔱 CORVUS GLAIVE: 'I serve a master who craves your souls!'", Col.RED + Col.BOLD))

    @staticmethod
    def _apply_glaive_damage(engine, loc_idx, base_amount, source_name):
        """
        ↳ LOCAL DAMAGE HOOK: 
        Checks for 'dangerous_terrain' locally to amplify damage.
        """
        loc = engine.locations[loc_idx]
        extra_dmg = 0
        
        # 🛡️ STATE ARMOR: Safe attribute check for threat identification
        t_id = (getattr(loc.threat, 'id_internal', None) or getattr(loc.threat, 'id', "")).lower()
        if loc.threat and not loc.threat.cleared and t_id == 'dangerous_terrain':
            extra_dmg = 1
            engine.log.append(Col.wrap(f"   ↳ {loc.threat.name} makes the terrain lethal (+1 Damage)!", Col.RED))

        total_dmg = base_amount + extra_dmg
        # Base logic _hit_sector is already armored with getattr
        BaseVillainLogic._hit_sector(engine, loc_idx, total_dmg, source_name)

    @staticmethod
    def handle_hero_ko(engine, hero):
        """Corvus advances the KO Track toward his specific win condition."""
        # 🛡️ GATEKEEPER: Prevent double-counting a single KO
        if getattr(hero, 'is_ko', False): return
        
        v = engine.villain
        v.plot_value += 1
        engine.log.append(Col.wrap(f"   📈 KO TOKEN ACQUIRED! ({v.plot_value}/{v.plot_max})", Col.RED))
        
        if v.plot_value >= v.plot_max:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = f"GLAIVE SUPREMACY: Corvus has claimed {v.plot_max} hero souls."
            
        BaseVillainLogic.handle_hero_ko(engine, hero)

    @staticmethod
    def handle_movement(engine, villain, card):
        move = card.get("move", 0)
        # Pursuit cards handle their own movement in resolve_special
        if move == "cw" or card.get("special_id"):
            return 
        BaseVillainLogic.handle_movement(engine, villain, {"move": move})

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx != -1:
            engine.log.append(Col.wrap(f" 🔪 CORVUS BAM: A sweeping strike at {engine.locations[v_idx].name}!", Col.RED))
            CorvusGlaiveLogic._apply_glaive_damage(engine, v_idx, damage, "Corvus's BAM")

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        try:
            loc_idx = engine.locations.index(loc)
            engine.log.append(Col.wrap(f"   ! OVERFLOW: Chaos at {loc.name} spills into violence!", Col.RED))
            CorvusGlaiveLogic._apply_glaive_damage(engine, loc_idx, 1, "Overflow Chaos")
        except ValueError:
            pass

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        t_id = (getattr(threat, 'trigger_id', None) or getattr(threat, 'id', "")).lower()
        loc = engine.locations[loc_idx]

        if "peril" in t_id:
            civs = getattr(loc, 'civilians', 0)
            if civs > 0:
                loc.civilians = 0
                engine.log.append(Col.wrap(f" ! CIVILIANS IN PERIL: {civs} civilians discarded at {loc.name}!", Col.RED))
                if not hasattr(engine, 'queued_events'): engine.queued_events = []
                engine.queued_events.append({"type": "extra_card"})

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "glaive_attack":
            # 🎯 PURSUE: Find the first clockwise location with EXACTLY 1 active hero
            target_idx = -1
            
            # ⚡ OPTIMIZED & ARMORED: Precompute counts, but only for ALIVE heroes
            alive_heroes = [h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)]
            hero_counts = collections.Counter(alive_heroes)
            
            for i in range(1, 7):
                idx = (villain.location_index + i) % 6
                if hero_counts.get(idx, 0) == 1:
                    target_idx = idx
                    break
            
            if target_idx != -1:
                villain.location_index = target_idx
                engine.log.append(Col.wrap(f" ⚔️ Glaive Attack: Corvus hunts a lone hero to {engine.locations[target_idx].name}!", Col.RED))
                CorvusGlaiveLogic._apply_glaive_damage(engine, target_idx, 2, "Glaive Attack")
            else:
                engine.log.append(Col.wrap(f" ⚔️ Glaive Attack: No lone target found. Striking current location!", Col.RED))
                CorvusGlaiveLogic._apply_glaive_damage(engine, villain.location_index, 1, "Glaive Sweep")

        elif sid == "slaughter":
            # 🎯 PURSUE: Find nearest clockwise location with ANY active heroes
            target_idx = -1
            
            # ⚡ OPTIMIZED & ARMORED: Precompute set of ALIVE hero locations (O(1) lookups)
            active_locations = {h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)}
            
            for i in range(1, 7):
                idx = (villain.location_index + i) % 6
                if idx in active_locations:
                    target_idx = idx
                    break
            
            if target_idx != -1:
                villain.location_index = target_idx
                engine.log.append(Col.wrap(f" 🔪 Slaughter: Corvus hunts to {engine.locations[target_idx].name}!", Col.RED))
                CorvusGlaiveLogic._apply_glaive_damage(engine, target_idx, 1, "Slaughter")

    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Corvus Glaive is the cruel and cunning right hand of Thanos. \n"
                "He is a master tactician who excels at isolating his targets \n"
                "and breaking them down through sheer attrition."
            ),
            "rules": (
                "\"The Soul Harvest & Predator's Instinct\"\n"
                "Corvus claims a KO Token for every fallen hero. If his tally \n"
                "matches your squad size, the mission is lost. Do not let him \n"
                "pick you off one by one.\n\n"
                "Beware his pursuit tactics: his 'Glaive Attack' specifically \n"
                "hunts for sectors containing exactly ONE isolated hero, rushing \n"
                "there to deliver a devastating 2-damage strike."
            ),
            "bam": (
                "\"Sweeping Strike\"\n"
                "A direct and brutal assault. He deals 1 damage to every \n"
                "hero currently standing in his sector."
            ),
            "overflow": (
                "\"Collateral Bloodshed\"\n"
                "If a location overruns, the ensuing panic turns into a killing \n"
                "field. Every hero in the overflowing sector instantly takes 1 damage."
            ),
            "threats": (
                "His vanguard has rigged the battlefield with lethal traps.\n"
                "- Dangerous Terrain: Amplifies ALL damage taken here by 1.\n"
                "- Civilians in Peril: A massacre that discards all civilians \n"
                "  and forces an EXTRA Master Plan card to be played immediately!\n"
                "- Hidden Traps: Taking shelter here at the end of a turn \n"
                "  incurs 1 damage."
            )
        }
