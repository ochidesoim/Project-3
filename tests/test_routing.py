import sys
from pathlib import Path
import unittest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import Agent
from src.core.registry import DNA_CATALOG

class TestAgentRouting(unittest.TestCase):
    def setUp(self):
        # Mock paths since we don't need actual AI for routing logic tests
        self.system_prompt = Path("resources/system_prompt.txt")
        self.cheatsheet = Path("resources/picogk_cheatsheet.md")
        
        # Ensure resources exist or mock them
        if not self.system_prompt.exists():
            self.system_prompt.parent.mkdir(exist_ok=True)
            self.system_prompt.write_text("dummy")
            
        self.agent = Agent(
            system_prompt_path=self.system_prompt,
            cheatsheet_path=self.cheatsheet,
            local_model_name="dummy" # We won't call the LLM for valid routing
        )

    def test_routing_rocket(self):
        """Test that 'rocket' keywords route to Engineering Mode"""
        inputs = [
            "create a rocket",
            "generate rocket boosters",
            "build me a engine",
            "thruster design"
        ]
        
        for user_input in inputs:
            with self.subTest(input=user_input):
                # We expect solve_problem to find the keyword and return engineering mode
                # It might try to call LLM for params, but we want to check the *Decision*
                
                # Mock _query_local to avoid actual LLM calls during param extraction
                original_query = self.agent._query_local
                self.agent._query_local = lambda x: '{"thrust": 100}' 
                
                result = self.agent.solve_problem(user_input)
                
                # Restore
                self.agent._query_local = original_query
                
                self.assertEqual(result.get("mode"), "engineering", f"Input '{user_input}' failed to route to Engineering")
                self.assertIn("operations", result)

    def test_routing_creative(self):
        """Test that non-engineering keywords fall back to Creative Mode"""
        inputs = [
            "make a cube",
            "random shape",
            "something cool"
        ]
        
        for user_input in inputs:
            with self.subTest(input=user_input):
                # Mock _query_local for creative mode generation
                original_query = self.agent._query_local
                self.agent._query_local = lambda x: '{"operations": []}'
                
                result = self.agent.solve_problem(user_input)
                
                self.agent._query_local = original_query
                
                self.assertEqual(result.get("mode"), "creative", f"Input '{user_input}' wrongly routed to Engineering")

if __name__ == "__main__":
    unittest.main()
