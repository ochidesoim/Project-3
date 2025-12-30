import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.compiler import AtomicCompiler

def verify_gravity():
    print("🧪 Verifying Gravity Module...")
    
    # Faulty recipe: Box H=10, Cylinder floating at Z=50
    recipe = {
        "steps": [
            {
                "id": "step_0",
                "op": "box",
                "params": {"dx": 100, "dy": 100, "height": 10, "x": 0, "y": 0, "z": 0}
            },
            {
                "id": "step_1",
                "op": "cylinder",
                "params": {"radius": 10, "height": 30, "x": 0, "y": 0, "z": 50} 
            }
        ]
    }
    
    compiler = AtomicCompiler()
    # Mock runner.run_engine to avoid actual execution
    compiler.runner.run_engine = lambda x: print("   (Engine execution skipped)")
    
    # Run compiler
    json_path = compiler.compile(recipe)
    
    # Read result
    with open(json_path, 'r') as f:
        result = json.load(f)
        
    # Check Step 1 Z-position
    # Step 0 should be at Z=0, Height=10
    # Step 1 should snap to Z=10
    
    step_0 = result['steps'][0]
    step_1 = result['steps'][1]
    
    z0 = step_0['params']['z']
    z1 = step_1['params']['z']
    
    print(f"\n📊 Results:")
    print(f"   [step_0] Z={z0} (Expected 0.0)")
    print(f"   [step_1] Z={z1} (Expected 10.0)")
    
    if abs(z1 - 10.0) < 0.001:
        print("\n✅ Gravity Module Working! Gap closed.")
    else:
        print("\n❌ Gravity Module Failed. Gap remains.")

if __name__ == "__main__":
    verify_gravity()
