---
description: How to use PicoGK for advanced voxel geometry in LumenOrb
---

# PicoGK Workflow for LumenOrb

PicoGK is now installed and working on your system. Use this workflow for advanced voxel operations.

## Quick Start

// turbo-all
1. Navigate to PicoGK_Examples:
   ```powershell
   cd "D:\Project 3\PicoGK_Examples"
   ```

2. Run PicoGK with the default example:
   ```powershell
   dotnet run
   ```

3. The PicoGK viewer window will open showing boolean operations demo.

## Creating Custom Geometry

### Step 1: Edit Program.cs

Open `D:\Project 3\PicoGK_Examples\Program.cs` and modify the task:

```csharp
using PicoGK;
using PicoGKExamples;

// Change the task to your custom geometry
Library.Go(0.5f, YourCustomTask.Task);
```

### Step 2: Create Your Task File

Create a new C# file (e.g., `MyGeometry.cs`) in the `01_GettingStarted` folder:

```csharp
using PicoGK;

namespace PicoGKExamples
{
    class MyGeometry
    {
        public static void Task()
        {
            // Create a cylinder
            Lattice lat = new();
            lat.AddBeam(
                new Vector3(0, 0, 0),
                new Vector3(0, 0, 100),  // 100mm height
                30,                       // 30mm radius
                30,
                true
            );
            
            Voxels vox = new(lat);
            Mesh mesh = new(vox);
            
            // Save to STL
            mesh.SaveToStlFile("D:\\Project 3\\output\\picogk_cylinder.stl");
            
            // Show in viewer
            Library.oViewer().Add(mesh);
        }
    }
}
```

### Step 3: Build and Run

```powershell
cd "D:\Project 3\PicoGK_Examples"
dotnet run
```

## Integration with LumenOrb

### Export from LumenOrb → Process in PicoGK

1. Use LumenOrb to generate initial geometry (trimesh-based)
2. Export STL from LumenOrb: `D:\Project 3\output\session_XXX\meshes\`
3. Import into PicoGK for advanced operations (gyroids, complex booleans)

### PicoGK Output → LumenOrb Visualization

1. Generate mesh in PicoGK
2. Save to: `D:\Project 3\output\picogk_output.stl`
3. In LumenOrb console: Load the mesh in PyVista viewport

## Available PicoGK Operations

| Operation | Method |
|-----------|--------|
| **Cylinder** | `lat.AddBeam(start, end, radius1, radius2, rounded)` |
| **Sphere** | `lat.AddSphere(center, radius, thickness)` |
| **Boolean Add** | `vox.BoolAdd(otherVox)` |
| **Boolean Subtract** | `vox.BoolSubtract(otherVox)` |
| **Convert to Mesh** | `new Mesh(voxels)` |
| **Save STL** | `mesh.SaveToStlFile(path)` |

## Gyroid Example (Advanced)

```csharp
using PicoGK;

class GyroidExample
{
    public static void Task()
    {
        // Use implicit functions for true gyroid
        // PicoGK supports custom implicit function evaluation
        
        Lattice lat = new();
        
        float period = 10f;  // mm
        float thickness = 1f;  // mm
        
        // Sample gyroid surface
        for (float z = 0; z < 50; z += period/4)
        {
            for (float y = 0; y < 50; y += period/4)
            {
                for (float x = 0; x < 50; x += period/4)
                {
                    float scale = 2f * MathF.PI / period;
                    float val = MathF.Sin(x*scale)*MathF.Cos(y*scale) +
                                MathF.Sin(y*scale)*MathF.Cos(z*scale) +
                                MathF.Sin(z*scale)*MathF.Cos(x*scale);
                    
                    if (MathF.Abs(val) < 0.3f)
                    {
                        lat.AddSphere(new Vector3(x, y, z), thickness, thickness);
                    }
                }
            }
        }
        
        Voxels vox = new(lat);
        Mesh mesh = new(vox);
        mesh.SaveToStlFile("D:\\Project 3\\output\\gyroid.stl");
        Library.oViewer().Add(mesh);
    }
}
```

## Path Reference

| Item | Path |
|------|------|
| PicoGK Project | `D:\Project 3\PicoGK_Examples\` |
| LumenOrb Output | `D:\Project 3\output\` |
| PicoGK Examples | `D:\Project 3\PicoGK_Examples\01_GettingStarted\` |

## Troubleshooting

- **Viewer doesn't open**: Make sure you're running from the correct directory
- **Build fails**: Run `dotnet restore` first
- **DLL errors**: Ensure Visual C++ Redistributables are installed
