using System.Collections.Generic;
using RimWorld;
using Verse;
using Verse.AI;

namespace TerminalKeeper
{
    public class JobDriver_DownloadBlueprint : JobDriver
    {
        private Building_LatticeTerminal Terminal =>
            (Building_LatticeTerminal)job.GetTarget(TargetIndex.A).Thing;

        public override bool TryMakePreToilReservations(bool errorOnFailed) =>
            pawn.Reserve(job.GetTarget(TargetIndex.A), job, 1, -1, null, errorOnFailed);

        protected override IEnumerable<Toil> MakeNewToils()
        {
            this.FailOnDespawnedNullOrForbidden(TargetIndex.A);

            yield return Toils_Goto.GotoThing(TargetIndex.A, PathEndMode.InteractionCell);

            var download = new Toil
            {
                defaultCompleteMode = ToilCompleteMode.Delay,
                defaultDuration     = 1200,
            };
            download.AddFinishAction(() =>
            {
                string context =
                    $"colony_wealth={pawn.Map?.wealthWatcher?.WealthTotal:F0} " +
                    $"colonists={pawn.Map?.mapPawns?.FreeColonistsCount}";

                TerminalDepthsClient.RequestBlueprint(context,
                    onSuccess: bp =>
                    {
                        if (bp == null) return;
                        Messages.Message(
                            "TK_Message_BlueprintReceived".Translate(bp.Name ?? "unnamed"),
                            MessageTypeDefOf.PositiveEvent, false);
                    },
                    onError: e => TKLog.Warning($"Blueprint download failed: {e}"));
            });
            yield return download;
        }
    }
}
