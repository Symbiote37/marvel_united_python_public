import random
from src.logic.villains.base_villain import BaseVillainLogic
from src.utils.helpers import Col

class DormammuLogic(BaseVillainLogic):
    
    @staticmethod
    def check_custom_game_status(engine):
        """WIN CONDITION: Dormammu's deck runs out."""
        if len(engine.villain.plan_deck) == 0:
            engine.game_over = True
            engine.victory_status = "HEROES_WIN"
            engine.victory_reason = "ETERNAL DEFENSE: The Dark Dimension's influence has withered!"
            return True
        return False
        
    @staticmethod
    def is_defeated(engine):
        """Dormammu cannot be defeated by standard damage."""
        return False

    @staticmethod
    def perform_setup(engine, villain):
        villain.plot_name = "RITUAL TRACK"
        villain.plot_max = 20
        villain.plot_value = 0
        
        # 🚨 THE SACRIFICE: Setup card removal based on player count
        num_players = len(engine.heroes)
        cards_to_remove = {2: 2, 3: 1}.get(num_players, 0)
            
        if cards_to_remove > 0:
            random.shuffle(villain.plan_deck)
            for _ in range(cards_to_remove):
                if villain.plan_deck:
                    villain.plan_deck.pop()
            engine.log.append(Col.wrap(f" 🌀 DIMENSIONAL WEAKNESS: {cards_to_remove} cards removed for {num_players} players.", Col.PURP))

        engine.log.append(Col.wrap(" 🪐 DORMAMMU: 'Your world is but a morsel for my hunger!'", Col.PURP + Col.BOLD))

    @staticmethod
    def on_bam(engine, villain, damage=2):
        """BAM: 2 damage to all heroes at Dormammu's site."""
        v_idx = villain.location_index
        if v_idx == -1: return
        v_loc = engine.locations[v_idx]
        
        # 🚨 ARMOR FIX: getattr for list comprehension
        targets = [h for h in engine.heroes if h.location_index == v_idx and not getattr(h, 'is_ko', False)]
        
        if not targets:
            engine.log.append(Col.wrap(f"   💥 BAM! Dormammu's power surges at {v_loc.name} but finds no one!", Col.PURP))
            return

        engine.log.append(Col.wrap(f"   💥 BAM! Dormammu unleashes the Dark Dimension at {v_loc.name}! ", Col.PURP + Col.BOLD))
        for h in targets:
            for _ in range(damage):
                h.take_damage(engine)
            engine.log.append(Col.wrap(f"       💥 {h.name} takes {damage} dmg!", Col.RED))
            
            # 🚨 ARMOR FIX: getattr for the KO check
            if getattr(h, 'is_ko', False):
                DormammuLogic.handle_hero_ko(engine, h)

    @staticmethod
    def on_overflow(engine, villain, loc, t_type):
        """Overflow feeds the Ritual Track."""
        engine.log.append(Col.wrap(f"   🌀 RITUAL OVERFLOW: Chaos at {loc.name} feeds the Dark Dimension!", Col.PURP))
        villain.plot_value += 1
        DormammuLogic.check_destabilization(engine)

    @staticmethod
    def handle_hero_ko(engine, hero):
        """Hero KOs fuel the ritual."""
        engine.villain.plot_value += 1
        engine.log.append(Col.wrap("   📈 RITUAL TRACK advances from Hero KO!", Col.PURP))
        DormammuLogic.check_destabilization(engine)
        BaseVillainLogic.handle_hero_ko(engine, hero)

    @staticmethod
    def get_attack_options(engine, hero, location_override=None):
        """🚨 PERMANENT INVULNERABILITY: Removes the 'Attack Villain' option entirely."""
        target_idx = location_override if location_override is not None else hero.location_index
        loc = engine.locations[target_idx]
        opts = []
        if loc.thugs > 0:
            opts.append({"label": "Attack Thug", "id": "m"})
        if loc.threat and not loc.threat.cleared:
            if getattr(loc.threat, 'hp', 0) > 0 and getattr(loc.threat, 'heroic_req', 0) <= 0:
                opts.append({"label": f"Attack {loc.threat.name}", "id": "h"})
        return opts

    @staticmethod
    def resolve_special(engine, villain, card):
        """Handles Ritual card: Track increases by total population (T+C) at his site."""
        if card.get("special_id") == "ritual":
            loc = engine.locations[villain.location_index]
            count = loc.civilians + loc.thugs
            villain.plot_value += count
            engine.log.append(Col.wrap(f" 🕯️ RITUAL: Dormammu consumes {count} souls at {loc.name}!", Col.PURP))
            DormammuLogic.check_destabilization(engine)

    @staticmethod
    def check_destabilization(engine):
        """Loss Condition: The Ritual Track hits 20."""
        v = engine.villain
        if v.plot_value >= v.plot_max:
            engine.game_over = True
            engine.victory_status = "VILLAIN_WINS"
            engine.loss_reason = "RITUAL COMPLETE: The Dark Dimension has consumed our reality."

    @staticmethod
    def get_intel_report():
        """Returns the thematic dossier for the pre-game S.H.I.E.L.D. briefing."""
        return {
            "profile": (
                "Dormammu is an interdimensional conqueror of incalculable power. \n"
                "He cannot be defeated by physical means; you must outlast his \n"
                "assault and prevent him from dragging Earth into the Dark Dimension."
            ),
            "rules": (
                "\"The Dark Ritual & War of Attrition\"\n"
                "Dormammu is completely IMMUNE to damage. To win, you must survive \n"
                "until his Master Plan deck runs completely dry.\n\n"
                "However, if his Ritual Track reaches 20, he consumes our reality \n"
                "and you lose. KOs feed the ritual (+1) instead of triggering a BAM. \n"
                "Clearing 2 missions will burn the top card of his deck, bringing \n"
                "you one step closer to outlasting him!"
            ),
            "bam": (
                "\"Dimensional Blast\"\n"
                "A devastating localized attack. Dormammu deals 2 damage to every \n"
                "hero currently standing in his location."
            ),
            "overflow": (
                "\"Dimensional Bleed\"\n"
                "When a sector overruns, the barrier between worlds weakens. Every \n"
                "unplaceable token immediately advances the Ritual Track by 1."
            ),
            "threats": (
                "His very presence warps the reality of the battlefield.\n"
                "- Banishment: Reality is distorted; rescuing Civilians costs 2 ★.\n"
                "- Dark Dimension: Minions are empowered; defeating Thugs costs 2 ✸.\n"
                "- Elemental Control: Amplifies all damage taken in this sector by 1."
            )
        }
