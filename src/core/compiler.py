"""
LumenOrb v2.0 - Atomic Compiler (Refactored for Noyron Architecture)
"""
import json
from src.core.runner import PicoRunner

class AtomicCompiler:
    def __init__(self):
        self.runner = PicoRunner()

    def compile(self, recipe_dict):
        print("\n[ATOMIC COMPILER] processing...")
        
        # 1. Normalize Input
        # Support both 'steps' (DNA) and 'operations' (Legacy/Creative)
        steps = recipe_dict.get('steps', recipe_dict.get('operations', []))
        mode = recipe_dict.get('mode', 'unknown')
        
        print(f"   -> Mode: {mode.upper()}")
        print(f"   -> Steps: {len(steps)}")
        
        # 2. Gravity Logic
        # If Engineering Mode -> We TRUST the Z coordinates.
        # If Creative/Unknown Mode -> We SNAP Z coordinates to a stack.
        
        enable_gravity = (mode != 'engineering')
        cursor_z = 0.0
        
        normalized_steps = []
        
        for i, step in enumerate(steps):
            # Normalize Op Name
            op = step.get('op', step.get('type', '')).replace('create_', '')
            pid = step.get('id', f'step_{i}')
            
            # Normalize Params (snake_case preference)
            params = step.get('params', step.get('parameters', {}))
            
            # Handle aliases (w->dx, etc) - Common in both modes
            self._normalize_params(params)
            
            # --- Z-AXIS LOGIC ---
            if enable_gravity:
                # CREATIVE MODE: Snap structural elements
                if op in ['box', 'cylinder', 'cone', 'sphere', 'smart_flange']:
                    print(f"      📍 Gravity: Snapping {pid} to Z={cursor_z}")
                    params['z'] = cursor_z
                    
                    # Update Cursor
                    h = self._get_height(op, params)
                    cursor_z += h
            else:
                # ENGINEERING MODE: Validate but do not touch Z
                # (Unless Z is missing, then default to 0)
                if 'z' not in params and 'center' not in params:
                     params['z'] = 0.0 # Safety fallback
            
            # Reconstruct step
            new_step = {
                "id": pid,
                "op": op,
                "params": params
            }
            print(f"      -> Processed Step: {pid} limit={op}")
            normalized_steps.append(new_step)

        # 3. Output Generation
        # STRIP any 'meta' fields, just pure steps for C#
        final_recipe = {
            "steps": normalized_steps
        }
        
        json_path = self.runner.recipe_path
        try:
            with open(json_path, "w") as f:
                json.dump(final_recipe, f, indent=2)
            print(f"   ✅ Computed Recipe saved to {json_path}")
            
            # 4. Execute
            self.runner.run_engine(json_path)
            
        except Exception as e:
            print(f"   ❌ Compiler Error: {e}")
            return None
            
        return json_path

    def _normalize_params(self, params):
        """Standardize parameter names in-place"""
        # Dimensions
        if 'width_mm' in params: params['dx'] = params.pop('width_mm')
        if 'depth_mm' in params: params['dy'] = params.pop('depth_mm')
        if 'height_mm' in params: params['height'] = params.pop('height_mm')
        if 'radius_mm' in params: params['radius'] = params.pop('radius_mm')
        
        # Center list to x/y/z
        if 'center' in params and isinstance(params['center'], list):
            c = params.pop('center')
            if len(c) >= 3:
                params['x'], params['y'], params['z'] = c[0], c[1], c[2]
                
    def _get_height(self, op, params):
        """Extract height for stacking"""
        if op == 'sphere':
             return float(params.get('radius', 10)) * 2
        return float(params.get('height', params.get('h', 0)))
