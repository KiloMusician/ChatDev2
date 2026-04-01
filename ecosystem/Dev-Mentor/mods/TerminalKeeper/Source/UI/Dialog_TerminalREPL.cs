using System;
using System.Collections.Generic;
using UnityEngine;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Full interactive Terminal Depths REPL dialog.
    /// Opens when a colonist "Plays Terminal Depths" at a Lattice Terminal.
    /// Renders a scrollable output buffer and a text-input field at the bottom.
    /// All commands are dispatched to /api/game/command; responses stream into the buffer.
    /// </summary>
    public class Dialog_TerminalREPL : Window
    {
        private readonly Pawn   _pawn;
        private readonly string _agentId;

        private string        _input     = "";
        private bool          _busy      = false;
        private Vector2       _scroll    = Vector2.zero;
        private bool          _scrollBottom = true;

        private readonly List<REPLLine> _lines = new();
        private const int MaxLines = 500;

        private static readonly Color ColBg        = new(0.04f, 0.04f, 0.10f);
        private static readonly Color ColPrompt     = new(0.2f,  0.8f,  0.3f);
        private static readonly Color ColOutput     = new(0.85f, 0.90f, 0.85f);
        private static readonly Color ColSystem     = new(0.4f,  0.6f,  1.0f);
        private static readonly Color ColError      = new(1.0f,  0.3f,  0.3f);
        private static readonly Color ColInputBg    = new(0.06f, 0.06f, 0.14f);
        private static readonly Color ColBorder     = new(0.2f,  0.5f,  0.3f);

        private const string InputControlName = "TK_REPLInput";

        public override Vector2 InitialSize => new(760f, 520f);

        public Dialog_TerminalREPL(Pawn pawn, string agentId)
        {
            _pawn    = pawn;
            _agentId = agentId;
            doCloseButton        = false;
            doCloseX             = true;
            absorbInputAroundWindow = true;
            forcePause           = false;
            resizeable           = true;

            // Boot message
            _lines.Add(new REPLLine("TK_REPL — Terminal Depths Interface v1.0", ColSystem));
            _lines.Add(new REPLLine($"Agent: {agentId}  |  Surface: RimWorld Lattice Terminal", ColSystem));
            _lines.Add(new REPLLine("Type 'help' for commands. Type 'exit' to close.", ColSystem));
            _lines.Add(new REPLLine("", ColOutput));

            // Send a status command on open to prime the session
            SendCommand("status");
        }

        public override void DoWindowContents(Rect inRect)
        {
            // ── Title bar ────────────────────────────────────────────────────
            GUI.color = ColPrompt;
            Text.Font = GameFont.Medium;
            Widgets.Label(new Rect(0, 0, inRect.width - 60f, 32f),
                $"Terminal Depths — {_pawn.Name?.ToStringShort}");
            Text.Font = GameFont.Small;
            GUI.color = Color.white;

            // Close button
            if (Widgets.ButtonText(new Rect(inRect.width - 56f, 2f, 54f, 26f), "✕ Exit"))
                Close();

            float y = 36f;

            // ── Output console ────────────────────────────────────────────────
            float inputH  = 36f;
            float consoleH = inRect.height - y - inputH - 16f;
            var   consoleR  = new Rect(0, y, inRect.width, consoleH);

            Widgets.DrawBoxSolid(consoleR, ColBg);

            // Border
            GUI.color = ColBorder;
            Widgets.DrawBox(consoleR, 1);
            GUI.color = Color.white;

            // Measure total content height
            float lineH = Text.LineHeight + 2f;
            float totalH = _lines.Count * lineH + 12f;
            float viewH  = Mathf.Max(totalH, consoleH);

            var viewR    = new Rect(0, 0, consoleR.width - 16f, viewH);

            if (_scrollBottom)
            {
                _scroll.y = Mathf.Max(0f, totalH - consoleH);
                _scrollBottom = false;
            }

            Widgets.BeginScrollView(consoleR, ref _scroll, viewR);
            float ty = 6f;
            for (int i = 0; i < _lines.Count; i++)
            {
                var line = _lines[i];
                GUI.color = line.Color;
                Widgets.Label(new Rect(6f, ty, viewR.width - 12f, lineH), line.Text);
                ty += lineH;
            }
            GUI.color = Color.white;

            if (_busy)
            {
                GUI.color = ColSystem;
                Widgets.Label(new Rect(6f, ty, viewR.width - 12f, lineH), "[ processing... ]");
                GUI.color = Color.white;
            }
            Widgets.EndScrollView();

            y += consoleH + 8f;

            // ── Input row ────────────────────────────────────────────────────
            Widgets.DrawBoxSolid(new Rect(0, y, inRect.width, inputH), ColInputBg);
            GUI.color = ColPrompt;
            Widgets.Label(new Rect(4f, y + 8f, 20f, 22f), "▶");
            GUI.color = Color.white;

            GUI.SetNextControlName(InputControlName);
            _input = Widgets.TextField(new Rect(26f, y + 4f, inRect.width - 80f, 28f), _input);
            GUI.FocusControl(InputControlName);

            bool sendBtn = Widgets.ButtonText(
                new Rect(inRect.width - 50f, y + 4f, 48f, 28f), "Send");

            // Handle Enter key or Send button
            bool enterPressed = Event.current.type == EventType.KeyDown &&
                                Event.current.keyCode == KeyCode.Return &&
                                GUI.GetNameOfFocusedControl() == InputControlName;

            if ((sendBtn || enterPressed) && !_busy && !string.IsNullOrWhiteSpace(_input))
            {
                if (enterPressed) Event.current.Use();
                string cmd = _input.Trim();
                _input = "";

                if (cmd.Equals("exit", StringComparison.OrdinalIgnoreCase) ||
                    cmd.Equals("quit", StringComparison.OrdinalIgnoreCase))
                {
                    Close();
                    return;
                }
                if (cmd.Equals("clear", StringComparison.OrdinalIgnoreCase))
                {
                    _lines.Clear();
                    return;
                }

                // Echo command
                _lines.Add(new REPLLine($"▶ {cmd}", ColPrompt));
                TrimBuffer();
                SendCommand(cmd);
            }
        }

        // ── API call ──────────────────────────────────────────────────────────

        private void SendCommand(string cmd)
        {
            _busy = true;
            TerminalDepthsClient.SendCommand(_agentId, cmd,
                onSuccess: resp =>
                {
                    _busy = false;
                    string text = resp?.PlainOutput ?? resp?.Output?.ToString() ?? "(no output)";
                    foreach (var line in text.Split('\n'))
                    {
                        string stripped = StripAnsi(line.TrimEnd());
                        if (stripped.Length == 0 && _lines.Count > 0 &&
                            _lines[_lines.Count - 1].Text.Length == 0)
                            continue;
                        _lines.Add(new REPLLine(stripped, ColOutput));
                    }
                    TrimBuffer();
                    _scrollBottom = true;

                    // XP feedback
                    if (resp?.XP > 0)
                    {
                        _lines.Add(new REPLLine(
                            $"[+{resp.XP} XP — Lattice session rewarded]", ColSystem));
                        _scrollBottom = true;
                    }
                },
                onError: e =>
                {
                    _busy = false;
                    _lines.Add(new REPLLine($"[ERROR] {e}", ColError));
                    _scrollBottom = true;
                });
        }

        private void TrimBuffer()
        {
            while (_lines.Count > MaxLines)
                _lines.RemoveAt(0);
        }

        private static string StripAnsi(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            int i = 0;
            var sb = new System.Text.StringBuilder(s.Length);
            while (i < s.Length)
            {
                if (s[i] == '\x1B' && i + 1 < s.Length && s[i + 1] == '[')
                {
                    i += 2;
                    while (i < s.Length && s[i] != 'm') i++;
                    i++;
                }
                else sb.Append(s[i++]);
            }
            return sb.ToString();
        }

        private struct REPLLine
        {
            public string Text;
            public Color  Color;
            public REPLLine(string text, Color color) { Text = text; Color = color; }
        }
    }
}
