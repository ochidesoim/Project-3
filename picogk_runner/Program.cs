using PicoGK;
using System.Numerics;
using System.Text.Json;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System;
using System.Text.Json.Serialization;

class Program
{
    static Dictionary<string, Voxels> _voxels = new();

    public static void Main(string[] args)
    {
        try 
        {
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;

            string jsonPath = "recipe.json";
            if (args.Length > 0) jsonPath = args[0];

            if (!File.Exists(jsonPath)) {
                Console.WriteLine("❌ Waiting for recipe.json...");
                return;
            }

            Console.WriteLine($"🔍 Reading Recipe from: {Path.GetFullPath(jsonPath)}");
            string rawJson = File.ReadAllText(jsonPath);
            Console.WriteLine($"📄 Raw Content ({rawJson.Length} bytes): {rawJson}");
            
            var recipe = JsonSerializer.Deserialize<Recipe>(rawJson, new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            
            PicoGK.Library.Go(0.5f, () => ExecuteRecipe(recipe));
        }
        catch (Exception e) { Console.WriteLine($"💥 Critical Error: {e.Message}"); }
    }

    static void ExecuteRecipe(Recipe recipe)
    {
        Console.WriteLine($"--- 🏭 Processing {recipe.steps.Count} Steps (Mesh Optimized / Binary STL) ---");
        
        HashSet<string> hiddenIngredients = new HashSet<string>();

        foreach (var step in recipe.steps)
        {
            try 
            {
                Voxels? v = null;
                switch (step.op.ToLower())
                {
                    case "box":      v = MakeBox(step); break;
                    case "cylinder": v = MakeCylinder(step); break;
                    case "cone":     v = MakeCone(step); break; 
                    
                    case "union":    v = BoolOp(step, "union"); HideIngredients(step, hiddenIngredients); break;
                    case "subtract": v = BoolOp(step, "subtract"); HideIngredients(step, hiddenIngredients); break;
                }
                
                if (v != null) {
                    _voxels[step.id] = v;
                    Console.WriteLine($"   ✓ Built: {step.id} ({step.op})");
                }
            }
            catch (Exception ex) { Console.WriteLine($"   ❌ Failed Step '{step.id}': {ex.Message}"); }
        }

        Voxels? finalObject = null;
        foreach(var kvp in _voxels)
        {
            if (!hiddenIngredients.Contains(kvp.Key)) finalObject = kvp.Value;
        }
        
        if (finalObject != null)
        {
            try 
            {
                Mesh m = new Mesh(finalObject);
                string outPath = Path.Combine(Directory.GetCurrentDirectory(), "render.stl");
                m.SaveToStlFile(outPath);
                Console.WriteLine($"✅ Geometry saved to: {outPath}");
            }
            catch (Exception e) { Console.WriteLine($"❌ Failed to save STL: {e.Message}"); }
        }
        
        Environment.Exit(0);
    }

    // --- MESH BUILDERS ---

    static Voxels MakeBox(Step s)
    {
        float x = Get(s,"x"), y = Get(s,"y"), z = Get(s,"z");
        float dx = Get(s,"dx",10), dy = Get(s,"dy",10), h = Get(s,"height",10);
        string file = ProceduralMesh.CreateBox(new Vector3(x, y, z), new Vector3(dx, dy, h));
        return LoadVoxelsFromStl(file);
    }

    static Voxels MakeCylinder(Step s) {
        float x = Get(s,"x"), y = Get(s,"y"), z = Get(s,"z");
        float h = Get(s,"height", 10);
        float r = Get(s,"radius", 10);
        string file = ProceduralMesh.CreateCylinder(new Vector3(x, y, z), h, r);
        return LoadVoxelsFromStl(file);
    }

    static Voxels MakeCone(Step s)
    {
        float x = Get(s,"x"), y = Get(s,"y"), z = Get(s,"z");
        float h = Get(s,"height", 20);
        float rBottom = Get(s,"radius", 15);
        float rTop = Get(s,"radius_top", 0); 
        string file = ProceduralMesh.CreateCone(new Vector3(x, y, z), h, rBottom, rTop);
        return LoadVoxelsFromStl(file);
    }

    static Voxels LoadVoxelsFromStl(string path)
    {
        Mesh m = Mesh.mshFromStlFile(path); 
        return new Voxels(m);
    }

    // --- HELPERS ---

    static void HideIngredients(Step s, HashSet<string> hidden)
    {
        string t = GetString(s, "target");
        string tool = GetString(s, "tool");
        if(t != "") hidden.Add(t);
        if(tool != "") hidden.Add(tool);
    }

    static Voxels? BoolOp(Step s, string op) {
        string tID = GetString(s,"target");
        string toolID = GetString(s,"tool");
        if(!_voxels.ContainsKey(tID) || !_voxels.ContainsKey(toolID)) return null;
        var target = new Voxels(_voxels[tID]);
        var tool = _voxels[toolID];
        if (op == "union") target.BoolAdd(tool);
        if (op == "subtract") target.BoolSubtract(tool);
        return target;
    }

    static float Get(Step s, string k, float d=0) => s.@params != null && s.@params.ContainsKey(k) ? (float)s.@params[k].GetDouble() : d;
    static string GetString(Step s, string k) => s.@params != null && s.@params.ContainsKey(k) ? s.@params[k].GetString() : "";
}

// --- PROCEDURAL MESH GENERATOR (BINARY STL WRITER) ---

public static class ProceduralMesh
{
    private struct Triangle
    {
        public Vector3 n;
        public Vector3 v1, v2, v3;
        public Triangle(Vector3 a, Vector3 b, Vector3 c)
        {
            v1=a; v2=b; v3=c;
            n = Vector3.Normalize(Vector3.Cross(b-a, c-a));
            if(float.IsNaN(n.X)) n = Vector3.UnitZ;
        }
    }

