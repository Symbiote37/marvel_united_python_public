import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col, ICON

class BullseyeLogic(BaseVillainLogic):
    @staticmethod
    def perform_setup(engine, villain):
        # 🎯 Plot: Bullseye wins if KOs reach the number of heroes
        villain.plot_name = "THE CONTRACT"
        villain.plot_max = len(engine.heroes)
        villain.plot_value = 0
        
        engine.log.append(Col.wrap(" 🎯 BULLSEYE: 'I never miss. Ever.' ", Col.RED + Col.BOLD))
        engine.log.append(Col.wrap(f" 📑 CONTRACT: Bullseye wins if he achieves {villain.plot_max} KOs or any Overflow! ", Col.DARK_GRAY))

    @staticmethod
    def handle_movement(engine, villain, card):
        sid = card.get("special_id")
        
        # 🎯 MASTER ASSASSIN: Move Clockwise to the next location WITHOUT heroes.
        if sid == "master_assassin" or card.get("move") == "cw":
            current_idx = villain.location_index
            target_idx = current_idx
            
            # 🚨 OPTIMIZATION & ARMOR: O(1) set lookup, safely ignoring KO'd heroes
            occupied_locations = {h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)}
            
            for i in range(1, 6):
                check_idx = (current_idx + i) % 6
                if check_idx not in occupied_locations:
                    target_idx = check_idx
                    break
            
            villain.location_index = target_idx
            engine.log.append(Col.wrap(f" 🏃 MASTER ASSASSIN: Bullseye relocates to {engine.locations[target_idx].name} to take aim. ", Col.YLW))
        else:
            BaseVillainLogic.handle_movement(engine, villain, card)

    @staticmethod
    def on_bam(engine, villain, damage=1):
        """BAM: 1 damage to each hero in BOTH adjacent locations."""
        v_idx = villain.location_index
        affected = [(v_idx - 1) % 6, (v_idx + 1) % 6]
        
        engine.log.append(Col.wrap(" 🎯 BAM! Bullseye snipes from his nest! ", Col.RED))
        
        for idx in affected:
            BullseyeLogic._hit_sector_with_tax(engine, idx, damage, "Snipe")

    @staticmethod
    def resolve_special(engine, villain, card):
        sid = card.get("special_id")
        v_idx = villain.location_index

        # 🃏 MASTER ASSASSIN: 2 DMG to each Hero in adjacent locations
        if sid == "master_assassin":
            engine.log.append(Col.wrap(" 🃏 MASTER ASSASSIN: Point-blank is for amateurs. ", Col.CYAN + Col.BOLD))
            affected = [(v_idx - 1) % 6, (v_idx + 1) % 6]
            for idx in affected:
                BullseyeLogic._hit_sector_with_tax(engine, idx, 2, "Assassination Strike")

        # 🃏 IMPOSSIBLE SHOT: 2 DMG to Heroes in the OPPOSITE location
        elif sid == "impossible_shot":
            engine.log.append(Col.wrap(" 🃏 IMPOSSIBLE SHOT: 'Bet you didn't see that coming.' ", Col.CYAN + Col.BOLD))
            opposite_idx = (v_idx + 3) % 6
            BullseyeLogic._hit_sector_with_tax(engine, opposite_idx, 2, "Impossible Shot")

    @staticmethod
    def _hit_sector_with_tax(engine, loc_idx, amount, flavor):
        """Standard hit with 'Striking Unseen' tax support."""
        loc = engine.locations[loc_idx]
        final_dmg = amount
        
        # 👁️ STRIKING UNSEEN: +1 Damage at this location
        if loc.threat and not loc.threat.cleared:
            t_id = getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', ""))
            if t_id and "striking_unseen" in t_id:
                final_dmg += 1
            engine.log.append(Col.wrap(f"   👁️ STRIKING UNSEEN: Sniper nest advantage (+1 DMG)! ", Col.PURP))

        heroes = [h for h in engine.heroes if h.location_index == loc_idx and not getattr(h, 'is_ko', False)]
        if heroes:
            for h in heroes:
                engine.log.append(Col.wrap(f"   🎯 {flavor}: {h.name} hit for {final_dmg}! ", Col.RED))
                for _ in range(final_dmg):
                    h.take_damage(engine)
        else:
            engine.log.append(Col.wrap(f"   💨 {flavor}: The shot whistled through an empty street. ", Col.DARK_GRAY))

    @staticmethod
    def is_villain_shielded(engine, villain):
        """
        Handles 'Diversion' (No Win) and 'Hiding Place' (No DMG).
        """
        # ❌ DIVERSION: Cannot be defeated while this threat is active
        if any(l.threat and not l.threat.cleared and "diversion" in str(l.threat.id_internal).lower() for l in engine.locations):
            return True, Col.wrap(" ❌ DIVERSION: You're chasing a decoy! Bullseye cannot be defeated yet. ", Col.YLW + Col.BOLD)

        # ❌ DIVERSION: Cannot be defeated while this threat is active
        for l in engine.locations:
            if l.threat and not l.threat.cleared:
                t_id = getattr(l.threat, 'id_internal', getattr(l.threat, 'id', ""))
                if t_id and "diversion" in t_id:
                    return True, Col.wrap(" ❌ DIVERSION: You're chasing a decoy! Bullseye cannot be defeated yet. ", Col.YLW + Col.BOLD)

        # 🏚️ HIDING PLACE: No damage if Bullseye is in the same location as the threat
        loc = engine.locations[villain.location_index]
        if loc.threat and not loc.threat.cleared:
            t_id = getattr(loc.threat, 'id_internal', getattr(loc.threat, 'id', ""))
            if t_id and "hiding_place" in t_id:
                return True, Col.wrap(f" 🏚️ HIDING PLACE: Bullseye is obscured in {loc.name}! (No Damage) ", Col.CYAN)
        
        return False, ""

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Any Overflow is an instant win."""
        engine.log.append(Col.wrap(f" 🚨 OVERFLOW at {loc.name}! Bullseye completes the hit! ", Col.RED + Col.BOLD))
        engine.game_over = True
        engine.victory_status = "VILLAIN_WINS"
        engine.loss_reason = f"Bullseye achieved victory through an Overflow at {loc.name}! "

    @staticmethod
    def handle_hero_ko(engine, hero):
        """KOs increment the Contract Plot. No BAM (Ronan Rule)."""
        if getattr(hero, 'is_ko', False): return
        hero.is_ko = True
        
        v = engine.villain
        v.plot_value += 1
        engine.log.append(Col.wrap(f" 🎯 CONTRACT: {hero.name} has been taken out! ({v.plot_value}/{v.plot_max}) ", Col.RED + Col.BOLD))
        
        if v.plot_value >= v.plot_max:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = f"Bullseye completed his contract by KO'ing the entire team!"
            
    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Benjamin Poindexter is a psychopathic assassin who turns \n"
                "anything into a lethal projectile. He avoids direct brawls, \n"
                "preferring to establish kill zones and strike from afar."
            ),
            "rules": (
                "\"The Hit List & Sniper's Vantage\"\n"
                "Bullseye doesn't frenzy when a hero falls; he just crosses \n"
                "a name off his contract. If the total number of KOs equals \n"
                "your squad size, the mission is a failure.\n\n"
                "Furthermore, when relocating, he actively avoids close combat. \n"
                "He will skip occupied sectors to find an empty location to aim."
            ),
            "bam": (
                "\"Ricochet & Impossible Shots\"\n"
                "He rarely shoots at what's right in front of him. Bullseye \n"
                "deals damage to EVERY hero standing in the two sectors \n"
                "directly adjacent to him. Beware his Master Plan deck: he \n"
                "can even snipe heroes on the exact opposite side of the map!"
            ),
            "overflow": (
                "\"Perfect Execution\"\n"
                "Bullseye's plot relies on perfectly orchestrated collateral \n"
                "damage. If ANY location overflows with unplaceable tokens, \n"
                "he uses the resulting chaos to finish his contract and \n"
                "escape. An overflow results in immediate game over."
            ),
            "threats": (
                "He rigs the city with lethal traps and sniper nests.\n"
                "- Diversion: You cannot achieve victory while this is active.\n"
                "- Hiding Place: Bullseye is immune to damage while here.\n"
                "- Striking Unseen: Sniper tax. Damage taken here is increased by 1."
            )
        }
