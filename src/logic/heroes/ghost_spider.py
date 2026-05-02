from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("ghost-spider")
class GhostSpiderLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "ghost-spider_webweaver":
            return GhostSpiderLogic._webweaver(engine, hero)
        elif sid == "ghost-spider_acrobatic_fighting":
            return GhostSpiderLogic._acrobatic_fighting(engine, hero)
        return False

    @staticmethod
    def _webweaver(engine, hero):
        print(f"\n{Col.wrap('🕸️ WEBWEAVER:', Col.CYAN)} Swap 2 active Threat cards.")
        
        threat_locs = [loc for loc in engine.locations if loc.threat and not loc.threat.cleared]
        if len(threat_locs) < 2:
            print(Col.wrap(" ! Not enough active threats to swap.", Col.RED))
            return False
            
        print(" Select the FIRST threat to swap:")
        for i, loc in enumerate(threat_locs, 1):
            print(f" [{i}] {loc.threat.name} (at {loc.name})")
        
        choice1 = Col.get_choice(" >> ", 1, len(threat_locs)) - 1
        loc1 = threat_locs[choice1]
        
        print("\n Select the SECOND threat to swap:")
        for i, loc in enumerate(threat_locs, 1):
            if i - 1 != choice1:
                print(f" [{i}] {loc.threat.name} (at {loc.name})")
                
        choice2 = Col.get_choice(" >> ", 1, len(threat_locs)) - 1
        loc2 = threat_locs[choice2]
        
        # Perform the swap
        loc1.threat, loc2.threat = loc2.threat, loc1.threat
        engine.log.append(Col.wrap(f" 🕸️ {hero.name} webbed and swapped {loc1.threat.name} and {loc2.threat.name}!", Col.CYAN))
        return True

    @staticmethod
    def _acrobatic_fighting(engine, hero):
        loc = engine.locations[hero.location_index]
        if loc.thugs <= 0:
            print(Col.wrap(" ! No thugs in this location to defeat.", Col.RED))
            return False
            
        from src.systems.action_system import ActionSystem
        from src.systems.token_system import TokenSystem
        thugs_cleared = loc.thugs
        for _ in range(thugs_cleared):
            TokenSystem.apply_thug_defeat(engine, loc, hero, amount=1)
            
        engine.log.append(Col.wrap(f" 🕸️ ACROBATICS: {hero.name} cleared all {thugs_cleared} Thugs from {loc.name}!", Col.CYAN))
        return True
        