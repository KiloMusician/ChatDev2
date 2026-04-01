using Verse;

namespace TerminalKeeper
{
    /// <summary>ThingComp that carries per-tier Lattice Terminal config.</summary>
    public class CompLatticeTerminal : ThingComp
    {
        public CompProperties_LatticeTerminal Props =>
            (CompProperties_LatticeTerminal)props;
    }

    public class CompProperties_LatticeTerminal : CompProperties
    {
        public int    tier                  = 1;
        public string requiredSkill         = "Intellectual";
        public int    requiredSkillLevel    = 4;
        public int    xpGranted             = 25;
        public string apiRoute              = "/api/game/command";
        public bool   enableCouncilVoting   = false;
        public bool   enableBlueprintDownload = false;

        public CompProperties_LatticeTerminal() => compClass = typeof(CompLatticeTerminal);
    }

    /// <summary>ThingComp for the Lattice Nexus.</summary>
    public class CompLatticeNexus : ThingComp
    {
        public CompProperties_LatticeNexus Props =>
            (CompProperties_LatticeNexus)props;
    }

    public class CompProperties_LatticeNexus : CompProperties
    {
        public float influenceRadius       = 15f;
        public int   broadcastIntervalTicks = 600;

        public float InfluenceRadius         => influenceRadius;
        public int   BroadcastIntervalTicks  => broadcastIntervalTicks;

        public CompProperties_LatticeNexus() => compClass = typeof(CompLatticeNexus);
    }
}
