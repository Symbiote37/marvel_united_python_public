# [Target: src/logic/villains/mysterio.py]
import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class MysterioLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = ""
        villain.plot_max = 0 
        villain.plot_value = 0
        for loc in engine.locations:
            if loc.threat:
                loc.threat.is_facedown = True
                
        engine.log.append(Col.wrap(" 🔮 MYSTERIO: 'Welcome to the grand illusion!'", Col.PURP + Col.BOLD))

    # --- THE MENU INTERCEPTS ---

    @staticmethod
    def get_attack_options(engine, hero):
        """Standard attacks, except we gate Facedown Reveal and ghost the Broken Illusion."""
        opts = BaseVillainLogic.get_attack_options(engine, hero)
        loc = engine.locations[hero.location_index]
        
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', '') or loc.threat.id).lower()

            # 1. Facedown Reveal Logic
            if getattr(loc.threat, 'is_facedown', False):
                opts = [opt for opt in opts if opt['id'] != 'h']
                opts.append({
                    "label": "Reveal Illusion (Attack)", 
                    "id": "reveal_a", 
                    "execute": lambda e: MysterioLogic.execute_reveal(e, loc, hero)
                })
            
            # 2. GHOST EXCEPTION: Broken Illusion cannot be attacked/cleared
            elif t_id == "broken_illusion":
                opts = [opt for opt in opts if opt['id'] != 'h']
                
        return opts

    @staticmethod
    def get_heroic_options(engine, hero):
        """Standard heroic acts, except we gate Facedown Reveal and ghost the Broken Illusion."""
        opts = BaseVillainLogic.get_heroic_options(engine, hero)
        loc = engine.locations[hero.location_index]
        
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', '') or loc.threat.id).lower()

            # 1. Facedown Reveal Logic
            if getattr(loc.threat, 'is_facedown', False):
                opts = [opt for opt in opts if opt['id'] != 't_h']
                opts.append({
                    "label": "Reveal Illusion (Heroic)", 
                    "id": "reveal_h", 
                    "execute": lambda e: MysterioLogic.execute_reveal(e, loc, hero)
                })
            
            # 2. GHOST EXCEPTION: Broken Illusion cannot be diffused/cleared
            elif t_id == "broken_illusion":
                opts = [opt for opt in opts if opt['id'] != 't_h']
                
        return opts

    @staticmethod
    def get_move_options(engine, hero):
        """Allows reveal via Move, and ghosts Broken Illusion."""
        opts = BaseVillainLogic.get_move_options(engine, hero)
        loc = engine.locations[hero.location_index]
        
        if loc.threat and not loc.threat.cleared:
            t_id = (getattr(loc.threat, 'id_internal', '') or loc.threat.id).lower()

            # 1. Facedown Reveal Logic
            if getattr(loc.threat, 'is_facedown', False):
                opts = [opt for opt in opts if opt['id'] != 't_m']
                opts.append({
                    "label": "Reveal Illusion (Move)", 
                    "id": "reveal_m", 
                    "execute": lambda e: MysterioLogic.execute_reveal(e, loc, hero)
                })
            
            # 2. GHOST EXCEPTION
            elif t_id == "broken_illusion":
                opts = [opt for opt in opts if opt['id'] != 't_m']
                
        return opts

    # --- MYSTERIO MECHANICS ---

    @staticmethod
    def execute_reveal(engine, loc, hero):
        loc.threat.is_facedown = False
        engine.log.append(Col.wrap(f" 🔍 {hero.name} reveals the illusion: {loc.threat.name}!", Col.CYAN))
        
        t_id = (getattr(loc.threat, 'id_internal', None) or loc.threat.id).lower()
        if t_id == "battle_drones":
            engine.log.append(Col.wrap("   ⚔️ BATTLE DRONES: The illusion bites back!", Col.RED))
            hero.take_damage(engine)
        elif t_id == "smoke_mirrors":
            if not loc.is_full:
                loc.thugs += 1
                engine.log.append(Col.wrap("   💨 SMOKE & MIRRORS: A Thug emerges from the fog!", Col.YLW))
            else:
                MysterioLogic.on_overflow(engine, engine.villain, loc, "thugs")
        elif t_id == "broken_illusion":
            engine.log.append(Col.wrap("   ✨ BROKEN ILLUSION: A gap in Mysterio's defenses is exposed!", Col.GRN))
            
        return True

    @staticmethod
    def is_villain_shielded(engine, villain):
        revealed_broken = any(
            l.threat and not getattr(l.threat, 'is_facedown', False) and 
            (getattr(l.threat, 'id_internal', '') or l.threat.id).lower() == 'broken_illusion'
            for l in engine.locations
        )
        
        if not revealed_broken:
            return True, " 🛡️ MYSTERIO is cloaked in ILLUSIONS! (Needs 'Broken Illusion' revealed)"
        return False, ""

    @staticmethod
    def on_bam(engine, villain, damage=1):
        v_idx = villain.location_index
        if v_idx == -1: return
        loc = engine.locations[v_idx]
        
        engine.log.append(Col.wrap(f" 💨 MYSTERIO BAM: Reality warps at {loc.name}!", Col.PURP))
        loc.civilians, loc.thugs = loc.thugs, loc.civilians
        engine.log.append(Col.wrap("   🌀 Civilians and Thugs have swapped forms!", Col.YLW))
        
        if not loc.is_full:
            loc.civilians += 1
            engine.log.append(Col.wrap("   👤 A new civilian apparition appears!", Col.YLW))
        else:
            MysterioLogic.on_overflow(engine, villain, loc, "civilians")

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        engine.log.append(Col.wrap(f"   ! OVERFLOW: Mysterio accelerates his timeline at {loc.name}!", Col.PURP))
        BaseVillainLogic.add_plan_facedown(engine)

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        if sid == "holographic_technology":
            engine.log.append(Col.wrap(" 📽️ HOLOGRAPHIC TECH: The illusions shift!", Col.PURP))
            active_threats = []
            for loc in engine.locations:
                if loc.threat and not loc.threat.cleared:
                    loc.threat.damage = 0 
                    loc.threat.heroic_tokens = 0
                    loc.threat.is_facedown = True
                    active_threats.append(loc.threat)
                    loc.threat = None
                    
            random.shuffle(active_threats)
            
            v_idx = villain.location_index
            for i, threat in enumerate(active_threats):
                target_idx = (v_idx + i) % 6
                engine.locations[target_idx].threat = threat

        elif sid == "fake_heroics":
            max_c = max(l.civilians for l in engine.locations)
            target_idx = villain.location_index
            for i in range(1, 7):
                idx = (villain.location_index + i) % 6
                if engine.locations[idx].civilians == max_c:
                    target_idx = idx
                    break
                    
            villain.location_index = target_idx
            loc = engine.locations[target_idx]
            
            engine.log.append(Col.wrap(f" 🎭 FAKE HEROICS: Mysterio strikes {loc.name}!", Col.PURP))
            c_count, t_count = loc.civilians, loc.thugs
            loc.civilians = 0
            loc.thugs = 0
            if c_count > 0 or t_count > 0:
                engine.log.append(Col.wrap(f"   💨 {c_count} Civilians and {t_count} Thugs vanished into smoke!", Col.YLW))
                
            BaseVillainLogic.add_plan_facedown(engine)
