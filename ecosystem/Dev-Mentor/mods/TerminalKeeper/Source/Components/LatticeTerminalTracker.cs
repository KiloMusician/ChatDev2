using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Helper to find the nearest active Lattice Terminal or Console for a pawn.
    /// </summary>
    public static class LatticeTerminalTracker
    {
        private const float MaxRange = 6f;

        public static Building_LatticeTerminal? FindNearbyTerminal(Pawn pawn)
        {
            if (pawn.Map == null) return null;

            Building_LatticeTerminal? best = null;
            float bestDist = float.MaxValue;

            foreach (var b in pawn.Map.listerBuildings.allBuildingsColonist)
            {
                if (b is not Building_LatticeTerminal t) continue;
                if (!t.IsActive) continue;
                float d = pawn.Position.DistanceTo(b.Position);
                if (d <= MaxRange && d < bestDist) { best = t; bestDist = d; }
            }

            return best;
        }
    }
}
