using System.Collections.Generic;
using System.Linq;
using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// The Lattice Terminal and Console buildings (Tier 1 &amp; 2).
    /// Grants the Access Lattice interaction and tracks session stats.
    /// </summary>
    public class Building_LatticeTerminal : Building
    {
        // Persistent stats
        public int TotalSessions;
        public int TotalXPGranted;
        public string? LastAgentId;

        public bool IsActive => this.TryGetComp<CompPowerTrader>()?.PowerOn ?? false;

        public CompProperties_LatticeTerminal? TerminalProps =>
            GetComp<CompLatticeTerminal>()?.Props;

        // ─── Gizmos ───────────────────────────────────────────────────────────

        public override IEnumerable<Gizmo> GetGizmos()
        {
            foreach (var g in base.GetGizmos()) yield return g;

            yield return new Command_Action
            {
                defaultLabel = "TK_Gizmo_AccessTerminal".Translate(),
                defaultDesc  = "TK_Gizmo_AccessTerminal_Desc".Translate(),
                icon         = ContentFinder<UnityEngine.Texture2D>.Get(
                                   "UI/Icons/LatticeTerminalGizmo", false),
                Disabled     = !IsActive,
                action       = OpenDialog,
            };

            yield return new Command_Action
            {
                defaultLabel = "TK_Gizmo_ModAudit".Translate(),
                defaultDesc  = "TK_Gizmo_ModAudit_Desc".Translate(),
                icon         = ContentFinder<UnityEngine.Texture2D>.Get(
                                   "UI/Icons/LatticeModAuditGizmo", false),
                Disabled     = !IsActive,
                action       = () => Find.WindowStack.Add(new Dialog_ModAudit()),
            };
        }

        private void OpenDialog()
        {
            // Find a usable colonist near the terminal (prefer selected)
            Pawn? user = null;
            foreach (var s in Find.Selector.SelectedPawns)
            {
                if (s.IsColonistPlayerControlled &&
                    s.Position.DistanceTo(Position) <= 6f)
                { user = s; break; }
            }
            user ??= GridsUtility.GetFirstPawn(Position, Map);

            if (user == null)
            {
                Messages.Message("No colonist near terminal.", MessageTypeDefOf.RejectInput, false);
                return;
            }

            Find.WindowStack.Add(new Dialog_TerminalAccess(user, this));
        }

        // ─── Inspection ───────────────────────────────────────────────────────

        public override string GetInspectString()
        {
            string s = base.GetInspectString();
            if (TotalSessions > 0)
            {
                s += $"\n{"TK_Inspect_TotalUploads".Translate(TotalSessions)}";
                if (LastAgentId != null)
                    s += $"\n{"TK_Inspect_AgentId".Translate(LastAgentId)}";
            }

            // Show live session log for colonist currently using this terminal
            var mgr = LatticeAgentManager.Instance;
            if (mgr != null && Map != null)
            {
                var user = Map.mapPawns.FreeColonists
                    .FirstOrDefault(p => p.CurJobDef?.defName == "TK_UseLatticeTerminal"
                                      && p.CurJob?.targetA.Thing == this);
                if (user != null && mgr.SessionLog.TryGetValue(user.thingIDNumber, out var log) && log.Count > 0)
                {
                    s += $"\n[{user.Name?.ToStringShort} is jacked in]";
                    s += "\n" + string.Join("\n", log);
                }
            }
            return s;
        }

        // ─── Persistence ──────────────────────────────────────────────────────

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref TotalSessions,  "totalSessions");
            Scribe_Values.Look(ref TotalXPGranted, "totalXPGranted");
            Scribe_Values.Look(ref LastAgentId,    "lastAgentId");
        }
    }
}
