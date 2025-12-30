# Noyron Unity Bridge

This folder contains the assets needed to turn Unity into a "Cinematic Physics Renderer" for Noyron.

## Project Setup

1.  **Install Unity** (Unity 6 or 2022+ recommended).
2.  **Create a New Project** (3D URP or HDRP template for best visuals).
3.  **Install an STL Importer**:
    *   Unity does not load STL files at runtime by default.
    *   **Recommendation**: [Runtime OBJ Importer](https://github.com/Dummiesman/RuntimeOBJImporter) (Best for OBJ) or search "Runtime STL Loader" on GitHub/Asset Store.
    *   *Note*: If you use an OBJ loader, we might need to update Noyron to export `.obj` instead of `.stl`.

## Installation

1.  Copy `NoyronBridge.cs` into your Unity project's `Assets/Scripts` folder.
2.  Create an **Empty GameObject** in your scene (name it "NoyronHost").
3.  Attach the `NoyronBridge` script to it.
4.  **Important**: Open the script and check the `ImportMesh` function. You will need to uncomment/hook up the specific line of code for the Importer library you installed (e.g., `new OBJLoader().Load(path)`).

## Visuals (Hyper-Realism)

1.  Create a new Material (Right-click -> Create -> Material).
2.  Set it to "Autodesk Interactive" or "Standard".
3.  **Metallic**: 1.0
4.  **Smoothness**: 0.7 - 0.9
5.  Assign this material to the `Target Material` slot on the `NoyronBridge` component in the Inspector.

## Physics

The script automatically adds a `MeshCollider` and `Rigidbody` (Mass 1000kg) to generated objects, so they will fall, collide, and interact with the world physics!
