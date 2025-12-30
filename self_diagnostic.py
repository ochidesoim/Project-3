import json
import os
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.compiler import AtomicCompiler

# Initialize the "Smart Compiler" (This has the Gravity + Auto-Correct modules)
compiler = AtomicCompiler()

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 TEST CASE: {title}")
    print(f"{'='*60}")

def verify_json(check_name, condition):
    if condition:
        print(f"   ✅ PASS: {check_name}")
        return True
    else:
        print(f"   ❌ FAIL: {check_name}")
        return False

# ==========================================
# 🧪 TEST A: GRAVITY & STACKING
# Input: Floating parts with huge gaps.
# Expected: Parts snapped together (Z=0, Z=10, Z=30).
# ==========================================
def run_gravity_test():
    print_header("GRAVITY & AUTO-STACKING")
    
    # 1. Simulate "Dumb AI" Output (Floating parts)
    bad_recipe = {
        "steps": [
            { "id": "step_0", "op": "box", "params": { "dx": 100, "dy": 100, "height": 10, "z": 0 } },
            # FLOATING AT Z=50 (Gap of 40mm!)
            { "id": "step_1", "op": "cylinder", "params": { "radius": 20, "height": 20, "z": 50 } }, 
            # FLOATING AT Z=200 (Huge gap!)
            { "id": "step_2", "op": "box", "params": { "dx": 10, "dy": 10, "height": 10, "z": 200 } }
        ]
    }

    # 2. Run Compiler (Should apply Gravity)
    print("   📉 Running Compiler with Gravity Module...")
    # Mock runner to avoid actual execution for this test
    original_runner = compiler.runner.run_engine
    compiler.runner.run_engine = lambda x: None 
    
    final_json_path = compiler.compile(bad_recipe)
    
    # Restore runner
    compiler.runner.run_engine = original_runner

    # 3. Verify the Correction
    with open(final_json_path, 'r') as f:
        data = json.load(f)
        s0 = data['steps'][0]['params']['z']
        s1 = data['steps'][1]['params']['z']
        s2 = data['steps'][2]['params']['z']
        
        verify_json("Step 0 at Base (0.0)", s0 == 0.0)
        verify_json("Step 1 Snapped to Box Top (10.0)", s1 == 10.0)
        verify_json("Step 2 Snapped to Cyl Top (30.0)", s2 == 30.0)

# ==========================================
# 🧪 TEST B: BOOLEAN SELF-REPAIR
# Input: "Union" with NO target/tool.
# Expected: Compiler injects target="step_0", tool="step_1".
# ==========================================
def run_repair_test():
    print_header("BOOLEAN SELF-REPAIR")

    # 1. Simulate "Forgetful AI" (Missing params)
    broken_recipe = {
        "steps": [
            { "id": "part_A", "op": "box", "params": { "dx": 10, "dy": 10, "height": 10 } },
            { "id": "part_B", "op": "sphere", "params": { "radius": 10 } },
            # BROKEN UNION (No inputs!)
            { "id": "part_C", "op": "union", "params": { } } 
        ]
    }

    # 2. Run Compiler
    print("   🔧 Running Compiler with Auto-Corrector...")
    
    # Mock runner
    original_runner = compiler.runner.run_engine
    compiler.runner.run_engine = lambda x: None
    
    final_json_path = compiler.compile(broken_recipe)
    
    # Restore runner
    compiler.runner.run_engine = original_runner

    # 3. Verify
    with open(final_json_path, 'r') as f:
        data = json.load(f)
        union_step = data['steps'][2]
        
        has_target = union_step['params'].get('target') == "part_A"
        has_tool = union_step['params'].get('tool') == "part_B"
        
        verify_json("Injected 'target' correctly", has_target)
        verify_json("Injected 'tool' correctly", has_tool)

# ==========================================
# 🧪 TEST C: THE ROCKET (FULL SYSTEM)
# Input: Complex Cone + Cylinder Logic.
# Expected: C# Engine runs successfully (Exit Code 0).
# ==========================================
def run_rocket_test():
    print_header("FULL SYSTEM: THE ROCKET")
    
    rocket_recipe = {
        "steps": [
            { "id": "step_0", "op": "cylinder", "params": { "radius": 20, "height": 40 } },
            { "id": "step_1", "op": "cylinder", "params": { "radius": 15, "height": 60 } },
            { "id": "step_2", "op": "cone", "params": { "radius": 15, "height": 20 } }, # REQUIRES C# UPDATE
            { "id": "step_3", "op": "union", "params": {} }, # Test auto-link
            { "id": "step_4", "op": "union", "params": {} }  # Test chaining
        ]
    }

    print("   🚀 Compiling & Launching Engine...")
    compiler.compile(rocket_recipe)
    print("   (Check the Viewer window for a 3-stage Rocket)")
    print("   ✅ If you see the Rocket, the entire pipeline is 100% HEALTHY.")

# ==========================================
# MAIN EXECUTION LOOP
# ==========================================
if __name__ == "__main__":
    print("\n🕵️ STARTING SELF-DIAGNOSTIC SEQUENCE...")
    time.sleep(1)
    
    try:
        run_gravity_test()
        time.sleep(1)
        
        run_repair_test()
        time.sleep(1)
        
        run_rocket_test()
        
    except Exception as e:
        print(f"\n💥 CRITICAL FAILURE: {e}")
