using System;
using System.Collections.Generic;
using System.Linq;
using RimWorld;
using RimWorld.Planet;
using Verse;
using Verse.AI;

namespace TerminalKeeper
{
    /// <summary>
    /// Per-colony singleton (WorldComponent) that maps each colonist to their
    /// Terminal Depths agent ID and manages periodic state pushes.
    /// </summary>
    public class LatticeAgentManager : WorldComponent
    {
        // colonist thing ID → Terminal Depths agent ID
        private Dictionary<int, string> _agentIds = new();
        private Dictionary<int, int>    _lastPush  = new();

        // Cascade incident polling
        private long _lastIncidentPollTick   = 0;
        private long _lastCascadeIncidentTs  = 0;   // Unix ms watermark
        private const int IncidentPollEvery  = 1500; // ~25 real-seconds at 1× speed

        // XP sync
        private long _lastXpSyncTick         = 0;
        private const int XpSyncEvery        = 6000; // ~100 real-seconds

        // Autonomous colonist play
        private int  _lastAutoPlayTick       = 0;
        private const int AutoPlayEvery      = 3000; // ~50 real-seconds at 1× speed

        // Session log: colonist thingID → last N command/response pairs
        public readonly Dictionary<int, List<string>> SessionLog = new();
        private const int SessionLogMax = 5;

        // Commands colonists issue autonomously (beginner-level, lore-friendly)
        private static readonly string[] AutoCommands = {
            "status", "ls", "help", "whoami", "ps",
            "scan", "ping", "netstat", "df", "uptime",
        };

        public LatticeAgentManager(World world) : base(world) { }

        public static LatticeAgentManager? Instance =>
            Find.World?.GetComponent<LatticeAgentManager>();

        // ─── API ──────────────────────────────────────────────────────────────

        public string GetOrCreateAgentId(Pawn pawn)
        {
            if (_agentIds.TryGetValue(pawn.thingIDNumber, out var id)) return id;

            id = $"rw_{pawn.ThingID}_{pawn.Name?.ToStringShort?.ToLower().Replace(" ", "_") ?? "unknown"}";
            _agentIds[pawn.thingIDNumber] = id;

            // Fire-and-forget registration
            TerminalDepthsClient.RegisterAgent(id, pawn.Name?.ToStringShort ?? "Unknown",
                onSuccess: _ => TKLog.Debug($"Agent registered: {id}"),
                onError:   e => TKLog.Warning($"Agent registration failed for {id}: {e}"));

            return id;
        }

        public void OnJobComplete(Pawn pawn, Job? job)
        {
            if (job == null) return;
            if (!ShouldPush(pawn)) return;

            string agentId = GetOrCreateAgentId(pawn);
            var state = ColonistState.From(pawn, agentId);

            TerminalDepthsClient.PushColonistState(state,
                onSuccess: _ => TKLog.Debug($"State pushed for {agentId}"),
                onError:   e => TKLog.Debug($"State push failed: {e}"));

            _lastPush[pawn.thingIDNumber] = Find.TickManager.TicksGame;
        }

        public static void OnLatticeSession(Pawn pawn, string command, int xpGranted)
        {
            var inst = Instance;
            if (inst == null) return;

            string agentId = inst.GetOrCreateAgentId(pawn);

            TerminalDepthsClient.SendCommand(agentId, command,
                onSuccess: resp =>
                {
                    var display = resp?.PlainOutput ?? resp?.Output?.ToString() ?? "";
                    if (!string.IsNullOrWhiteSpace(display))
                        Messages.Message(display.Truncate(200), MessageTypeDefOf.NeutralEvent, false);
                },
                onError: e => TKLog.Warning($"Command failed for {agentId}: {e}"));

            // Grant in-game hediff boost
            HealthUtility.AdjustSeverity(pawn,
                DefDatabase<HediffDef>.GetNamedSilentFail("TK_LatticeSessionBuff") ?? HediffDefOf.Pregnant, // fallback safe
                0.5f);
        }

