"""
DEBUG TEST - AI Bypass Script
Writes a perfect recipe manually to test the C# Engine without AI involvement.
"""
import json
import os
import subprocess

# 1. Define a PERFECT Recipe (No AI hallucinations)
recipe = {
  "steps": [
    # Box: 100x100x10 at -50,-50 (Centered)
    { "id": "step_0", "op": "box", "params": { "dx": 100, "dy": 100, "height": 10, "x": -50, "y": -50, "z": 0 } },
    
    # Cylinder: Radius 30, Height 50 (Centered)
    { "id": "step_1", "op": "cylinder", "params": { "radius": 30, "height": 50, "x": 0, "y": 0, "z": 10 } },
    
    # Union: Combine them (CORRECT format with target/tool!)
    { "id": "step_2", "op": "union", "params": { "target": "step_0", "tool": "step_1" } }
  ]
}

# 2. Save it to the runner folder
json_path = os.path.join("picogk_runner", "recipe.json")
with open(json_path, "w") as f:
    json.dump(recipe, f, indent=2)
print(f"✅ MANUAL DEBUG: Wrote perfect JSON to {json_path}")
print(f"   - step_0: Box (100x100x10)")
print(f"   - step_1: Cylinder (r=30, h=50)")
print(f"   - step_2: Union (target=step_0, tool=step_1)")

# 3. Run the Engine
print("\n🚀 Launching C# Engine...")
result = subprocess.run(["dotnet", "run", "--", "recipe.json"], cwd="picogk_runner")

if result.returncode == 0:
    print("\n✅ Engine completed successfully!")
else:
    print(f"\n❌ Engine failed with code: {result.returncode}")
