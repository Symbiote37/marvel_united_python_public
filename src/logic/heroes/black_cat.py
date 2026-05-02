from src.utils.helpers import Col, ICON, get_plan_intel
from src.systems.special_abilities import SpecialAbilitySystem

@SpecialAbilitySystem.register("black_cat")
class BlackCatLogic:
    @classmethod # 🚥 CHANGE: Use classmethod
    def initialize(cls): # 🚥 CHANGE: Accepts 'cls'
        """
        By using 'cls', we avoid the NameError because we reference the 
        class object directly instead of looking it up by name.
        """
        from src.systems.status_system import StatusSystem
        # 🚥 CHANGE: Reference via cls
        StatusSystem.register_draw_interceptor(cls.execute_luck_swap)

    @staticmethod
    def resolve_special(engine, hero, card):
        """The 'Front Door' for Black Cat's play-time abilities."""
        sid = card.get("special_id")
        
        if sid == "black_cat_cat_instincts":
            return BlackCatLogic._cat_instincts(engine, hero)
            
        elif sid in ["black_cat_cat_luck", "black_cat_cat_claws"]:
            from src.systems.status_system import StatusSystem
            # 💡 DECOUPLED: We just apply a tag. The interceptor handles the rest.
            StatusSystem.apply_status(hero, "cat_luck", duration=1)
            engine.log.append(Col.wrap(" 🐈‍⬛ LUCK: Prepared to alter the next Master Plan!", Col.CYAN))
            return True
            
        return False

    @staticmethod
    def execute_luck_swap(engine, plan):
        from src.systems.status_system import StatusSystem
        from src.utils.helpers import Col, get_plan_intel
        
        for hero in engine.heroes:
            if StatusSystem.has_status(hero, "cat_luck"):
                p_intel = get_plan_intel(plan)
                
                print(f"\n{Col.wrap('🐈‍⬛ CAT LUCK:', Col.CYAN)} {hero.name} senses a bad omen!")
                print(f" Current Card: {Col.wrap(p_intel, Col.RED)}")
                
                # 🚨 HEADLESS FIX
                choice = engine.ui.ask_yes_no(" Use Luck to swap this to the bottom?")
                
                if choice:
                    # 🚥 THE RE-ROUTE:
                    # 1. Put the bad card on the bottom
                    engine.villain.plan_deck.append(plan)
                    
                    # 2. IMMEDIATELY draw the next one to replace it
                    # This ensures the VillainSystem still has a 'plan' to process
                    plan = engine.villain.draw_plan() 
                    
                    engine.log.append(Col.wrap(f" 🍀 {hero.name} altered the timeline.", Col.CYAN))
                
                StatusSystem.remove_status(hero, "cat_luck")
                break

        # Always return a plan object so the VillainSystem has something to resolve
        return plan
        
    @staticmethod
    def _cat_instincts(engine, hero):
        """Manual token selection logic."""
        print(f"\n--- {Col.wrap('CAT INSTINCTS', Col.CYAN + Col.BOLD)} ---")
        print(" Choose any combination of 2 tokens (Attack, Heroic, or Move):")
        
        options = {
            "1": ("attack", ICON['attack']),
            "2": ("heroic", ICON['heroic']),
            "3": ("move", ICON['move'])
        }
        
        chosen_icons = []
        for i in range(1, 3):
            # 🚨 HEADLESS FIX
            choice_int = engine.ui.ask_choice(f" Select Token #{i}: [1] {ICON['attack']} [2] {ICON['heroic']} [3] {ICON['move']} >> ", 1, 3)
            choice_str = str(choice_int)
            
            t_name, icon = options[choice_str]
            hero.add_token(t_name)
            chosen_icons.append(icon)
        
        token_display = " and ".join(chosen_icons)
        engine.log.append(Col.wrap(f" 🐈‍⬛ CAT INSTINCTS: {hero.name} gathered {token_display} tokens.", Col.CYAN))
        return True
