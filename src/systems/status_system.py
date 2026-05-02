# src/systems/status_system.py

class StatusSystem:
    _draw_interceptors = []

    @staticmethod
    def register_draw_interceptor(callback):
        """Allows Hero Logic to 'sign up' for Villain draw events."""
        if callback not in StatusSystem._draw_interceptors:
            StatusSystem._draw_interceptors.append(callback)

    @staticmethod
    def route_draw_interception(engine, plan):
        """
        The Switchboard: Passes the plan through registered logic.
        The System doesn't know what happens inside; it just routes.
        """
        for interceptor in StatusSystem._draw_interceptors:
            plan = interceptor(engine, plan)
        return plan
        
    @staticmethod
    def apply_status(entity, status_type, duration=1):
        """Applies a temporary status tag to any entity."""
        if not hasattr(entity, 'statuses'):
            entity.statuses = {}
        current = entity.statuses.get(status_type, 0)
        entity.statuses[status_type] = max(current, duration)

    @staticmethod
    def has_status(entity, status_type):
        """Checks if an entity currently has an active status tag."""
        if not hasattr(entity, 'statuses'):
            return False
        return entity.statuses.get(status_type, 0) > 0

    @staticmethod
    def decrement_status(entity, status_type):
        """Manually decrement a specific status."""
        if hasattr(entity, 'statuses') and status_type in entity.statuses:
            entity.statuses[status_type] -= 1
            if entity.statuses[status_type] <= 0:
                del entity.statuses[status_type]

    @staticmethod
    def remove_status(entity, status_type):
        """Immediately and entirely removes a specific status."""
        if hasattr(entity, 'statuses') and status_type in entity.statuses:
            del entity.statuses[status_type]

    # The Automated Clock
    @staticmethod
    def tick_all_statuses(entity):
        """
        Decrements all active statuses on an entity by 1.
        Call this at the end of the entity's turn to auto-expire buffs/debuffs.
        """
        if not hasattr(entity, 'statuses'):
            return
            
        expired = []
        for status_type in entity.statuses:
            entity.statuses[status_type] -= 1
            if entity.statuses[status_type] <= 0:
                expired.append(status_type)
                
        for status_type in expired:
            del entity.statuses[status_type]
