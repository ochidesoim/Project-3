"""
LumenOrb v2.0 - Design Pattern Library
Reusable parameterized mechanical engineering design patterns
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


# Built-in patterns (always available without loading files)
BUILTIN_PATTERNS = {
    # ═══════════════════════════════════════════════════════════════════════
    # STRUCTURAL PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "hollow_cylinder": {
        "name": "Hollow Cylinder",
        "category": "structural",
        "description": "Cylindrical shell with specified wall thickness",
        "parameters": {
            "outer_radius": {"default": 30, "unit": "mm", "description": "Outer radius"},
            "wall_thickness": {"default": 3, "unit": "mm", "description": "Wall thickness"},
            "height": {"default": 50, "unit": "mm", "description": "Total height"},
            "z": {"default": 0, "unit": "mm", "description": "Z position"}
        },
        "recipe": {
            "steps": [
                {"id": "outer", "op": "cylinder", "params": {"radius": "{outer_radius}", "height": "{height}", "z": "{z}"}},
                {"id": "inner", "op": "cylinder", "params": {"radius": "{outer_radius}-{wall_thickness}", "height": "{height}+2", "z": "{z}-1"}},
                {"id": "shell", "op": "subtract", "params": {"target": "outer", "tool": "inner"}}
            ]
        }
    },
    
    "ribbed_panel": {
        "name": "Ribbed Panel",
        "category": "structural",
        "description": "Flat panel with reinforcing ribs for stiffness",
        "parameters": {
            "width": {"default": 100, "unit": "mm"},
            "depth": {"default": 80, "unit": "mm"},
            "thickness": {"default": 3, "unit": "mm"},
            "rib_height": {"default": 10, "unit": "mm"},
            "rib_spacing": {"default": 20, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "base_plate", "op": "box", "params": {"x": 0, "y": 0, "z": 0, "w": "{width}", "d": "{depth}", "h": "{thickness}"}},
                {"id": "rib1", "op": "box", "params": {"x": 0, "y": "{rib_spacing}", "z": "{thickness}", "w": "{width}", "d": 2, "h": "{rib_height}"}},
                {"id": "assembly", "op": "union", "params": {"target": "base_plate", "tool": "rib1"}}
            ]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # THERMAL PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "heat_sink": {
        "name": "Heat Sink with Lattice Core",
        "category": "thermal",
        "description": "Cylindrical heat sink with gyroid infill for maximum surface area",
        "parameters": {
            "radius": {"default": 25, "unit": "mm"},
            "height": {"default": 40, "unit": "mm"},
            "wall_thickness": {"default": 2, "unit": "mm"},
            "unit_size": {"default": 5, "unit": "mm"},
            "strut_thickness": {"default": 0.8, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "outer_shell", "op": "cylinder", "params": {"radius": "{radius}", "height": "{height}", "z": 0}},
                {"id": "lattice_core", "op": "lattice", "params": {"type": "gyroid", "bounds": ["-{radius}+{wall_thickness}", "-{radius}+{wall_thickness}", "{wall_thickness}", "{radius}*2-{wall_thickness}*2", "{radius}*2-{wall_thickness}*2", "{height}-{wall_thickness}*2"], "unit_size": "{unit_size}", "thickness": "{strut_thickness}"}},
                {"id": "heat_sink", "op": "union", "params": {"target": "outer_shell", "tool": "lattice_core"}}
            ]
        }
    },
    
    "cooling_jacket": {
        "name": "Cooling Jacket",
        "category": "thermal",
        "description": "Double-walled shell with lattice infill for fluid cooling",
        "parameters": {
            "inner_radius": {"default": 20, "unit": "mm"},
            "jacket_thickness": {"default": 8, "unit": "mm"},
            "wall_thickness": {"default": 1.5, "unit": "mm"},
            "height": {"default": 60, "unit": "mm"},
            "unit_size": {"default": 4, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "outer_wall", "op": "cylinder", "params": {"radius": "{inner_radius}+{jacket_thickness}", "height": "{height}", "z": 0}},
                {"id": "inner_wall", "op": "cylinder", "params": {"radius": "{inner_radius}", "height": "{height}+2", "z": -1}},
                {"id": "jacket_shell", "op": "subtract", "params": {"target": "outer_wall", "tool": "inner_wall"}},
                {"id": "lattice_fill", "op": "lattice", "params": {"type": "gyroid", "bounds": ["-{inner_radius}-{jacket_thickness}+{wall_thickness}", "-{inner_radius}-{jacket_thickness}+{wall_thickness}", "{wall_thickness}", "({inner_radius}+{jacket_thickness})*2-{wall_thickness}*2", "({inner_radius}+{jacket_thickness})*2-{wall_thickness}*2", "{height}-{wall_thickness}*2"], "unit_size": "{unit_size}", "thickness": 1}},
                {"id": "cooling_jacket", "op": "union", "params": {"target": "jacket_shell", "tool": "lattice_fill"}}
            ]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # CONNECTOR PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "flange_joint": {
        "name": "Pipe Flange",
        "category": "connectors",
        "description": "Standard pipe flange with bolt holes",
        "parameters": {
            "pipe_radius": {"default": 15, "unit": "mm"},
            "flange_radius": {"default": 30, "unit": "mm"},
            "flange_thickness": {"default": 8, "unit": "mm"},
            "bolt_circle_radius": {"default": 22, "unit": "mm"},
            "bolt_hole_radius": {"default": 3, "unit": "mm"},
            "num_bolts": {"default": 4, "unit": "count"}
        },
        "recipe": {
            "steps": [
                {"id": "flange_disc", "op": "cylinder", "params": {"radius": "{flange_radius}", "height": "{flange_thickness}", "z": 0}},
                {"id": "pipe_bore", "op": "cylinder", "params": {"radius": "{pipe_radius}", "height": "{flange_thickness}+2", "z": -1}},
                {"id": "flange_with_bore", "op": "subtract", "params": {"target": "flange_disc", "tool": "pipe_bore"}}
            ]
        }
    },
    
    "threaded_boss": {
        "name": "Threaded Boss",
        "category": "connectors",
        "description": "Cylindrical boss for threaded fastener",
        "parameters": {
            "outer_radius": {"default": 6, "unit": "mm"},
            "bore_radius": {"default": 2.5, "unit": "mm", "description": "Tap drill size"},
            "height": {"default": 12, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "boss", "op": "cylinder", "params": {"radius": "{outer_radius}", "height": "{height}", "z": 0}},
                {"id": "tap_hole", "op": "cylinder", "params": {"radius": "{bore_radius}", "height": "{height}+2", "z": -1}},
                {"id": "threaded_boss", "op": "subtract", "params": {"target": "boss", "tool": "tap_hole"}}
            ]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # FLOW PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "filter_element": {
        "name": "Filter Element",
        "category": "flow",
        "description": "Cylindrical filter with lattice core for particle filtration",
        "parameters": {
            "outer_radius": {"default": 25, "unit": "mm"},
            "inner_radius": {"default": 10, "unit": "mm"},
            "height": {"default": 60, "unit": "mm"},
            "unit_size": {"default": 3, "unit": "mm"},
            "wall_thickness": {"default": 1.5, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "outer_tube", "op": "cylinder", "params": {"radius": "{outer_radius}", "height": "{height}", "z": 0}},
                {"id": "inner_bore", "op": "cylinder", "params": {"radius": "{inner_radius}", "height": "{height}+2", "z": -1}},
                {"id": "filter_shell", "op": "subtract", "params": {"target": "outer_tube", "tool": "inner_bore"}},
                {"id": "lattice_media", "op": "lattice", "params": {"type": "gyroid", "bounds": ["-{outer_radius}+{wall_thickness}", "-{outer_radius}+{wall_thickness}", "{wall_thickness}", "{outer_radius}*2-{wall_thickness}*2", "{outer_radius}*2-{wall_thickness}*2", "{height}-{wall_thickness}*2"], "unit_size": "{unit_size}", "thickness": 0.8}},
                {"id": "filter", "op": "union", "params": {"target": "filter_shell", "tool": "lattice_media"}}
            ]
        }
    },
    
    "nozzle_de_laval": {
        "name": "De Laval Nozzle",
        "category": "flow",
        "description": "Converging-diverging nozzle for supersonic flow",
        "parameters": {
            "inlet_radius": {"default": 40, "unit": "mm"},
            "throat_radius": {"default": 15, "unit": "mm"},
            "outlet_radius": {"default": 35, "unit": "mm"},
            "converging_length": {"default": 30, "unit": "mm"},
            "diverging_length": {"default": 50, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "converging", "op": "loft", "params": {"r_bottom": "{inlet_radius}", "r_top": "{throat_radius}", "h": "{converging_length}", "z": 0}},
                {"id": "diverging", "op": "loft", "params": {"r_bottom": "{throat_radius}", "r_top": "{outlet_radius}", "h": "{diverging_length}", "z": "{converging_length}"}},
                {"id": "nozzle", "op": "union", "params": {"target": "converging", "tool": "diverging"}}
            ]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # HOUSING PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "bearing_housing": {
        "name": "Bearing Housing",
        "category": "housings",
        "description": "Cylindrical housing for standard bearing with mounting flange",
        "parameters": {
            "bearing_od": {"default": 35, "unit": "mm"},
            "bearing_width": {"default": 11, "unit": "mm"},
            "housing_wall": {"default": 5, "unit": "mm"},
            "flange_width": {"default": 15, "unit": "mm"},
            "flange_thickness": {"default": 8, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "housing_body", "op": "cylinder", "params": {"radius": "{bearing_od}/2+{housing_wall}", "height": "{bearing_width}+{flange_thickness}", "z": 0}},
                {"id": "bearing_bore", "op": "cylinder", "params": {"radius": "{bearing_od}/2", "height": "{bearing_width}+1", "z": "{flange_thickness}"}},
                {"id": "housing", "op": "subtract", "params": {"target": "housing_body", "tool": "bearing_bore"}}
            ]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # IMPACT/ENERGY PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "impact_absorber": {
        "name": "Impact Absorber",
        "category": "energy",
        "description": "Crushable structure with lattice core for energy absorption",
        "parameters": {
            "radius": {"default": 30, "unit": "mm"},
            "height": {"default": 80, "unit": "mm"},
            "wall_thickness": {"default": 2, "unit": "mm"},
            "unit_size": {"default": 6, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "outer_shell", "op": "cylinder", "params": {"radius": "{radius}", "height": "{height}", "z": 0}},
                {"id": "crush_core", "op": "lattice", "params": {"type": "gyroid", "bounds": ["-{radius}+{wall_thickness}", "-{radius}+{wall_thickness}", "{wall_thickness}", "{radius}*2-{wall_thickness}*2", "{radius}*2-{wall_thickness}*2", "{height}-{wall_thickness}*2"], "unit_size": "{unit_size}", "thickness": 1}},
                {"id": "absorber", "op": "union", "params": {"target": "outer_shell", "tool": "crush_core"}}
            ]
        }
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # ROCKET PROPULSION PATTERNS
    # ═══════════════════════════════════════════════════════════════════════
    
    "combustion_chamber": {
        "name": "Combustion Chamber",
        "category": "propulsion",
        "description": "Cylindrical combustion chamber with thick pressure walls",
        "parameters": {
            "inner_radius": {"default": 40, "unit": "mm"},
            "wall_thickness": {"default": 8, "unit": "mm"},
            "length": {"default": 100, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "outer_wall", "op": "cylinder", "params": {"radius": "{inner_radius}+{wall_thickness}", "height": "{length}", "z": 0}},
                {"id": "inner_bore", "op": "cylinder", "params": {"radius": "{inner_radius}", "height": "{length}+2", "z": -1}},
                {"id": "chamber", "op": "subtract", "params": {"target": "outer_wall", "tool": "inner_bore"}}
            ]
        }
    },
    
    "regenerative_engine": {
        "name": "Regeneratively Cooled Engine",
        "category": "propulsion",
        "description": "Rocket engine with gyroid cooling channels in walls",
        "parameters": {
            "chamber_radius": {"default": 50, "unit": "mm"},
            "chamber_length": {"default": 80, "unit": "mm"},
            "throat_radius": {"default": 20, "unit": "mm"},
            "exit_radius": {"default": 45, "unit": "mm"},
            "nozzle_length": {"default": 60, "unit": "mm"},
            "wall_thickness": {"default": 10, "unit": "mm"},
            "skin_thickness": {"default": 1.5, "unit": "mm"},
            "cooling_unit_size": {"default": 4, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "chamber_outer", "op": "cylinder", "params": {"radius": "{chamber_radius}+{wall_thickness}", "height": "{chamber_length}", "z": 0}},
                {"id": "chamber_inner", "op": "cylinder", "params": {"radius": "{chamber_radius}", "height": "{chamber_length}+2", "z": -1}},
                {"id": "chamber_shell", "op": "subtract", "params": {"target": "chamber_outer", "tool": "chamber_inner"}},
                {"id": "cooling_lattice", "op": "lattice", "params": {"type": "gyroid", "bounds": ["-{chamber_radius}-{wall_thickness}+{skin_thickness}", "-{chamber_radius}-{wall_thickness}+{skin_thickness}", "{skin_thickness}", "({chamber_radius}+{wall_thickness})*2-{skin_thickness}*2", "({chamber_radius}+{wall_thickness})*2-{skin_thickness}*2", "{chamber_length}-{skin_thickness}*2"], "unit_size": "{cooling_unit_size}", "thickness": 1}},
                {"id": "cooled_chamber", "op": "union", "params": {"target": "chamber_shell", "tool": "cooling_lattice"}},
                {"id": "converging", "op": "loft", "params": {"r_bottom": "{chamber_radius}", "r_top": "{throat_radius}", "h": 30, "z": "{chamber_length}"}},
                {"id": "chamber_with_converge", "op": "union", "params": {"target": "cooled_chamber", "tool": "converging"}},
                {"id": "diverging", "op": "loft", "params": {"r_bottom": "{throat_radius}", "r_top": "{exit_radius}", "h": "{nozzle_length}", "z": "{chamber_length}+30"}},
                {"id": "complete_engine", "op": "union", "params": {"target": "chamber_with_converge", "tool": "diverging"}}
            ]
        }
    },
    
    "rocket_nozzle_cooled": {
        "name": "Cooled Rocket Nozzle",
        "category": "propulsion",
        "description": "De Laval nozzle with regenerative cooling jacket",
        "parameters": {
            "inlet_radius": {"default": 50, "unit": "mm"},
            "throat_radius": {"default": 18, "unit": "mm"},
            "exit_radius": {"default": 40, "unit": "mm"},
            "converge_length": {"default": 35, "unit": "mm"},
            "diverge_length": {"default": 55, "unit": "mm"},
            "jacket_thickness": {"default": 8, "unit": "mm"},
            "cooling_unit_size": {"default": 3, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "converging_inner", "op": "loft", "params": {"r_bottom": "{inlet_radius}", "r_top": "{throat_radius}", "h": "{converge_length}", "z": 0}},
                {"id": "diverging_inner", "op": "loft", "params": {"r_bottom": "{throat_radius}", "r_top": "{exit_radius}", "h": "{diverge_length}", "z": "{converge_length}"}},
                {"id": "inner_nozzle", "op": "union", "params": {"target": "converging_inner", "tool": "diverging_inner"}},
                {"id": "converging_outer", "op": "loft", "params": {"r_bottom": "{inlet_radius}+{jacket_thickness}", "r_top": "{throat_radius}+{jacket_thickness}", "h": "{converge_length}", "z": 0}},
                {"id": "diverging_outer", "op": "loft", "params": {"r_bottom": "{throat_radius}+{jacket_thickness}", "r_top": "{exit_radius}+{jacket_thickness}", "h": "{diverge_length}", "z": "{converge_length}"}},
                {"id": "outer_nozzle", "op": "union", "params": {"target": "converging_outer", "tool": "diverging_outer"}},
                {"id": "nozzle_jacket", "op": "subtract", "params": {"target": "outer_nozzle", "tool": "inner_nozzle"}}
            ]
        }
    },
    
    "fuel_tank": {
        "name": "Cylindrical Fuel Tank",
        "category": "propulsion",
        "description": "Pressure vessel with domed ends for propellant storage",
        "parameters": {
            "radius": {"default": 60, "unit": "mm"},
            "cylinder_length": {"default": 150, "unit": "mm"},
            "wall_thickness": {"default": 3, "unit": "mm"},
            "dome_height": {"default": 30, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "main_cylinder", "op": "cylinder", "params": {"radius": "{radius}", "height": "{cylinder_length}", "z": "{dome_height}"}},
                {"id": "bottom_dome", "op": "sphere", "params": {"radius": "{radius}", "z": "{dome_height}"}},
                {"id": "tank_body", "op": "union", "params": {"target": "main_cylinder", "tool": "bottom_dome"}},
                {"id": "top_dome", "op": "sphere", "params": {"radius": "{radius}", "z": "{dome_height}+{cylinder_length}"}},
                {"id": "full_tank", "op": "union", "params": {"target": "tank_body", "tool": "top_dome"}}
            ]
        }
    },
    
    "injector_plate": {
        "name": "Injector Plate",
        "category": "propulsion",
        "description": "Flat plate with fuel/oxidizer injection holes pattern",
        "parameters": {
            "radius": {"default": 45, "unit": "mm"},
            "thickness": {"default": 12, "unit": "mm"},
            "hole_radius": {"default": 3, "unit": "mm"},
            "hole_circle_radius": {"default": 30, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "plate", "op": "cylinder", "params": {"radius": "{radius}", "height": "{thickness}", "z": 0}},
                {"id": "center_hole", "op": "cylinder", "params": {"radius": "{hole_radius}", "height": "{thickness}+2", "z": -1}},
                {"id": "plate_with_hole", "op": "subtract", "params": {"target": "plate", "tool": "center_hole"}}
            ]
        }
    },
    
    "thruster_assembly": {
        "name": "Complete Thruster",
        "category": "propulsion",
        "description": "Small attitude control thruster with chamber and nozzle",
        "parameters": {
            "chamber_radius": {"default": 15, "unit": "mm"},
            "chamber_length": {"default": 30, "unit": "mm"},
            "throat_radius": {"default": 5, "unit": "mm"},
            "exit_radius": {"default": 12, "unit": "mm"},
            "nozzle_length": {"default": 25, "unit": "mm"},
            "wall_thickness": {"default": 2, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "chamber", "op": "cylinder", "params": {"radius": "{chamber_radius}", "height": "{chamber_length}", "z": 0}},
                {"id": "converge", "op": "loft", "params": {"r_bottom": "{chamber_radius}", "r_top": "{throat_radius}", "h": 10, "z": "{chamber_length}"}},
                {"id": "with_converge", "op": "union", "params": {"target": "chamber", "tool": "converge"}},
                {"id": "diverge", "op": "loft", "params": {"r_bottom": "{throat_radius}", "r_top": "{exit_radius}", "h": "{nozzle_length}", "z": "{chamber_length}+10"}},
                {"id": "thruster", "op": "union", "params": {"target": "with_converge", "tool": "diverge"}}
            ]
        }
    },
    
    "nozzle_extension": {
        "name": "Nozzle Extension",
        "category": "propulsion",
        "description": "Conical nozzle extension with cooling ribs",
        "parameters": {
            "inlet_radius": {"default": 35, "unit": "mm"},
            "exit_radius": {"default": 55, "unit": "mm"},
            "length": {"default": 80, "unit": "mm"},
            "wall_thickness": {"default": 2, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "outer_cone", "op": "loft", "params": {"r_bottom": "{inlet_radius}+{wall_thickness}", "r_top": "{exit_radius}+{wall_thickness}", "h": "{length}", "z": 0}},
                {"id": "inner_cone", "op": "loft", "params": {"r_bottom": "{inlet_radius}", "r_top": "{exit_radius}", "h": "{length}+2", "z": -1}},
                {"id": "extension", "op": "subtract", "params": {"target": "outer_cone", "tool": "inner_cone"}}
            ]
        }
    },
    
    "engine_mount_ring": {
        "name": "Engine Mount Ring",
        "category": "propulsion",
        "description": "Structural ring for mounting engine to vehicle",
        "parameters": {
            "inner_radius": {"default": 55, "unit": "mm"},
            "outer_radius": {"default": 75, "unit": "mm"},
            "height": {"default": 20, "unit": "mm"},
            "mount_hole_radius": {"default": 4, "unit": "mm"}
        },
        "recipe": {
            "steps": [
                {"id": "ring_outer", "op": "cylinder", "params": {"radius": "{outer_radius}", "height": "{height}", "z": 0}},
                {"id": "ring_inner", "op": "cylinder", "params": {"radius": "{inner_radius}", "height": "{height}+2", "z": -1}},
                {"id": "mount_ring", "op": "subtract", "params": {"target": "ring_outer", "tool": "ring_inner"}}
            ]
        }
    }
}


class PatternLibrary:
    """
    Library of reusable mechanical design patterns.
    
    Features:
    - Load patterns from files or use built-in patterns
    - Parameterize patterns with custom dimensions
    - List available patterns by category
    - Generate recipes from patterns
    """
    
    def __init__(self, patterns_dir: Optional[Path] = None):
        """
        Initialize the pattern library.
        
        Args:
            patterns_dir: Optional directory containing pattern JSON files
        """
        self.patterns_dir = patterns_dir
        self.patterns: Dict[str, Dict] = {}
        
        # Load built-in patterns
        self.patterns.update(BUILTIN_PATTERNS)
        print(f"✅ Loaded {len(BUILTIN_PATTERNS)} built-in patterns")
        
        # Load patterns from directory if provided
        if patterns_dir:
            self._load_patterns_from_directory(patterns_dir)
    
    def _load_patterns_from_directory(self, patterns_dir: Path):
        """Load patterns from JSON files in directory."""
        patterns_dir = Path(patterns_dir)
        if not patterns_dir.exists():
            return
        
        for json_file in patterns_dir.glob("**/*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    pattern = json.load(f)
                    pattern_id = json_file.stem
                    self.patterns[pattern_id] = pattern
                    print(f"  Loaded pattern: {pattern_id}")
            except Exception as e:
                print(f"⚠️ Could not load {json_file}: {e}")
    
    def get_pattern(self, name: str) -> Optional[Dict]:
        """Get a pattern by name."""
        return self.patterns.get(name)
    
    def list_patterns(self, category: Optional[str] = None) -> List[Dict]:
        """
        List available patterns.
        
        Args:
            category: Optional filter by category
            
        Returns:
            List of pattern summaries
        """
        result = []
        for pattern_id, pattern in self.patterns.items():
            if category and pattern.get('category') != category:
                continue
            
            result.append({
                "id": pattern_id,
                "name": pattern.get('name', pattern_id),
                "category": pattern.get('category', 'general'),
                "description": pattern.get('description', ''),
                "parameters": list(pattern.get('parameters', {}).keys())
            })
        
        return result
    
    def list_categories(self) -> List[str]:
        """List all available categories."""
        categories = set()
        for pattern in self.patterns.values():
            categories.add(pattern.get('category', 'general'))
        return sorted(categories)
    
    def parameterize(self, pattern_name: str, params: Dict[str, Any]) -> Dict:
        """
        Generate a recipe from a pattern with custom parameters.
        
        Args:
            pattern_name: Name of the pattern to use
            params: Dictionary of parameter values to override defaults
            
        Returns:
            A recipe dictionary ready for execution
        """
        pattern = self.get_pattern(pattern_name)
        if not pattern:
            raise ValueError(f"Pattern not found: {pattern_name}")
        
        # Merge with defaults
        all_params = {}
        for param_name, param_def in pattern.get('parameters', {}).items():
            if param_name in params:
                all_params[param_name] = params[param_name]
            else:
                all_params[param_name] = param_def.get('default', 0)
        
        # Deep copy and substitute parameters in recipe
        recipe = json.loads(json.dumps(pattern.get('recipe', {})))
        
        def substitute(obj):
            if isinstance(obj, str):
                # Replace parameter placeholders
                result = obj
                for key, value in all_params.items():
                    result = result.replace(f"{{{key}}}", str(value))
                
                # Try to evaluate math expressions
                try:
                    # Simple eval for math expressions
                    if any(op in result for op in ['+', '-', '*', '/']):
                        result = str(eval(result))
                except:
                    pass
                
                return result
            elif isinstance(obj, dict):
                return {k: substitute(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute(item) for item in obj]
            else:
                return obj
        
        return substitute(recipe)
    
    def get_pattern_prompt(self) -> str:
        """Generate a prompt snippet listing available patterns for AI."""
        lines = ["AVAILABLE DESIGN PATTERNS:"]
        
        for category in self.list_categories():
            lines.append(f"\n[{category.upper()}]")
            for pattern in self.list_patterns(category):
                params = ", ".join(pattern['parameters'][:3])
                if len(pattern['parameters']) > 3:
                    params += "..."
                lines.append(f"  - {pattern['name']}: {pattern['description']} ({params})")
        
        return "\n".join(lines)