        // ─── Periodic Tick ───────────────────────────────────────────────────

        public override void WorldComponentTick()
        {
            base.WorldComponentTick();
            int tick = Find.TickManager.TicksGame;

            // ── Cascade incident polling ──────────────────────────────────────
            if (tick - _lastIncidentPollTick >= IncidentPollEvery)
            {
                _lastIncidentPollTick = tick;
                PollCascadeIncidents();
            }

            // ── XP sync (colony-wide) ─────────────────────────────────────────
            if (tick - _lastXpSyncTick >= XpSyncEvery)
            {
                _lastXpSyncTick = tick;
                SyncAllColonistXP();
            }

            // ── Autonomous colonist play ──────────────────────────────────────
            if (tick - _lastAutoPlayTick >= AutoPlayEvery)
            {
                _lastAutoPlayTick = tick;
                TickAutoPlay();
            }
        }

        private void TickAutoPlay()
        {
            var map = Find.AnyPlayerHomeMap;
            if (map == null) return;

            // Find colonists sitting at any Rimnet/Lattice terminal
            var terminals = map.listerBuildings.AllBuildingsColonistOfClass<Building_LatticeTerminal>();
            foreach (var terminal in terminals)
            {
                if (!(terminal.TryGetComp<CompPowerTrader>()?.PowerOn ?? true)) continue;

                // Check for a colonist using this terminal right now
                var user = terminal.Map.mapPawns.FreeColonists
                    .FirstOrDefault(p => p.CurJobDef?.defName == "TK_UseLatticeTerminal"
                                      && p.CurJob?.targetA.Thing == terminal);
                if (user == null) continue;

                string agentId = GetOrCreateAgentId(user);
                string cmd = AutoCommands[Rand.Range(0, AutoCommands.Length)];

                var capturedUser  = user;
                var capturedAgent = agentId;
                var capturedCmd   = cmd;

                TerminalDepthsClient.SendCommand(agentId, cmd,
                    onSuccess: resp =>
                    {
                        string output = resp?.PlainOutput ?? resp?.Output?.ToString() ?? "";
                        string logEntry = $"[{capturedUser.Name?.ToStringShort}] > {capturedCmd}";
                        AddToSessionLog(capturedUser.thingIDNumber, logEntry);
                        if (!string.IsNullOrWhiteSpace(output))
                            AddToSessionLog(capturedUser.thingIDNumber,
                                output.Split('\n')[0].Trim().Truncate(120));

                        // Feed XP back to Intellectual skill
                        if ((resp?.XP ?? 0) > 0)
                        {
                            var s = capturedUser.skills?.GetSkill(SkillDefOf.Intellectual);
                            s?.Learn(resp!.XP * 5, false);
                        }
                    },
                    onError: _ => { });
            }
        }

        private void AddToSessionLog(int pawnId, string entry)
        {
            if (!SessionLog.TryGetValue(pawnId, out var log))
            {
                log = new List<string>();
                SessionLog[pawnId] = log;
            }
            log.Add(entry);
            while (log.Count > SessionLogMax)
                log.RemoveAt(0);
        }

        private void PollCascadeIncidents()
        {
            long since = _lastCascadeIncidentTs;
            TerminalDepthsClient.GetCascadeIncidents((double)since,
                onSuccess: raw =>
                {
                    try
                    {
                        var resp = Newtonsoft.Json.JsonConvert.DeserializeObject<CascadeIncidentsResponse>(raw);
                        var incidents = resp?.Incidents;
                        if (incidents == null || incidents.Count == 0) return;
                        _lastCascadeIncidentTs = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

                        var map = Find.AnyPlayerHomeMap;
                        if (map == null) return;

                        foreach (var inc in incidents)
                            SpawnCascadeIncident(inc, map);
                    }
                    catch (Exception ex) { TKLog.Debug($"Cascade parse error: {ex.Message}"); }
                },
                onError: e => TKLog.Debug($"Cascade poll failed: {e}"));
        }

