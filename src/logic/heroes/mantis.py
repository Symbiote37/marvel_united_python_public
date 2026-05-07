from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("mantis")
class MantisLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "mantis_astral_projection":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(hero, "astral_projection", duration=1)
            engine.log.append(Col.wrap(" 🧘‍♀️ ASTRAL PROJECTION: Mantis can interact with any Location this turn!", Col.GRN))
            return True
        elif sid == "mantis_psychic_healing":
            engine.log.append(Col.wrap(" 🧠 PSYCHIC HEALING:", Col.GRN))
            
            # 🚨 THE FIX: Exclude Mantis (hero) from the target pool
            active_heroes = [h for h in engine.heroes if not getattr(h, 'is_ko', False) and h != hero]
            
            if not active_heroes:
                engine.log.append(Col.wrap("   ...But there are no conscious allies to heal!", Col.DARK_GRAY))
                return True

            if len(active_heroes) == 1:
                target = active_heroes[0]
            else:
                print(Col.wrap("\n SELECT TARGET FOR PSYCHIC HEALING (Draw 2 Cards):", Col.CYAN))
                for i, h in enumerate(active_heroes):
                    print(f" [{i+1}] {h.name} (Hand: {len(h.hand)}, Deck: {len(h.deck)})")
                choice = engine.ui.ask_choice(" Choose >> ", 1, len(active_heroes))
                target = active_heroes[choice - 1]

            cards_drawn = 0
            for _ in range(2):
                if target.deck:
                    target.hand.append(target.deck.pop(0))
                    cards_drawn += 1
            engine.log.append(Col.wrap(f"   ✨ {target.name} recovered {cards_drawn} cards from their deck!", Col.CYAN))
            return True

        elif sid == "mantis_emphatic":
            from src.systems.status_system import StatusSystem
            StatusSystem.apply_status(engine, "cancel_next_bam", duration=1)
            engine.log.append(Col.wrap(" 🧠 EMPATHIC: The next BAM! is cancelled!", Col.GRN))
            return True
        return False
        