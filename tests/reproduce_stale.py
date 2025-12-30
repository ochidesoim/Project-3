import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.compiler import AtomicCompiler

def test_compiler_output():
    print("🧪 TEST: Reproducing Stale Geometry Bug")
    
    # 1. Mock Data (What Agent sends to Compiler)
    # Based on Rocket Engine DNA logic
    mock_input = {
        "intent": "Rocket, thrust 1000",
        "mode": "engineering",
        "operations": [
            {'id': 'chamber_out', 'op': 'cylinder', 'params': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'radius': 50.59, 'height': 80.95}},
            {'id': 'chamber_in', 'op': 'cylinder', 'params': {'x': 0.0, 'y': 0.0, 'z': -1.0, 'radius': 45.59, 'height': 82.95}},
            {'id': 'chamber_final', 'op': 'subtract', 'params': {'target': 'chamber_out', 'tool': 'chamber_in'}},
            {'id': 'nozzle_solid', 'op': 'cone', 'params': {'x': 0.0, 'y': 0.0, 'z': 80.95, 'height': 39.0, 'radius': 50.59, 'radius_top': 0.0}},
            {'id': 'nozzle_void', 'op': 'cone', 'params': {'x': 0.0, 'y': 0.0, 'z': 79.95, 'height': 41.0, 'radius': 45.59, 'radius_top': 0.0}},
            {'id': 'nozzle_final', 'op': 'subtract', 'params': {'target': 'nozzle_solid', 'tool': 'nozzle_void'}},
            {'id': 'rocket_assembly', 'op': 'union', 'params': {'target': 'chamber_final', 'tool': 'nozzle_solid'}}
        ],
        "meta": {"class": "RocketEngineDNA"}
    }
    
    print(f"   Input Operations: {len(mock_input['operations'])}")
    
    # 2. Init Compiler
    compiler = AtomicCompiler()
    
    # Mock the runner so we don't actually launch C# (unless we want to test that too)
    # For now, we want to see what file gets written.
    # But AtomicCompiler calls self.runner.run_engine(json_path)
    # We can let it run or mock it. Let's let it run to be identical to prod, 
    # but we mostly care about the file state BEFORE run.
    
    # 3. Run Compile
    print("   Running compile()...")
    json_path = compiler.compile(mock_input)
    
    print(f"   JSON Path returned: {json_path}")
    
    # 4. Inspect File
    if json_path and json_path.exists():
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        print("\n   📂 File Content (recipe.json):")
        print(json.dumps(data, indent=2))
        
        step_count = len(data.get('steps', []))
        print(f"\n   ✅ Steps in File: {step_count}")
        
        if step_count == len(mock_input['operations']):
            print("   ✅ SUCCESS: Compiler logic is working correctly locally.")
        else:
            print("   ❌ FAILURE: Step count mismatch!")
    else:
        print("   ❌ FAILURE: File not created!")

if __name__ == "__main__":
    test_compiler_output()