        private static void SpawnCascadeIncident(CascadeIncident inc, Map map)
        {
            IncidentDef? def = null;
            switch (inc.IncidentType)
            {
                case "raid":
                    def = IncidentDefOf.RaidEnemy;
                    break;
                case "nexus_retaliation":
                    def = IncidentDefOf.RaidEnemy;
                    break;
                case "first_exploit":
                case "root_achieved":
                    def = IncidentDefOf.Eclipse;   // "something changed in the colony..."
                    break;
                case "chimera_connected":
                case "council_vote":
                case "culture_ship":
                case "ascension":
                    def = IncidentDefOf.SolarFlare;
                    break;
                case "ghost_activated":
                    def = DefDatabase<IncidentDef>.GetNamedSilentFail("ShortCircuit")
                       ?? DefDatabase<IncidentDef>.GetNamedSilentFail("ElectricStorm");
                    break;
                default:
                    def = null;
                    break;
            }

            if (def != null)
            {
                var parms = StorytellerUtility.DefaultParmsNow(def.category, map);
                def.Worker?.TryExecute(parms);
            }

            // Always show a message
            string msg = $"[Lattice] {inc.Beat}: {inc.Description ?? inc.IncidentType}";
            Messages.Message(msg, MessageTypeDefOf.NeutralEvent, false);
            TKLog.Debug($"Cascade incident spawned: {inc.IncidentType}");
        }

        private void SyncAllColonistXP()
        {
            if (Find.AnyPlayerHomeMap == null) return;
            var pawns = PawnsFinder.AllMaps_FreeColonists;
            if (pawns == null) return;

            foreach (var pawn in pawns)
            {
                if (!_agentIds.TryGetValue(pawn.thingIDNumber, out string? agentId)) continue;

                // Capture pawn reference for the closure
                var capturedPawn = pawn;
                var capturedId   = agentId;

                // Build a minimal skills dict from pawn's current game progression
                var skillsDict = new Dictionary<string, int>();
                if (pawn.skills != null)
                {
                    foreach (var skill in pawn.skills.skills)
                        skillsDict[skill.def.defName] = skill.Level * 200;  // rough XP mapping
                }

                TerminalDepthsClient.SyncXP(capturedId, skillsDict,
                    onSuccess: raw =>
                    {
                        try
                        {
                            var resp = Newtonsoft.Json.JsonConvert.DeserializeObject<XpSyncResponse>(raw);
                            if (resp?.RwSkills == null) return;
                            foreach (var kv in resp.RwSkills)
                            {
                                var skillDef = DefDatabase<SkillDef>.GetNamedSilentFail(kv.Key);
                                if (skillDef == null) continue;
                                var s = capturedPawn.skills?.GetSkill(skillDef);
                                if (s == null) continue;
                                if (kv.Value > s.Level)
                                {
                                    s.Level = kv.Value;
                                    TKLog.Debug($"XP sync: {capturedPawn.Name?.ToStringShort} {kv.Key} → {kv.Value}");
                                }
                            }
                        }
                        catch (Exception ex) { TKLog.Debug($"XP parse error: {ex.Message}"); }
                    },
                    onError: e => TKLog.Debug($"XP sync failed for {capturedId}: {e}"));
            }
        }

        // ─── Persistence ──────────────────────────────────────────────────────

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Collections.Look(ref _agentIds, "agentIds", LookMode.Value, LookMode.Value);
            Scribe_Collections.Look(ref _lastPush,  "lastPush",  LookMode.Value, LookMode.Value);
            _agentIds ??= new();
            _lastPush  ??= new();
        }

        // ─── Helpers ──────────────────────────────────────────────────────────

        private bool ShouldPush(Pawn pawn)
        {
            if (!_lastPush.TryGetValue(pawn.thingIDNumber, out int last)) return true;
            return Find.TickManager.TicksGame - last >= TKSettings.UpdateInterval;
        }
    }
}
