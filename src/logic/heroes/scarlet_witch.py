from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("scarlet_witch")
class ScarletWitchLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "scarlet_witch_chaos_magic":
            return ScarletWitchLogic._chaos_magic(engine, hero)
        elif sid == "scarlet_witch_psionic_energy_blast":
            return ScarletWitchLogic._psionic_energy_blast(engine, hero)
        elif sid == "scarlet_witch_psionic_energy_field":
            return ScarletWitchLogic._psionic_energy_field(engine, hero)
        return False

    @staticmethod
    def _chaos_magic(engine, hero):
        """Another Hero swaps a hand card with their faceup Storyline card."""
        other_heroes = [h for h in engine.heroes if h != hero and not h.is_ko]
        
        if not other_heroes:
            print(Col.wrap(" ! No other active heroes to benefit from Chaos Magic.", Col.RED))
            return False

        print(f"\n--- {Col.wrap('CHAOS MAGIC: SELECT HERO', Col.CYAN)} ---")
        for i, h in enumerate(other_heroes, 1):
            print(f" [{i}] {h.name}")
        
        choice = engine.ui.ask_choice(" >> ", 1, len(other_heroes))
        target_hero = other_heroes[choice - 1]

        # Reuse the existing swap logic helper from its new home
        from src.systems.special_abilities import SpecialAbilitySystem
        # We simulate the Stark Labs prompt for the targeted hero
        SpecialAbilitySystem.swap_with_storyline(engine, target_hero, {"text": f"Chaos Magic: {target_hero.name}, swap a card!"})
        return True

    @staticmethod
    def _psionic_energy_blast(engine, hero):
        """3 Damage against a single enemy in an adjacent Location."""
        from src.systems.action_system import ActionSystem
        from src.systems.damage_system import DamageSystem
        from src.systems.token_system import TokenSystem
        from src.systems.villain_system import VillainSystem
        
        loc_idx = hero.location_index
        adj_indices = [(loc_idx - 1) % 6, (loc_idx + 1) % 6]
        
        print(f"\n--- {Col.wrap('PSIONIC BLAST: SELECT SECTOR', Col.CYAN)} ---")
        for i, idx in enumerate(adj_indices, 1):
            print(f" [{i}] {engine.locations[idx].name}")
        
        choice = Col.get_choice(" >> ", 1, 2)
        target_idx = adj_indices[choice - 1]
        target_loc = engine.locations[target_idx]

        # Gather single-target options
        targets = []
        # 1. Add Villain/Henchmen (Standard)
        from src.systems.villain_system import VillainSystem
        for v in VillainSystem.get_attackable_villains_at(engine, target_idx):
            targets.append({"name": v["name"], "obj": v["ref"], "type": "v"})
            
        if target_loc.threat and not target_loc.threat.cleared and getattr(target_loc.threat, 'hp', 0) > 0:
            from src.logic.shield_logic import is_target_vulnerable
            if is_target_vulnerable(engine, target_loc.threat)[0]:
                targets.append({"name": target_loc.threat.name, "obj": target_loc.threat, "type": "h"})
        
        # 2. Add Single Thug (Corrected targeting)
        if target_loc.thugs > 0:
            targets.append({"name": "A single Thug", "obj": target_loc, "type": "thug"})

        if not targets:
            print(Col.wrap(" ! No single-enemy targets available in that location.", Col.RED))
            return False

        print(f"\n--- {Col.wrap('SELECT TARGET (3 DAMAGE)', Col.RED)} ---")
        for i, t in enumerate(targets, 1):
            print(f" [{i}] {t['name']}")
        
        t_choice = Col.get_choice(" >> ", 1, len(targets))
        selection = targets[t_choice - 1]

        engine.log.append(Col.wrap(f" ⚛️ PSIONIC BLAST: Wanda detonates energy in {target_loc.name}!", Col.MAGENTA + Col.BOLD))
        
        from src.systems.action_system import ActionSystem
        from src.systems.damage_system import DamageSystem
        from src.systems.token_system import TokenSystem
        if selection["type"] == "thug":
            # 3 Damage to a single 1-HP enemy just defeats it once. Overkill is wasted.
            TokenSystem.apply_thug_defeat(engine, selection["obj"], hero)
            engine.log.append("   💥 The blast vaporized the Thug!")
        else:
            DamageSystem.deal_enemy_damage(engine, selection["obj"], amount=3, flavor="Blasted")

        return True

    @staticmethod
    def _psionic_energy_field(engine, hero):
        """Cancel the first damage each hero would suffer from the next Master Plan."""
        from src.systems.status_system import StatusSystem
        engine.log.append(Col.wrap(f" 🛡️ PSIONIC FIELD: Wanda weaves a protective barrier around the team!", Col.MAGENTA))
        
        for h in engine.heroes:
            if not h.is_ko:
                StatusSystem.apply_status(h, "prevent_next_damage", duration=1)
        return True
        