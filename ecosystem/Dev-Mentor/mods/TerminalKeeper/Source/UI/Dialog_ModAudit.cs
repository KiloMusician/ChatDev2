using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// In-game mod manager dialog, opened from the Lattice Terminal gizmo.
    ///
    /// Three tabs:
    ///   [Conflicts]   — critical + warning conflict list with per-entry fix text
    ///   [Load Order]  — current vs optimal order, violations highlighted
    ///   [AI Surfaces] — detected AI/LLM mods with integration seam notes
    ///
    /// The C# LocalModScanner harvests the mod list locally; the report is fetched
    /// from /api/rimworld/mod_audit via TerminalDepthsClient.FetchModAudit().
    /// On first open a POST is triggered; subsequent opens show the cached result.
    /// </summary>
    public class Dialog_ModAudit : Window
    {
        // ─── State ────────────────────────────────────────────────────────────

        private ModAuditReport? _report;
        private bool            _loading     = false;
        private bool            _requested   = false;
        private string          _errorMsg    = "";
        private int             _tab         = 0;   // 0=Conflicts 1=LoadOrder 2=AI
        private Vector2         _scroll      = Vector2.zero;
        private Vector2         _scrollOrder = Vector2.zero;
        private Vector2         _scrollAi    = Vector2.zero;

        // ─── Colours (cyberpunk palette matching Dialog_TerminalREPL) ─────────

        private static readonly Color ColBg       = new(0.04f, 0.04f, 0.10f);
        private static readonly Color ColBorder   = new(0.2f,  0.5f,  0.3f);
        private static readonly Color ColHeader   = new(0.2f,  0.8f,  0.3f);
        private static readonly Color ColOk       = new(0.3f,  0.9f,  0.4f);
        private static readonly Color ColWarn     = new(1.0f,  0.85f, 0.1f);
        private static readonly Color ColCritical = new(1.0f,  0.3f,  0.3f);
        private static readonly Color ColInfo     = new(0.4f,  0.6f,  1.0f);
        private static readonly Color ColDim      = new(0.55f, 0.55f, 0.55f);
        private static readonly Color ColTabAct   = new(0.15f, 0.40f, 0.18f);
        private static readonly Color ColTabInact = new(0.08f, 0.08f, 0.16f);
        private static readonly Color ColAi       = new(0.8f,  0.5f,  1.0f);

        private static readonly string[] TabLabels =
            { "⛔ Conflicts", "⇅ Load Order", "🤖 AI Surfaces" };

        public override Vector2 InitialSize => new(860f, 600f);

        public Dialog_ModAudit()
        {
            doCloseButton         = false;
            doCloseX              = true;
            absorbInputAroundWindow = true;
            forcePause            = false;
            resizeable            = true;
        }

        // ─── Lifecycle ────────────────────────────────────────────────────────

        public override void PostOpen()
        {
            base.PostOpen();
            if (!_requested)
            {
                _requested = true;
                _loading   = true;
                _errorMsg  = "";
                RequestAudit();
            }
        }

        // ─── Render ───────────────────────────────────────────────────────────

        public override void DoWindowContents(Rect inRect)
        {
            // Title bar
            GUI.color = ColHeader;
            Text.Font = GameFont.Medium;
            Widgets.Label(new Rect(0f, 0f, inRect.width - 60f, 30f), "TK_ModAudit_Title".Translate());
            Text.Font = GameFont.Small;
            GUI.color = Color.white;

            // Close button
            if (Widgets.ButtonText(new Rect(inRect.width - 56f, 2f, 54f, 26f), "✕ Close"))
                Close();

            float y = 34f;

            // Health bar / loading indicator
            y = DrawHealthBar(inRect, y);

            // Tab strip
            y = DrawTabs(inRect, y);

            // Content area
            var contentRect = new Rect(0f, y, inRect.width, inRect.height - y);
            DrawBackground(contentRect);

            if (_loading)
            {
                DrawCentered(contentRect, "TK_ModAudit_Loading".Translate(), ColDim);
                return;
            }
            if (!string.IsNullOrEmpty(_errorMsg))
            {
                DrawCentered(contentRect, $"Error: {_errorMsg}", ColCritical);
                if (Widgets.ButtonText(
                    new Rect(contentRect.x + contentRect.width / 2f - 60f,
                             contentRect.y + contentRect.height / 2f + 20f,
                             120f, 28f), "Retry"))
                {
                    _loading = true; _errorMsg = ""; RequestAudit();
                }
                return;
            }
            if (_report == null)
            {
                DrawCentered(contentRect, "No audit data.", ColDim);
                return;
            }

            switch (_tab)
            {
                case 0: DrawConflictsTab(contentRect); break;
                case 1: DrawLoadOrderTab(contentRect); break;
                case 2: DrawAiSurfacesTab(contentRect); break;
            }
        }

        // ─── Health bar ──────────────────────────────────────────────────────

        private float DrawHealthBar(Rect inRect, float y)
        {
            var barRect = new Rect(0f, y, inRect.width, 20f);

            if (_report != null)
            {
                int score = _report.HealthScore;
                Color barCol = score >= 80 ? ColOk
                             : score >= 50 ? ColWarn
                                           : ColCritical;

                Widgets.DrawBoxSolid(barRect, new Color(0.1f, 0.1f, 0.15f));
                Widgets.DrawBoxSolid(
                    new Rect(barRect.x, barRect.y, barRect.width * score / 100f, barRect.height),
                    barCol * 0.7f);

                GUI.color = barCol;
                Text.Font = GameFont.Tiny;
                Widgets.Label(
                    new Rect(barRect.x + 4f, barRect.y + 2f, barRect.width - 8f, 16f),
                    $"Mod Health: {score}%  |  {_report.ModCount} mods  |  "
                    + $"{_report.Conflicts?.Count(c => c.Severity == "critical") ?? 0} critical  "
                    + $"{_report.Conflicts?.Count(c => c.Severity == "warning") ?? 0} warnings");
                Text.Font = GameFont.Small;
                GUI.color = Color.white;
            }
            else
            {
                Widgets.DrawBoxSolid(barRect, new Color(0.1f, 0.1f, 0.15f));
                GUI.color = ColDim;
                Text.Font = GameFont.Tiny;
                Widgets.Label(new Rect(barRect.x + 4f, barRect.y + 2f, 300f, 16f),
                    _loading ? "Running mod audit…" : "No audit data");
                Text.Font = GameFont.Small;
                GUI.color = Color.white;
            }

            // Refresh button
            if (Widgets.ButtonText(
                new Rect(inRect.width - 90f, y, 88f, 20f), "↻ Re-scan"))
            {
                _loading = true; _errorMsg = ""; RequestAudit();
            }

            return y + 22f;
        }

        // ─── Tab strip ────────────────────────────────────────────────────────

        private float DrawTabs(Rect inRect, float y)
        {
            float tabW = inRect.width / TabLabels.Length;
            for (int i = 0; i < TabLabels.Length; i++)
            {
                var tabRect = new Rect(i * tabW, y, tabW, 26f);
                Widgets.DrawBoxSolid(tabRect, i == _tab ? ColTabAct : ColTabInact);
                GUI.color = i == _tab ? ColHeader : ColDim;
                if (Widgets.ButtonInvisible(tabRect)) _tab = i;
                Widgets.Label(
                    new Rect(tabRect.x + 4f, tabRect.y + 4f, tabRect.width - 8f, 18f),
                    TabLabels[i]);
                GUI.color = Color.white;

                // Border
                GUI.color = ColBorder;
                Widgets.DrawBox(tabRect, 1);
                GUI.color = Color.white;
            }
            return y + 28f;
        }

        // ─── Conflicts tab ────────────────────────────────────────────────────

        private void DrawConflictsTab(Rect r)
        {
            var conflicts = _report!.Conflicts;
            if (conflicts == null || conflicts.Count == 0)
            {
                DrawCentered(r, "✓ No conflicts detected", ColOk);
                return;
            }

            float lineH = Text.LineHeight;
            float totalH = conflicts.Count * (lineH * 4 + 14f) + 8f;
            var viewRect = new Rect(0f, 0f, r.width - 18f, Mathf.Max(totalH, r.height));

            Widgets.BeginScrollView(r, ref _scroll, viewRect);
            float y = 4f;

            foreach (var c in conflicts)
            {
                Color sevCol = c.Severity == "critical" ? ColCritical
                             : c.Severity == "warning"  ? ColWarn
                                                        : ColInfo;

                float entH = lineH * 3 + 14f;
                var entRect = new Rect(0f, y, viewRect.width - 4f, entH);
                Widgets.DrawBoxSolid(entRect, new Color(0.06f, 0.06f, 0.12f));

                GUI.color = sevCol;
                Widgets.DrawBox(entRect, 1);
                GUI.color = Color.white;

                // Severity badge
                GUI.color = sevCol;
                Text.Font = GameFont.Tiny;
                Widgets.Label(new Rect(entRect.x + 4f, entRect.y + 3f, 70f, lineH),
                    c.Severity?.ToUpperInvariant() ?? "");

                // Mod pair
                GUI.color = Color.white;
                Widgets.Label(new Rect(entRect.x + 80f, entRect.y + 3f, entRect.width - 84f, lineH),
                    $"{c.ModA}  ↔  {c.ModB}");

                // Message
                GUI.color = new Color(0.85f, 0.85f, 0.85f);
                Widgets.Label(new Rect(entRect.x + 6f, entRect.y + lineH + 4f,
                                       entRect.width - 10f, lineH),
                    c.Message ?? "");

                // Fix
                GUI.color = ColDim;
                Widgets.Label(new Rect(entRect.x + 6f, entRect.y + lineH * 2 + 5f,
                                       entRect.width - 10f, lineH),
                    $"Fix: {c.Fix ?? ""}");

                Text.Font = GameFont.Small;
                GUI.color = Color.white;

                y += entH + 5f;
            }

            Widgets.EndScrollView();
        }

        // ─── Load Order tab ───────────────────────────────────────────────────

        private void DrawLoadOrderTab(Rect r)
        {
            var lo = _report!.LoadOrder;
            if (lo == null)
            {
                DrawCentered(r, "No load-order data.", ColDim);
                return;
            }

            float headerH = Text.LineHeight + 6f;

            // Violations section header
            GUI.color = lo.HasChanges ? ColWarn : ColOk;
            Widgets.Label(new Rect(r.x + 4f, r.y + 4f, r.width - 8f, headerH),
                lo.HasChanges
                    ? $"⚠ {lo.Violations?.Count ?? 0} load-order violation(s). Optimal order differs."
                    : "✓ Load order is optimal.");
            GUI.color = Color.white;

            float topSectionH = lo.Violations?.Count > 0
                ? Mathf.Min(lo.Violations.Count * 48f + 8f, 160f)
                : 0f;
            float y = r.y + headerH + 6f;

            // Violation list (compact)
            if (lo.Violations != null && lo.Violations.Count > 0)
            {
                var violRect = new Rect(r.x, y, r.width, topSectionH);
                float vTotalH = lo.Violations.Count * 46f + 4f;
                var vViewRect = new Rect(0f, 0f, violRect.width - 18f,
                                         Mathf.Max(vTotalH, violRect.height));
                Vector2 vScroll = _scrollOrder;
                Widgets.BeginScrollView(violRect, ref vScroll, vViewRect);
                _scrollOrder = vScroll;

                float vy = 2f;
                foreach (var v in lo.Violations)
                {
                    var vr = new Rect(0f, vy, vViewRect.width - 4f, 42f);
                    Widgets.DrawBoxSolid(vr, new Color(0.08f, 0.05f, 0.05f));
                    GUI.color = ColWarn;
                    Widgets.DrawBox(vr, 1);
                    GUI.color = Color.white;

                    Text.Font = GameFont.Tiny;
                    GUI.color = ColWarn;
                    Widgets.Label(new Rect(vr.x + 4f, vr.y + 2f, vr.width - 8f, 18f),
                        $"VIOLATION: {v.Before}  must load before  {v.After}");
                    GUI.color = ColDim;
                    Widgets.Label(new Rect(vr.x + 4f, vr.y + 20f, vr.width - 8f, 18f),
                        v.Message ?? "");
                    Text.Font = GameFont.Small;
                    GUI.color = Color.white;

                    vy += 46f;
                }
                Widgets.EndScrollView();
                y += topSectionH + 4f;
            }

            // Divider label
            GUI.color = ColDim;
            Widgets.Label(new Rect(r.x + 4f, y, r.width, Text.LineHeight),
                "Optimal load order:");
            GUI.color = Color.white;
            y += Text.LineHeight + 2f;

            // Optimal order list
            var orderRect = new Rect(r.x, y, r.width, r.yMax - y);
            var optimal   = lo.Optimal ?? lo.Current ?? new List<string>();
            var current   = lo.Current ?? new List<string>();

            float oTotalH = optimal.Count * (Text.LineHeight + 2f) + 4f;
            var oViewRect  = new Rect(0f, 0f, orderRect.width - 18f,
                                      Mathf.Max(oTotalH, orderRect.height));
            Widgets.BeginScrollView(orderRect, ref _scrollOrder, oViewRect);

            float oy = 2f;
            for (int i = 0; i < optimal.Count; i++)
            {
                string pid = optimal[i];
                bool isViolated = lo.Violations?.Any(
                    v => v.Before == pid || v.After == pid) ?? false;

                GUI.color = isViolated ? ColWarn : ColOk;
                Text.Font = GameFont.Tiny;
                Widgets.Label(new Rect(0f, oy, oViewRect.width - 4f, Text.LineHeight),
                    $"{i + 1,4}.  {pid}");
                Text.Font = GameFont.Small;
                GUI.color = Color.white;
                oy += Text.LineHeight + 2f;
            }
            Widgets.EndScrollView();
        }

        // ─── AI Surfaces tab ─────────────────────────────────────────────────

        private void DrawAiSurfacesTab(Rect r)
        {
            var surfaces = _report!.AiSurfaces;
            if (surfaces == null || surfaces.Count == 0)
            {
                DrawCentered(r, "No AI/LLM surface mods detected.", ColDim);
                return;
            }

            // Intro blurb
            GUI.color = ColAi;
            Text.Font = GameFont.Tiny;
            Widgets.Label(
                new Rect(r.x + 4f, r.y + 4f, r.width - 8f, Text.LineHeight * 2),
                "These mods are AI/LLM surfaces. TerminalKeeper can share its local provider "
                + "registry with them — avoiding duplicate API keys and enabling Ollama/LM Studio routing.");
            Text.Font = GameFont.Small;
            GUI.color = Color.white;

            float startY = r.y + Text.LineHeight * 2 + 10f;
            float entH   = Text.LineHeight * 4 + 14f;
            float totalH = surfaces.Count * (entH + 6f) + 4f;
            var viewRect  = new Rect(0f, 0f, r.width - 18f, Mathf.Max(totalH, r.yMax - startY));
            var scrollRect = new Rect(r.x, startY, r.width, r.yMax - startY);

            Widgets.BeginScrollView(scrollRect, ref _scrollAi, viewRect);
            float y = 2f;

            foreach (var s in surfaces)
            {
                var entRect = new Rect(0f, y, viewRect.width - 4f, entH);
                Widgets.DrawBoxSolid(entRect, new Color(0.06f, 0.04f, 0.12f));
                GUI.color = ColAi;
                Widgets.DrawBox(entRect, 1);
                GUI.color = Color.white;

                Text.Font = GameFont.Small;
                GUI.color = ColAi;
                Widgets.Label(
                    new Rect(entRect.x + 4f, entRect.y + 3f, entRect.width - 8f, Text.LineHeight),
                    s.DisplayName ?? s.PackageId ?? "");

                GUI.color = ColDim;
                Text.Font = GameFont.Tiny;
                Widgets.Label(
                    new Rect(entRect.x + 4f, entRect.y + Text.LineHeight + 4f,
                             entRect.width - 8f, Text.LineHeight),
                    s.PackageId ?? "");

                GUI.color = new Color(0.82f, 0.82f, 0.90f);
                Widgets.Label(
                    new Rect(entRect.x + 4f, entRect.y + Text.LineHeight * 2 + 5f,
                             entRect.width - 8f, Text.LineHeight * 2),
                    s.IntegrationNote ?? "");

                Text.Font = GameFont.Small;
                GUI.color = Color.white;
                y += entH + 6f;
            }

            Widgets.EndScrollView();
        }

        // ─── Helpers ─────────────────────────────────────────────────────────

        private static void DrawBackground(Rect r)
        {
            Widgets.DrawBoxSolid(r, ColBg);
            GUI.color = ColBorder;
            Widgets.DrawBox(r, 1);
            GUI.color = Color.white;
        }

        private static void DrawCentered(Rect r, string text, Color col)
        {
            GUI.color = col;
            var sz = Text.CalcSize(text);
            Widgets.Label(
                new Rect(r.x + (r.width  - sz.x) / 2f,
                         r.y + (r.height - sz.y) / 2f,
                         sz.x, sz.y),
                text);
            GUI.color = Color.white;
        }

        // ─── Network calls ────────────────────────────────────────────────────

        private void RequestAudit()
        {
            TerminalDepthsClient.SendModAudit(
                LocalModScanner.BuildPayload(),
                onSuccess: report =>
                {
                    _report  = report;
                    _loading = false;
                },
                onError: err =>
                {
                    _errorMsg = err;
                    _loading  = false;
                }
            );
        }
    }
}
