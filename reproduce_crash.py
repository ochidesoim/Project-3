import json
import os
import subprocess
import sys
import time

RUNNER_DIR = "picogk_runner"
RECIPE_PATH = os.path.join(RUNNER_DIR, "recipe.json")

# User's reported "Faulty" JSON - BIGGER (100x100)
crash_recipe = {
  "steps": [
    {
      "id": "step_0",
      "op": "box",
      "params": {
        "dx": 100,
        "dy": 100,
        "height": 10,
        "x": -50,
        "y": -50,
        "z": 0.0
      }
    },
    {
      "id": "step_1",
      "op": "cylinder",
      "params": {
        "radius": 10,  
        "height": 30,
        "x": 0,
        "y": 0,
        "z": 50.0
      }
    },
    {
      "id": "step_2",
      "op": "union",
      "params": {
        "target": "step_0",
        "tool": "step_1"
      }
    }
  ]
}

def reproduce():
    with open(RECIPE_PATH, "w") as f:
        json.dump(crash_recipe, f, indent=2)
        
    with open("crash_output.txt", "w", encoding="utf-8") as log_file:
        try:
            log_file.write("--- CRASH REPRODUCTION 5 (HEAVY 100x100 SAFE) ---\n")
            proc = subprocess.Popen(
                ["dotnet", "run"],
                cwd=RUNNER_DIR,
                stdout=log_file,
                stderr=log_file
            )
            
            start = time.time()
            crashed = False
            while time.time() - start < 15:
                if proc.poll() is not None:
                    log_file.write(f"\n❌ Process DIED with code {proc.returncode}\n")
                    crashed = True
                    break
                time.sleep(1)
                
            if not crashed:
                log_file.write("\n✅ Process still running after 15s (Stable)\n")
                proc.terminate()
                
        except Exception as e:
            log_file.write(f"\nError: {e}\n")

if __name__ == "__main__":
    reproduce()