    public static string CreateBox(Vector3 pos, Vector3 size)
    {
        List<Triangle> tris = new();
        float x1 = pos.X, x2 = pos.X + size.X;
        float y1 = pos.Y, y2 = pos.Y + size.Y;
        float z1 = pos.Z, z2 = pos.Z + size.Z;
        
        AddQuad(tris, new Vector3(x1,y1,z1), new Vector3(x2,y1,z1), new Vector3(x2,y2,z1), new Vector3(x1,y2,z1));
        AddQuad(tris, new Vector3(x1,y2,z2), new Vector3(x2,y2,z2), new Vector3(x2,y1,z2), new Vector3(x1,y1,z2));
        AddQuad(tris, new Vector3(x1,y1,z1), new Vector3(x2,y1,z1), new Vector3(x2,y1,z2), new Vector3(x1,y1,z2));
        AddQuad(tris, new Vector3(x2,y2,z1), new Vector3(x1,y2,z1), new Vector3(x1,y2,z2), new Vector3(x2,y2,z2));
        AddQuad(tris, new Vector3(x1,y2,z1), new Vector3(x1,y1,z1), new Vector3(x1,y1,z2), new Vector3(x1,y2,z2));
        AddQuad(tris, new Vector3(x2,y1,z1), new Vector3(x2,y2,z1), new Vector3(x2,y2,z2), new Vector3(x2,y1,z2));

        return WriteBinaryStl(tris);
    }

    public static string CreateCylinder(Vector3 c, float h, float r) => CreateCone(c, h, r, r);

    public static string CreateCone(Vector3 c, float h, float r1, float r2)
    {
        List<Triangle> tris = new();
        int segments = 64; 
        float angle = (float)(Math.PI * 2.0 / segments);
        for (int i = 0; i < segments; i++) {
            float a1 = i * angle, a2 = (i+1) * angle;
            float x1 = (float)Math.Cos(a1), y1 = (float)Math.Sin(a1);
            float x2 = (float)Math.Cos(a2), y2 = (float)Math.Sin(a2);
            Vector3 b1 = new Vector3(c.X + x1*r1, c.Y + y1*r1, c.Z);
            Vector3 b2 = new Vector3(c.X + x2*r1, c.Y + y2*r1, c.Z);
            Vector3 t1 = new Vector3(c.X + x1*r2, c.Y + y1*r2, c.Z+h);
            Vector3 t2 = new Vector3(c.X + x2*r2, c.Y + y2*r2, c.Z+h);
            AddQuad(tris, b2, b1, t1, t2);
            if(r1>0) tris.Add(new Triangle(new Vector3(c.X,c.Y,c.Z), b2, b1));
            if(r2>0) tris.Add(new Triangle(new Vector3(c.X,c.Y,c.Z+h), t1, t2));
        }
        return WriteBinaryStl(tris);
    }

    static void AddQuad(List<Triangle> tris, Vector3 p1, Vector3 p2, Vector3 p3, Vector3 p4)
    {
        tris.Add(new Triangle(p1, p2, p3));
        tris.Add(new Triangle(p1, p3, p4));
    }

    static string WriteBinaryStl(List<Triangle> tris)
    {
        string path = Path.GetTempFileName() + ".stl";
        using (var stream = new FileStream(path, FileMode.Create))
        using (var writer = new BinaryWriter(stream))
        {
            // 80 byte header
            writer.Write(new byte[80]);
            // Number of triangles (uint32)
            writer.Write((uint)tris.Count);
            
            foreach (var t in tris)
            {
                // Normal
                writer.Write(t.n.X); writer.Write(t.n.Y); writer.Write(t.n.Z);
                // V1
                writer.Write(t.v1.X); writer.Write(t.v1.Y); writer.Write(t.v1.Z);
                // V2
                writer.Write(t.v2.X); writer.Write(t.v2.Y); writer.Write(t.v2.Z);
                // V3
                writer.Write(t.v3.X); writer.Write(t.v3.Y); writer.Write(t.v3.Z);
                // Attribute (2 bytes)
                writer.Write((ushort)0);
            }
        }
        return path;
    }
}

public class Recipe { public List<Step> steps { get; set; } }
public class Step { public string id { get; set; } public string op { get; set; } [JsonPropertyName("params")] public Dictionary<string, JsonElement> @params { get; set; } }
