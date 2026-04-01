using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using RimWorld;

namespace TerminalKeeper.EventBridge;

[HarmonyPatch]
internal static class IncidentPatches
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return typeof(IncidentWorker)
            .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            .Where(method => method.Name == "TryExecute");
    }

    internal static void Postfix(IncidentWorker __instance, bool __result)
    {
        if (!__result)
        {
            return;
        }

        EventDispatcher.QueueEvent(
            "incident_fired",
            $"{{\"incident\":\"{BridgeJson.Escape(__instance.def?.defName)}\",\"worker\":\"{BridgeJson.Escape(__instance.GetType().FullName)}\"}}");
    }
}
