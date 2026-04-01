using System;
using System.IO;
using System.Linq;
using System.Xml;
using Verse;

namespace TerminalKeeper.EventBridge;

internal static class BridgeSettings
{
    public static string ServerBaseUrl { get; private set; } = "http://127.0.0.1:9000";
    public static int EventFlushIntervalTicks { get; private set; } = 90;
    public static int CommandPollIntervalTicks { get; private set; } = 180;
    public static bool EnableBootstrapEvent { get; private set; } = true;
    private const string PackageId = "com.devmentor.terminalkeeper.eventbridge";

    public static void Load()
    {
        var path = Path.Combine(ResolveModRoot(), "Config", "BridgeSettings.xml");

        if (!File.Exists(path))
        {
            Log.Warning($"[TKEB] Settings file not found at {path}. Using defaults.");
            return;
        }

        try
        {
            var doc = new XmlDocument();
            doc.Load(path);
            var root = doc.DocumentElement;
            if (root == null)
            {
                return;
            }

            ServerBaseUrl = Read(root, "ServerBaseUrl", ServerBaseUrl);
            EventFlushIntervalTicks = ParseInt(Read(root, "EventFlushIntervalTicks", "90"), 90);
            CommandPollIntervalTicks = ParseInt(Read(root, "CommandPollIntervalTicks", "180"), 180);
            EnableBootstrapEvent = ParseBool(Read(root, "EnableBootstrapEvent", "true"), true);
        }
        catch (Exception ex)
        {
            Log.Error($"[TKEB] Failed to load settings: {ex}");
        }
    }

    private static string ResolveModRoot()
    {
        try
        {
            var assemblyPath = typeof(BridgeSettings).Assembly.Location;
            if (!string.IsNullOrWhiteSpace(assemblyPath))
            {
                var assembliesDir = Path.GetDirectoryName(assemblyPath);
                if (!string.IsNullOrWhiteSpace(assembliesDir))
                {
                    var candidate = Path.GetFullPath(Path.Combine(assembliesDir, ".."));
                    if (Directory.Exists(candidate) && File.Exists(Path.Combine(candidate, "About", "About.xml")))
                    {
                        return candidate;
                    }
                }
            }
        }
        catch
        {
        }

        try
        {
            var matchingMod = LoadedModManager.RunningModsListForReading.FirstOrDefault(mod =>
                string.Equals(mod.PackageIdPlayerFacing, PackageId, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(mod.PackageId, PackageId, StringComparison.OrdinalIgnoreCase));
            if (matchingMod != null && !string.IsNullOrWhiteSpace(matchingMod.RootDir))
            {
                return matchingMod.RootDir;
            }
        }
        catch
        {
        }

        return ".";
    }

    private static string Read(XmlElement root, string key, string fallback)
    {
        var node = root.SelectSingleNode(key);
        return string.IsNullOrWhiteSpace(node?.InnerText) ? fallback : node.InnerText.Trim();
    }

    private static int ParseInt(string value, int fallback)
    {
        return int.TryParse(value, out var parsed) ? parsed : fallback;
    }

    private static bool ParseBool(string value, bool fallback)
    {
        return bool.TryParse(value, out var parsed) ? parsed : fallback;
    }
}
