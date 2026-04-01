using System;
using System.Reflection;
using HarmonyLib;
using RimWorld;
using Verse;

namespace DeepTalk
{
    /// <summary>
    /// Main mod class - initializes DeepTalk on game load.
    /// </summary>
    public class DeepTalkMod : Mod
    {
        public static DeepTalkSettings Settings;

        public DeepTalkMod(ModContentPack content) : base(content)
        {
            Settings = GetSettings<DeepTalkSettings>();

            // Apply Harmony patches
            var harmony = new Harmony("nusyq.deeptalk");
            harmony.PatchAll(Assembly.GetExecutingAssembly());

            Log.Message("[DeepTalk] Initialized! Colonists can now have deeper conversations.");
            Log.Message($"[DeepTalk] Ollama endpoint: {Settings.OllamaEndpoint}");
        }

        public override string SettingsCategory() => "DeepTalk";

        public override void DoSettingsWindowContents(UnityEngine.Rect inRect)
        {
            var listing = new Listing_Standard();
            listing.Begin(inRect);

            listing.Label("Ollama Endpoint:");
            Settings.OllamaEndpoint = listing.TextEntry(Settings.OllamaEndpoint);

            listing.Label("Model Name:");
            Settings.ModelName = listing.TextEntry(Settings.ModelName);

            listing.CheckboxLabeled("Enable Deep Conversations", ref Settings.EnableDeepConversations);
            listing.CheckboxLabeled("Show AI Responses in Log", ref Settings.DebugMode);

            listing.End();
        }
    }

    /// <summary>
    /// Mod settings persisted between sessions.
    /// </summary>
    public class DeepTalkSettings : ModSettings
    {
        public string OllamaEndpoint = "http://localhost:11434";
        public string ModelName = "phi3.5:latest";
        public bool EnableDeepConversations = true;
        public bool DebugMode = false;

        public override void ExposeData()
        {
            Scribe_Values.Look(ref OllamaEndpoint, "OllamaEndpoint", "http://localhost:11434");
            Scribe_Values.Look(ref ModelName, "ModelName", "phi3.5:latest");
            Scribe_Values.Look(ref EnableDeepConversations, "EnableDeepConversations", true);
            Scribe_Values.Look(ref DebugMode, "DebugMode", false);
            base.ExposeData();
        }
    }
}
