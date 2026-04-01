using System;
using System.Collections;
using System.Net;
using System.Text;
using Newtonsoft.Json;
using Verse;
using UnityEngine;

namespace TerminalKeeper
{
    /// <summary>
    /// Async HTTP client for the Terminal Depths REST API.
    /// All calls are fire-and-forget coroutines to avoid freezing the game.
    /// </summary>
    public static class TerminalDepthsClient
    {
        private static string Base => TKSettings.ApiEndpoint;
        private static string Token => TKSettings.ApiToken;

        // ─── Public surface ───────────────────────────────────────────────────

        /// <summary>Push a game command as a named agent pawn.</summary>
        public static void SendCommand(string agentId, string command,
                                       Action<CommandResponse?>? onSuccess = null,
                                       Action<string>? onError = null)
        {
            var body = JsonConvert.SerializeObject(new
            {
                agent_id = agentId,
                command,
                source   = "rimworld"
            });

            CoroutineHost.Start(Post("/api/game/command", body, raw =>
            {
                try
                {
                    var resp = JsonConvert.DeserializeObject<CommandResponse>(raw);
                    onSuccess?.Invoke(resp);
                }
                catch (Exception ex)
                {
                    TKLog.Error($"Deserialize error: {ex.Message}");
                    onError?.Invoke(ex.Message);
                }
            }, onError));
        }

        /// <summary>Register a colonist as a persistent Terminal Depths agent.</summary>
        public static void RegisterAgent(string agentId, string displayName,
                                         Action<string>? onSuccess = null,
                                         Action<string>? onError   = null)
        {
            var body = JsonConvert.SerializeObject(new
            {
                agent_id     = agentId,
                display_name = displayName,
                source       = "rimworld"
            });
            CoroutineHost.Start(Post("/api/agent/register", body, onSuccess, onError));
        }

        /// <summary>Fetch colony-wide analytics from Serena.</summary>
        public static void GetColonyAnalytics(Action<string>? onSuccess = null,
                                               Action<string>? onError   = null)
        {
            CoroutineHost.Start(Get("/api/serena/colony_analytics", onSuccess, onError));
        }

        /// <summary>Request a blueprint from the AI Council.</summary>
        public static void RequestBlueprint(string colonyContext,
                                             Action<BlueprintResponse?>? onSuccess = null,
                                             Action<string>? onError = null)
        {
            var body = JsonConvert.SerializeObject(new { context = colonyContext });
            CoroutineHost.Start(Post("/api/council/blueprint", body, raw =>
            {
                try
                {
                    var resp = JsonConvert.DeserializeObject<BlueprintResponse>(raw);
                    onSuccess?.Invoke(resp);
                }
                catch (Exception ex) { onError?.Invoke(ex.Message); }
            }, onError));
        }

        /// <summary>Push colonist state telemetry to NuSyQ-Hub via Terminal Depths.</summary>
        public static void PushColonistState(ColonistState state,
                                              Action<string>? onSuccess = null,
                                              Action<string>? onError   = null)
        {
            var body = JsonConvert.SerializeObject(state);
            CoroutineHost.Start(Post("/api/nusyq/colonist_state", body, onSuccess, onError));
        }

        /// <summary>
        /// Sync Terminal Depths cyberware installs to RimWorld HediffDefs.
        /// Call after any cyberware install/uninstall in the game terminal.
        /// </summary>
        public static void SyncCyberware(string agentId,
                                          string[] installed, string[] uninstalled,
                                          Action<string>? onSuccess = null,
                                          Action<string>? onError   = null)
        {
            var body = JsonConvert.SerializeObject(new
            {
                agent_id    = agentId,
                installed,
                uninstalled,
            });
            CoroutineHost.Start(Post("/api/nusyq/cyberware_sync", body, onSuccess, onError));
        }

        /// <summary>
        /// Poll for cascade incidents queued since a given Unix timestamp.
        /// The mod should spawn corresponding RimWorld incidents from the results.
        /// </summary>
        public static void GetCascadeIncidents(double since,
                                                Action<string>? onSuccess = null,
                                                Action<string>? onError   = null)
        {
            CoroutineHost.Start(Get($"/api/nusyq/cascade_incidents?since={since}", onSuccess, onError));
        }

        /// <summary>
        /// Push Terminal Depths skill XP to derive RimWorld skill levels.
        /// The backend maps TD skills to RimWorld SkillDef names and computes levels.
        /// </summary>
        public static void SyncXP(string agentId,
                                   System.Collections.Generic.Dictionary<string, int> skills,
                                   Action<string>? onSuccess = null,
                                   Action<string>? onError   = null)
        {
            var body = JsonConvert.SerializeObject(new { agent_id = agentId, skills });
            CoroutineHost.Start(Post("/api/nusyq/xp_sync", body, onSuccess, onError));
        }

        // ─── Mod Audit ────────────────────────────────────────────────────────

