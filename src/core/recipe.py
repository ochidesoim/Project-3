"""
LumenOrb v2.0 - Recipe Executor
Assembles geometry from AI-generated operation sequences
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

from src.computational.atoms import AtomLibrary


class Operation(BaseModel):
    """Single atomic operation in a recipe"""
    id: str = Field(description="Unique identifier for this operation")
    type: str = Field(description="Operation type (e.g., 'create_cube', 'boolean_union')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")
    inputs: List[str] = Field(default_factory=list, description="IDs of previous operations to use as inputs")


class GeometryRecipe(BaseModel):
    """
    Recipe: Sequence of atomic operations to build geometry
    This is what the AI generates instead of selecting a template
    """
    intent: str = Field(description="Brief description of what this recipe creates")
    operations: List[Operation] = Field(description="Ordered list of atomic operations")
    output_name: str = Field(default="output", description="Name for the final result")


class RecipeExecutor:
    """
    Executes a geometry recipe by running atomic operations in sequence
    """
    
    def __init__(self):
        self.library = AtomLibrary()
        self._results: Dict[str, Any] = {}
    
    def execute(self, recipe: GeometryRecipe, output_path: Path) -> Path:
        """
        Execute a geometry recipe and save the result
        
        Args:
            recipe: GeometryRecipe to execute
            output_path: Where to save the final STL file
            
        Returns:
            Path to saved file
        """
        self._results.clear()
        
        print(f"Executing recipe: {recipe.intent}")
        print(f"Operations: {len(recipe.operations)}")
        
        # Execute operations in order
        for i, op in enumerate(recipe.operations):
            print(f"  [{i+1}/{len(recipe.operations)}] {op.type} (id: {op.id})")
            
            try:
                result = self._execute_operation(op)
                self._results[op.id] = result
            except Exception as e:
                print(f"    ERROR: {str(e)}")
                raise RuntimeError(f"Operation {op.id} ({op.type}) failed: {e}")
        
        # Get final result (last operation or specified output)
        if recipe.output_name in self._results:
            final_mesh = self._results[recipe.output_name]
        elif recipe.operations:
            # Use last operation's result
            final_mesh = self._results[recipe.operations[-1].id]
        else:
            raise ValueError("Recipe has no operations")
        
        # Ensure mesh is valid
        if not hasattr(final_mesh, 'vertices') or len(final_mesh.vertices) == 0:
            raise ValueError("Recipe produced empty mesh")
        
        # Repair mesh if needed (wrapped in try/except for robustness)
        if not final_mesh.is_watertight:
            print("  Attempting mesh repair...")
            try:
                final_mesh.fill_holes()
            except Exception:
                pass
            try:
                final_mesh.merge_vertices()
            except Exception:
                pass
            try:
                final_mesh.remove_degenerate_faces()
            except Exception:
                pass
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_mesh.export(str(output_path))
        
        print(f"SUCCESS: Recipe executed, saved to {output_path}")
        print(f"  Vertices: {len(final_mesh.vertices)}, Faces: {len(final_mesh.faces)}")
        print(f"  Watertight: {final_mesh.is_watertight}")
        
        return output_path
    
    def _execute_operation(self, op: Operation):
        """Execute a single atomic operation"""
        
        # Get input meshes
        input_meshes = []
        for input_id in op.inputs:
            if input_id not in self._results:
                raise ValueError(f"Input '{input_id}' not found (operation {op.id} depends on it)")
            input_meshes.append(self._results[input_id])
        
        # Dispatch to appropriate atomic operation
        op_type = op.type
        
        if op_type == "create_cube":
            size = op.parameters.get("size_mm", 10.0)
            center = tuple(op.parameters.get("center", [0, 0, 0]))
            return self.library.create_cube(size_mm=size, center=center)
        
        elif op_type == "create_box":
            width = op.parameters.get("width_mm", 10.0)
            depth = op.parameters.get("depth_mm", 10.0)
            height = op.parameters.get("height_mm", 10.0)
            center = tuple(op.parameters.get("center", [0, 0, 0]))
            return self.library.create_box(width_mm=width, depth_mm=depth, 
                                          height_mm=height, center=center)
        
        elif op_type == "create_cylinder":
            radius = op.parameters.get("radius_mm", 5.0)
            height = op.parameters.get("height_mm", 10.0)
            center = tuple(op.parameters.get("center", [0, 0, 0]))
            sections = op.parameters.get("sections", 64)
            return self.library.create_cylinder(radius_mm=radius, height_mm=height,
                                              center=center, sections=sections)
        
        elif op_type == "create_cone":
            r_bottom = op.parameters.get("r_bottom_mm", 10.0)
            r_top = op.parameters.get("r_top_mm", 0.0)
            height = op.parameters.get("height_mm", 10.0)
            center = tuple(op.parameters.get("center", [0, 0, 0]))
            sections = op.parameters.get("sections", 64)
            return self.library.create_cone(r_bottom_mm=r_bottom, r_top_mm=r_top,
                                           height_mm=height, center=center, sections=sections)
        
        elif op_type == "create_loft":
            r_bottom = op.parameters.get("r_bottom_mm", 10.0)
            r_top = op.parameters.get("r_top_mm", 5.0)
            height = op.parameters.get("height_mm", 10.0)
            center = tuple(op.parameters.get("center", [0, 0, 0]))
            sections = op.parameters.get("sections", 64)
            return self.library.create_loft(r_bottom_mm=r_bottom, r_top_mm=r_top,
                                           height_mm=height, center=center, sections=sections)
        
        elif op_type == "create_sphere":
            radius = op.parameters.get("radius_mm", 5.0)
            center = tuple(op.parameters.get("center", [0, 0, 0]))
            subdivisions = op.parameters.get("subdivisions", 2)
            return self.library.create_sphere(radius_mm=radius, center=center,
                                            subdivisions=subdivisions)
        
        elif op_type == "create_lattice":
            lattice_type = op.parameters.get("type", "gyroid")
            bounds = op.parameters.get("bounds", [0, 0, 0, 50, 50, 50])
            unit_size = op.parameters.get("unit_size_mm", op.parameters.get("unit_size", 5.0))
            thickness = op.parameters.get("thickness_mm", op.parameters.get("thickness", 1.0))
            return self.library.create_lattice(
                lattice_type=lattice_type,
                bounds=bounds,
                unit_size_mm=unit_size,
                thickness_mm=thickness
            )
        
        elif op_type == "boolean_union":
            if len(input_meshes) < 2:
                raise ValueError("boolean_union requires at least 2 inputs")
            result = input_meshes[0]
            for mesh in input_meshes[1:]:
                result = self.library.boolean_union(result, mesh)
            return result
        
        elif op_type == "boolean_subtract":
            if len(input_meshes) < 2:
                raise ValueError("boolean_subtract requires at least 2 inputs")
            result = input_meshes[0]
            for mesh in input_meshes[1:]:
                result = self.library.boolean_subtract(result, mesh)
            return result
        
        elif op_type == "boolean_intersect":
            if len(input_meshes) < 2:
                raise ValueError("boolean_intersect requires at least 2 inputs")
            result = input_meshes[0]
            for mesh in input_meshes[1:]:
                result = self.library.boolean_intersect(result, mesh)
            return result
        
        elif op_type == "translate":
            if len(input_meshes) < 1:
                raise ValueError("translate requires at least 1 input")
            x = op.parameters.get("x", 0.0)
            y = op.parameters.get("y", 0.0)
            z = op.parameters.get("z", 0.0)
            return self.library.translate(input_meshes[0], x, y, z)
        
        elif op_type == "rotate":
            if len(input_meshes) < 1:
                raise ValueError("rotate requires at least 1 input")
            axis = tuple(op.parameters.get("axis", [0, 0, 1]))
            angle = op.parameters.get("angle_deg", 0.0)
            return self.library.rotate(input_meshes[0], axis, angle)
        
        elif op_type == "scale":
            if len(input_meshes) < 1:
                raise ValueError("scale requires at least 1 input")
            x = op.parameters.get("x", 1.0)
            y = op.parameters.get("y", 1.0)
            z = op.parameters.get("z", 1.0)
            return self.library.scale(input_meshes[0], x, y, z)
        
        elif op_type == "smooth":
            if len(input_meshes) < 1:
                raise ValueError("smooth requires at least 1 input")
            iterations = op.parameters.get("iterations", 1)
            return self.library.smooth(input_meshes[0], iterations)
        
        elif op_type == "chamfer_edges":
            if len(input_meshes) < 1:
                raise ValueError("chamfer_edges requires at least 1 input")
            distance = op.parameters.get("distance_mm", 0.5)
            return self.library.chamfer_edges(input_meshes[0], distance)
        
        else:
            raise ValueError(f"Unknown operation type: {op_type}")



