using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;

namespace TerminalKeeper.EventBridge;

[HarmonyPatch]
internal static class CaravanPatches
{
    internal static IEnumerable<MethodBase> TargetMethods()
    {
        var caravanMakerType = AccessTools.TypeByName("RimWorld.Planet.CaravanMaker");
        if (caravanMakerType == null)
        {
            return Enumerable.Empty<MethodBase>();
        }

        return caravanMakerType
            .GetMethods(BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic)
            .Where(method => method.Name == "MakeCaravan");
    }

    internal static void Postfix()
    {
        EventDispatcher.QueueEvent(
            "caravan_created",
            "{\"source\":\"RimWorld.Planet.CaravanMaker.MakeCaravan\"}");
    }
}
