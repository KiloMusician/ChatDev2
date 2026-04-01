using HarmonyLib;
using RimWorld;
using Verse;
using Verse.AI;

namespace TerminalKeeper
{
    // ─── Pawn.Tick ────────────────────────────────────────────────────────────
    // After each pawn tick: refresh Lattice-linked hediff if inside Nexus range.
    [HarmonyPatch(typeof(Pawn), "Tick")]
    internal static class Patch_Pawn_Tick
    {
        private static int _tickCounter;

        internal static void Postfix(Pawn __instance)
        {
            if (__instance.IsHashIntervalTick(TKSettings.UpdateInterval))
                LatticeNexusTracker.RefreshPawnLink(__instance);
        }
    }

    // ─── Pawn.GetGizmos ──────────────────────────────────────────────────────
    // Inject "Access Lattice" gizmo when pawn is selected and a terminal is nearby.
    [HarmonyPatch(typeof(Pawn), nameof(Pawn.GetGizmos))]
    internal static class Patch_Pawn_GetGizmos
    {
        internal static System.Collections.Generic.IEnumerable<Gizmo> Postfix(
            System.Collections.Generic.IEnumerable<Gizmo> __result,
            Pawn __instance)
        {
            foreach (var g in __result) yield return g;

            if (!__instance.IsColonistPlayerControlled) yield break;
            if (LatticeTerminalTracker.FindNearbyTerminal(__instance) == null) yield break;

            yield return new Command_Action
            {
                defaultLabel = "TK_Gizmo_AccessTerminal".Translate(),
                defaultDesc  = "TK_Gizmo_AccessTerminal_Desc".Translate(),
                icon         = ContentFinder<UnityEngine.Texture2D>.Get("UI/Icons/LatticeTerminalGizmo", false),
                action       = () =>
                {
                    var terminal = LatticeTerminalTracker.FindNearbyTerminal(__instance);
                    if (terminal == null) return;
                    Find.WindowStack.Add(new Dialog_TerminalAccess(__instance, terminal));
                }
            };
        }
    }

    // ─── InteractionWorker_RomanceAttempt ─────────────────────────────────────
    // Intercept social interactions: if both pawns are Lattice-linked, occasionally
    // reroute the interaction through the Lattice conversation system.
    [HarmonyPatch(typeof(InteractionWorker_RomanceAttempt), nameof(InteractionWorker_RomanceAttempt.Interacted))]
    internal static class Patch_Interaction_Reroute
    {
        internal static void Postfix(Pawn initiator, Pawn recipient)
        {
            if (LatticeConversationSystem.BothLinked(initiator, recipient))
                LatticeConversationSystem.TryQueueLatticeConversation(initiator, recipient, "romance");
        }
    }

    // ─── Pawn_JobTracker.EndCurrentJob ───────────────────────────────────────
    // When a colonist finishes a job, push a brief state update to Terminal Depths.
    [HarmonyPatch(typeof(Pawn_JobTracker), nameof(Pawn_JobTracker.EndCurrentJob))]
    internal static class Patch_JobTracker_EndCurrentJob
    {
        internal static void Postfix(Pawn_JobTracker __instance, JobCondition condition)
        {
            var pawn = (Pawn?)typeof(Pawn_JobTracker)
                .GetField("pawn", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)
                ?.GetValue(__instance);
            if (pawn == null || !pawn.IsColonistPlayerControlled) return;
            if (condition != JobCondition.Succeeded) return;

            LatticeAgentManager.Instance?.OnJobComplete(pawn, __instance.curDriver?.job);
        }
    }
}
