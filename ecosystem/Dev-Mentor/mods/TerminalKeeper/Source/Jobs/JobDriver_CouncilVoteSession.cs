using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace TerminalKeeper
{
    public class JobDriver_CouncilVoteSession : JobDriver
    {
        private Building_LatticeTerminal Terminal =>
            (Building_LatticeTerminal)job.GetTarget(TargetIndex.A).Thing;

        public override bool TryMakePreToilReservations(bool errorOnFailed) =>
            pawn.Reserve(job.GetTarget(TargetIndex.A), job, 1, -1, null, errorOnFailed);

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDespawnedNullOrForbidden(TargetIndex.A);

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.InteractionCell);

            var vote = new Toil
            {
                defaultCompleteMode = ToilCompleteMode.Delay,
                defaultDuration     = 2400,
            };
            vote.AddFinishAction(() =>
            {
                var agentId = LatticeAgentManager.Instance?.GetOrCreateAgentId(pawn) ?? "rw_unknown";
                TerminalDepthsClient.SendCommand(agentId, "council vote",
                    onSuccess: resp =>
                    {
                        string decision = (string?)(resp?.Output) ?? "No decision returned.";
                        Messages.Message(
                            "TK_Message_CouncilDecision".Translate(decision.Truncate(150)),
                            MessageTypeDefOf.NeutralEvent, false);
                    },
                    onError: e => TKLog.Warning($"Council vote failed: {e}"));
            });
            yield return vote;
        }
    }
}
