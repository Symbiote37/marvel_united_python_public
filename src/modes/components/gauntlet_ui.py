from src.utils.helpers import Col, ICON

class GauntletUI:
    @staticmethod
    def render_dashboard(state, engine, icons):
        rows = []
        
        # 1. The Doom Clock
        v_id = state.roster[state.stage_index]
        v_name = v_id.replace('_', ' ').title()
        rows.append(f" GAUNTLET: {v_name} ({state.stage_index+1}/4)")
        
        vault = " ".join([icons.get(s, '') for s in state.thanos_vault])
        rows.append(f" VAULT: {vault or 'NONE'} ({len(state.thanos_vault)}/6)")
        
        # 2. Prelude Progress (Only stages 1-3)
        if state.stage_index < 3 and state.active_pu_token:
            reqs = state.active_pu_token.get("req", {})
            prog = []
            for k, target in reqs.items():
                cur = state.pu_progress.get(k, 0)
                # Maps glyphs: Attack -> ✸, Move -> ➡, etc.
                glyph = '❖' if k == 'threat' else ICON.get(k, k[0].upper())
                txt = f"{cur}/{target}{glyph}"
                prog.append(Col.wrap(txt, Col.GRN) if cur >= target else txt)
            
            rows.append(Col.wrap(f" [ACTIONS]: {state.active_pu_token['effect_text']} ({' '.join(prog)})   ", Col.CYAN))
            rows.append(Col.wrap(f" [M3 REWARD]: {state.active_pu_mission['effect_text']}   ", Col.CYAN))

        # 3. The Arsenal (Current Power-Ups)
        if state.acquired_power_ups:
            arsenal = " | ".join([pu["name"] for pu in state.acquired_power_ups])
            rows.append(Col.wrap(f" 🌟 ARSENAL: {arsenal}   ", Col.GRN + Col.BOLD))
            
        # 4. 🚩 THE RESTORED MISSION TRACKER
        rows.append("-" * 53)
        m = engine.missions
        # Creates the "Civilians : ✔ | Thugs : ✔" visual
        parts = []
        for k in ["civilians", "thugs", "threats"]:
            cur, total = m.get(k, 0), m.get(f"{k}_max", 1)
            label = k.capitalize()
            icon = ICON.get(k, '')
            
            if cur >= total:
                parts.append(f"{label} {icon}: {Col.wrap('✔', Col.GRN)}")
            else:
                parts.append(f"{label} {icon}: {cur}/{total}")
        
        rows.append(f" MISSIONS: | {parts[0]} | {parts[1]}")
        rows.append(f"           | {parts[2]}")
            
        return rows
