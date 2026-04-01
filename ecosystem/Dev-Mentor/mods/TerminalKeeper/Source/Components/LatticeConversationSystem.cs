using System;
using System.Collections.Generic;
using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Intercepts colonist social interactions and, when both participants are
    /// Lattice-linked, routes a summary through Terminal Depths to get an
    /// AI-flavoured conversation snippet shown as a letter/message.
    /// </summary>
    public static class LatticeConversationSystem
    {
        // pawn pair hash → last conversation tick
        private static readonly Dictionary<int, int> _cooldowns = new();

        public static bool BothLinked(Pawn a, Pawn b)
        {
            return HasLatticeHediff(a) && HasLatticeHediff(b);
        }

        public static void TryQueueLatticeConversation(Pawn initiator, Pawn recipient,
                                                        string context = "chat")
        {
            int pairHash = PairHash(initiator, recipient);
            int now = Find.TickManager.TicksGame;

            if (_cooldowns.TryGetValue(pairHash, out int last) &&
                now - last < TKSettings.ConvCooldown) return;

            _cooldowns[pairHash] = now;

            string agentA = LatticeAgentManager.Instance?.GetOrCreateAgentId(initiator) ?? "rw_unknown";
            string agentB = LatticeAgentManager.Instance?.GetOrCreateAgentId(recipient)  ?? "rw_unknown2";

            // Build a prompt that Terminal Depths can respond to via Gordon/Serena
            string cmd = $"converse agent_a={agentA} agent_b={agentB} context={context}";

            TerminalDepthsClient.SendCommand(agentA, cmd,
                onSuccess: resp =>
                {
                    string text = (string?)(resp?.Output) ?? "";
                    if (string.IsNullOrWhiteSpace(text)) return;

                    // Show as a floating message on the initiator
                    MoteMaker.ThrowText(initiator.DrawPos, initiator.Map,
                        text.Truncate(120), 6f);
                },
                onError: e => TKLog.Debug($"Conversation request failed: {e}"));
        }

        private static bool HasLatticeHediff(Pawn p) =>
            p.health?.hediffSet?.HasHediff(
                DefDatabase<HediffDef>.GetNamedSilentFail("TK_LatticeLinkedHediff")) ?? false;

        private static int PairHash(Pawn a, Pawn b)
        {
            int lo = Math.Min(a.thingIDNumber, b.thingIDNumber);
            int hi = Math.Max(a.thingIDNumber, b.thingIDNumber);
            return (lo * 31) ^ hi;
        }
    }
}
