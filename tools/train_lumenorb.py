import json
import random
from pathlib import Path

def create_modelfile():
    print("🧠 Training Processor: Loading Data...")
    
    # 1. Load Data
    data_path = Path("data/rocket_training_data.jsonl")
    if not data_path.exists():
        print("❌ Error: Training data not found.")
        return

    examples = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    
    print(f"   -> Loaded {len(examples)} raw samples.")
    
    # 2. Select Diverse Subset (Few-Shot)
    # We don't want to overload the context window, so we pick ~20 diverse shots.
    # 10 Explicit, 10 Physics
    explicit_samples = [e for e in examples if e['meta']['mode'] == 'engineering_explicit']
    physics_samples = [e for e in examples if e['meta']['mode'] == 'engineering_physics']
    
    selected_samples = []
    selected_samples.extend(random.sample(explicit_samples, min(10, len(explicit_samples))))
    selected_samples.extend(random.sample(physics_samples, min(10, len(physics_samples))))
    
    random.shuffle(selected_samples)
    print(f"   -> Selected {len(selected_samples)} high-quality shots for embedding.")

    # 3. Build Modelfile Content
    # Base Model
    base_model = "qwen2.5-coder:latest"
    
    # System Prompt with Strict JSON enforcement
    system_prompt = """You are LumenOrb AI, an expert aerospace engineer.
Your goal is to parse user requests into engineering parameters.
ALWAYS output raw JSON. NO markdown. NO explanations.

MODES:
1. PHYSICS MODE: If user gives Thrust/Pressure -> Output {"thrust": float, "pressure": float}
2. EXPLICIT MODE: If user gives Dimensions (throat, chamber, exit) -> Output {"throat_radius": float, "chamber_radius": float, "exit_radius": float}
   * NOTE: Convert DIAMETERS (e.g. "20mm throat") to RADIUS (10.0).

Follow these examples perfectly:"""

    modelfile_content = f"FROM {base_model}\n\n"
    modelfile_content += f'SYSTEM "{system_prompt}"\n\n'
    
    # Embed Examples (Few-Shot Learning)
    for sample in selected_samples:
        user_msg = sample['prompt']
        # Ensure regex consistency by cleaning the JSON string
        raw_json = sample['completion'] 
        
        modelfile_content += f'MESSAGE user "{user_msg}"\n'
        modelfile_content += f'MESSAGE assistant "{raw_json}"\n'
    
    # Save Modelfile
    with open("Modelfile", "w", encoding="utf-8") as f:
        f.write(modelfile_content)
        
    print("✅ Generated 'Modelfile' with embedded training data.")
    print("   -> Run 'ollama create lumenorb-v1 -f Modelfile' to finalize.")

if __name__ == "__main__":
    create_modelfile()
