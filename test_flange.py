"""
Test script to validate JSON Bridge architecture with smart_flange.
"""
import sys
sys.path.insert(0, ".")

from src.core.compiler import AtomicCompiler

# Create a simple smart_flange recipe
recipe = {
    "steps": [
        {
            "id": "my_flange",
            "op": "smart_flange",
            "params": {
                "radius": 40,
                "height": 12,
                "holes": 6,
                "hole_radius": 4,
                "x": 0,
                "y": 0,
                "z": 0
            }
        }
    ]
}

print("=" * 50)
print("Testing JSON Bridge Architecture")
print("=" * 50)

compiler = AtomicCompiler()

# Compile and execute (now uses JSON Bridge mode!)
print("\n🔧 Compiling recipe (JSON Bridge mode)...")
result = compiler.compile(recipe)

print("\n✅ Done!")
print("The PicoGK viewer should open showing the flange.")
