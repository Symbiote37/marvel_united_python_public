import sys
import termios
import tty
import select
import re

class Col:
    # Colors
    RED = '\033[91m'
    YLW = '\033[93m'
    GRN = '\033[92m'
    BLU = '\033[94m'
    PURP = '\033[95m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    DARK_GRAY = '\033[90m'
    ORN = '\033[38;5;208m'
    C111 = "\033[38;5;111m"  # Pale Sky Blue
    BOLD = '\033[1m'
    WHT = "\033[37m"  # Standard White
    END = '\033[0m'

    @staticmethod
    def wrap(text, color):
        return f"{color}{text}{Col.END}"

    # ⚡ CACHED REGEX: Eliminates recompilation overhead in hot UI loops
    _ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    @staticmethod
    def strip(text):
        """Removes ANSI escape sequences to get true visible length."""
        return Col._ANSI_ESCAPE_RE.sub('', text)

    @staticmethod
    def ljust(text, width):
        """Color-safe left justification."""
        visible_len = len(Col.strip(text))
        padding = width - visible_len
        return text + (" " * max(0, padding))

    @staticmethod
    def get_choice(prompt, min_val, max_val):
        """Standardized safe input for menu selections."""
        while True:
            try:
                val = int(input(prompt))
                if min_val <= val <= max_val:
                    return val
                print(Col.wrap(f" Invalid: Range {min_val}-{max_val}", Col.RED))
            except ValueError:
                print(Col.wrap(" Please enter a number", Col.RED))

    @staticmethod
    def get_neighbors(index, include_self=False):
        """
        Calculates adjacent indices in a 6-sector circular array.
        index: 0-5
        """
        left = (index - 1) % 6
        right = (index + 1) % 6
        
        neighbors = [left, right]
        if include_self:
            neighbors.append(index)
        return neighbors
        
    @staticmethod
    def _get_card_label(card):
        """Standardized card labeling for menus and logs."""
        if not card: return "[Empty]"
        
        # 1. Extract actions and map to icons, joining with exactly ONE space
        actions = card.get('actions', [])
        icons_str = " ".join([ICON.get(a.lower(), a.upper()) for a in actions])
        
        # 2. Format the name (stripping generic 'Action Card' clutter)
        c_name = card.get('name', '').replace('Action Card', '').strip()
        name_display = f" {c_name}" if c_name and "(" not in c_name else ""
        
        # 3. Combine and return the unified string
        if icons_str:
            return f"[{icons_str}]{name_display} "
        elif name_display:
            return name_display.strip() # Fallback for text-only/facedown cards
            
        return "[?]"
        
    @staticmethod
    def prompt_y_n(header, text):
        """Mandatory Y/N selection loop for Location Effects."""
        print(f"\n {Col.wrap(header, Col.CYAN)}")
        print(f" {text}")
        while True:
            choice = input(f" Use this effect? ({Col.wrap('y/n', Col.YLW)}): ").lower().strip()
            if choice in ['y', 'n']:
                return choice == 'y'
            print(Col.wrap(" ! Invalid input. Please enter 'y' or 'n'.", Col.RED))

# 🚨 MOVED: ICON dict must be declared after Col so we can use Col.wrap!
ICON = {
    "attack":    "✸",
    "heroic":    "★",
    "move":    "➡",
    "wild":    "❖",
    "crisis":  "Δ",
    "card":    "🂠",
    "threat":  "☠",
    "civilian": "🧑",
    "infected": "Δ",
    "thug": "👤"
}

def wait_for_user():
    # Flushes buffer and flickers the ▼
    termios.tcflush(sys.stdin, termios.TCIFLUSH)
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        visible = True
        while True:
            char = "▼" if visible else " "
            sys.stdout.write(char)
            sys.stdout.flush()
            rlist, _, _ = select.select([sys.stdin], [], [], 0.4)
            if rlist:
                sys.stdin.read(1)
                sys.stdout.write("\b \b")
                sys.stdout.flush()
                break
            visible = not visible
            sys.stdout.write("\b") 
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("")

def get_plan_intel(card):
    """Universal translator for Hero Oracle abilities."""
    if card.get('name'): return card.get('name').upper()
    
    parts = []
    
    move_val = card.get('move', 0)
    if isinstance(move_val, int) and move_val > 0: 
        parts.append(f"MOVE {move_val}")
    elif isinstance(move_val, str): 
        parts.append(f"MOVE {move_val.upper()}")
        
    if card.get('bam'): parts.append("BAM!")
    
    add_data = card.get('add', {})
    if add_data:
        has_thugs = any('thugs' in z for z in add_data.values())
        has_civs = any('civilians' in z for z in add_data.values())
        if has_thugs and has_civs: parts.append("+ 🧑 + 👤")
        elif has_thugs: parts.append(f"{ICON['thug']}s")
        elif has_civs: parts.append(f"{ICON['civilian']}s")
        
    return " | ".join(parts) if parts else "SCHEME"
    