from src.utils.helpers import Col
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("mockingbird")
class MockingbirdLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "mockingbird_spymaster":
            return MockingbirdLogic._spymaster(engine, hero)
        elif sid == "mockingbird_battle_staves":
            return MockingbirdLogic._battle_staves(engine, hero)
        return False

    @staticmethod
    def _spymaster(engine, hero):
        from src.systems.status_system import StatusSystem
        loc = engine.locations[hero.location_index]
        StatusSystem.apply_status(loc, "block_reinforcements", duration=1)
        engine.log.append(f" [*] PASSIVE: {hero.name} secures {loc.name}. No reinforcements allowed!")
        return True

    @staticmethod
    def _battle_staves(engine, hero):
        loc = engine.locations[hero.location_index]
        if loc.thugs <= 0:
            print(Col.wrap(" ! No thugs in this location to defeat.", Col.RED))
            return False
            
        from src.systems.action_system import ActionSystem
        from src.systems.token_system import TokenSystem
        defeated = min(2, loc.thugs)
        for _ in range(defeated):
            TokenSystem.apply_thug_defeat(engine, loc, hero, amount=1)
            
        engine.log.append(Col.wrap(f" 🦯 BATTLE STAVES: {hero.name} defeated {defeated} Thugs!", Col.CYAN))
        return True
