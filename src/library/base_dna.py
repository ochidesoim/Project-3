from abc import ABC, abstractmethod

class EngineeringDNA(ABC):
    """
    The Abstract Base Class that enforces Engineering Rigor.
    All DNA (Rocket, Piston, Gear) must inherit from this.
    """
    def __init__(self, **kwargs):
        self.params = kwargs
        self.validate_physics() # Auto-run safety checks
    
    @abstractmethod
    def validate_physics(self):
        """
        Must raise ValueError if physics are impossible (e.g. negative thrust).
        This acts as the first line of defense against "hallucinated parameters".
        """
        pass

    @abstractmethod
    def generate(self) -> list:
        """
        Returns the list of geometric steps.
        Format: [{"id": "...", "op": "...", "params": {...}}]
        """
        pass
    
    def clamp(self, value, min_val, max_val, name="Parameter"):
        """Helper to clamp values within safe engineering limits"""
        if value < min_val:
            print(f"⚠️ Warning: {name} {value} clamped to min {min_val}")
            return min_val
        if value > max_val:
            print(f"⚠️ Warning: {name} {value} clamped to max {max_val}")
            return max_val
        return value
