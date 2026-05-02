from src.utils.helpers import Col, ICON
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("vision")
class VisionLogic:
    @staticmethod
    def resolve_special(engine, hero, card):
        sid = card.get("special_id")
        if sid == "vision_intangibility": return VisionLogic._intangibility(engine, hero)
        elif sid == "vision_evolving_intellect": return VisionLogic._evolving_intellect(engine, hero)
        elif sid == "vision_solar_gem_blast": return VisionLogic._solar_gem_blast(engine, hero)
        return False

    @staticmethod
    def _intangibility(engine, hero):
        print(f"\n--- {Col.wrap('👻 INTANGIBILITY', Col.CYAN)} ---")
        # 🚨 HEADLESS FIX
        if engine.ui.ask_raw(" [1] Execute: Evade damage until next turn\n [0] Cancel\n >> ", {'1', '0'}) != '1': return False
        
        hero.is_invincible = True
        hero.invincible_deflect_msg = f" 👻 The attack phases right through {hero.name}!"
        hero.invincible_wear_off_msg = f" 🤖 {hero.name} solidifies."
        engine.log.append(Col.wrap(f" 👻 {hero.name} becomes completely intangible!", Col.PURP))
        return True

    @staticmethod
    def _evolving_intellect(engine, hero):
        print(f"\n--- {Col.wrap('🧠 EVOLVING INTELLECT', Col.CYAN)} ---")
        # 🚨 HEADLESS FIX
        if engine.ui.ask_raw(" [1] Execute: Gain ❖ per full location\n [0] Cancel\n >> ", {'1', '0'}) != '1': return False
        
        count = sum(1 for loc in engine.locations if loc.total_figures() >= loc.capacity)
        if count > 0:
            if not hasattr(hero, 'action_tokens'): hero.action_tokens = []
            for _ in range(count): hero.action_tokens.append("wild")
            engine.log.append(Col.wrap(f" 🧠 Evolving Intellect: {hero.name} gains {count} {ICON['wild']} tokens!", Col.CYAN))
        else:
            engine.log.append(Col.wrap(f" 🧠 {hero.name} analyzes the board, but finds no full locations.", Col.YLW))
        return True

    @staticmethod
    def _solar_gem_blast(engine, hero):
        print(f"\n--- {Col.wrap('☀️ SOLAR GEM BLAST', Col.RED)} ---")
        # 🚨 HEADLESS FIX
        if engine.ui.ask_raw(" [1] Execute: Consume timeline ✸ for massive damage\n [0] Cancel\n >> ", {'1', '0'}) != '1': return False

        story = engine.storyline.cards
        recent_hero_cards = [c for c in story if not c.get("is_facedown")][-4:]
        attack_count = sum(c.get("actions", []).count("attack") for c in recent_hero_cards)
        
        if attack_count > 0:
            engine.log.append(Col.wrap(f" ☀️ {hero.name} channels {attack_count} power into a Solar Gem Blast!", Col.RED))
            return DamageSystem.apply_targeted_damage(engine, hero, hero.location_index, attack_count, "Solar Gem Blast")
        else:
            engine.log.append(Col.wrap(f" ☀️ {hero.name}'s Solar Gem lacks charge (0 ✸ in recent timeline).", Col.YLW))
            return True
