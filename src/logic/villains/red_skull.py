# src/logic/villains/red_skull.py
import random

from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class RedSkullLogic(BaseVillainLogic):
    @staticmethod
    def on_bam(engine, villain):
        quotes = [
            "If they cut off one head, two more shall take its place.",
            "Freedom is only for the one who rules! All others must be slaves!",
            "And now a toast... to unending conquest!",
            "It is the fist that conquers, not worthless 'inner peace'!",
            "Always one step ahead of you."
        ]
        selected_quote = random.choice(quotes)
        # 1. DO THE BASE STUFF (Damage + Logs)
        BaseVillainLogic.on_bam(engine, villain)
        
        # 2. ADD THE SEASONING (Fear)
        RedSkullLogic.advance_fear(engine, 2, "Villain BAM!")

    @staticmethod
    def on_overflow(engine, villain, location, token_type):
        """Red Skull Overflow: Penalty is +1 Fear instead of standard log."""
        engine.log.append(Col.wrap(f" ⚠️ Overflow at {location.name}!", Col.RED))
        RedSkullLogic.advance_fear(engine, 1, f"Overflow: {token_type}")

    @staticmethod
    def resolve_special(engine, villain, card):
        """Handle specific Red Skull Master Plan cards."""
        sid = card.get("special_id")
        
        if sid == "skull_hail_hydra":
            total_discarded = 0
            purged_sectors = set() 
            
            # Step 1 & 2: Identify and Purge
            hero_locations = {h.location_index for h in engine.heroes}
            for loc_idx in hero_locations:
                loc = engine.locations[loc_idx]
                if loc.civilians > 0:
                    total_discarded += loc.civilians
                    loc.civilians = 0
                    purged_sectors.add(loc_idx) 
                    engine.log.append(Col.wrap(f" ☠️ Civilians purged at {loc.name}!", Col.RED))

            # Step 3: Damage ONLY heroes at the purged locations
            for h in engine.heroes:
                # REVERTED: Using the original hero damage method
                if h.location_index in purged_sectors:
                    h.take_damage(engine)
                    engine.log.append(f" 💥 {h.name} caught in the Hail Hydra strike!")
                elif h.location_index in hero_locations:
                    engine.log.append(f" 🛡️ {h.name} is safe—no civilians lost in this sector.")
            
            # Step 4: Final Fear calculation
            if total_discarded > 0:
                RedSkullLogic.advance_fear(engine, total_discarded, "Hail Hydra!")

        elif sid == "skull_hydra_insurgency":
            # Effect: Fear +1 per Crisis token held by Heroes
            total_crisis = sum(h.crisis_tokens for h in engine.heroes)
            if total_crisis > 0:
                RedSkullLogic.advance_fear(engine, total_crisis, "Hydra Insurgency")
            else:
                engine.log.append(" 🐙 INSURGENCY: No crisis tokens found. The plot stalls.")

    @staticmethod
    def advance_fear(engine, amount, reason):
        """Specific helper to manage Red Skull's win condition."""
        v = engine.villain
        
        # 1. Increment and Clamp
        v.plot_value = min(v.plot_max, v.plot_value + amount)
        
        # 2. Update the log immediately
        engine.log.append(Col.wrap(
            f" 📈 {v.plot_name} +{amount} ({reason}) -> {v.plot_value}/{v.plot_max} ", 
            Col.RED + Col.BOLD
        ))
        
        # 3. SET ENGINE FLAGS (Instead of trigger_defeat)
        if v.plot_value >= v.plot_max:
            engine.log.append(Col.wrap(f" 💀 FEAR TRACK AT MAXIMUM: {v.plot_value}/{v.plot_max}", Col.RED + Col.BOLD))
            
            # These flags tell the core engine loop to stop AFTER the next render
            engine.game_over = True
            engine.loss_reason = f"VILLAINOUS PLOT COMPLETE: {v.plot_name} reached {v.plot_max}!"

    @staticmethod
    def resolve_trigger(engine, threat, loc_idx):
        """
        Processes the 'H' Trigger signal for Red Skull's specific Threats.
        Maps the trigger_id from the JSON to a mechanical effect.
        """
        tid = threat.trigger_id
        
        # 1. BRAINWASHING: The AoE Crisis strike
        if tid == "aoe_crisis":
            # Current location + left/right neighbors
            affected = Col.get_neighbors(loc_idx, include_self=True)
            
            for h in engine.heroes:
                if h.location_index in affected:
                    h.crisis_tokens += 1
                    engine.log.append(Col.wrap(
                        f"   🔺 {h.name} hit by Brainwashing from Sector {loc_idx + 1}!", 
                        Col.YLW
                    ))

        # 2. SUBVERSION: The Resource Purge
        elif tid == "token_purge":
            loc = engine.locations[loc_idx]
            total_removed = loc.thugs + loc.civilians
            
            if total_removed > 0:
                engine.log.append(Col.wrap(f" 🐙 {threat.name} purges {total_removed} tokens from {loc.name}!", Col.RED))
                loc.thugs = 0
                loc.civilians = 0
                # This feeds directly into your advance_fear helper!
                RedSkullLogic.advance_fear(engine, total_removed, f"Subversion at {loc.name}")
            else:
                engine.log.append(f"   🐙 Subversion at {loc.name}: No tokens to purge.")

    @staticmethod
    def resolve_threat_bam(engine, threat, loc_idx):
        """Red Skull Specialized BAM: Choice between Team Damage or Crisis Tokens."""
        targets = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
        
        if not targets:
            engine.log.append(Col.wrap(f"   [!] {threat.name} strikes at {engine.locations[loc_idx].name}, but the streets are empty.", Col.DARK_GRAY))
            return

        loc_name = engine.locations[loc_idx].name
        tid = (getattr(threat, 'id_internal', None) or threat.id).lower()
        impact_text = "Poison Strike" if "hydra" in tid else "Heavy Assault" if "crossbones" in tid else "Henchman Strike"

        # Resolve Pattern
        bid = getattr(threat, 'bam_id', "light_damage_bam")
        pattern = BaseVillainLogic.BAM_PATTERNS.get(bid, (1, 0, False))
        dmg = pattern[0] 
        is_single = pattern[2] if len(pattern) == 3 else False
        crisis_cost = dmg 

        # HEADLESS FIX: Concatenate prompts into a single string for the UI Adapter
        prompt_text = (
            f"\n [!] {Col.wrap(threat.name.upper(), Col.RED)} BAM! at {loc_name}\n"
            f" (1) IMPACT: {impact_text} ({dmg} Damage to Sector)\n"
            f" (2) SHIELD: ONE Hero (anywhere) takes {crisis_cost} Crisis Tokens\n"
            " Choose (1/2): "
        )
        
        choice = engine.ui.ask_choice(prompt_text, 1, 2)

        if choice == 2:
            hero_prompt = f"\n {Col.wrap('SELECT TARGET FOR CRISIS TOKENS', Col.BOLD)}\n"
            for i, h in enumerate(engine.heroes):
                hero_prompt += f" [{i+1}] {h.name} (Crisis: {h.crisis_tokens})\n"
            hero_prompt += f" Which hero takes the {crisis_cost} tokens? "
            
            target_idx = engine.ui.ask_choice(hero_prompt, 1, len(engine.heroes)) - 1
            target_hero = engine.heroes[target_idx]
            target_hero.crisis_tokens += crisis_cost
            engine.log.append(f" [+] {target_hero.name} took {crisis_cost} Crisis to shield the team.")
        else:
            BaseVillainLogic._hit_sector(engine, loc_idx, dmg, f"{threat.name} {impact_text}", single_target=is_single)
