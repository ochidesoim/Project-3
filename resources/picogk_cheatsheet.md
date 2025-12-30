# PicoGK API Cheatsheet (Compressed)

## Core Imports
```python
import PicoGK as pk
```

## Essential Functions

### Initialization
```python
pk.Library.oViewer()  # Initialize PicoGK library
```

### Voxel Creation
```python
vox = pk.Voxels()  # Create empty voxel field
```

### Lattice Generation
```python
lat = pk.Lattice()  # Create lattice structure
lat.AddSphere(pk.Vector3(x, y, z), radius, thickness)
lat.AddBeam(pk.Vector3(x1,y1,z1), pk.Vector3(x2,y2,z2), radius, thickness, rounded=True)
vox = pk.Voxels(lat)  # Convert lattice to voxels
```

### Boolean Operations
```python
vox_result = pk.Voxels.voxBoolAdd(vox1, vox2)      # Union
vox_result = pk.Voxels.voxBoolSubtract(vox1, vox2) # Subtraction
vox_result = pk.Voxels.voxBoolIntersect(vox1, vox2) # Intersection
```

### Mesh Conversion
```python
mesh = pk.Mesh(voxels)  # Marching Cubes: Voxels -> Mesh
```

### File I/O
```python
pk.Mesh.mshFromStlFile("path/to/file.stl")  # Load STL
mesh.SaveToStlFile("output.stl")             # Save STL
```

### Geometry Primitives
```python
# Sphere (via lattice)
lat = pk.Lattice()
lat.AddSphere(pk.Vector3(0, 0, 0), radius, thickness)

# Cylinder (via beam)
lat.AddBeam(pk.Vector3(0, 0, 0), pk.Vector3(0, 0, height), radius, thickness)
```

### Gyroid Lattice
```python
# Gyroid is typically generated via implicit functions
# PicoGK uses signed distance fields (SDF)
# Example pattern (pseudo-code, verify with actual PicoGK docs):
# vox = pk.Voxels.voxFromImplicit(lambda x,y,z: gyroid_sdf(x,y,z, period), bounds)
```

## Critical Notes
- **Vector3**: All coordinates use `pk.Vector3(x, y, z)`
- **Units**: PicoGK uses millimeters by default
- **Voxel Size**: Set via `pk.Library.fVoxelSizeMM` (global setting)
- **Memory**: Large voxel grids (small voxel size) consume significant RAM

## Common Patterns

### Create Hollow Shell
```python
outer = pk.Voxels(outer_lattice)
inner = pk.Voxels(inner_lattice)
shell = pk.Voxels.voxBoolSubtract(outer, inner)
```

### Export Workflow
```python
pk.Library.oViewer()  # Init
# ... create voxels ...
mesh = pk.Mesh(voxels)
mesh.SaveToStlFile("output/result.stl")
```

## Windows-Specific
- Ensure PicoGK DLLs are in PATH or same directory
- Use `pathlib.Path` for file paths to handle backslashes
