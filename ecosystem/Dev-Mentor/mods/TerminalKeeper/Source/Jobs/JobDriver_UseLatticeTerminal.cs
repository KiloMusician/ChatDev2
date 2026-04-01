using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;
using Verse.AI;

namespace TerminalKeeper
{
    /// <summary>
    /// Drives a colonist to walk to a Lattice Terminal and perform a session.
    /// Duration scales with Intellectual skill (more skilled → shorter session).
    /// </summary>
    public class JobDriver_UseLatticeTerminal : JobDriver
    {
        private Building_LatticeTerminal Terminal =>
            (Building_LatticeTerminal)job.GetTarget(TargetIndex.A).Thing;

        public override bool TryMakePreToilReservations(bool errorOnFailed) =>
            pawn.Reserve(job.GetTarget(TargetIndex.A), job, 1, -1, null, errorOnFailed);

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDespawnedNullOrForbidden(TargetIndex.A);
            this.FailOnBurningImmobile(TargetIndex.A);

            // Walk to terminal
            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.InteractionCell);

            // Work at terminal
            var session = new Toil
            {
                defaultCompleteMode = ToilCompleteMode.Delay,
                defaultDuration  = SessionDuration(),
                handlingFacing   = true,
            };
            session.AddPreInitAction(() =>
            {
                pawn.rotationTracker?.FaceTarget(Terminal);
            });
            session.tickAction = () =>
            {
                pawn.skills?.Learn(SkillDefOf.Intellectual, 0.12f);
                PawnUtility.GainComfortFromCellIfPossible(pawn, 1, false);
            };
            session.AddFinishAction(() =>
            {
                int xp = Terminal.TerminalProps?.xpGranted ?? 25;
                LatticeAgentManager.OnLatticeSession(pawn, "polyglot run python", xp);
                pawn.needs?.mood?.thoughts?.memories?.TryGainMemory(
                    DefDatabase<ThoughtDef>.GetNamedSilentFail("TK_CompletedLatticeTask"));
            });
            yield return session;
        }

        private int SessionDuration()
        {
            int skill = pawn.skills?.GetSkill(SkillDefOf.Intellectual)?.Level ?? 5;
            // 600–3000 ticks (10s–50s) depending on skill
            return GenMath.RoundRandom(Mathf.Lerp(3000f, 600f, skill / 20f));
        }
    }
}
