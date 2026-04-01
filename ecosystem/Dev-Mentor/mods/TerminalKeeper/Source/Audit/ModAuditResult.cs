using System.Collections.Generic;
using Newtonsoft.Json;

namespace TerminalKeeper
{
    // ─── Incoming payload types (sent to the API) ─────────────────────────────

    public class ModAuditPayload
    {
        [JsonProperty("mod_ids")]    public List<string>              ModIds    { get; set; } = new();
        [JsonProperty("about_xmls")] public Dictionary<string, string> AboutXmls { get; set; } = new();
    }

    // ─── Response types (returned by the API) ─────────────────────────────────

    public class ModAuditReport
    {
        [JsonProperty("timestamp")]    public string?           Timestamp   { get; set; }
        [JsonProperty("elapsed_ms")]   public int               ElapsedMs   { get; set; }
        [JsonProperty("mod_count")]    public int               ModCount    { get; set; }
        [JsonProperty("health_score")] public int               HealthScore { get; set; }
        [JsonProperty("summary")]      public string?           Summary     { get; set; }
        [JsonProperty("duplicates")]   public List<DuplicateEntry>?  Duplicates  { get; set; }
        [JsonProperty("conflicts")]    public List<ConflictWarning>? Conflicts   { get; set; }
        [JsonProperty("load_order")]   public LoadOrderResult?  LoadOrder   { get; set; }
        [JsonProperty("ai_surfaces")]  public List<AiSurface>?  AiSurfaces  { get; set; }
    }

    public class DuplicateEntry
    {
        [JsonProperty("package_id")] public string?     PackageId { get; set; }
        [JsonProperty("positions")]  public List<int>?  Positions { get; set; }
    }

    public class ConflictWarning
    {
        [JsonProperty("severity")] public string? Severity { get; set; }
        [JsonProperty("mod_a")]    public string? ModA     { get; set; }
        [JsonProperty("mod_b")]    public string? ModB     { get; set; }
        [JsonProperty("source")]   public string? Source   { get; set; }
        [JsonProperty("message")]  public string? Message  { get; set; }
        [JsonProperty("fix")]      public string? Fix      { get; set; }
    }

    public class LoadOrderResult
    {
        [JsonProperty("current")]      public List<string>?         Current     { get; set; }
        [JsonProperty("optimal")]      public List<string>?         Optimal     { get; set; }
        [JsonProperty("violations")]   public List<OrderViolation>? Violations  { get; set; }
        [JsonProperty("cycles")]       public List<List<string>>?   Cycles      { get; set; }
        [JsonProperty("has_changes")]  public bool                  HasChanges  { get; set; }
    }

    public class OrderViolation
    {
        [JsonProperty("rule")]    public string? Rule    { get; set; }
        [JsonProperty("before")]  public string? Before  { get; set; }
        [JsonProperty("after")]   public string? After   { get; set; }
        [JsonProperty("message")] public string? Message { get; set; }
    }

    public class AiSurface
    {
        [JsonProperty("package_id")]        public string? PackageId       { get; set; }
        [JsonProperty("display_name")]      public string? DisplayName     { get; set; }
        [JsonProperty("integration_note")]  public string? IntegrationNote { get; set; }
    }
}
