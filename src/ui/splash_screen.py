import os
import time
from src.utils.helpers import Col

class SplashScreen:
    # 🚨 PADDED BORDER FRAME: Centered strictly to a 50-character inner width
    LOGO = r"""
 __________________________________________________
/                                                  \
|                                                  |
|         ___  ___                     _           |
|         |  \/  |                    | |          |
|         | .  . | __ _ _ ____   _____| |          |
|         | |\/| |/ _` | '__\ \ / / _ \ |          |
|         | |  | | (_| | |   \ V /  __/ |          |
|         \_|  |_/\__,_|_|    \_/ \___|_|          |
|                                                  |
|          _   _       _ _           _             |
|         | | | |     (_) |         | |            |
|         | | | |_ __  _| |_ ___  __| |            |
|         | | | | '_ \| | __/ _ \/ _` |            |
|         | |_| | | | | | ||  __/ (_| |            |
|          \___/|_| |_|_|\__\___|\__,_|            |
|                                                  |
|         -- P Y T H O N   E D I T I O N --        |
|                                                  |
\__________________________________________________/
    """

    @staticmethod
    def show():
        """Renders the splash sequence and waits for user interaction."""
        # 1. Clear the terminal of any background noise/paths
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # 2. Add some vertical padding to center it
        print("\n" * 4)
        
        # 3. Print the logo in bold red
        print(Col.wrap(SplashScreen.LOGO, Col.RED + Col.BOLD))
        
        # 4. Print the subtitle/prompt
        print(Col.wrap("                   [ TERMINAL ENGINE ]\n", Col.YLW))
        print(Col.wrap("                  Press ENTER to begin...", Col.DARK_GRAY))
        
        # 5. Hold the screen until the user acts
        input()
        
        # 6. Clear the screen again before handing off to the Main Menu
        os.system('clear' if os.name == 'posix' else 'cls')
        