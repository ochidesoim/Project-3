"""
LumenOrb v2.0 - Atomic Operations Library
The "Lego Box" - Small, verified building blocks for infinite geometry combinations
"""

import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import trimesh
    from trimesh.creation import box, cylinder, icosphere
    import trimesh.transformations
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False


class AtomLibrary:
    """
    Library of atomic geometry operations.
    Each operation is a verified, reusable building block.
    """
    
    def __init__(self):
        self._mesh_cache: Dict[str, trimesh.Trimesh] = {}
    
    def create_cube(self, size_mm: float, center: tuple = (0, 0, 0)) -> trimesh.Trimesh:
        """
        Atom: Create a cube
        
        Args:
            size_mm: Edge length in millimeters
            center: (x, y, z) center position
            
        Returns:
            Trimesh cube
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        mesh = box(extents=[size_mm, size_mm, size_mm])
        mesh.apply_translation(center)
        return mesh
    
    def create_box(self, width_mm: float, depth_mm: float, height_mm: float, 
                   center: tuple = (0, 0, 0)) -> trimesh.Trimesh:
        """
        Atom: Create a rectangular box
        
        Args:
            width_mm: X dimension
            depth_mm: Y dimension
            height_mm: Z dimension
            center: (x, y, z) center position
            
        Returns:
            Trimesh box
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        mesh = box(extents=[width_mm, depth_mm, height_mm])
        mesh.apply_translation(center)
        return mesh
    
    def create_cylinder(self, radius_mm: float, height_mm: float,
                       center: tuple = (0, 0, 0), sections: int = 64) -> trimesh.Trimesh:
        """
        Atom: Create a cylinder
        
        Args:
            radius_mm: Cylinder radius
            height_mm: Cylinder height
            center: (x, y, z) - z is the BOTTOM of the cylinder, not center
            sections: Number of radial sections (smoothness)
            
        Returns:
            Trimesh cylinder
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        mesh = cylinder(radius=radius_mm, height=height_mm, sections=sections)
        # trimesh creates cylinder centered at origin
        # We want Z to be the BOTTOM, so translate up by height/2
        x, y, z = center
        mesh.apply_translation([x, y, z + height_mm / 2])
        return mesh
    
    def create_sphere(self, radius_mm: float, center: tuple = (0, 0, 0),
                     subdivisions: int = 2) -> trimesh.Trimesh:
        """
        Atom: Create a sphere
        
        Args:
            radius_mm: Sphere radius
            center: (x, y, z) center position
            subdivisions: Icosphere subdivisions (higher = smoother)
            
        Returns:
            Trimesh sphere
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        mesh = icosphere(subdivisions=subdivisions, radius=radius_mm)
        mesh.apply_translation(center)
        return mesh
    
    def create_cone(self, r_bottom_mm: float, r_top_mm: float, height_mm: float,
                   center: tuple = (0, 0, 0), sections: int = 64) -> trimesh.Trimesh:
        """
        Atom: Create a cone or truncated cone (frustum)
        
        Args:
            r_bottom_mm: Bottom radius (larger end)
            r_top_mm: Top radius (0 for sharp cone, >0 for frustum/nozzle)
            height_mm: Cone height
            center: (x, y, z) - z is the BOTTOM of the cone, not center
            sections: Number of radial sections (smoothness)
            
        Returns:
            Trimesh cone
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        x, y, z = center
        
        # If we need a truncated cone (frustum), create manually starting at z=0
        if r_top_mm > 0:
            # Create frustum vertices manually starting at z=0
            theta = np.linspace(0, 2 * np.pi, sections, endpoint=False)
            
            # Bottom vertices at z=0
            bottom_x = r_bottom_mm * np.cos(theta)
            bottom_y = r_bottom_mm * np.sin(theta)
            bottom_z = np.zeros(sections)
            
            # Top vertices at z=height_mm
            top_x = r_top_mm * np.cos(theta)
            top_y = r_top_mm * np.sin(theta)
            top_z = np.full(sections, height_mm)
            
            # Combine vertices
            vertices = np.vstack([
                np.column_stack([bottom_x, bottom_y, bottom_z]),
                np.column_stack([top_x, top_y, top_z]),
                [[0, 0, 0]],  # Bottom center
                [[0, 0, height_mm]]  # Top center
            ])
            
            # Create faces
            faces = []
            n = sections
            bottom_center = 2 * n
            top_center = 2 * n + 1
            
            for i in range(n):
                i_next = (i + 1) % n
                
                # Side quad (as two triangles)
                faces.append([i, i_next, n + i_next])
                faces.append([i, n + i_next, n + i])
                
                # Bottom cap
                faces.append([bottom_center, i_next, i])
                
                # Top cap
                faces.append([top_center, n + i, n + i_next])
            
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            mesh.fix_normals()
            # Frustum starts at z=0, just translate by center
            mesh.apply_translation([x, y, z])
        else:
            # Sharp cone using trimesh (it's centered, need to offset)
            from trimesh.creation import cone as trimesh_cone
            mesh = trimesh_cone(radius=r_bottom_mm, height=height_mm, sections=sections)
            # trimesh cone is centered at origin, translate so bottom is at z
            mesh.apply_translation([x, y, z + height_mm / 2])
        
        return mesh
    
    def create_loft(self, r_bottom_mm: float, r_top_mm: float, height_mm: float,
                   center: tuple = (0, 0, 0), sections: int = 64) -> trimesh.Trimesh:
        """
        Atom: Create a smooth lofted shape (curved frustum)
        
        Args:
            r_bottom_mm: Bottom radius
            r_top_mm: Top radius
            height_mm: Loft height
            center: (x, y, z) - z is the BOTTOM of the loft, not center
            sections: Number of radial sections (smoothness)
            
        Returns:
            Trimesh loft with smooth curved profile
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        x, y, z_base = center
        
        # Create a curved loft using multiple stacked rings
        # Use a smooth bezier-like curve for the radius transition
        n_rings = max(16, sections // 4)
        
        vertices = []
        faces = []
        
        # Generate smooth radius profile using cosine interpolation
        # Vertices start at local z=0 and go to z=height_mm
        for ring_idx in range(n_rings + 1):
            t = ring_idx / n_rings
            # Smooth cosine interpolation for radius
            smooth_t = (1 - np.cos(t * np.pi)) / 2
            radius = r_bottom_mm + (r_top_mm - r_bottom_mm) * smooth_t
            local_z = t * height_mm
            
            theta = np.linspace(0, 2 * np.pi, sections, endpoint=False)
            ring_verts = np.column_stack([
                radius * np.cos(theta),
                radius * np.sin(theta),
                np.full(sections, local_z)
            ])
            vertices.append(ring_verts)
        
        vertices = np.vstack(vertices)
        
        # Add center points for caps
        bottom_center_idx = len(vertices)
        vertices = np.vstack([vertices, [[0, 0, 0]]])
        top_center_idx = len(vertices)
        vertices = np.vstack([vertices, [[0, 0, height_mm]]])
        
        # Create faces between rings
        for ring_idx in range(n_rings):
            for i in range(sections):
                i_next = (i + 1) % sections
                base = ring_idx * sections
                next_base = (ring_idx + 1) * sections
                
                # Quad as two triangles
                faces.append([base + i, base + i_next, next_base + i_next])
                faces.append([base + i, next_base + i_next, next_base + i])
        
        # Bottom cap
        for i in range(sections):
            i_next = (i + 1) % sections
            faces.append([bottom_center_idx, i_next, i])
        
        # Top cap
        top_ring_start = n_rings * sections
        for i in range(sections):
            i_next = (i + 1) % sections
            faces.append([top_center_idx, top_ring_start + i, top_ring_start + i_next])
        
        mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
        mesh.fix_normals()
        # Translate so bottom is at z_base
        mesh.apply_translation([x, y, z_base])
        return mesh
    
    def create_lattice(self, lattice_type: str = "gyroid", 
                      bounds: list = None,
                      unit_size_mm: float = 5.0,
                      thickness_mm: float = 1.0) -> trimesh.Trimesh:
        """
        Atom: Create a lattice structure (gyroid)
        
        Args:
            lattice_type: Type of lattice ("gyroid" supported)
            bounds: [x, y, z, width, depth, height] bounding box
            unit_size_mm: Size of unit cell in mm
            thickness_mm: Wall thickness of lattice struts
            
        Returns:
            Trimesh lattice
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        if bounds is None:
            bounds = [0, 0, 0, 50, 50, 50]
        
        x0, y0, z0 = bounds[0], bounds[1], bounds[2]
        w, d, h = bounds[3], bounds[4], bounds[5]
        
        # Create gyroid using marching cubes on the gyroid implicit function
        # Gyroid: sin(x)*cos(y) + sin(y)*cos(z) + sin(z)*cos(x) = 0
        from skimage import measure
        
        # Resolution based on unit size
        resolution = max(int(max(w, d, h) / (unit_size_mm / 4)), 20)
        
        # Create sample grid
        x = np.linspace(0, w, resolution)
        y = np.linspace(0, d, resolution)
        z = np.linspace(0, h, resolution)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
        
        # Scale for unit cell size
        scale = 2 * np.pi / unit_size_mm
        
        # Gyroid implicit function
        gyroid = (np.sin(X * scale) * np.cos(Y * scale) + 
                  np.sin(Y * scale) * np.cos(Z * scale) + 
                  np.sin(Z * scale) * np.cos(X * scale))
        
        # Threshold for thickness (smaller = thicker struts)
        iso_value = thickness_mm / unit_size_mm
        
        try:
            # Extract isosurface using marching cubes
            verts, faces, normals, values = measure.marching_cubes(
                gyroid, level=iso_value, spacing=(w/resolution, d/resolution, h/resolution)
            )
            
            # Also extract the negative side for solid lattice
            verts2, faces2, normals2, values2 = measure.marching_cubes(
                gyroid, level=-iso_value, spacing=(w/resolution, d/resolution, h/resolution)
            )
            
            # Combine both surfaces
            mesh1 = trimesh.Trimesh(vertices=verts + [x0, y0, z0], faces=faces)
            mesh2 = trimesh.Trimesh(vertices=verts2 + [x0, y0, z0], faces=faces2)
            
            # Try to create solid, fallback to surface if fails
            try:
                mesh = trimesh.util.concatenate([mesh1, mesh2])
                mesh.fix_normals()
            except:
                mesh = mesh1
                mesh.fix_normals()
            
            return mesh
            
        except Exception as e:
            # Fallback: create a simple porous box if gyroid fails
            print(f"Warning: Gyroid generation failed ({e}), using fallback")
            return self.create_box(w, d, h, center=(x0 + w/2, y0 + d/2, z0 + h/2))
    
    def boolean_union(self, mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Atom: Combine two meshes (Union)
        
        Args:
            mesh_a: First mesh
            mesh_b: Second mesh
            
        Returns:
            Combined mesh
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        try:
            result = mesh_a.union(mesh_b)
            if result is None or len(result.vertices) == 0:
                # Fallback: concatenate if union fails
                print("   ⚠️ Boolean union returned empty, using concatenation fallback")
                return trimesh.util.concatenate([mesh_a, mesh_b])
            return result
        except Exception as e:
            # Fallback for non-watertight meshes
            print(f"   ⚠️ Boolean union failed ({e}), using concatenation fallback")
            return trimesh.util.concatenate([mesh_a, mesh_b])
    
    def boolean_subtract(self, mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Atom: Cut mesh_b from mesh_a (Subtract)
        
        Args:
            mesh_a: Base mesh
            mesh_b: Mesh to subtract
            
        Returns:
            Result mesh
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        try:
            result = mesh_a.difference(mesh_b)
            if result is None or len(result.vertices) == 0:
                # If subtraction fails, return original
                print("   ⚠️ Boolean subtract returned empty, returning original mesh")
                return mesh_a
            return result
        except Exception as e:
            # Fallback for non-watertight meshes
            print(f"   ⚠️ Boolean subtract failed ({e}), returning original mesh")
            return mesh_a
    
    def boolean_intersect(self, mesh_a: trimesh.Trimesh, mesh_b: trimesh.Trimesh) -> trimesh.Trimesh:
        """
        Atom: Keep only overlapping region (Intersect)
        
        Args:
            mesh_a: First mesh
            mesh_b: Second mesh
            
        Returns:
            Intersection mesh
        """
        if not TRIMESH_AVAILABLE:
            raise ImportError("trimesh not installed")
        
        try:
            result = mesh_a.intersection(mesh_b)
            if result is None or len(result.vertices) == 0:
                # Return empty mesh if intersection fails
                print("   ⚠️ Boolean intersect returned empty")
                return trimesh.Trimesh()
            return result
        except Exception as e:
            # Fallback for non-watertight meshes
            print(f"   ⚠️ Boolean intersect failed ({e}), returning first mesh")
            return mesh_a
    
    def translate(self, mesh: trimesh.Trimesh, x: float, y: float, z: float) -> trimesh.Trimesh:
        """
        Atom: Move mesh to new position
        
        Args:
            mesh: Mesh to translate
            x, y, z: Translation in millimeters
            
        Returns:
            Translated mesh (new copy)
        """
        result = mesh.copy()
        result.apply_translation([x, y, z])
        return result
    
    def rotate(self, mesh: trimesh.Trimesh, axis: tuple, angle_deg: float) -> trimesh.Trimesh:
        """
        Atom: Rotate mesh around axis
        
        Args:
            mesh: Mesh to rotate
            axis: (x, y, z) rotation axis vector
            angle_deg: Rotation angle in degrees
            
        Returns:
            Rotated mesh (new copy)
        """
        result = mesh.copy()
        angle_rad = np.radians(angle_deg)
        direction = np.array(axis)
        direction = direction / np.linalg.norm(direction)  # Normalize
        result.apply_transform(trimesh.transformations.rotation_matrix(angle_rad, direction))
        return result
    
    def scale(self, mesh: trimesh.Trimesh, x: float, y: float, z: float) -> trimesh.Trimesh:
        """
        Atom: Scale mesh dimensions
        
        Args:
            mesh: Mesh to scale
            x, y, z: Scale factors for each axis
            
        Returns:
            Scaled mesh (new copy)
        """
        result = mesh.copy()
        result.apply_scale([x, y, z])
        return result
    
    def smooth(self, mesh: trimesh.Trimesh, iterations: int = 1) -> trimesh.Trimesh:
        """
        Atom: Smooth mesh surface (Laplacian smoothing)
        
        Args:
            mesh: Mesh to smooth
            iterations: Number of smoothing iterations
            
        Returns:
            Smoothed mesh (new copy)
        """
        result = mesh.copy()
        # Use trimesh's Laplacian smoothing filter
        try:
            import trimesh.smoothing
            trimesh.smoothing.filter_laplacian(result, iterations=iterations)
        except Exception as e:
            print(f"   ⚠️ Smoothing failed: {e}, returning original mesh")
        return result
    
    def chamfer_edges(self, mesh: trimesh.Trimesh, distance: float) -> trimesh.Trimesh:
        """
        Atom: Chamfer (bevel) sharp edges
        
        Args:
            mesh: Mesh to chamfer
            distance: Chamfer distance in millimeters
            
        Returns:
            Chamfered mesh (new copy)
        """
        # Note: trimesh doesn't have built-in chamfer, this is a placeholder
        # In production, you'd use a proper chamfer algorithm
        result = mesh.copy()
        # For now, return original (would need external library for real chamfer)
        return result
    
    def get_available_operations(self) -> List[str]:
        """Return list of all available atomic operation names"""
        return [
            "create_cube",
            "create_box",
            "create_cylinder",
            "create_sphere",
            "boolean_union",
            "boolean_subtract",
            "boolean_intersect",
            "translate",
            "rotate",
            "scale",
            "smooth",
            "chamfer_edges"
        ]

