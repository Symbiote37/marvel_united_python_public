# src/entities/locations.py

class Location:
    def __init__(self, data):
        # Initializing from JSON dictionary
        self.index = data.get("id", 0)
        self.name = data.get("name", "Unknown Sector")
        self.capacity = data.get("capacity", 5)
        # Starting token counts defined in data
        self.thugs = data.get("start_thugs", 0)
        self.civilians = data.get("start_civs", 0)
        self.infected = 0
        self.crisis_tokens = 0
        self.threat = None 
        self.end_effect = data.get("end_effect")
        self.short_effect = data.get("short_effect", "CLEARED") 

    @property
    def threat_cleared(self):
        """Dynamic check: if there's no threat, or it's marked cleared."""
        if not self.threat:
            return True
        return self.threat.cleared

    def total_figures(self):
        """Returns the absolute sum of all occupants for capacity checks."""
        # Now universally includes infected without needing Villain-specific logic
        return self.thugs + self.civilians + self.infected

    def __repr__(self):
        return f"Loc({self.index}: {self.name} T:{self.thugs} C:{self.civilians})"

    @property
    def is_full(self):
        """Returns True if the location is at or over capacity."""
        return self.total_figures() >= self.capacity

    # 🌟 NEW: THE INTEGRATED DATA HANDLER
    def add_figures(self, engine, thugs=0, civs=0):
        """
        The Location's internal bouncer. 
        Checks room for every single figure before letting them in.
        """
        from src.systems.event_system import EventSystem
        added_count = 0

        # Process Thugs one-by-one
        for _ in range(thugs):
            if self.total_figures() < self.capacity:
                self.thugs += 1
                added_count += 1
            else:
                EventSystem.broadcast_overflow(engine, self, "thugs")
                break # Once full, stop adding this batch

        # Process Civilians one-by-one
        for _ in range(civs):
            if self.total_figures() < self.capacity:
                self.civilians += 1
                added_count += 1
            else:
                EventSystem.broadcast_overflow(engine, self, "civilians")
                break

        return added_count
