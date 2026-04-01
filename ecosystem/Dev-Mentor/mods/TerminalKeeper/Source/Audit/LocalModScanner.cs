using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Xml;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Reads RimWorld's active mod list and harvests About.xml metadata for
    /// every installed mod so the audit payload is as rich as possible.
    ///
    /// Does not touch the network — pure local filesystem reads.
    /// </summary>
    public static class LocalModScanner
    {
        // ─── Public API ───────────────────────────────────────────────────────

        /// <summary>
        /// Build the audit payload from the current game state.
        /// Call this after StaticConstructorOnStartup so ModLister is populated.
        /// </summary>
        public static ModAuditPayload BuildPayload()
        {
            var payload = new ModAuditPayload();

            var runningList = LoadedModManager.RunningMods.ToList();
            var activeMods = ModLister.AllInstalledMods
                .Where(m => m.Active)
                .OrderBy(m => runningList.IndexOf(
                    runningList.FirstOrDefault(r => r.PackageId == m.PackageIdPlayerFacing)
                ))
                .ToList();

            foreach (var meta in activeMods)
            {
                string pid = meta.PackageIdPlayerFacing?.ToLowerInvariant() ?? "";
                if (string.IsNullOrWhiteSpace(pid)) continue;

                payload.ModIds.Add(pid);

                string aboutPath = Path.Combine(meta.RootDir.FullName, "About", "About.xml");
                if (File.Exists(aboutPath))
                {
                    try
                    {
                        payload.AboutXmls[pid] = File.ReadAllText(aboutPath);
                    }
                    catch (Exception ex)
                    {
                        TKLog.Warning($"[ModAudit] Could not read About.xml for {pid}: {ex.Message}");
                    }
                }
            }

            TKLog.Info($"[ModAudit] Payload built: {payload.ModIds.Count} mods, "
                       + $"{payload.AboutXmls.Count} About.xml files harvested.");
            return payload;
        }

        // ─── Helpers ──────────────────────────────────────────────────────────

        /// <summary>
        /// Parse a single About.xml text and return a flat dict of metadata.
        /// Used for display in Dialog_ModAudit without a round-trip to the server.
        /// </summary>
        public static Dictionary<string, string> ParseAboutXml(string xmlText)
        {
            var result = new Dictionary<string, string>();
            try
            {
                var doc = new XmlDocument();
                doc.LoadXml(xmlText);
                var root = doc.DocumentElement;
                if (root == null) return result;

                result["packageId"]   = NodeText(root, "packageId");
                result["name"]        = NodeText(root, "name");
                result["author"]      = NodeText(root, "author");
                result["url"]         = NodeText(root, "url");
                var desc = NodeText(root, "description");
                result["description"] = desc.Length > 200
                    ? desc.Substring(0, 200) + "…"
                    : desc;
            }
            catch (Exception ex)
            {
                TKLog.Warning($"[ModAudit] XML parse error: {ex.Message}");
            }
            return result;
        }

        private static string NodeText(XmlElement root, string tag)
        {
            var node = root.SelectSingleNode(tag);
            return node?.InnerText?.Trim() ?? "";
        }
    }
}
