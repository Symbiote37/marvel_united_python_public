# [Target: src/logic/villains/killmonger.py]
import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class KillmongerLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "UNSTABLE SECTORS"
        villain.plot_max = 4 
        villain.plot_value = 0
        engine.log.append(Col.wrap(" 🐆 KILLMONGER: 'I've waited my whole life for this!'", Col.RED + Col.BOLD))

    @staticmethod
    def _radicalize_at_location(engine, loc, log_prefix="   ⚠️"):
        """
        Randomly radicalizes a Thug or Civilian if present.
        Ensures the tactical attempt is logged even if the location is empty.
        """
        targets = []
        if loc.civilians > 0: targets.append("civ")
        if loc.thugs > 0: targets.append("thug")

        if not targets:
            engine.log.append(Col.wrap(f"{log_prefix} No population remains to radicalize.", Col.YLW))
            return False

        choice = random.choice(targets)
        if choice == "civ":
            loc.civilians -= 1
            msg = "Civilian radicalized!"
        else:
            loc.thugs -= 1
            msg = "Local forces integrated!"

        loc.infected += 1
        engine.log.append(Col.wrap(f"{log_prefix} {msg} {ICON['infected']}", Col.YLW))
        return True

    @staticmethod
    def handle_movement(engine, villain, card):
        """Sanitizes 'move'/'movement' keys and translates 'cw' to 1."""
        move = card.get("move", card.get("movement", 0))
        if move == "cw":
            move = 1
        BaseVillainLogic.handle_movement(engine, villain, {"move": move})
        
    @staticmethod
    def check_destabilization(engine):
        """WIN CONDITION: 4 sectors reach 3+ Radicalized insurgents (Δ)."""
        v = engine.villain
        unstable_locs = [l for l in engine.locations if l.infected >= 3]
        v.plot_value = len(unstable_locs)
        
        if v.plot_value >= v.plot_max:
            engine.log.append(Col.wrap(f" 💀 WAKANDA HAS FALLEN: {v.plot_value} sectors radicalized!", Col.RED + Col.BOLD))
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = f"COUP COMPLETE: {v.plot_value} locations reached critical instability (3+ Δ)."

    @staticmethod
    def on_bam(engine, villain, damage=1):
        """Tactical Coup leads the BAM resolution, followed by Hero damage."""
        v_idx = villain.location_index
        if v_idx != -1:
            loc = engine.locations[v_idx]
            engine.log.append(Col.wrap(
                f" 🔪 KILLMONGER BAM: Instigating tactical coup at {loc.name}!", 
                Col.RED + Col.BOLD
            ))
            KillmongerLogic._radicalize_at_location(engine, loc)
        
        BaseVillainLogic.on_bam(engine, villain, damage=damage)
        KillmongerLogic.check_destabilization(engine)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Lateral destabilization: Overflow elsewhere radicalizes Killmonger's site."""
        v_idx = villain.location_index
        if v_idx != -1:
            target_loc = engine.locations[v_idx]
            engine.log.append(Col.wrap(f"   ! OVERFLOW: Chaos at {loc.name} spreads!", Col.RED))
            KillmongerLogic._radicalize_at_location(engine, target_loc, log_prefix="   📈")
            KillmongerLogic.check_destabilization(engine)

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        """Weapon Smuggling radicalizes its specific location."""
        t_id = (getattr(threat, 'trigger_id', None) or getattr(threat, 'id', "")).lower()
        loc = engine.locations[loc_idx]

        if t_id == "weapon_smuggling":
            engine.log.append(Col.wrap(f" 📦 Weapon Smuggling triggered at {loc.name}!", Col.YLW))
            KillmongerLogic._radicalize_at_location(engine, loc, log_prefix="   📦")
            KillmongerLogic.check_destabilization(engine)

    @staticmethod
    def on_civilians_flee(engine, loc):
        """Protects Δ tokens from being cleared by displacement effects."""
        if loc.civilians > 0:
            count = loc.civilians
            loc.civilians = 0
            engine.log.append(Col.wrap(f"   💨 {count} Civilians fled the scene!", Col.YLW))
        
        if loc.infected > 0:
            engine.log.append(Col.wrap(f"   🛡️ {loc.infected} Insurgents {ICON['infected']} hold their ground!", Col.RED))

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        
        if sid == "duel":
            hero_locs = {h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)}
            
            for i in range(1, 7):
                idx = (villain.location_index + i) % 6
                if idx in hero_locs:
                    villain.location_index = idx
                    break
            loc = engine.locations[villain.location_index]
            engine.log.append(Col.wrap(f" ⚔️ Duel: Killmonger hunts to {loc.name}!", Col.RED))
            BaseVillainLogic._hit_sector(engine, villain.location_index, 2, "Killmonger's Duel", single_target=True)

        elif sid == "overthrow":
            target_idx = max(range(len(engine.locations)), key=lambda i: engine.locations[i].civilians)
            villain.location_index = target_idx
            loc = engine.locations[target_idx]
            
            engine.log.append(Col.wrap(f" 🏃 Overthrow: Destabilizing {loc.name}!", Col.RED))
            c_to_replace = loc.civilians
            loc.civilians = 0
            loc.infected += c_to_replace
            engine.log.append(f"   ⚠️ {c_to_replace} inhabitants radicalized {ICON['infected']}.")
            KillmongerLogic.check_destabilization(engine)

    @staticmethod
    def get_heroic_options(engine, hero):
        """Standard Heroic actions are blocked from removing Δ insurgents."""
        return BaseVillainLogic.get_heroic_options(engine, hero)
