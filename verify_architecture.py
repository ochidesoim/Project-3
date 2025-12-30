import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, ".")

from src.core.agent import Agent
from src.core.compiler import AtomicCompiler

def verify_architecture():
    print("="*60)
    print("🚀 TARGET: NOYRON ARCHITECTURE VERIFICATION")
    print("="*60)
    
    # Setup
    system_prompt = Path("resources/system_prompt.txt")
    cheatsheet = Path("resources/picogk_cheatsheet.md")
    
    agent = Agent(
        system_prompt_path=system_prompt,
        cheatsheet_path=cheatsheet,
        local_model_name="qwen2.5-coder:latest"
    )
    
    compiler = AtomicCompiler()
    
    # ---------------------------------------------------------
    # TEST 1: ENGINEERING MODE (Rocket)
    # ---------------------------------------------------------
    print("\n\n--- [TEST 1] ENGINEERING MODE: 'Rocket, thrust 50' ---")
    
    # Mocking the LLM param extraction for stability in this test script
    # (We want to test the Architecture, not the LLM's ability to regex)
    agent._query_local = lambda prompt: '{"thrust": 50.0, "pressure": 20.0}' if "Extract engineering parameters" in prompt else "{}"
    
    input_text = "Rocket, thrust 50"
    result_eng = agent.solve_problem(input_text)
    
    if result_eng.get("mode") == "engineering":
        print("✅ SUCCESS: Agent entered Engineering Mode")
        ops = result_eng.get("operations", [])
        print(f"   Generated {len(ops)} operations")
        
        # Verify Physics Math (Thrust 50 -> Radius ~5.65 * scale)
        # Expected: math.sqrt(50) * 0.8 * 2.0 = 11.31
        chamber_r = ops[0]["params"]["radius"]
        print(f"   Chamber Radius: {chamber_r:.2f} (Expected ~11.31)")
        
        if 11.0 < chamber_r < 11.5:
            print("✅ PHYSICS CHECK PASSED")
        else:
            print("❌ PHYSICS CHECK FAILED")
            
        # Compile
        compiler.compile(result_eng)
        
    else:
        print(f"❌ FAIL: Agent did not enter Engineering Mode. Data: {result_eng}")

    # ---------------------------------------------------------
    # TEST 2: CREATIVE MODE (Box)
    # ---------------------------------------------------------
    print("\n\n--- [TEST 2] CREATIVE MODE: 'Make a box' ---")
    
    # Mocking LLM for Creative Mode
    agent._query_local = lambda prompt: json.dumps({
        "operations": [
            {"id": "b1", "type": "create_box", "params": {"width_mm": 10, "height_mm": 5}},
            {"id": "c1", "type": "create_cylinder", "params": {"radius_mm": 2, "height_mm": 10}}
        ]
    })
    
    input_creative = "Make a box"
    result_creative = agent.solve_problem(input_creative)
    
    if result_creative.get("mode") == "creative":
        print("✅ SUCCESS: Agent entered Creative Mode")
        
        # Compile (Check Gravity)
        # We need to capture the gravity effect. 
        # The compiler writes to file, so we could inspect that, or just check the logic manually?
        # Let's inspect the logs by running it.
        compiler.compile(result_creative)
        print("✅ Creative Mode Compiled")
        
    else:
         print(f"❌ FAIL: Agent did not enter Creative Mode. Data: {result_creative}")

if __name__ == "__main__":
    verify_architecture()
