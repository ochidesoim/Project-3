"""
LumenOrb v2.0 - Pydantic Models for Parameter Validation
Ensures AI outputs valid, type-safe JSON parameters
"""

from typing import Literal, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class BaseCylinderParams(BaseModel):
    """Parameters for base_cylinder template"""
    radius_mm: float = Field(gt=0, description="Outer radius in millimeters")
    height_mm: float = Field(gt=0, description="Total height in millimeters")
    voxel_size_mm: float = Field(default=0.5, gt=0, le=2.0, description="Voxelization resolution")


class BaseBoxParams(BaseModel):
    """Parameters for base_box template"""
    width_mm: float = Field(gt=0, description="Width (x-dimension) in millimeters")
    depth_mm: float = Field(gt=0, description="Depth (y-dimension) in millimeters")
    height_mm: float = Field(gt=0, description="Height (z-dimension) in millimeters")
    voxel_size_mm: float = Field(default=0.5, gt=0, le=2.0, description="Voxelization resolution")


class ShellLatticeGyroidParams(BaseModel):
    """Parameters for shell_lattice_gyroid template"""
    outer_radius_mm: float = Field(gt=0, description="Outer radius")
    wall_thickness_mm: float = Field(ge=0.5, description="Shell wall thickness (min 0.5mm)")
    lattice_period_mm: float = Field(gt=0, description="Gyroid cell size")
    lattice_thickness_mm: float = Field(gt=0, description="Gyroid strut thickness")
    voxel_size_mm: float = Field(default=0.5, gt=0, le=2.0)
    
    @field_validator('wall_thickness_mm')
    @classmethod
    def validate_wall_thickness(cls, v, info):
        """Ensure wall thickness is less than outer radius"""
        if 'outer_radius_mm' in info.data and v >= info.data['outer_radius_mm']:
            raise ValueError("Wall thickness must be less than outer radius")
        return v


class BoundingBox(BaseModel):
    """3D bounding box dimensions"""
    x: float = Field(gt=0)
    y: float = Field(gt=0)
    z: float = Field(gt=0)


class CutDimensions(BaseModel):
    """Dimensions for boolean cut shapes"""
    # Flexible schema - can contain radius, height, width, etc.
    pass


class BooleanCutParams(BaseModel):
    """Parameters for boolean_cut template"""
    base_mesh_path: str = Field(description="Path to existing STL file")
    cut_shape: Literal["sphere", "cylinder", "box"] = Field(description="Shape to subtract")
    cut_dimensions: Dict[str, float] = Field(description="Dimensions specific to cut shape")
    voxel_size_mm: float = Field(default=0.5, gt=0, le=2.0)


class GyroidInfillParams(BaseModel):
    """Parameters for gyroid_infill template"""
    bounding_box_mm: BoundingBox = Field(description="XYZ dimensions")
    period_mm: float = Field(gt=0, description="Gyroid cell size")
    thickness_mm: float = Field(gt=0, description="Strut thickness")
    voxel_size_mm: float = Field(default=0.5, gt=0, le=2.0)


class DeLavalNozzleParams(BaseModel):
    """Parameters for de_laval_nozzle template"""
    chamber_radius_mm: float = Field(gt=0, description="Combustion chamber radius in millimeters")
    throat_radius_mm: float = Field(gt=0, description="Throat radius (minimum) in millimeters")
    exit_radius_mm: float = Field(gt=0, description="Exit radius in millimeters")
    wall_thickness_mm: float = Field(ge=0.5, description="Wall thickness (min 0.5mm)")
    converging_length_mm: float = Field(gt=0, description="Length of converging section")
    diverging_length_mm: float = Field(gt=0, description="Length of diverging section")
    add_flange: bool = Field(default=False, description="Add structural lattice flange at throat")
    flange_radius_mm: Optional[float] = Field(default=None, gt=0, description="Flange outer radius (if add_flange=True)")
    flange_height_mm: Optional[float] = Field(default=None, gt=0, description="Flange height (if add_flange=True)")
    flange_lattice_period_mm: Optional[float] = Field(default=5.0, gt=0, description="Flange lattice cell size")
    flange_lattice_thickness_mm: Optional[float] = Field(default=0.5, gt=0, description="Flange lattice strut thickness")
    voxel_size_mm: float = Field(default=0.5, gt=0, le=2.0)
    
    @field_validator('throat_radius_mm')
    @classmethod
    def validate_throat(cls, v, info):
        """Ensure throat is smaller than chamber and exit"""
        if 'chamber_radius_mm' in info.data and v >= info.data['chamber_radius_mm']:
            raise ValueError("Throat radius must be less than chamber radius")
        if 'exit_radius_mm' in info.data and v >= info.data['exit_radius_mm']:
            raise ValueError("Throat radius must be less than exit radius")
        return v


class GeometryRequest(BaseModel):
    """
    Top-level schema for AI-generated geometry requests
    Supports both legacy template-based and new recipe-based approaches
    """
    intent: str = Field(description="Brief description of user's goal")
    mode: Literal["recipe", "template", "engineering"] = Field(default="recipe", description="Generation mode")
    
    # Template mode (legacy)
    template_id: Optional[Literal[
        "base_cylinder",
        "base_box",
        "shell_lattice_gyroid",
        "boolean_cut",
        "gyroid_infill",
        "de_laval_nozzle"
    ]] = Field(default=None, description="Template to use (if mode=template)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Template-specific parameters")
    
    # Recipe mode (new atomic composition approach)
    recipe: Optional[Dict[str, Any]] = Field(default=None, description="Geometry recipe (if mode=recipe)")
    
    def get_validated_params(self):
        """
        Validate parameters against the appropriate schema
        Returns the validated Pydantic model (template mode only)
        """
        if self.mode != "template" or self.template_id is None:
            return None
            
        param_map = {
            "base_cylinder": BaseCylinderParams,
            "base_box": BaseBoxParams,
            "shell_lattice_gyroid": ShellLatticeGyroidParams,
            "boolean_cut": BooleanCutParams,
            "gyroid_infill": GyroidInfillParams,
            "de_laval_nozzle": DeLavalNozzleParams,
        }
        
        model_class = param_map[self.template_id]
        return model_class(**self.parameters or {})


class SessionMetadata(BaseModel):
    """Schema for session manifest.json"""
    session_id: str
    hardware_profile: str = "HP OMEN 16"
    history: list[Dict[str, Any]] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    """Result from geometry execution"""
    id: int
    timestamp: str
    user_prompt: str
    ai_model_used: str
    script_path: str
    status: Literal["SUCCESS", "FAILURE", "CRASH", "ERROR"]
    mesh_path: Optional[str] = None
    error_log: Optional[str] = None
    execution_time_ms: Optional[int] = None
