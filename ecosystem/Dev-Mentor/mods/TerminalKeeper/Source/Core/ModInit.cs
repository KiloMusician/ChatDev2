using HarmonyLib;
using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Mod entry point. Applies Harmony patches and initialises singletons.
    /// Loaded automatically by [StaticConstructorOnStartup].
    /// </summary>
    [StaticConstructorOnStartup]
    public static class ModInit
    {
        public static readonly string ModId = "com.devmentor.terminalkeeper";

        static ModInit()
        {
            TKLog.Info("Terminal Keeper initialising...");

            var harmony = new Harmony(ModId);
            harmony.PatchAll();

            TKSettings.Load();

            TKLog.Info($"Terminal Keeper ready | API={TKSettings.ApiEndpoint} backend={TKSettings.LLMBackend}");

            // Fire-and-forget startup mod audit — result is cached server-side
            // so Dialog_ModAudit can open instantly after game load.
            TerminalDepthsClient.SendModAudit(
                LocalModScanner.BuildPayload(),
                onSuccess: report =>
                {
                    if (report == null) return;
                    TKLog.Info(
                        $"[ModAudit] Startup audit complete: "
                        + $"{report.ModCount} mods | health={report.HealthScore}% | "
                        + $"conflicts={report.Conflicts?.Count ?? 0}");
                    if (report.HealthScore < 70)
                        Messages.Message(
                            $"[TerminalKeeper] Mod health {report.HealthScore}% — open Mod Audit for details.",
                            MessageTypeDefOf.CautionInput, false);
                },
                onError: err =>
                    TKLog.Warning($"[ModAudit] Startup audit failed (API offline?): {err}")
            );
        }
    }
}
