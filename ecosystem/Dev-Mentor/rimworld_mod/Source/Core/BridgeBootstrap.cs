using System;
using System.Linq;
using HarmonyLib;
using Verse;

namespace TerminalKeeper.EventBridge;

[StaticConstructorOnStartup]
internal static class BridgeBootstrap
{
    private const string ModId = "com.devmentor.terminalkeeper.eventbridge";

    static BridgeBootstrap()
    {
        BridgeSettings.Load();

        var harmony = new Harmony(ModId);
        harmony.PatchAll();

        Log.Message($"[TKEB] Loaded. Endpoint={BridgeSettings.ServerBaseUrl}");

        if (BridgeSettings.EnableBootstrapEvent)
        {
            var activeMods = LoadedModManager.RunningModsListForReading
                .Select(mod => mod.PackageIdPlayerFacing)
                .Where(id => !string.IsNullOrWhiteSpace(id))
                .ToList();
            var activeModsJoined = BridgeJson.Escape(string.Join(",", activeMods));

            EventDispatcher.QueueEvent(
                "bootstrap",
                $"{{\"source\":\"BridgeBootstrap\",\"activeModCount\":\"{activeMods.Count}\",\"activeMods\":\"{activeModsJoined}\"}}");
        }
    }
}
