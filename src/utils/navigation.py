# src/utils/navigation.py

class BoardNav:
    @staticmethod
    def parse_direction(direction):
        """
        Helper to parse string or boolean directions into a standard clockwise boolean.
        Accepts: "cw", "ccw", True, False
        """
        if isinstance(direction, str):
            return direction.lower() != "ccw"
        # Fallback for legacy boolean calls
        return bool(direction)

    @staticmethod
    def get_distance(start, end, direction="cw"):
        """Calculates steps between two indices based on direction."""
        is_cw = BoardNav.parse_direction(direction)
        return (end - start) % 6 if is_cw else (start - end) % 6

    @staticmethod
    def find_closest_hero(engine, start_idx, direction="cw", ignore_start_loc=False):
        """Scans the board... 🚨 THE VOID FIX: Ignores heroes at location -1."""
        is_cw = BoardNav.parse_direction(direction)
        
        for distance in range(1, 7):
            search_idx = (start_idx + distance) % 6 if is_cw else (start_idx - distance) % 6
            if ignore_start_loc and search_idx == start_idx:
                continue
            
            # 🚨 ARMOR RESTORED
            heroes_at_loc = [h for h in engine.heroes if h.location_index == search_idx and h.location_index != -1 and not getattr(h, 'is_ko', False)]
            if heroes_at_loc:
                return heroes_at_loc, distance
        return None, None

    @staticmethod
    def find_nearest_empty_location(engine, start_idx, direction="cw"):
        """Scans the board to find the first location without any active heroes."""
        is_cw = BoardNav.parse_direction(direction)
        
        # [!] JULES'S SPEED + OUR ARMOR
        occupied_locations = {h.location_index for h in engine.heroes if not getattr(h, 'is_ko', False)}
        
        for distance in range(1, 7):
            search_idx = (start_idx + distance) % 6 if is_cw else (start_idx - distance) % 6
            
            if search_idx not in occupied_locations:
                return search_idx, distance
                
        return None, None

    @staticmethod
    def find_densest_location(engine, start_idx, token_type="civilians", ignore_start_loc=True):
        """Finds the location with the most tokens of a specific type (with clockwise tie-breaker)."""
        best_idx = None
        max_count = -1
        
        for i in range(6):
            if ignore_start_loc and i == start_idx:
                continue
            
            loc = engine.locations[i]
            count = getattr(loc, token_type, 0)
            
            if count > max_count:
                max_count = count
                best_idx = i
            elif count == max_count and max_count > 0:
                # Tie-breaker: If already have a best_idx, pick the one closest clockwise to start
                if best_idx is not None:
                    current_dist = BoardNav.get_distance(start_idx, best_idx, "cw")
                    new_dist = BoardNav.get_distance(start_idx, i, "cw")
                    if new_dist < current_dist:
                        best_idx = i
                else:
                    best_idx = i
                    
        return best_idx, max_count

    @staticmethod
    def find_hero_concentration(engine, start_idx, ignore_start_loc=False):
        """Tactical Scan: Finds the location with the most active heroes."""
        best_idx = None
        max_count = -1

        # 🚨 JULES'S O(N) OPTIMIZATION: Pre-calculate hero density once
        hero_counts = {}
        for h in engine.heroes:
            # ARMOR: Only count conscious heroes NOT in the "Void" (-1)
            if h.location_index != -1 and not getattr(h, 'is_ko', False):
                idx = h.location_index
                hero_counts[idx] = hero_counts.get(idx, 0) + 1

        for i in range(6):
            if ignore_start_loc and i == start_idx:
                continue

            # Fast O(1) dictionary lookup
            count = hero_counts.get(i, 0)

            if count > max_count:
                max_count = count
                best_idx = i
            elif count == max_count and max_count > 0:
                # Tie-breaker: Closest clockwise to the start index
                if best_idx is not None:
                    curr_dist = BoardNav.get_distance(start_idx, best_idx, "cw")
                    new_dist = BoardNav.get_distance(start_idx, i, "cw")
                    if new_dist < curr_dist:
                        best_idx = i
                else:
                    best_idx = i
                    
        return best_idx, max_count
