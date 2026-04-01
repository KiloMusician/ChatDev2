using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Tier 3 Lattice Nexus — broadcasts colony telemetry and applies the
    /// Lattice-linked aura to all colonists within InfluenceRadius.
    /// </summary>
    public class Building_LatticeNexus : Building
    {
        private int _lastBroadcastTick;

        public float InfluenceRadius =>
            GetComp<CompLatticeNexus>()?.Props.InfluenceRadius ?? 15f;

        public bool IsActive => this.TryGetComp<CompPowerTrader>()?.PowerOn ?? false;

        protected override void Tick()
        {
            base.Tick();

            if (!IsActive) return;
            if (Find.TickManager.TicksGame - _lastBroadcastTick <
                (GetComp<CompLatticeNexus>()?.Props.BroadcastIntervalTicks ?? 600)) return;

            _lastBroadcastTick = Find.TickManager.TicksGame;
            BroadcastColonyState();
        }

        private void BroadcastColonyState()
        {
            if (Map == null) return;

            // Pick one colonist as the "anchor" to serialize colony-level state
            var anchor = Map.mapPawns.FreeColonists?.RandomElementWithFallback();
            if (anchor == null) return;

            var manager = LatticeAgentManager.Instance;
            if (manager == null) return;

            string agentId = manager.GetOrCreateAgentId(anchor);
            var state      = ColonistState.From(anchor, agentId);

            TerminalDepthsClient.PushColonistState(state,
                onSuccess: _ => TKLog.Debug("Nexus broadcast succeeded."),
                onError:   e => TKLog.Debug($"Nexus broadcast failed: {e}"));
        }

        public override string GetInspectString()
        {
            string s = base.GetInspectString();
            s += $"\nInfluence radius: {InfluenceRadius} tiles";
            s += IsActive ? "\nStatus: broadcasting" : "\nStatus: offline";
            return s;
        }

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref _lastBroadcastTick, "lastBroadcastTick");
        }
    }
}
