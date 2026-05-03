from src.utils.helpers import Col

class SpecialAbilitySystem:
    # 🚥 THE BUS: Starts empty, filled automatically by @register tags
    HERO_LOGIC_MAP = {}

    @classmethod
    def register(cls, hero_id):
        """
        The Automated Switchboard:
        1. Adds the hero to the map.
        2. Automatically triggers 'initialize()' if it exists.
        """
        def wrapper(logic_class):
            cls.HERO_LOGIC_MAP[hero_id] = logic_class
            
            # 🔌 AUTO-PLUG:
            # If the hero has a Villain-Phase listener (like Luck), 
            # it registers itself immediately.
            if hasattr(logic_class, "initialize"):
                logic_class.initialize()
                
            return logic_class
        return wrapper
    
    @staticmethod
    def resolve(engine, hero, card):
        sid = card.get("special_id")
        if not sid: 
            return False

        flavor_name = card.get("name", "Ability").upper()

        # ==========================================
        # 1. UNIVERSAL ABILITIES (The Interceptor)
        # ==========================================

        if sid == "invulnerability":
            hero.is_invincible = True 
            hero.invincible_deflect_msg = f"   🛡️ {hero.name} easily evaded the attack using {flavor_name}!"
            hero.invincible_wear_off_msg = f" 🧍 {hero.name}'s {flavor_name} wears off."
            engine.log.append(Col.wrap(f" 🛡️ PASSIVE: {hero.name} activated {flavor_name}. Damage nullified this round.", Col.CYAN + Col.BOLD))
            return True
            
        elif sid == "draw_up_to_3":
            needed = 3 - len(hero.hand)
            if needed > 0:
                actual_drawn = min(needed, len(hero.deck))
                if actual_drawn > 0:
                    hero.draw_cards(actual_drawn)
                    engine.log.append(Col.wrap(f" 🔋 PASSIVE: {flavor_name} triggered! {hero.name} drew {actual_drawn} card(s).", Col.CYAN))
                else:
                    engine.log.append(Col.wrap(f" 🔋 PASSIVE: {flavor_name} triggered, but deck is empty!", Col.RED))
            else:
                engine.log.append(Col.wrap(f" 🔋 PASSIVE: {flavor_name} triggered, but hand is already full.", Col.DARK_GRAY))
            return True

        # ==========================================
        # 2. HERO-SPECIFIC ABILITIES (The Router)
        # ==========================================
        
        logic_class = SpecialAbilitySystem.HERO_LOGIC_MAP.get(hero.internal_id)
        if logic_class and hasattr(logic_class, "resolve_special"):
            return logic_class.resolve_special(engine, hero, card)
        
        return False

    @staticmethod
    def initialize_interceptors(engine):
        for logic_class in SpecialAbilitySystem.HERO_LOGIC_MAP.values():
            if hasattr(logic_class, 'initialize'):
                logic_class.initialize()

    @classmethod
    def trigger_event(cls, engine, hero, event_name, **kwargs):
        """The Radio Tower: Shouts events to the hero logic brain."""
        h_id = (getattr(hero, 'internal_id', '')).replace("-", "_").lower()
        logic_class = cls.HERO_LOGIC_MAP.get(h_id)
        
        if logic_class and hasattr(logic_class, event_name):
            getattr(logic_class, event_name)(engine, hero, **kwargs)

# Move the import to the absolute bottom, unindented
import src.logic.heroes 
