import random
from src.utils.helpers import Col, wait_for_user

class BaseController:
    """The universal interface the GameEngine uses to ask questions."""
    def ask_choice(self, prompt_text, options_or_min, max_val=None, return_index=False): raise NotImplementedError
    def ask_raw(self, prompt_text, valid_options): raise NotImplementedError
    def ask_yes_no(self, prompt_text): raise NotImplementedError
    def wait(self): raise NotImplementedError
    def acknowledge(self, message): raise NotImplementedError

class HumanController(BaseController):
    """Translates engine requests into terminal prompts for a human player."""
    def ask_choice(self, prompt_text, options_or_min, max_val=None, return_index=False):
        # 🔌 JULES'S UPGRADE: Handling dynamic text lists
        if isinstance(options_or_min, list):
            options = options_or_min
            print(prompt_text)
            for i, opt in enumerate(options, 1):
                print(f" [{i}] {opt}")
            while True:
                choice = input(" >> ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(options):
                        return idx if return_index else options[idx]
                except ValueError:
                    pass
                print(Col.wrap(" [X] Invalid selection. Please enter a valid number.", Col.RED))
        
        # 🛡️ THE SECURE GATE: Handling min/max integer ranges natively
        else:
            min_val = options_or_min
            while True:
                choice = input(prompt_text).strip()
                try:
                    val = int(choice)
                    if min_val <= val <= max_val:
                        return val
                except ValueError:
                    pass
                print(Col.wrap(f" [X] Invalid selection. Must be between {min_val} and {max_val}.", Col.RED))

    def ask_raw(self, prompt_text, valid_options):
        while True:
            choice = input(prompt_text).strip().upper()
            if choice in valid_options: return choice
            elif choice == '9': return '9' 
            print(Col.wrap(" Invalid Selection.", Col.RED))

    def ask_yes_no(self, prompt_text):
        while True:
            choice = input(prompt_text).strip().lower()
            if choice in ['y', 'yes']: return True
            if choice in ['n', 'no']: return False
            print(Col.wrap(" Please enter 'y' or 'n'.", Col.RED))

    def wait(self):
        wait_for_user()
        
    def acknowledge(self, message):
        print(Col.wrap(message, Col.YLW))
        input(" >> ")
