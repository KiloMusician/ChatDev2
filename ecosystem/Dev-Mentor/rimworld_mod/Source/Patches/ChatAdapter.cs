using System.Collections.Generic;
using HarmonyLib;
using RimWorld;
using Verse;
using Verse.Grammar;

namespace TerminalKeeper.EventBridge;

internal static class ChatAdapterPayloads
{
    public const string OmniTag = "[Msg⛛{Chat}]";

    public static void QueueInteraction(
        string worker,
        string topic,
        string outcome,
        Pawn initiator,
        Pawn recipient,
        string? letterLabel,
        string? letterText)
    {
        EventDispatcher.QueueEvent(
            "chat_interaction",
            BuildInteractionPayload(
                worker,
                topic,
                outcome,
                initiator?.Name?.ToStringShort ?? initiator?.LabelShort ?? "unknown",
                recipient?.Name?.ToStringShort ?? recipient?.LabelShort ?? "unknown",
                initiator?.Faction?.Name ?? initiator?.Faction?.def?.defName ?? "none",
                recipient?.Faction?.Name ?? recipient?.Faction?.def?.defName ?? "none",
                letterLabel,
                letterText));
    }

    internal static string BuildInteractionPayload(
        string worker,
        string topic,
        string outcome,
        string initiatorName,
        string recipientName,
        string initiatorFaction,
        string recipientFaction,
        string? letterLabel,
        string? letterText)
    {
        return "{" +
               $"\"omniTag\":\"{BridgeJson.Escape(OmniTag)}\"," +
               $"\"source\":\"{BridgeJson.Escape(worker)}\"," +
               $"\"topic\":\"{BridgeJson.Escape(topic)}\"," +
               $"\"outcome\":\"{BridgeJson.Escape(outcome)}\"," +
               $"\"initiator\":\"{BridgeJson.Escape(initiatorName)}\"," +
               $"\"recipient\":\"{BridgeJson.Escape(recipientName)}\"," +
               $"\"initiatorFaction\":\"{BridgeJson.Escape(initiatorFaction)}\"," +
               $"\"recipientFaction\":\"{BridgeJson.Escape(recipientFaction)}\"," +
               $"\"letterLabel\":\"{BridgeJson.Escape(letterLabel)}\"," +
               $"\"letterText\":\"{BridgeJson.Escape(Summarize(letterText, 240))}\"" +
               "}";
    }

    internal static string Summarize(string? text, int maxLen)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            return string.Empty;
        }

        var compact = text.Replace("\r", " ").Replace("\n", " ").Trim();
        if (compact.Length <= maxLen)
        {
            return compact;
        }

        return compact.Substring(0, maxLen) + "...";
    }
}

/*
 * Assumed vanilla signatures, inferred from RimWorld interaction worker patterns
 * and local Harmony patch conventions:
 *
 *   void Interacted(
 *       Pawn initiator,
 *       Pawn recipient,
 *       List<RulePackDef> extraSentencePacks,
 *       out string letterText,
 *       out string letterLabel,
 *       out LetterDef letterDef,
 *       out LookTargets lookTargets)
 *
 * If the exact signature differs on this install, adjust the postfix parameter
 * list to match Assembly-CSharp.dll.
 */

[HarmonyPatch(typeof(InteractionWorker_RecruitAttempt), nameof(InteractionWorker_RecruitAttempt.Interacted))]
internal static class ChatAdapter_RecruitAttempt
{
    internal static void Postfix(
        Pawn initiator,
        Pawn recipient,
        List<RulePackDef> extraSentencePacks,
        ref string letterText,
        ref string letterLabel,
        ref LetterDef letterDef,
        ref LookTargets lookTargets)
    {
        var outcome = recipient?.Faction == Faction.OfPlayer ? "recruited" : "attempted";
        ChatAdapterPayloads.QueueInteraction(
            nameof(InteractionWorker_RecruitAttempt),
            "recruit_attempt",
            outcome,
            initiator,
            recipient,
            letterLabel,
            letterText);
    }
}

[HarmonyPatch(typeof(InteractionWorker_DeepTalk), nameof(InteractionWorker_DeepTalk.Interacted))]
internal static class ChatAdapter_DeepTalk
{
    internal static void Postfix(
        Pawn initiator,
        Pawn recipient,
        List<RulePackDef> extraSentencePacks,
        ref string letterText,
        ref string letterLabel,
        ref LetterDef letterDef,
        ref LookTargets lookTargets)
    {
        ChatAdapterPayloads.QueueInteraction(
            nameof(InteractionWorker_DeepTalk),
            "deep_talk",
            "completed",
            initiator,
            recipient,
            letterLabel,
            letterText);
    }
}

[HarmonyPatch(typeof(InteractionWorker_KindWords), nameof(InteractionWorker_KindWords.Interacted))]
internal static class ChatAdapter_KindWords
{
    internal static void Postfix(
        Pawn initiator,
        Pawn recipient,
        List<RulePackDef> extraSentencePacks,
        ref string letterText,
        ref string letterLabel,
        ref LetterDef letterDef,
        ref LookTargets lookTargets)
    {
        ChatAdapterPayloads.QueueInteraction(
            nameof(InteractionWorker_KindWords),
            "kind_words",
            "completed",
            initiator,
            recipient,
            letterLabel,
            letterText);
    }
}
