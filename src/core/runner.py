"""
LumenOrb v2.0 - PicoGK JSON Bridge Runner
Executes pre-compiled C# engine with recipe.json
"""

import subprocess
from pathlib import Path


class PicoRunner:
    """
    JSON Bridge Runner: Executes pre-compiled PicoGK C# engine with JSON recipes.
    No more C# code generation or compilation - just JSON + pre-built engine!
    """
    
    def __init__(self, runtime_dir: str = "picogk_runner"):
        self.runtime_dir = Path(runtime_dir)
        self.recipe_path = self.runtime_dir / "recipe_run.json"
        self.output_stl = self.runtime_dir / "render.stl"
    
    def run_engine(self, json_path: Path, timeout: int = 120) -> bool:
        """
        Execute the pre-compiled C# engine with a JSON recipe.
        Args:
            json_path: Path to the recipe.json file
            timeout: Maximum execution time in seconds
        Returns:
            True if execution succeeded, False otherwise
        """
        print("🚀 Launching PicoGK Engine...")
        print(f"   Recipe Path: {json_path}")
        
        # DEBUG: Verify content before handoff
        try:
            with open(json_path, 'r') as f:
                content = f.read()
                print(f"   📋 Handing off {len(content)} bytes to C#.")
                if len(content) < 50: print(f"      Use Head: {content}")
        except:
            print("   ⚠️ Could not verify file content!")

        try:
            # Run the pre-compiled engine with the JSON path as argument
            result = subprocess.run(
                ["dotnet", "run", "--", str(json_path.resolve())],
                cwd=self.runtime_dir,
                timeout=timeout,
                capture_output=False  # Let output go to console
            )
            
            if result.returncode == 0:
                print("✅ PicoGK Engine completed successfully")
                return True
            else:
                print(f"❌ PicoGK Engine failed with code: {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ PicoGK Engine timed out after {timeout}s")
            return False
        except FileNotFoundError:
            print("❌ Error: dotnet not found. Is .NET SDK installed?")
            return False
        except Exception as e:
            print(f"❌ Execution Error: {e}")
            return False
    
    def run(self, csharp_code: str, timeout: int = 60) -> bool:
        """
        DEPRECATED: Legacy method for C# code generation mode.
        Kept for backward compatibility. New code should use run_engine().
        """
        print("⚠️ WARNING: Using legacy code generation mode")
        print("   Consider switching to JSON Bridge mode with run_engine()")
        
        try:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            program_path = self.runtime_dir / "Program.cs"
            
            with open(program_path, "w", encoding='utf-8') as f:
                f.write(csharp_code)
            
            print(f"✅ Code saved to: {program_path}")
            print(f"   To run manually: cd {self.runtime_dir} && dotnet run")
            return True
            
        except Exception as e:
            print(f"❌ File Write Error: {e}")
            return False
    
    def get_output_path(self) -> Path:
        """Get path to where the output STL would be generated."""
        return self.output_stl
    
    def cleanup(self):
        """Remove generated output files."""
        if self.recipe_path.exists():
            self.recipe_path.unlink()
            print("🧹 Cleaned up recipe.json")


# Convenience function
def run_picogk_engine(json_path: Path, runtime_dir: str = "picogk_runner") -> bool:
    """Quick helper to run PicoGK engine with a JSON recipe."""
    runner = PicoRunner(runtime_dir)
    return runner.run_engine(json_path)
