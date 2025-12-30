import sys
from pathlib import Path
import unittest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.agent import Agent
from src.library.rocket_dna import RocketEngineDNA

class TestParametrization(unittest.TestCase):
    def setUp(self):
        # Mock paths
        self.system_prompt = Path("resources/system_prompt.txt")
        self.cheatsheet = Path("resources/picogk_cheatsheet.md")
        
        # Ensure resources exist or mock them
        if not self.system_prompt.exists():
            self.system_prompt.parent.mkdir(exist_ok=True)
            self.system_prompt.write_text("dummy")
            
        self.agent = Agent(
            system_prompt_path=self.system_prompt,
            cheatsheet_path=self.cheatsheet,
            local_model_name="dummy"
        )
        
        # Mock _query_local to avoid LLM
        self.agent._query_local = lambda x: '{}'

    def test_explicit_dimensions(self):
        """Test explicit dimension extraction (LumenOrb Mode)"""
        user_input = "Create a rocket with 60mm chamber and 20mm throat"
        
        # Manually invoke extraction logic by running _run_engineering_mode
        # We need to spy on the result.
        
        result = self.agent._run_engineering_mode(RocketEngineDNA, user_input)
        params = result['meta']['extracted_params']
        
        self.assertAlmostEqual(params.get('chamber_radius'), 30.0) # 60/2
        self.assertAlmostEqual(params.get('throat_radius'), 10.0)  # 20/2
        
    def test_full_dimensions(self):
         """Test all three dimensions"""
         user_input = "combustion chamber 60mm wide, 20mm throat, 80mm exit"
         
         result = self.agent._run_engineering_mode(RocketEngineDNA, user_input)
         params = result['meta']['extracted_params']
         
         self.assertAlmostEqual(params.get('chamber_radius'), 30.0)
         self.assertAlmostEqual(params.get('throat_radius'), 10.0)
         self.assertAlmostEqual(params.get('exit_radius'), 40.0)

    def test_legacy_thrust(self):
        """Test legacy thrust extraction"""
        user_input = "Rocket with 100N thrust"
        
        result = self.agent._run_engineering_mode(RocketEngineDNA, user_input)
        params = result['meta']['extracted_params']
        
        self.assertEqual(params.get('thrust'), 100.0)

if __name__ == "__main__":
    unittest.main()
