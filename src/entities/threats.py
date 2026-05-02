# src/entities/threats.py

from src.utils.helpers import Col, ICON

class Threat:
    def __init__(self, data):
        """Initializes from a dictionary (JSON data)."""
        # The internal ID is the 'fingerprint' for logic matching
        self.id = data.get("id") 
        self.id_internal = data.get("id_internal")
        self.name = data.get("name", "Unknown Threat")
        
        # The core dichotomy: HP vs Multi-Token Requirements
        self.hp = data.get("hp", 0)
        self.heroic_req = data.get("heroic_req", 0)
        self.move_req = data.get("move_req", 0)
        self.attack_req = data.get("attack_req", 0)
        
        # Track applied tokens
        self.heroic_tokens = 0
        self.move_tokens = 0
        self.attack_tokens = 0
        
        self.type = data.get("type", "threat")
        self.short_effect = data.get("short_effect", "")
        
        # Hooks for the Engine Logic
        self.bam_id = data.get("bam_id")
        self.passive_id = data.get("passive_id")
        self.trigger_id = data.get("trigger_id")
        self.effect_text = data.get("effect_text", "")
        
        self.cleared = False

    @property
    def is_defeated(self):
        """Dynamically evaluates if all token/HP requirements are met."""
        # If it has HP, it's a target you attack. Otherwise, it's a token threat.
        if self.hp > 0:
            return self.hp <= 0
            
        # Must meet ALL requirements that are greater than 0
        return (self.heroic_tokens >= self.heroic_req and 
                self.move_tokens >= self.move_req and 
                self.attack_tokens >= self.attack_req)

    @property
    def display_hp(self):
        """Standardized health/requirement display for the UI."""
        if self.hp > 0:
            return f"{ICON.get('attack', '✸')}{self.hp}"
        
        reqs = []
        if self.heroic_req > 0:
            reqs.append(f"{ICON.get('heroic', '★')}{self.heroic_req - self.heroic_tokens}")
        if self.move_req > 0:
            reqs.append(f"{ICON.get('move', '➡')}{self.move_req - self.move_tokens}")
        if self.attack_req > 0:
            reqs.append(f"{ICON.get('attack', '✸')}{self.attack_req - self.attack_tokens}")
            
        return " ".join(reqs) if reqs else "0"

    def apply_token(self, token_type, amount=1):
        """Applies a token and returns True if the threat was just cleared."""
        if self.cleared: return False
        
        if token_type == "heroic" and self.heroic_tokens < self.heroic_req:
            self.heroic_tokens += amount
        elif token_type == "move" and self.move_tokens < self.move_req:
            self.move_tokens += amount
        elif token_type == "attack" and self.attack_tokens < self.attack_req:
            self.attack_tokens += amount
        
        if self.is_defeated:
            self.cleared = True
            return True
        return False
        
    @property
    def has_target(self):
        """True if this threat has a movement-based trigger."""
        return self.trigger_id is not None

    def trigger(self):
        """Returns the formatted narrative log entry."""
        if self.has_target and not self.cleared:
            # Using the name and effect text from the JSON
            msg = f"▶ [🎯] {self.name.upper()}: {self.effect_text}"
            return Col.wrap(msg, Col.YLW)
        return None

    def on_bam(self, engine, loc_index):
        """Signals the specific Villain Logic to resolve this threat's BAM."""
        if self.cleared or not self.bam_id:
            return

        # We get the 'Brain' for the current villain (e.g., RedSkullLogic)
        from src.logic.registry import get_villain_logic
        logic = get_villain_logic(engine.villain.internal_id)
        
        # Hand off the signal to the logic plugin
        logic.resolve_threat_bam(engine, self, loc_index)
