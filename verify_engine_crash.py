
import subprocess
from pathlib import Path

def reproduce_engine_crash():
    runner_path = Path("D:/Project 3/picogk_runner")
    exe_path = runner_path / "bin" / "Debug" / "net9.0" / "PicoGKRunner.dll"
    recipe_path = runner_path / "recipe_run.json"
    
    print(f"🚀 Launching Engine with {recipe_path}")
    
    try:
        result = subprocess.run(
            ["dotnet", "run", "--", str(recipe_path)],
            cwd=str(runner_path),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print("\n--- STDOUT ---")
        print(result.stdout)
        print("\n--- STDERR ---")
        print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Crash Detected! Code: {result.returncode}")
        else:
            print("✅ Success!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reproduce_engine_crash()
