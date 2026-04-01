using RimWorld;
using UnityEngine;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Modal dialog that opens when a colonist accesses a Lattice Terminal.
    /// Shows colonist info, available actions, and last API response.
    /// </summary>
    public class Dialog_TerminalAccess : Window
    {
        private readonly Pawn _pawn;
        private readonly Building_LatticeTerminal _terminal;

        private string _outputBuffer = "";
        private bool   _busy;
        private Vector2 _scroll;

        public override Vector2 InitialSize => new(640f, 480f);

        public Dialog_TerminalAccess(Pawn pawn, Building_LatticeTerminal terminal)
        {
            _pawn     = pawn;
            _terminal = terminal;
            doCloseButton  = true;
            doCloseX       = true;
            absorbInputAroundWindow = true;
            forcePause = false;
        }

        public override void DoWindowContents(Rect inRect)
        {
            var titleFont = Text.Font;
            Text.Font = GameFont.Medium;
            Widgets.Label(new Rect(0, 0, inRect.width, 36f),
                "TK_DialogTitle".Translate(_pawn.Name?.ToStringShort ?? "?"));
            Text.Font = titleFont;

            float y = 44f;

            // ── Colonist state strip ──────────────────────────────────────────
            DrawStatStrip(ref y, inRect.width);

            y += 8f;
            Widgets.DrawLineHorizontal(0, y, inRect.width);
            y += 12f;

            // ── Action buttons ────────────────────────────────────────────────
            bool tier2Plus = (_terminal.TerminalProps?.tier ?? 1) >= 2;

            // Primary: open the full interactive Terminal Depths REPL
            var agentId = LatticeAgentManager.Instance?.GetOrCreateAgentId(_pawn) ?? "rw_unknown";
            DrawButton(ref y, inRect.width, "TK_PlayTerminalDepths".Translate(), true,
                () =>
                {
                    Close();
                    Find.WindowStack.Add(new Dialog_TerminalREPL(_pawn, agentId));
                });

            y += 4f;
            Widgets.DrawLineHorizontal(0, y, inRect.width);
            y += 8f;

            DrawButton(ref y, inRect.width, "TK_UploadLog".Translate(),     !_busy, OnUploadLog);
            if (tier2Plus)
            {
                DrawButton(ref y, inRect.width, "TK_DownloadBlueprint".Translate(),
                           !_busy && TKSettings.Blueprints, OnDownloadBlueprint);
                DrawButton(ref y, inRect.width, "TK_CouncilVote".Translate(),
                           !_busy && TKSettings.AICouncil, OnCouncilVote);
                DrawButton(ref y, inRect.width, "TK_ViewSerenaAnalytics".Translate(),
                           !_busy, OnSerenaQuery);
            }

            y += 8f;
            Widgets.DrawLineHorizontal(0, y, inRect.width);
            y += 12f;

            // ── Output console ────────────────────────────────────────────────
            float consoleH = inRect.height - y - 8f;
            var   consoleR = new Rect(0f, y, inRect.width, consoleH);
            Widgets.DrawBoxSolid(consoleR, new Color(0.05f, 0.05f, 0.12f));

            var textR = consoleR.ContractedBy(6f);
            Widgets.LabelScrollable(textR, _busy ? "..." : _outputBuffer, ref _scroll);
        }

        // ─── Actions ──────────────────────────────────────────────────────────

        private void OnUploadLog()
        {
            _busy = true;
            _outputBuffer = "";
            var agentId = LatticeAgentManager.Instance?.GetOrCreateAgentId(_pawn) ?? "rw_unknown";
            int skill   = _pawn.skills?.GetSkill(SkillDefOf.Intellectual)?.Level ?? 0;

            string cmd = $"upload_log colonist={_pawn.Name?.ToStringShort} " +
                         $"skill_int={skill} mood={_pawn.needs?.mood?.CurLevelPercentage:F2}";

            TerminalDepthsClient.SendCommand(agentId, cmd,
                onSuccess: resp =>
                {
                    _busy = false;
                    int xp = resp?.XP ?? (_terminal.TerminalProps?.xpGranted ?? 25);
                    _outputBuffer = $"{"TK_UploadSuccess".Translate(xp)}\n\n{resp?.Output}";
                    _terminal.TotalSessions++;
                    _terminal.TotalXPGranted += xp;
                    _terminal.LastAgentId = agentId;
                    _pawn.needs?.mood?.thoughts?.memories?.TryGainMemory(
                        DefDatabase<ThoughtDef>.GetNamedSilentFail("TK_CompletedLatticeTask"));
                },
                onError: e =>
                {
                    _busy = false;
                    _outputBuffer = "TK_UploadFailed".Translate(e);
                });
        }

        private void OnDownloadBlueprint()
        {
            _busy = true;
            string context = $"colony_wealth={_pawn.Map?.wealthWatcher?.WealthTotal:F0} " +
                             $"colonists={_pawn.Map?.mapPawns?.FreeColonistsCount}";

            TerminalDepthsClient.RequestBlueprint(context,
                onSuccess: bp =>
                {
                    _busy = false;
                    if (bp == null) { _outputBuffer = "No blueprint received."; return; }
                    _outputBuffer = $"Blueprint: {bp.Name}\n{bp.Description}\n\nRationale: {bp.Rationale}";
                    Messages.Message("TK_Message_BlueprintReceived".Translate(bp.Name),
                                     MessageTypeDefOf.PositiveEvent, false);
                },
                onError: e => { _busy = false; _outputBuffer = $"Blueprint request failed: {e}"; });
        }

        private void OnCouncilVote()
        {
            _busy = true;
            var agentId = LatticeAgentManager.Instance?.GetOrCreateAgentId(_pawn) ?? "rw_unknown";
            TerminalDepthsClient.SendCommand(agentId, "council vote",
                onSuccess: resp =>
                {
                    _busy = false;
                    _outputBuffer = $"AI Council decision:\n\n{resp?.Output}";
                    Messages.Message("TK_Message_CouncilDecision".Translate(((string?)(resp?.Output))?.Truncate(100)),
                                     MessageTypeDefOf.NeutralEvent, false);
                },
                onError: e => { _busy = false; _outputBuffer = $"Council vote failed: {e}"; });
        }

        private void OnSerenaQuery()
        {
            _busy = true;
            TerminalDepthsClient.GetColonyAnalytics(
                onSuccess: raw => { _busy = false; _outputBuffer = $"Serena Analytics:\n\n{raw}"; },
                onError:   e  => { _busy = false; _outputBuffer = $"Serena query failed: {e}"; });
        }

        // ─── Drawing helpers ──────────────────────────────────────────────────

        private void DrawStatStrip(ref float y, float width)
        {
            float hp   = _pawn.health?.summaryHealth?.SummaryHealthPercent ?? 0f;
            float mood = _pawn.needs?.mood?.CurLevelPercentage ?? 0f;
            int   intl = _pawn.skills?.GetSkill(SkillDefOf.Intellectual)?.Level ?? 0;

            Widgets.Label(new Rect(0, y, width, 22f),
                $"Health: {hp:P0}  |  Mood: {mood:P0}  |  Intellectual: {intl}");
            y += 26f;
        }

        private void DrawButton(ref float y, float width, string label, bool enabled,
                                 System.Action action)
        {
            var r = new Rect(0, y, 220f, 30f);
            if (Widgets.ButtonText(r, label, active: enabled))
                action();
            y += 36f;
        }
    }
}
