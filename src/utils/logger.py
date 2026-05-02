import sys
import traceback
import json
import os
from datetime import datetime

class DangerRoomRecorder:
    LOG_FILE = "logs/crash_history.json"

    @staticmethod
    def initialize():
        # Hijack the default error handler
        sys.excepthook = DangerRoomRecorder.record_crash

    @staticmethod
    def record_crash(exctype, value, tb):
        # 1. Capture the "DNA" of the crash
        crash_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error_type": str(exctype.__name__),
            "message": str(value),
            "traceback": "".join(traceback.format_exception(exctype, value, tb)),
            "last_module": traceback.extract_tb(tb)[-1].filename.split('/')[-1]
        }

        # 2. Append to persistent storage
        history = []
        if os.path.exists(DangerRoomRecorder.LOG_FILE):
            with open(DangerRoomRecorder.LOG_FILE, 'r') as f:
                try:
                    history = json.load(f)
                except:
                    history = []

        history.append(crash_data)
        history = history[-50:] # Keep the last 50 incidents

        if not os.path.exists("logs"): os.makedirs("logs")
        with open(DangerRoomRecorder.LOG_FILE, 'w') as f:
            json.dump(history, f, indent=4)

        # 3. Print to terminal so you still see the error live
        sys.__excepthook__(exctype, value, tb)
        