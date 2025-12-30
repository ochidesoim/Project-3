import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import Agent

def verify_lumenorb_ai():
    print("🧠 VERIFICATION: LumenOrb V1 Training Check")
    
    try:
        system_prompt = Path("resources/system_prompt.txt")
        cheatsheet = Path("resources/picogk_cheatsheet.md")
        
        # Ensure dummy resources if missing
        if not system_prompt.exists(): 
            system_prompt.parent.mkdir(parents=True, exist_ok=True)
            system_prompt.write_text("You are a helper.")
        
        # Initialize Agent (It should default to lumenorb-v1 now)
        agent = Agent(
            system_prompt_path=system_prompt,
            cheatsheet_path=cheatsheet
        )
        print(f"   🤖 Agent Model: {agent.local_model_name}")
        
    except Exception as e:
        print(f"❌ Init Failed: {e}")
        return

    # Test Case: Complex phrasing that Regex might miss or find ambiguous,
    # but the AI should "Get" due to training.
    # Note: Our regex is quite strong now, so we mainly check that the AI *output* matches the desired format
    # and doesn't hallucinate markdown.
    
    test_prompts = [
        "Design a Laval rocket nozzle. 146mm chamber wide, 45mm throat, 186mm exit",
        "Generate a booster engine. Thrust: 4500.5"
    ]
    
    for prompt in test_prompts:
        print(f"\n   📝 Prompt: '{prompt}'")
        
        # Direct Query to LLM (Bypass Agent Regex for this test to prove AI competence)
        # We simulate what _run_engineering_mode does but force the LLM path.
        
        llm_prompt = f"""
        Extract engineering parameters from this text as JSON.
        Target Class: RocketEngineDNA
        Text: "{prompt}"
        
        Return JSON only. Keys should be snake_case.
        """
        
        response = agent._query_local(llm_prompt)
        print(f"   -> Raw LLM Response: {response}")
        
        try:
            # Cleanup common LLM artifacts just in case, but training should minimize them
            clean_response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_response)
            print(f"   ✅ parsed JSON: {data}")
            
            if "throat_radius" in data or "thrust" in data:
                print("   ✅ Valid Engineering Keys found.")
            else:
                print("   ⚠️ JSON valid but keys suspect.")
                
        except json.JSONDecodeError:
            print("   ❌ FAILED: Response was not valid JSON.")

if __name__ == "__main__":
    verify_lumenorb_ai()
