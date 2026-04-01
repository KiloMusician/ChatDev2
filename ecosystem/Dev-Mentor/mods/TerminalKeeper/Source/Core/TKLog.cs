using Verse;

namespace TerminalKeeper
{
    /// <summary>Thin wrapper around Verse.Log that prepends a mod tag.</summary>
    public static class TKLog
    {
        private const string Tag = "[TerminalKeeper]";

        public static void Info(string msg)    => Log.Message($"{Tag} {msg}");
        public static void Warning(string msg) => Log.Warning($"{Tag} {msg}");
        public static void Error(string msg)   => Log.Error($"{Tag} {msg}");

        public static void Debug(string msg)
        {
            if (TKSettings.LogLevel == "Debug")
                Log.Message($"{Tag} [DEBUG] {msg}");
        }
    }
}
