using System.IO;
using System.Linq;
using System.Xml;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Loads Config/TerminalKeeperSettings.xml at startup.
    /// Falls back to sane defaults if the file is missing or malformed.
    /// </summary>
    public static class TKSettings
    {
        public static string ApiEndpoint    { get; private set; } = "http://localhost:5000";
        public static string OllamaEndpoint { get; private set; } = "http://localhost:11434";
        public static string LMStudioEndpoint { get; private set; } = "http://localhost:1234";
        public static string LLMBackend     { get; private set; } = "terminal_depths";
        public static string DefaultModel   { get; private set; } = "llama3.2-3b";
        public static int    UpdateInterval { get; private set; } = 300;
        public static int    ConvProximity  { get; private set; } = 3;
        public static int    ConvCooldown   { get; private set; } = 3600;
        public static bool   AICouncil      { get; private set; } = true;
        public static bool   Blueprints     { get; private set; } = true;
        public static string LogLevel       { get; private set; } = "Info";
        public static string ApiToken       { get; private set; } = "";

        public static void Load()
        {
            string path = Path.Combine(
                LoadedModManager.RunningModsListForReading
                    .FirstOrDefault(m => m.assemblies?.loadedAssemblies
                        ?.Contains(typeof(TKSettings).Assembly) ?? false)
                    ?.RootDir ?? ".",
                "Config",
                "TerminalKeeperSettings.xml");

            if (!File.Exists(path))
            {
                TKLog.Warning($"Settings file not found at {path}. Using defaults.");
                return;
            }

            try
            {
                var doc = new XmlDocument();
                doc.Load(path);
                var root = doc.DocumentElement!;

                ApiEndpoint      = Read(root, "ApiEndpoint",              ApiEndpoint);
                OllamaEndpoint   = Read(root, "OllamaEndpoint",           OllamaEndpoint);
                LMStudioEndpoint = Read(root, "LMStudioEndpoint",         LMStudioEndpoint);
                LLMBackend       = Read(root, "LLMBackend",               LLMBackend);
                DefaultModel     = Read(root, "DefaultModel",             DefaultModel);
                UpdateInterval   = int.Parse(Read(root, "ColonistUpdateIntervalTicks", "300"));
                ConvProximity    = int.Parse(Read(root, "ConversationProximityTiles",  "3"));
                ConvCooldown     = int.Parse(Read(root, "ConversationCooldownTicks",   "3600"));
                AICouncil        = bool.Parse(Read(root, "EnableAICouncil",           "true"));
                Blueprints       = bool.Parse(Read(root, "EnableBlueprintGeneration", "true"));
                LogLevel         = Read(root, "LogLevel",                 LogLevel);
                ApiToken         = Read(root, "ApiToken",                 "");

                TKLog.Info($"Settings loaded from {path}");
            }
            catch (System.Exception ex)
            {
                TKLog.Error($"Failed to load settings: {ex.Message}. Using defaults.");
            }
        }

        private static string Read(XmlElement root, string key, string fallback)
        {
            var node = root.SelectSingleNode(key);
            return node?.InnerText?.Trim() is { Length: > 0 } v ? v : fallback;
        }
    }
}
