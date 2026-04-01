using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;

namespace TerminalKeeper.EventBridge;

[HarmonyPatch]
internal static class TradePatches
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        var tradeSessionType = AccessTools.TypeByName("RimWorld.TradeSession");
        if (tradeSessionType == null)
        {
            return Enumerable.Empty<MethodBase>();
        }

        return tradeSessionType
            .GetMethods(BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
            .Where(method => method.Name == "SetupWith");
    }

    internal static void Postfix()
    {
        EventDispatcher.QueueEvent(
            "trade_session_started",
            "{\"source\":\"RimWorld.TradeSession.SetupWith\"}");
    }
}
