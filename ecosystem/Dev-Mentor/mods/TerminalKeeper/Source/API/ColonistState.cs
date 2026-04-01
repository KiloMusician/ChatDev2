using Newtonsoft.Json;
using RimWorld;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Snapshot of a colonist's RimWorld state serialised for the Terminal Depths API.
    /// </summary>
    public class ColonistState
    {
        [JsonProperty("agent_id")]       public string AgentId     { get; set; } = "";
        [JsonProperty("name")]           public string Name        { get; set; } = "";
        [JsonProperty("source")]         public string Source      => "rimworld";

        // Bio
        [JsonProperty("age")]            public float  Age         { get; set; }
        [JsonProperty("gender")]         public string Gender      { get; set; } = "";
        [JsonProperty("health")]         public float  Health      { get; set; }
        [JsonProperty("mood")]           public float  Mood        { get; set; }

        // Skills (subset)
        [JsonProperty("skill_shooting")]     public int SkillShooting    { get; set; }
        [JsonProperty("skill_melee")]        public int SkillMelee       { get; set; }
        [JsonProperty("skill_construction")] public int SkillConstruction{ get; set; }
        [JsonProperty("skill_cooking")]      public int SkillCooking     { get; set; }
        [JsonProperty("skill_plants")]       public int SkillPlants      { get; set; }
        [JsonProperty("skill_animals")]      public int SkillAnimals     { get; set; }
        [JsonProperty("skill_crafting")]     public int SkillCrafting    { get; set; }
        [JsonProperty("skill_art")]          public int SkillArt         { get; set; }
        [JsonProperty("skill_medicine")]     public int SkillMedicine    { get; set; }
        [JsonProperty("skill_social")]       public int SkillSocial      { get; set; }
        [JsonProperty("skill_intellectual")] public int SkillIntellectual{ get; set; }
        [JsonProperty("skill_mining")]       public int SkillMining      { get; set; }

        // Work state
        [JsonProperty("current_job")]    public string? CurrentJob   { get; set; }
        [JsonProperty("is_downed")]      public bool   IsDowned      { get; set; }
        [JsonProperty("is_mental_state")]public bool   IsMentalState { get; set; }

        // Colony
        [JsonProperty("colony_wealth")]  public float  ColonyWealth  { get; set; }
        [JsonProperty("colonist_count")] public int    ColonistCount { get; set; }
        [JsonProperty("tick")]           public int    Tick          { get; set; }

        /// <summary>Build a state snapshot from a live pawn.</summary>
        public static ColonistState From(Pawn pawn, string agentId)
        {
            int Skill(SkillDef def) => pawn.skills?.GetSkill(def)?.Level ?? 0;

            return new ColonistState
            {
                AgentId          = agentId,
                Name             = pawn.Name?.ToStringShort ?? "Unknown",
                Age              = pawn.ageTracker?.AgeBiologicalYearsFloat ?? 0f,
                Gender           = pawn.gender.ToString(),
                Health           = pawn.health?.summaryHealth?.SummaryHealthPercent ?? 0f,
                Mood             = pawn.needs?.mood?.CurLevelPercentage ?? 0f,
                SkillShooting    = Skill(SkillDefOf.Shooting),
                SkillMelee       = Skill(SkillDefOf.Melee),
                SkillConstruction= Skill(SkillDefOf.Construction),
                SkillCooking     = Skill(SkillDefOf.Cooking),
                SkillPlants      = Skill(SkillDefOf.Plants),
                SkillAnimals     = Skill(SkillDefOf.Animals),
                SkillCrafting    = Skill(SkillDefOf.Crafting),
                SkillArt         = Skill(SkillDefOf.Artistic),
                SkillMedicine    = Skill(SkillDefOf.Medicine),
                SkillSocial      = Skill(SkillDefOf.Social),
                SkillIntellectual= Skill(SkillDefOf.Intellectual),
                SkillMining      = Skill(SkillDefOf.Mining),
                CurrentJob       = pawn.CurJobDef?.label,
                IsDowned         = pawn.Downed,
                IsMentalState    = pawn.InMentalState,
                ColonyWealth     = pawn.Map?.wealthWatcher?.WealthTotal ?? 0f,
                ColonistCount    = pawn.Map?.mapPawns?.FreeColonistsCount ?? 0,
                Tick             = Find.TickManager.TicksGame,
            };
        }
    }
}
