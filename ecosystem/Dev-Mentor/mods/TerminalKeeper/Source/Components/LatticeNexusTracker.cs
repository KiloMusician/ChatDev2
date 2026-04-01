using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Maintains the Lattice-linked hediff on all colonists within range of
    /// an active Lattice Nexus, and broadcasts telemetry when the Nexus ticks.
    /// </summary>
    public static class LatticeNexusTracker
    {
        private static readonly HediffDef? _linkedDef =
            DefDatabase<HediffDef>.GetNamedSilentFail("TK_LatticeLinkedHediff");

        public static void RefreshPawnLink(Pawn pawn)
        {
            if (!pawn.IsColonistPlayerControlled) return;
            if (pawn.Map == null) return;

            bool inRange = IsInsideNexusRange(pawn);

            if (inRange)
                GiveLatticeHediff(pawn);
            else
                RemoveLatticeHediff(pawn);
        }

        private static bool IsInsideNexusRange(Pawn pawn)
        {
            foreach (var building in pawn.Map.listerBuildings.allBuildingsColonist)
            {
                if (building is not Building_LatticeNexus nexus) continue;
                if (!nexus.IsActive) continue;
                if (pawn.Position.DistanceTo(building.Position) <= nexus.InfluenceRadius)
                    return true;
            }
            return false;
        }

        private static void GiveLatticeHediff(Pawn pawn)
        {
            if (_linkedDef == null) return;
            var existing = pawn.health?.hediffSet?.GetFirstHediffOfDef(_linkedDef);
            if (existing != null)
            {
                // Refresh / increase severity up to cap
                existing.Severity = Math.Min(existing.Severity + 0.01f, 1.0f);
                return;
            }
            var hediff = HediffMaker.MakeHediff(_linkedDef, pawn);
            hediff.Severity = 0.1f;
            pawn.health.AddHediff(hediff);
        }

        private static void RemoveLatticeHediff(Pawn pawn)
        {
            if (_linkedDef == null) return;
            var existing = pawn.health?.hediffSet?.GetFirstHediffOfDef(_linkedDef);
            if (existing == null) return;
            pawn.health.RemoveHediff(existing);

            // Give brief negative thought for loss of signal
            pawn.needs?.mood?.thoughts?.memories?.TryGainMemory(
                DefDatabase<ThoughtDef>.GetNamedSilentFail("TK_LatticeOffline"));
        }

        private static class Math
        {
            public static float Min(float a, float b) => a < b ? a : b;
        }
    }
}
