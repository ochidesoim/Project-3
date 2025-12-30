using UnityEngine;
using System.IO;
using System.Collections;

// INSTRUCTIONS:
// 1. Install a Runtime STL Importer (search "Runtime OBJ Importer" or "TriLib" or "StlLoader" in Unity Asset Store/GitHub).
//    For example: https://github.com/Dummiesman/RuntimeOBJImporter (Supports OBJ)
//    Or a simple STL loader script.
//
// 2. Attach this script to an empty GameObject in your scene.
// 3. Assign your "Sleek Metal" material to the 'targetMaterial' slot in the Inspector.

public class NoyronBridge : MonoBehaviour
{
    [Header("Configuration")]
    // Adjust this path to point to your d:\Project 3\picogk_runner\render.stl
    // Note: Use forward slashes in Unity Inspector or rely on this default.
    public string modelPath = @"D:\Project 3\picogk_runner\render.stl";
    
    public Material targetMaterial;
    public bool addPhysics = true;
    public float scaleFactor = 0.1f; // Adjust depending on unit mismatch (mm vs m)

    private FileSystemWatcher watcher;
    private bool needsUpdate = false;

    void Start()
    {
        SetupWatcher();
        // Initial load
        if (File.Exists(modelPath))
        {
            LoadModel();
        }
    }

    void SetupWatcher()
    {
        string dir = Path.GetDirectoryName(modelPath);
        string file = Path.GetFileName(modelPath);

        if (!Directory.Exists(dir))
        {
            Debug.LogError($"[Noyron] Directory not found: {dir}");
            return;
        }

        watcher = new FileSystemWatcher(dir);
        watcher.Filter = file;
        watcher.NotifyFilter = NotifyFilters.LastWrite;
        watcher.Changed += (s, e) => needsUpdate = true;
        watcher.EnableRaisingEvents = true;

        Debug.Log($"[Noyron] Watching for {file} in {dir}...");
    }

    void Update()
    {
        if (needsUpdate)
        {
            needsUpdate = false;
            // Delay slightly to ensure write is finished? 
            StartCoroutine(LoadAfterDelay(0.5f));
        }
    }

    IEnumerator LoadAfterDelay(float delay)
    {
        yield return new WaitForSeconds(delay);
        LoadModel();
    }

    void LoadModel()
    {
        Debug.Log("[Noyron] Hot-Loading Geometry...");

        // 1. Destroy old children
        foreach (Transform child in transform) Destroy(child.gameObject);

        // 2. Load Mesh
        // NOTE: This part depends on which Importer you use.
        // Option A: If you have a LoadSTL function:
        GameObject loadedObject = ImportMesh(modelPath);
        
        if (loadedObject != null)
        {
            loadedObject.transform.SetParent(transform, false);
            loadedObject.transform.localScale = Vector3.one * scaleFactor;
            loadedObject.transform.localRotation = Quaternion.Euler(-90, 0, 0); // PicoGK Z-up vs Unity Y-up correction

            // 3. Apply Material
            if (targetMaterial != null)
            {
                var renderers = loadedObject.GetComponentsInChildren<Renderer>();
                foreach (var r in renderers) r.material = targetMaterial;
            }

            // 4. Add Physics
            if (addPhysics)
            {
                var meshFilter = loadedObject.GetComponentInChildren<MeshFilter>();
                if (meshFilter != null)
                {
                    var mc = loadedObject.AddComponent<MeshCollider>();
                    mc.sharedMesh = meshFilter.sharedMesh;
                    mc.convex = true; // Required for Rigidbody
                    
                    var rb = loadedObject.AddComponent<Rigidbody>();
                    rb.mass = 1000; // Heavy metal
                }
            }
        }
    }

    // PLUG YOUR IMPORTER HERE
    GameObject ImportMesh(string path)
    {
        // Example logic using Dummiesman OBJ Loader (renamed for STL conceptual usage)
        // Or generic mesh importer.
        // For STL specifically, you need a parsing library.
        // See README.md in the bridge folder for suggestions.
        
        // Pseudo-code placeholder:
        // return STLImporter.Load(path);
        
        Debug.LogWarning("ImportMesh needs a library! See script comments.");
        return null; 
    }
}
