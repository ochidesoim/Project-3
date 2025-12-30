"""
LumenOrb v2.0 - AI Agent (Refactored for Noyron Architecture)
"""
import json
import re
from pathlib import Path
from typing import Optional, Literal
from openai import OpenAI
import google.generativeai as genai

# New Architecture Imports
from src.core.registry import get_dna_class
from src.core.models import GeometryRequest

class Agent:
    """
    AI Agent that routes between Engineering Mode (Physics) and Creative Mode (LLM).
    """
    
    def __init__(
        self,
        system_prompt_path: Path,
        cheatsheet_path: Path,
        gemini_api_key: Optional[str] = None,
        local_endpoint: str = "http://localhost:11434/v1",
        local_model_name: str = "lumenorb-v1:latest",
        use_recipe_mode: bool = True
    ):
        self.system_prompt = system_prompt_path.read_text(encoding='utf-8')
        
        # Initialize LLM Clients (for Creative Mode & Param Extraction)
        self.local_client = OpenAI(base_url=local_endpoint, api_key="ollama")
        self.local_model_name = local_model_name
        self.history = []

    def solve_problem(self, user_input: str) -> dict:
        """
        The Main Router: Decides between Engineering Mode and Creative Mode.
        """
        print(f"\n[AGENCY ROUTER] Analyzing: '{user_input}'")
        
        # 1. Check Registry for Engineering Intent
        # Robust Regex Matching against all registry keys
        # This handles cases like "rocket," or "ROCKET!" better than split()
        user_lower = user_input.lower()
        dna_class = None
        
        # We need to access the registry keys. 
        # Since we can't import DNA_CATALOG directly here without circular imports (maybe),
        # we rely on get_dna_class. But iteration is better.
        # Let's import the catalog for iteration access.
        from src.core.registry import DNA_CATALOG
        
        for keyword, cls in DNA_CATALOG.items():
            # Check for whole word match
            if re.search(r'\b' + re.escape(keyword) + r'\b', user_lower):
                dna_class = cls
                print(f"   -> Match Found: '{keyword}' -> {dna_class.__name__}")
                break
        
        # 2. Branch A: Engineering Mode
        if dna_class:
            print("   -> 🟢 Mode: ENGINEERING (Deterministic)")
            return self._run_engineering_mode(dna_class, user_input)
            
        # 3. Branch B: Creative Mode (Fallback)
        print("   -> 🎨 Mode: CREATIVE (LLM)")
        return self._run_creative_mode(user_input)

    def _run_engineering_mode(self, dna_class, user_input: str) -> dict:
        """
        Extracts parameters and executes DNA code.
        """
        # Step 1: Extract Parameters using Regex (Priority) + LLM (Fallback)
        params = {}
        prompt_lower = user_input.lower()
        
        # 1. Physics Mode (Thrust/Pressure)
        # Pattern A: "Thrust: 100"
        t_match = re.search(r'thrust\s*[:=]?\s*(\d+(\.\d+)?)', prompt_lower)
        if t_match: 
            params['thrust'] = float(t_match.group(1))
        else:
            # Pattern B: "100N Thrust"
            t_match_b = re.search(r'(\d+(\.\d+)?)\s*n?\s*thrust', prompt_lower)
            if t_match_b: params['thrust'] = float(t_match_b.group(1))
        
        p_match = re.search(r'pressure\s*[:=]?\s*(\d+(\.\d+)?)', prompt_lower)
        if p_match: params['pressure'] = float(p_match.group(1))

        # 2. Explicit Geometry Mode (New Feature!)
        # Looks for "20mm throat" or "throat 20"
        throat_match = re.search(r'(\d+(\.\d+)?)\s*(mm|cm)?\s*throat', prompt_lower)
        if throat_match: params['throat_radius'] = float(throat_match.group(1)) / 2.0 # Convert diameter to radius

        chamber_match = re.search(r'(\d+(\.\d+)?)\s*(mm|cm)?\s*(chamber|wide)', prompt_lower)
        if chamber_match: params['chamber_radius'] = float(chamber_match.group(1)) / 2.0

        exit_match = re.search(r'(\d+(\.\d+)?)\s*(mm|cm)?\s*exit', prompt_lower)
        if exit_match: params['exit_radius'] = float(exit_match.group(1)) / 2.0

        print(f"   -> 🔍 Extracted Params (Regex): {params}")

        # Fallback to LLM if no params found (optional, or merge)
        if not params:
            param_prompt = f"""
            Extract engineering parameters from this text as JSON.
            Target Class: {dna_class.__name__}
            Text: "{user_input}"
            
            Return JSON only. Keys should be snake_case.
            Common keys: thrust, pressure, radius, height, count.
            Example: {{"thrust": 50.0, "pressure": 20.0}}
            """
            
            try:
                param_json_str = self._query_local(param_prompt)
                # Basic cleanup
                if "```" in param_json_str:
                    param_json_str = param_json_str.split("```")[1].replace("json", "")
                
                llm_params = json.loads(param_json_str)
                params.update(llm_params) # Merge LLM params
                print(f"   -> Extracted Params (LLM merged): {params}")
                
            except Exception as e:
                print(f"   -> ⚠️ Param Extraction Failed: {e}. Using extracted defaults.")

        # Step 2: Instantiate DNA and Generate
        try:
            dna_instance = dna_class(**params) # Validates physics automatically
            steps = dna_instance.generate()
            
            return {
                "intent": user_input,
                "mode": "engineering",
                "operations": steps, # Already in correct format
                "meta": {
                    "class": dna_class.__name__,
                    "extracted_params": params
                }
            }
        except ValueError as ve:
            return {"error": f"Physics Violation: {ve}"}
        except Exception as e:
            return {"error": f"Engineering Error: {e}"}

    def _run_creative_mode(self, user_input: str) -> dict:
        """
        Legacy LLM-based generation for generic shapes.
        """
        # Enhanced Drafter Prompt
        prompt = f"""
        {self.system_prompt}
        
        User Request: "{user_input}"
        
        Output valid JSON recipe with 'create_' operations.
        Example: {{"operations": [{{"id": "box1", "type": "create_box", "parameters": {{"width_mm": 10...}}}}]}}
        """
        
        try:
            # Enhanced prompt to ensure JSON output
            response = self._query_local(prompt)
            print(f"   -> LLM Raw Response: {response}") # DEBUG

             # Basic cleanup
            if "```" in response:
                # Handle ```json and just ```
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            recipe = json.loads(response.strip())
            
            # --- ADAPTER: Handle "Template" Style Response ---
            # If the LLM returns a single object with "parameters", wrap it in a box operation
            # This handles the case where it returns: {"intent": "cube", "parameters": {...}}
            if isinstance(recipe, dict) and "operations" not in recipe and "steps" not in recipe:
                params = recipe.get("parameters", {})
                template_id = recipe.get("template_id", "box").lower()
                
                # Simple mapping for common shapes
                op_type = "create_box" # default
                if "cylinder" in template_id: op_type = "create_cylinder"
                if "sphere" in template_id: op_type = "create_sphere"
                if "cone" in template_id: op_type = "create_cone"
                
                recipe = {
                    "operations": [
                        {
                            "id": "generated_shape",
                            "type": op_type,
                            "parameters": params
                        }
                    ]
                }

            # Ensure "operations" key exists
            if "steps" in recipe and "operations" not in recipe:
                recipe["operations"] = recipe["steps"]
                
             # Direct list support (if LLM returns just the list)
            if isinstance(recipe, list):
                recipe = {"operations": recipe}
            
            return {
                "intent": user_input,
                "mode": "creative",
                "operations": recipe.get("operations", [])
            }
        except Exception as e:
            print(f"   -> ❌ Creative Mode Error: {e}")
            return {"error": f"Creative Mode Failed: {e}"}

    def _query_local(self, prompt: str) -> str:
        """Query local model via Ollama"""
        try:
            response = self.local_client.chat.completions.create(
                model=self.local_model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return "{}"

    # Legacy method support if needed by main.py
    def query(self, user_input: str, **kwargs):
        result = self.solve_problem(user_input)
        if "error" in result:
            raise ValueError(result["error"])
        
        recipe = result
        if "recipe" not in recipe:
             recipe = {"recipe": result} # wrap it if needed for compatibility
            
        return GeometryRequest(
            intent=user_input,
            mode=result.get("mode", "unknown"),
            recipe=result
        )
