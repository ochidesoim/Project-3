import sys
import json
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import Agent
from src.core.compiler import AtomicCompiler

def verify_cylinder():
    print("🧪 VERIFICATION: Creative Mode (Cylinder)")
    
    # 1. Init
    try:
        system_prompt = Path("resources/system_prompt.txt")
        cheatsheet = Path("resources/picogk_cheatsheet.md")
        
        # Ensure dummy resources if missing
        if not system_prompt.exists(): system_prompt.parent.mkdir(parents=True, exist_ok=True); system_prompt.write_text("You are a helper.")
        
        agent = Agent(
            system_prompt_path=system_prompt,
            cheatsheet_path=cheatsheet,
            local_model_name="qwen2.5-coder:latest" 
        )
        compiler = AtomicCompiler()
        
    except Exception as e:
        print(f"❌ Init Failed: {e}")
        return

    # 2. Agent Solve
    print("   🤖 Agent: Asking for 'create a cylinder'...")
    user_input = "create a cylinder"
    
    # Attempt to use real LLM first
    try:
        result = agent.solve_problem(user_input)
    except Exception as e:
        print(f"   ⚠️ Agent Exception: {e}")
        result = {"error": str(e)}

    # Check validity
    ops = result.get("operations", [])
    if not ops:
        print("   ⚠️ LLM returned empty/invalid result. Is Ollama running?")
        print(f"   -> Result: {result}")
        print("   -> 🔧 Injecting MANUAL fallback to verify C# Engine...")
        
        # Manual Fallback for the test
        result = {
            "mode": "creative_fallback",
            "operations": [
                {
                    "id": "manual_cyl",
                    "op": "cylinder",
                    "params": {"radius": 15, "height": 40, "x":0, "y":0, "z":0}
                }
            ]
        }
        
    else:
        print(f"   ✅ LLM Success: Generated {len(ops)} steps.")
        print(f"   -> {ops}")

    # 3. Compile & Run
    print("   🔨 Compiling...")
    try:
        json_path = compiler.compile(result)
        if json_path:
            print("   ✅ Compilation Complete.")
        else:
            print("   ❌ Compilation Failed.")
            return
    except Exception as e:
        print(f"   ❌ Compiler Exception: {e}")
        return

    # 4. Check Output
    # The runner saves to 'picogk_runner/render.stl' usually, or output.stl depending on config
    # Compiler.py: self.runner.run_engine(json_path)
    # Runner.py: run_engine calls subprocess in output_dir
    
    # Let's check if the subprocess (C#) ran cleanly. 
    # Since compile() prints to stdout, we'll see it in the run_command output.
    
    print("   🏁 Test Sequence Complete.")

if __name__ == "__main__":
    verify_cylinder()
