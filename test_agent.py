import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.agent import Agent

def test_agent():
    # Paths for dummy files
    system_prompt = Path("resources/system_prompt.txt")
    cheatsheet = Path("resources/picogk_cheatsheet.md")
    
    # Initialize Agent
    agent = Agent(
        system_prompt_path=system_prompt,
        cheatsheet_path=cheatsheet,
        local_model_name="qwen2.5-coder:latest"
    )
    
    # Test case
    problem = "My nozzle is melting"
    print(f"Testing problem: {problem}")
    
    result = agent.solve_problem(problem)
    
    print("\n[FINAL RESULT]")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_agent()
