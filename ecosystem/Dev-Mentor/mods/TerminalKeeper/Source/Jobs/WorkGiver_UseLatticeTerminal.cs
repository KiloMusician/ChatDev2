using RimWorld;
using Verse;
using Verse.AI;

namespace TerminalKeeper
{
    /// <summary>
    /// Tells colonists assigned to "Lattice Work" to autonomously seek out
    /// available Lattice Terminals and queue a session job.
    /// </summary>
    public class WorkGiver_UseLatticeTerminal : WorkGiver_Scanner
    {
        public override ThingRequest PotentialWorkThingRequest =>
            ThingRequest.ForGroup(ThingRequestGroup.BuildingArtificial);

        public override PathEndMode PathEndMode => PathEndMode.InteractionCell;

        public override bool HasJobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            if (t is not Building_LatticeTerminal terminal) return false;
            if (!terminal.IsActive) return false;

            // Check skill requirement
            var props = terminal.TerminalProps;
            if (props != null)
            {
                var skillDef = DefDatabase<SkillDef>.GetNamedSilentFail(props.requiredSkill);
                if (skillDef != null &&
                    (pawn.skills?.GetSkill(skillDef)?.Level ?? 0) < props.requiredSkillLevel)
                    return false;
            }

            if (!pawn.CanReserveAndReach(t, PathEndMode.InteractionCell, Danger.None)) return false;

            return true;
        }

        public override Job? JobOnThing(Pawn pawn, Thing t, bool forced = false)
        {
            return JobMaker.MakeJob(
                DefDatabase<JobDef>.GetNamedSilentFail("TK_UseLatticeTerminal") ?? JobDefOf.Goto,
                t);
        }
    }
}
