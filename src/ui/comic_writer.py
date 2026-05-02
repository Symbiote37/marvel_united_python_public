import random
from src.utils.helpers import Col

class ComicWriter:
    @staticmethod
    def _format_names(names):
        """Intelligently formats a list of MVP names with commas and 'and'."""
        if not names: return ""
        if len(names) == 1: return names[0]
        if len(names) == 2: return f"{names[0]} and {names[1]}"
        return ", ".join(names[:-1]) + f", and {names[-1]}"

    @staticmethod
    def display_issue_summary(engine):
        stats = getattr(engine, 'match_stats', {})
        if not stats: return

        print(Col.wrap(f"\n{'='*50}", Col.CYAN))
        
        # 🚨 DYNAMIC TITLE LOGIC
        if engine.victory_status == "HEROES_WIN":
            print(Col.wrap(f" 📖 ISSUE SUMMARY: THE FALL OF {engine.villain.name.upper()}", Col.CYAN + Col.BOLD))
        else:
            print(Col.wrap(f" 📖 ISSUE SUMMARY: THE TRIUMPH OF {engine.villain.name.upper()}", Col.RED + Col.BOLD))
            
        print(Col.wrap(f"{'='*50}", Col.CYAN))

        # 🚨 TIE-BREAKER LOGIC: Finds ALL heroes who share the top score
        def get_mvps(stat_key):
            max_val = max((v.get(stat_key, 0) for v in stats.values()), default=0)
            if max_val == 0: return [], 0
            return [k.replace('_', ' ').title() for k, v in stats.items() if v.get(stat_key, 0) == max_val], max_val

        hitters, dmg = get_mvps('damage')
        saviors, civs = get_mvps('civs')
        brawlers, thugs = get_mvps('thugs')
        tacticians, threats = get_mvps('threats')
        vanguards, moves = get_mvps('moves')
        martyrs, kos = get_mvps('kos')

        if hitters:
            names = ComicWriter._format_names(hitters)
            verb = "were absolute wrecking balls" if len(hitters) > 1 else "was an absolute wrecking ball"
            lines = [
                f"{names} {verb}, dealing {dmg} damage directly to the enemy forces.",
                f"The villain had no answer for {names}, who relentlessly pounded them for {dmg} damage."
            ]
            print(Col.wrap(f"\n 💥 THE HEAVY HITTER: {names}", Col.RED + Col.BOLD))
            print(f"    {random.choice(lines)}")

        if saviors:
            names = ComicWriter._format_names(saviors)
            c_word = "civilian" if civs == 1 else "civilians"
            lines = [
                f"Countless lives were saved today because {names} prioritized rescuing {civs} {c_word}.",
                f"{names} rushed into the crossfire, prioritizing the escort of {civs} bystanders to safety."
            ]
            print(Col.wrap(f"\n ✨ THE SAVIOR: {names}", Col.YLW + Col.BOLD))
            print(f"    {random.choice(lines)}")

        if brawlers:
            names = ComicWriter._format_names(brawlers)
            t_word = "thug" if thugs == 1 else "thugs"
            print(Col.wrap(f"\n 👊 THE BRAWLER: {names}", Col.PURP + Col.BOLD))
            print(f"    {names} kept the streets clear, taking down {thugs} {t_word} in hand-to-hand combat.")

        if tacticians:
            names = ComicWriter._format_names(tacticians)
            t_word = "major threat" if threats == 1 else "major threats"
            verb = "were" if len(tacticians) > 1 else "was"
            lines = [
                f"{names} {verb} the ultimate problem solver, dismantling {threats} {t_word} during the crisis.",
                f"When the situation looked dire, {names} stepped up and neutralized {threats} {t_word}."
            ]
            print(Col.wrap(f"\n 🧠 THE TACTICIAN: {names}", Col.CYAN + Col.BOLD))
            print(f"    {random.choice(lines)}")

        if vanguards:
            names = ComicWriter._format_names(vanguards)
            lines = [
                f"Constantly on the move, {names} repositioned {moves} times to control the battlefield.",
                f"With unmatched mobility, {names} executed {moves} tactical maneuvers across the city."
            ]
            print(Col.wrap(f"\n ⚡ THE VANGUARD: {names}", Col.BLU + Col.BOLD))
            print(f"    {random.choice(lines)}")

        if martyrs:
            names = ComicWriter._format_names(martyrs)
            k_word = "time" if kos == 1 else "times"
            print(Col.wrap(f"\n 🛡️ THE MARTYR: {names}", Col.DARK_GRAY + Col.BOLD))
            print(f"    Sacrificing everything, {names} acted as the team's shield, falling {kos} {k_word}.")
