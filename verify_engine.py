import json
import os
import sys
import time
from pathlib import Path

# --- CONFIGURATION ---
RUNNER_DIR = "picogk_runner"
RECIPE_PATH = os.path.join(RUNNER_DIR, "recipe.json")

# Ensure imports work regardless of CWD
sys.path.insert(0, os.getcwd())

try:
    from src.core.compiler import AtomicCompiler
    from src.core.runner import PicoRunner
except ImportError:
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from core.compiler import AtomicCompiler
        from core.runner import PicoRunner
    except ImportError as e:
        print(f"CRITICAL ERROR: Could not import Engine Core: {e}")
        sys.exit(1)

# --- THE "GOLDEN RECIPE" ---
# This complex recipe tests every fix implemented.
golden_recipe = {
  "steps": [
    # 1. TEST BOX (Tests 'dx/dy' logic & Lattice/Sphere filling)
    { 
      "id": "step_0", 
      "op": "box", 
      "params": { 
        "dx": 100, "dy": 100, "height": 10,  # Dimensions
        "x": -50, "y": -50, "z": 0           # Centered at 0,0
      } 
    },

    # 2. TEST SMART FLANGE (Tests Math & Coordinate Offsets)
    # NOTE: This creates multiple sub-steps (cylinders) via AtomicCompiler
    { 
      "id": "step_1", 
      "op": "smart_flange", 
      "params": { 
        "radius": 40, 
        "height": 20, 
        "holes": 4,           
        "hole_radius": 5,
        "z": 10               # Sitting exactly ON TOP of the box
      } 
    },

    # 3. TEST UNION & HIDING (The "Z-Fighting" Fix)
    # If 'hiddenIngredients' logic works, step_0 and step_1 should VANISH.
    { 
      "id": "step_2", 
      "op": "union", 
      "params": { "target": "step_0", "tool": "step_1" } 
    },

    # 4. TEST SUBTRACTION (The "Bore")
    { 
      "id": "step_3", 
      "op": "cylinder", 
      "params": { "radius": 20, "height": 100, "z": -20 } 
    },

    { 
      "id": "step_4", 
      "op": "subtract", 
      "params": { "target": "step_2", "tool": "step_3" } 
    }
  ]
}

def run_test():
    print("--- STARTING FINAL SYSTEM CHECK ---")
    
    # Compile & Run using the Agentic Core
    print(f"Compiling Golden Recipe using AtomicCompiler...")
    
    start_time = time.time()
    try:
        # Initialize Compiler (which initializes Runner)
        compiler = AtomicCompiler()
        
        # This will:
        # 1. Expand 'smart_flange' into primitives
        # 2. Handle chain of custody for booleans
        # 3. Write normalized JSON to recipe.json
        # 4. Execute the C# engine
        compiler.compile(golden_recipe)
        
    except Exception as e:
        print(f"FAILED during System Check: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"--- TEST COMPLETED in {round(time.time() - start_time, 2)}s ---")
    print("\nVISUAL INSPECTION CHECKLIST:")
    print("1. [ ] Do you see ONE single fused object? (Blue/Aluminum)")
    print("2. [ ] Is the Z-Fighting (flickering overlap) GONE?")
    print("   (This confirms step_0 and step_1 were successfully hidden)")
    print("3. [ ] Is there a Box base + Flange top + 4 Bolt Holes + 1 Big Hole?")
    print("4. [ ] Did the C# Engine Log show 'Rendering Final Object' for step_4?")

if __name__ == "__main__":
    run_test()
