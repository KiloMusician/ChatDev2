using System.Collections.Generic;
using System.Reflection;
using System.Linq;
using HarmonyLib;
using Verse;

namespace TerminalKeeper.EventBridge;

[HarmonyPatch]
internal static class PawnDeathPatches
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        return typeof(Pawn)
            .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
            .Where(method => method.Name == "Kill");
    }

    internal static void Postfix(Pawn __instance)
    {
        if (__instance == null || !__instance.Dead)
        {
            return;
        }

        EventDispatcher.QueueEvent(
            "pawn_death",
            $"{{\"pawn\":\"{BridgeJson.Escape(__instance.LabelShortCap)}\",\"kind\":\"{BridgeJson.Escape(__instance.kindDef?.defName)}\",\"map\":\"{BridgeJson.Escape(__instance.Map?.ToString() ?? "world")}\"}}");
    }
}
