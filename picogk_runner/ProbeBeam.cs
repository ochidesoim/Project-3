using System;
using PicoGK;
using System.Numerics;

class ProbeBeam
{
    public static void Run()
    {
        Console.WriteLine("Probing AddBeam...");
        Lattice lat = new Lattice();
        // Try simple beam
        lat.AddBeam(new Vector3(0,0,0), new Vector3(0,0,10), 5.0f, 5.0f);
        
        Voxels v = new Voxels(lat);
        Console.WriteLine("Beam Created Successfully.");
    }
}
