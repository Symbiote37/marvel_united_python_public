# src/ui/board.py

import sys
from src.utils.helpers import Col, ICON

class BoardRenderer:
    # 🎨 THE MASTER PALETTE: Distinct brights, reserving Cyan for system UI
    HERO_COLORS = [Col.ORN, Col.C111, Col.GRN, Col.MAGENTA]

    @staticmethod
    def clear():
        sys.stdout.write("\033c")
        sys.stdout.flush()

    @classmethod
    def get_loc_box(cls, loc, idx, engine, heroes, hero_presence=None):       
        is_destroyed = getattr(loc, 'is_destroyed', False)

        # 🚨 STATE HASH: Build the cache key including custom UI tokens
        if is_destroyed:
            v_icons = ""
            h_state = ()
            threat_state = None
        else:
            v_icons = engine.mode_handler.get_location_presence(idx)
            h_state = tuple(getattr(h, 'location_index', -1) for h in heroes)
            threat = getattr(loc, 'threat', None)
            threat_state = (getattr(threat, 'cleared', False), getattr(threat, 'display_hp', "0"), getattr(threat, 'name', ""), getattr(threat, 'short_effect', '')) if threat else None

        cache_key = (
            idx,
            is_destroyed,
            v_icons,
            h_state,
            loc.name,
            getattr(loc, 'thugs', 0),
            getattr(loc, 'civilians', 0),
            getattr(loc, 'crisis_tokens', 0),
            getattr(loc, 'journalists', 0),
            getattr(loc, 'infected', 0),
            getattr(getattr(loc, 'endangered_hero', None), 'name', None),
            getattr(loc, 'capacity', 5),
            threat_state,
            getattr(loc, 'short_effect', 'CLEARED')
        )

        # 🚨 CACHE HIT: Return pre-rendered string block
        if getattr(loc, '_box_cache_key', None) == cache_key:
            return loc._box_cache_data

        if is_destroyed:
            result = [
                f"[{idx+1}] {Col.wrap('COLLAPSED', Col.RED + Col.BOLD)}  ",   
                f"    {Col.wrap('----------', Col.RED)} ",         
                Col.ljust(" ", 16), 
                Col.ljust(" ", 16),      
                Col.ljust(Col.wrap("  🏚️ RUBBLE      ", Col.RED), 16),
                Col.ljust(" ", 16),
                Col.ljust(" ", 16)
            ]
            loc._box_cache_key = cache_key
            loc._box_cache_data = result
            return result

        # ⚡ OPTIMIZED LOOKUP
        if hero_presence is not None:
            h_icons = hero_presence.get(idx, "")
        else:
            # Fallback for manual or legacy calls
            h_icons = ""
            for i, h in enumerate(heroes):
                if getattr(h, 'location_index', -1) == idx and getattr(h, 'location_index', -1) != -1:
                    color = cls.HERO_COLORS[i % len(cls.HERO_COLORS)]
                    h_icons += Col.wrap(h.name[0], color)

        name_parts = loc.name.split()
        l1, l2 = (name_parts + [""])[:2]
        
        token_str = f"T:{loc.thugs} C:{loc.civilians} "
        # Endangered Location tag
        if getattr(loc, 'endangered_hero', None):
            try:
                h_idx = heroes.index(loc.endangered_hero)
                c_color = cls.HERO_COLORS[h_idx % len(cls.HERO_COLORS)]
            except ValueError:
                c_color = Col.WHT
            token_str += Col.wrap("θ ", c_color + Col.BOLD)
        # Crisis Tokens tag
        if getattr(loc, 'crisis_tokens', 0) > 0: 
            token_str += f"{ICON['crisis']}{loc.crisis_tokens} "
            
        # 🚨 NEW: Journalist Tokens
        if getattr(loc, 'journalists', 0) > 0:
            token_str += Col.wrap(f"📸 [{loc.journalists}] ", Col.CYAN)
        
        # 🚨 NEW: Infected/Radicalized Tokens
        if getattr(loc, 'infected', 0) > 0:
            # Reusing the crisis icon (Δ) visually to represent the volatile insurgency, colored red
            token_str += Col.wrap(f"Δ{loc.infected} ", Col.RED + Col.BOLD)
        current_occ = loc.total_figures()
        presence_str = f"P:{v_icons} {h_icons} ({current_occ}/{loc.capacity}) "
        
        if loc.threat and not loc.threat.cleared:
            display_val = getattr(loc.threat, 'display_hp', "0")
            line_threat_name = Col.wrap(f"☠ {loc.threat.name[:13]} ", Col.YLW)
            line_threat_hp = Col.wrap(f"  [{display_val}] ", Col.YLW)
            line_threat_effect = Col.wrap(f"({loc.threat.short_effect[:11]}) ", Col.CYAN)
        else:
            boon_raw = getattr(loc, 'short_effect', 'CLEARED').upper()
            b_parts = boon_raw.split('\n')
            b1, b2 = (b_parts + ["", ""])[:2]
            line_threat_name = Col.wrap(" CLEARED ", Col.CYAN)
            line_threat_hp = Col.wrap(f" {b1[:14]} ", Col.GRN)
            line_threat_effect = Col.wrap(f" {b2[:14]} ", Col.GRN)

        result = [
            f"[{idx+1}] {l1[:11]:<11} ", 
            f"    {l2[:11]:<11} ", 
            Col.ljust(token_str, 16), 
            Col.ljust(presence_str, 16), 
            Col.ljust(line_threat_name, 16), 
            Col.ljust(line_threat_hp, 16), 
            Col.ljust(line_threat_effect, 16)
        ]
        
        # 🚨 CACHE STORE: Save the result against the hash
        loc._box_cache_key = cache_key
        loc._box_cache_data = result
        return result

    @classmethod
    def _get_engine(cls, game_state):
        if hasattr(game_state, 'locations'):
            return game_state
        elif isinstance(game_state, dict) and "engine" in game_state:
            return game_state["engine"]
        return game_state.get("engine")

    @classmethod
    def _render_villain_header(cls, engine, frame):
        v = engine.villain
        turn_count = getattr(engine, 'turn_count', 0)
        v_tag = Col.wrap(v.name.upper(), Col.RED)
        frame.append(f" {v_tag} | HP:{ICON.get('attack', '💥')}x{v.hp} | TURN:{turn_count} | DECK:[{len(v.plan_deck)}] ")
        
        # 🚨 DECOUPLED STATE HOOK: Scan for universal mechanical flags, not specific heroes.
        story_cards = getattr(engine.storyline, 'cards', engine.storyline)
        reveal_plan = any(isinstance(c, dict) and c.get('persistent_effect') == "reveal_master_plan" for c in story_cards)
                
        if reveal_plan and v.plan_deck:
            top_card = v.plan_deck[0]
            plan_str = cls.format_master_plan(top_card)
            frame.append(Col.wrap(f" 🔮 VISIONS OF THE FUTURE: [ {plan_str} ] ", Col.MAGENTA + Col.BOLD))

        frame.append("=" * 53)

    @staticmethod
    def format_master_plan(card):
        """Universally translates Master Plan JSON data into a readable UI string."""
        parts = []
        move = card.get('movement', card.get('move', 0))
        
        if isinstance(move, int) and move > 0:
            parts.append(f"➡ {move}")
        elif isinstance(move, str) and move.strip():
            parts.append(f"➡ {move}")
            
        if card.get('bam'): parts.append("💥 BAM")
        if card.get('trigger'): parts.append("⚡ TRG")
            
        adds = card.get('add', {})
        add_str = []
        for k, v in adds.items():
            if k == 'thug': add_str.append(f"👊 {v}")
            elif k == 'civilian': add_str.append(f"🧍 {v}")
            elif k == 'threat': add_str.append(f"⚠️ {v}")
        if add_str: parts.append(f"➕ {' '.join(add_str)}")
            
        if card.get('special_id') or card.get('effect_text'):
            parts.append("🌟 SPEC")
            
        return " | ".join(parts) if parts else "Blank Plan"

    @classmethod
    def _render_locations_row(cls, engine, frame, indices, hero_presence=None):
        # Pass the pre-computed dictionary down to the layout builder
        loc_data = [cls.get_loc_box(engine.locations[i], i, engine, engine.heroes, hero_presence) for i in indices]
        for r in range(7):
            frame.append(f" {Col.ljust(loc_data[0][r], 16)}| {Col.ljust(loc_data[1][r], 16)}| {Col.ljust(loc_data[2][r], 16)}")
        frame.append("-" * 53)

    @classmethod
    def _render_dashboard(cls, engine, frame):
        custom_dash = engine.mode_handler.render_center_dashboard()
        if custom_dash:
            for row in custom_dash:
                frame.append(row)
        else:
            missions = engine.missions
            m_parts = [
                f"{k.capitalize()} {ICON.get(k, '')}: {Col.wrap('✔ ', Col.GRN) if missions.get(k, 0) >= missions.get(f'{k}_max', 1) else f'{missions.get(k,0)}/{missions.get(f'{k}_max',1)}'}"
                for k in ["civilians", "thugs", "threats"]
            ]
            frame.append(f" MISSIONS: | {' | '.join(m_parts[:2])}\n           | {m_parts[2]} ")
            
            # 🚨 Dynamic Plot vs Static Plot routing
            v = engine.villain
            v_logic = getattr(engine, 'villain_logic', None)
            
            if hasattr(v_logic, 'get_plot_display'):
                plot_str = v_logic.get_plot_display(engine)
                if plot_str: 
                    frame.append(Col.wrap(f" {plot_str} ", Col.RED + Col.BOLD))
            elif getattr(v, 'plot_max', 0) > 0:
                plot_label = getattr(v, 'plot_name', 'PLOT').upper()
                val = getattr(v, 'plot_value', 0)
                frame.append(Col.wrap(f" {plot_label}: {val}/{v.plot_max} ", Col.RED + Col.BOLD))
                
        frame.append("-" * 53)

    @classmethod
    def _render_team_hud(cls, engine, frame):
        is_solo = getattr(engine, 'is_solo_mode', False)
        heroes = engine.heroes
        
        if is_solo:
            initials = []
            for i, h in enumerate(heroes):
                c_color = cls.HERO_COLORS[i % len(cls.HERO_COLORS)]
                status_text = " (KO)" if h.is_ko else ""
                
                # 🚨 Keep Crisis Sensor for individual heroes
                crisis_count = getattr(h, 'crisis_tokens', 0)
                crisis_str = f" {Col.wrap(f'Δ{crisis_count}', Col.RED)}" if crisis_count > 0 else ""
                
                # 🚨 Exposure Tracker
                exp_count = getattr(h, 'exposure_tokens', 0)
                is_exposed = getattr(h, 'is_exposed', False)
                if is_exposed:
                    exp_str = f" {Col.wrap('🤳 EXPOSED', Col.RED)} "
                elif exp_count > 0:
                    exp_str = f" {Col.wrap(f'🤳 [{exp_count}]', Col.CYAN)} "
                else:
                    exp_str = ""
                    
                h_stat = f"[{h.name[0].upper()}]{status_text}{crisis_str}{exp_str}"
                initials.append(Col.wrap(h_stat, c_color))
                
            shared_h = heroes[0]
            team_hud_str = f"{' | '.join(initials)} | DECK:[{len(shared_h.hand)}|{len(shared_h.deck)}]"
            frame.append(f" TEAM HUD: {team_hud_str} ")
            
        else:
            team_line = []
            for i, h in enumerate(heroes):
                status_text = "KO" if h.is_ko else f"{len(h.hand)}|{len(h.deck)}"
                
                # 🚨 Crisis Sensor
                crisis_count = getattr(h, 'crisis_tokens', 0)
                crisis_str = f" {Col.wrap(f'Δ{crisis_count}', Col.RED)}" if crisis_count > 0 else ""
                
                # 🚨 Exposure Tracker
                exp_count = getattr(h, 'exposure_tokens', 0)
                is_exposed = getattr(h, 'is_exposed', False)
                if is_exposed:
                    exp_str = f" {Col.wrap('🤳EXPOSED', Col.RED)} "
                elif exp_count > 0:
                    exp_str = f" {Col.wrap(f'🤳{exp_count}', Col.CYAN)} "
                else:
                    exp_str = ""
                    
                h_stat = f"{h.name[0]}:[{status_text}]{crisis_str}{exp_str}"
                team_line.append(Col.wrap(h_stat, cls.HERO_COLORS[i % len(cls.HERO_COLORS)]))
                
            frame.append(f" TEAM HUD: {' | '.join(team_line)} ")
        frame.append("-" * 53)

    @classmethod
    def _render_active_card(cls, engine, frame):
        storyline = engine.storyline
        story_cards = getattr(storyline, 'cards', [])
        active_v_card = next((c for c in reversed(story_cards) if isinstance(c, dict) and c.get('is_villain') and not c.get('is_facedown', False)), None)
        frame.append(f" 🃏 ACTIVE: {Col.wrap(active_v_card.get('display_name', 'MASTER PLAN').upper(), Col.CYAN) if active_v_card else Col.wrap('NONE', Col.CYAN)} ")
        frame.append("-" * 53)

    @classmethod
    def _render_log(cls, engine, frame):
        for entry in engine.log[-30:]:
            frame.append(f" {entry} ")
        frame.append("=" * 53)

    @classmethod
    def _render_hero_context(cls, engine, frame, hero_context, played_card):
        story_cards = getattr(engine.storyline, 'cards', [])
        active_h = hero_context or engine.heroes[getattr(engine, 'current_hero_index', 0)]

        if hero_context and played_card is None:
            prev_hero_card = next((c for c in reversed(story_cards) if not c.get('is_villain') and not c.get('is_facedown')), None)
            if prev_hero_card:
                frame.append(Col.wrap(f" 🧬 INHERITING: [ {' '.join([ICON.get(a, a) for a in prev_hero_card.get('actions', [])])} ] ", Col.YLW + Col.BOLD))
            hand_line = [f"{i}:[{''.join([ICON.get(a, a) for a in c.get('actions', [])])}]" for i, c in enumerate(hero_context.hand, 1)]
            frame.append(f" HAND: {' '.join(hand_line)} ")

        pool_str = ""
        active_pool = getattr(engine, 'active_pool', {})
        if played_card is not None and active_pool:
            p_disp = " ".join([f"{ICON[k]}:{val}" for k, val in active_pool.items() if val > 0])
            if p_disp: pool_str = f" | {Col.wrap('TOTAL:', Col.YLW)} {p_disp}"

        h_idx = engine.heroes.index(active_h)
        h_tag = Col.wrap(active_h.name.upper(), cls.HERO_COLORS[h_idx % len(cls.HERO_COLORS)] + Col.BOLD)
        status = f" | {Col.wrap('KO', Col.RED + Col.BOLD)}" if getattr(active_h, 'is_ko', False) else ""
        
        # 🚨 Crisis Sensor
        crisis_count = getattr(active_h, 'crisis_tokens', 0)
        crisis_display = f" | {Col.wrap(f'Δ:[{crisis_count}]', Col.RED + Col.BOLD)}" if crisis_count > 0 else ""
        
        # 🚨 Exposure Sensor
        exp_count = getattr(active_h, 'exposure_tokens', 0)
        is_exposed = getattr(active_h, 'is_exposed', False)
        if is_exposed:
            exposure_display = f" | {Col.wrap('📸 EXPOSED', Col.RED + Col.BOLD)}"
        elif exp_count > 0:
            exposure_display = f" | {Col.wrap(f'📸 {exp_count}', Col.CYAN + Col.BOLD)}"
        else:
            exposure_display = ""

        frame.append(f" {h_tag} | Loc:{active_h.location_index+1} | DECK:[{len(active_h.deck)}] | HAND:[{len(active_h.hand)}]{status}{crisis_display}{exposure_display}{pool_str} ")
        frame.append("=" * 53)

    @classmethod
    def render(cls, game_state, hero_context=None, played_card=None, special_used=False, sub_menu=None):
        cls.clear()

        engine = cls._get_engine(game_state)
        frame = []

        # ⚡ OPTIMIZATION: Precompute hero presence mapping once per frame
        hero_presence = {}
        for i, h in enumerate(engine.heroes):
            if getattr(h, 'location_index', -1) != -1:
                color = cls.HERO_COLORS[i % len(cls.HERO_COLORS)]
                hero_presence[h.location_index] = hero_presence.get(h.location_index, "") + Col.wrap(h.name[0], color)

        cls._render_villain_header(engine, frame)
        cls._render_locations_row(engine, frame, [0, 1, 2], hero_presence)
        cls._render_dashboard(engine, frame)
        cls._render_locations_row(engine, frame, [5, 4, 3], hero_presence)
        cls._render_team_hud(engine, frame)
        cls._render_active_card(engine, frame)
        cls._render_log(engine, frame)
        cls._render_hero_context(engine, frame, hero_context, played_card)

        sys.stdout.write("\n".join(frame) + "\n")
        sys.stdout.flush()
