import sys
from src.ui.main_menu import MainMenu
from src.utils.helpers import Col
from src.utils.logger import DangerRoomRecorder

if __name__ == "__main__":
    # 🛰️ ACTIVATE BLACK BOX: This must be initialized first.
    # It hijacks the system crash handler to record telemetry before exit.
    DangerRoomRecorder.initialize()

    try:
        # 🔑 THE KEY: This is the entry point that boots the OS router
        MainMenu.run()
    except KeyboardInterrupt:
        # We keep this because a user 'quitting' isn't a 'crash'
        print(Col.wrap("\n\n [!] System Interrupted. Powering down...", Col.RED))
        sys.exit(0)
  