from src.utils.helpers import Col

class CampaignSystem:
    @staticmethod
    def use_blue_bolt(engine, hero):
        """Spends a Campaign Blue Bolt to grant an immediate Wild token to the active pool. """
        if not hasattr(engine, 'campaign_manager') or engine.campaign_manager is None:
            return False
            
        bolts = engine.campaign_manager.state.get("blue_bolts", 0)
        if bolts <= 0:
            print(Col.wrap(" [!] No Blue Bolts available. ", Col.RED))
            return False
            
        print(Col.wrap(f"\n ⚠️ You have {bolts} Blue Bolt(s) remaining for the entire campaign. ", Col.YLW))
        
        # 🛡️ HEADLESS FIX: UI adapter integration
        if not engine.ui.ask_yes_no(Col.wrap(" Spend 1 Blue Bolt to gain an immediate ❖ token?", Col.CYAN)):
            print(Col.wrap(" Blue Bolt conserved. ", Col.DARK_GRAY))
            return False
            
        # Tell the database (Manager) to deduct the resource
        engine.campaign_manager.state["blue_bolts"] -= 1
        engine.campaign_manager.save_state()
        
        # Apply the mechanical combat benefit
        if getattr(engine, 'active_pool', None) is None:
            engine.active_pool = {}
        engine.active_pool["wild"] = engine.active_pool.get("wild", 0) + 1
        
        engine.log.append(Col.wrap(f" ✨ SURGE: {hero.name} channels a Blue Bolt into a Wild Action! ", Col.CYAN + Col.BOLD))
        return True