        /// <summary>
        /// POST the active mod list to /api/rimworld/mod_audit and return the
        /// full ModAuditReport.  Payload is built by LocalModScanner.BuildPayload().
        /// </summary>
        public static void SendModAudit(ModAuditPayload payload,
                                         Action<ModAuditReport?>? onSuccess = null,
                                         Action<string>? onError = null)
        {
            var body = JsonConvert.SerializeObject(new
            {
                mod_ids    = payload.ModIds,
                about_xmls = payload.AboutXmls,
            });
            CoroutineHost.Start(Post("/api/rimworld/mod_audit", body, raw =>
            {
                try
                {
                    var report = JsonConvert.DeserializeObject<ModAuditReport>(raw);
                    onSuccess?.Invoke(report);
                }
                catch (Exception ex)
                {
                    TKLog.Error($"[ModAudit] Deserialize error: {ex.Message}");
                    onError?.Invoke(ex.Message);
                }
            }, onError));
        }

        /// <summary>
        /// GET the cached mod audit from /api/rimworld/mod_audit without
        /// re-running the scan.  Useful for polling from the dialog after an
        /// initial SendModAudit() call.
        /// </summary>
        public static void FetchModAudit(Action<ModAuditReport?>? onSuccess = null,
                                          Action<string>? onError = null)
        {
            CoroutineHost.Start(Get("/api/rimworld/mod_audit", raw =>
            {
                try
                {
                    var report = JsonConvert.DeserializeObject<ModAuditReport>(raw);
                    onSuccess?.Invoke(report);
                }
                catch (Exception ex)
                {
                    TKLog.Error($"[ModAudit] Deserialize error: {ex.Message}");
                    onError?.Invoke(ex.Message);
                }
            }, onError));
        }

        // ─── Coroutine helpers ────────────────────────────────────────────────

        private static IEnumerator Get(string path,
                                        Action<string>? onSuccess,
                                        Action<string>? onError)
        {
            string url = Base + path;
            using var req = new UnityEngine.Networking.UnityWebRequest(url, "GET");
            req.downloadHandler = new UnityEngine.Networking.DownloadHandlerBuffer();
            AddHeaders(req);
            yield return req.SendWebRequest();

            if (req.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                onSuccess?.Invoke(req.downloadHandler.text);
            else
            {
                TKLog.Warning($"GET {path} failed: {req.error}");
                onError?.Invoke(req.error);
            }
        }

        private static IEnumerator Post(string path, string json,
                                         Action<string>? onSuccess,
                                         Action<string>? onError)
        {
            string url     = Base + path;
            byte[] body    = Encoding.UTF8.GetBytes(json);
            using var req  = new UnityEngine.Networking.UnityWebRequest(url, "POST");
            req.uploadHandler   = new UnityEngine.Networking.UploadHandlerRaw(body);
            req.downloadHandler = new UnityEngine.Networking.DownloadHandlerBuffer();
            req.SetRequestHeader("Content-Type", "application/json");
            AddHeaders(req);
            yield return req.SendWebRequest();

            if (req.result == UnityEngine.Networking.UnityWebRequest.Result.Success)
                onSuccess?.Invoke(req.downloadHandler.text);
            else
            {
                TKLog.Warning($"POST {path} failed: {req.error}");
                onError?.Invoke(req.error);
            }
        }

        private static void AddHeaders(UnityEngine.Networking.UnityWebRequest req)
        {
            if (!string.IsNullOrEmpty(Token))
                req.SetRequestHeader("X-NuSyQ-Passkey", Token);
            req.SetRequestHeader("X-Source", "rimworld");
        }
    }

    // ─── Response models ──────────────────────────────────────────────────────

    public class CommandResponse
    {
        /// <summary>
        /// plain_output is a pre-joined string added by the backend in v0.3+.
        /// Fallback: output is a JSON array of line objects — use plain_output in preference.
        /// </summary>
        [JsonProperty("plain_output")] public string? PlainOutput { get; set; }
        [JsonProperty("output")]       public object? Output      { get; set; }
        [JsonProperty("success")]      public bool    Success     { get; set; }
        [JsonProperty("xp")]           public int     XP          { get; set; }
        [JsonProperty("session_id")]   public string? SessionId   { get; set; }
    }

    public class BlueprintResponse
    {
        [JsonProperty("name")]        public string? Name        { get; set; }
        [JsonProperty("description")] public string? Description { get; set; }
        [JsonProperty("rooms")]       public string[]? Rooms      { get; set; }
        [JsonProperty("items")]       public string[]? Items      { get; set; }
        [JsonProperty("rationale")]   public string? Rationale   { get; set; }
    }

    public class CascadeIncident
    {
        [JsonProperty("beat")]          public string? Beat         { get; set; }
        [JsonProperty("incident_type")] public string  IncidentType { get; set; } = "";
        [JsonProperty("description")]   public string? Description  { get; set; }
        [JsonProperty("ts")]            public long    Ts           { get; set; }
    }

    public class CascadeIncidentsResponse
    {
        [JsonProperty("incidents")] public System.Collections.Generic.List<CascadeIncident>? Incidents { get; set; }
        [JsonProperty("count")]     public int Count { get; set; }
    }

    public class XpSyncResponse
    {
        [JsonProperty("agent_id")]  public string? AgentId  { get; set; }
        [JsonProperty("rw_skills")] public System.Collections.Generic.Dictionary<string, int>? RwSkills { get; set; }
    }
}
