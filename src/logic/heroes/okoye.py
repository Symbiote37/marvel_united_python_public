from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("okoye")
class OkoyeLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        
        if sid == "okoye_dora_milaje":
            from src.systems.status_system import StatusSystem
            # 🚨 Updated to use the generic 'bodyguard' status
            StatusSystem.apply_status(hero, "bodyguard", duration=1)
            engine.log.append(Col.wrap(" 🛡️ DORA MILAJE: Okoye is guarding her location!", Col.YLW))
            return True
            
        elif sid == "okoye_vibranium_spear":
            from src.systems.action_system import ActionSystem
            print(f"\n--- {Col.wrap('VIBRANIUM SPEAR: SELECT SECTOR', Col.YLW)} ---")
            adj = [(hero.location_index - 1) % 6, (hero.location_index + 1) % 6]
            for i, idx in enumerate(adj, 1): print(f" [{i}] {engine.locations[idx].name}")
            c = Col.get_choice(" >> ", 1, 2) - 1
            
            engine.log.append(Col.wrap(f" ⚡ VIBRANIUM SPEAR thrust into {engine.locations[adj[c]].name}!", Col.YLW))
            for _ in range(2): ActionSystem._handle_targeted_attack(engine, hero, adj[c])
            return True
            
        elif sid == "okoye_accomplished_strategist":
            if hero.deck:
                top_card = hero.deck[0]
                print(f"\n 👁️ {Col.wrap('STRATEGIST:', Col.CYAN)} Top card is {Col._get_card_label(top_card)}")
                choice = input(f" Move to bottom of deck? ({Col.wrap('y/n', Col.YLW)}): ").strip().lower()
                if choice == 'y':
                    hero.deck.append(hero.deck.pop(0))
                    engine.log.append(Col.wrap(" 👁️ Okoye altered her strategy.", Col.CYAN))
            return True
        return False
