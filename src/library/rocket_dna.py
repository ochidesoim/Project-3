import math
from src.library.base_dna import EngineeringDNA

class RocketEngineDNA(EngineeringDNA):
    """
    Generates a Rocket Engine using physics-based calculations.
    
    Inputs:
    - thrust (float): Thrust in Newtons (default: 50.0)
    - pressure (float): Chamber pressure in bar (default: 20.0)
    """
    
    def validate_physics(self):
        # 1. Negative Physics Check
        if self.params.get("thrust", 50) <= 0:
            raise ValueError("Physics Error: Thrust must be positive.")
        if self.params.get("pressure", 20) <= 0:
            raise ValueError("Physics Error: Pressure must be positive.")
            
        # 2. Clamping for Safety (Prevent crash-inducing geometry)
        self.params["thrust"] = self.clamp(self.params.get("thrust", 50), 10.0, 10000.0, "Thrust")
        self.params["pressure"] = self.clamp(self.params.get("pressure", 20), 5.0, 200.0, "Pressure")

    def generate(self) -> list:
        # --- PHENOTYPE RULES ---
        
        # 1. Determine Throat Size (Manual Override vs Physics Calc)
        if 'throat_radius' in self.params:
            # User specified size (LumenOrb Mode)
            throat_radius = self.params['throat_radius']
            # If they didn't specify chamber, we infer it relative to throat
            chamber_radius = self.params.get('chamber_radius', throat_radius * 2.5)
            exit_radius = self.params.get('exit_radius', throat_radius * 3.5)
            
            # Recalculate generic "thrust" for scaling visual factors if needed
            thrust = self.params.get("thrust", 50)
        else:
            # Physics Mode (Thrust Calc)
            thrust = self.params.get("thrust", 50)
            pressure = self.params.get("pressure", 20) # Used in some advanced calc
            
            # Simple scaling factors for visual design
            scale_factor = 2.0
            throat_radius = math.sqrt(thrust) * 0.8 * scale_factor
            chamber_radius = throat_radius * 2.5
            exit_radius = throat_radius * 3.0
        
        chamber_height = chamber_radius * 4.0
        nozzle_height = (exit_radius - throat_radius) * 3.0 # 15 degree cone approx
        
        # Explicit Z-Stacking (Engineering Mode TRUSTS these values)
        z_cursor = 0.0
        
        steps = []
        
        # 1. Combustion Chamber
        steps.append({
            "id": "chamber_out",
            "op": "cylinder",
            "params": {
                "radius": chamber_radius,
                "height": chamber_height,
                "x": 0, "y": 0, "z": z_cursor
            }
        })
        
        # 2. Chamber Interior (Hollow)
        wall_thickness = 2.0
        steps.append({
            "id": "chamber_in",
            "op": "cylinder",
            "params": {
                "radius": chamber_radius - wall_thickness,
                "height": chamber_height - wall_thickness, # Floor thickness
                "x": 0, "y": 0, "z": z_cursor + wall_thickness
            }
        })
        
        # 3. Cut Chamber
        steps.append({
            "id": "chamber_final",
            "op": "subtract",
            "params": {
                "target": "chamber_out",
                "tool": "chamber_in"
            }
        })
        
        z_cursor += chamber_height
        
        # 4. Nozzle
        steps.append({
            "id": "nozzle_solid",
            "op": "cone",
            "params": {
                "r_bottom": chamber_radius, # Match chamber
                "r_top": exit_radius,
                "height": nozzle_height,
                "x": 0, "y": 0, "z": z_cursor
            }
        })
        
        # 5. Nozzle Interior
        steps.append({
            "id": "nozzle_void",
            "op": "cone",
            "params": {
                "r_bottom": chamber_radius - wall_thickness,
                "r_top": exit_radius - 0.5, # Sharp edge at exit
                "height": nozzle_height + 10, # Cut through
                "x": 0, "y": 0, "z": z_cursor - 1
            }
        })
        
        # 6. Cut Nozzle
        steps.append({
            "id": "nozzle_final",
            "op": "subtract",
            "params": {
                "target": "nozzle_solid",
                "tool": "nozzle_void"
            }
        })
        
        # 7. Weld Everything (Union)
        steps.append({
            "id": "rocket_assembly",
            "op": "union",
            "params": {
                "target": "chamber_final",
                "tool": "nozzle_final"
            }
        })
        
        return steps
