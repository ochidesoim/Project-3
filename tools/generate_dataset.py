import json
import random
import argparse
from pathlib import Path

def generate_physics_sample():
    """Generates a Physics Mode sample (Thrust/Pressure)"""
    thrust = round(random.uniform(10.0, 5000.0), 1)
    pressure = round(random.uniform(10.0, 100.0), 1)
    
    templates = [
        f"Create a rocket engine with {thrust}N thrust",
        f"Design a thruster, {thrust} Newtons, {pressure} bar",
        f"Generate a booster engine. Thrust: {thrust}",
        f"I need a {thrust}N rocket motor",
        f"Physics based nozzle, thrust={thrust}, pressure={pressure}"
    ]
    
    prompt = random.choice(templates)
    
    # Expected Output (Agent's Regex should catch this)
    params = {
        "thrust": thrust,
        "pressure": pressure
    }
    
    return prompt, params

def generate_explicit_sample():
    """Generates a LumenOrb Mode sample (Explicit Dimensions)"""
    # Realistic proportions
    throat = round(random.uniform(5.0, 50.0), 1)
    chamber = round(throat * random.uniform(2.0, 4.0), 1)
    exit_r = round(throat * random.uniform(2.5, 5.0), 1)
    
    # Text variations
    throat_txt = f"{int(throat*2)}mm throat" # Diameter usually spoken
    chamber_txt = f"{int(chamber*2)}mm chamber"
    exit_txt = f"{int(exit_r*2)}mm exit"
    
    templates = [
        f"Create a nozzle with {chamber_txt} and {throat_txt}",
        f"Design a rocket: {chamber_txt} wide, {throat_txt}, {exit_txt}",
        f"Laval nozzle, {throat_txt} narrowing from {chamber_txt}",
        f"{chamber_txt}, {throat_txt}, {exit_txt}",
        f"Geometry: {chamber_txt} / {throat_txt} / {exit_txt}"
    ]
    
    prompt = random.choice(templates)
    
    # Expected Output (Agent's Regex should catch this)
    # Note: Regex extracts RADIUS (Diameter / 2)
    params = {
        "chamber_radius": chamber,
        "throat_radius": throat,
        "exit_radius": exit_r
    }
    
    return prompt, params

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic rocket training data")
    parser.add_argument("--count", type=int, default=100, help="Number of samples to generate")
    parser.add_argument("--output", type=str, default="data/rocket_training_data.jsonl", help="Output file path")
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Generating {args.count} samples...")
    
    with open(output_path, "w", encoding="utf-8") as f:
        for _ in range(args.count):
            # 50/50 Split
            if random.random() < 0.5:
                prompt, params = generate_physics_sample()
                mode = "engineering_physics"
            else:
                prompt, params = generate_explicit_sample()
                mode = "engineering_explicit"
            
            # OpenAI Fine-tuning format (System, User, Assistant)
            # or simple Instruct format. Let's do a generic JSON structure.
            entry = {
                "prompt": prompt,
                "completion": json.dumps(params),
                "meta": {
                    "mode": mode,
                    "target_class": "RocketEngineDNA"
                }
            }
            
            f.write(json.dumps(entry) + "\n")
            
    print(f"✅ Saved to {output_path}")

if __name__ == "__main__":
    main()
