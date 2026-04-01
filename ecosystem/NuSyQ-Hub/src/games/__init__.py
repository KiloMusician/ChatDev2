"""Initialize games module with hacking/progression systems.

Exports core game mechanics, skill tree, faction system, quest templates,
analytics, narrative engine, AI opponents, procedural generation, and all
supporting game subsystems for easy integration with the rest of NuSyQ-Hub.

OmniTag: {
    "purpose": "module_initialization",
    "tags": ["Games", "Import", "Module"],
    "category": "infrastructure",
    "evolution_stage": "v2.0"
}

MegaTag: API⨳EXPORTS⦾COMPREHENSIVE→∞
"""

# ═══════════════════════════════════════════════════════════════════════════════
# ██ ACHIEVEMENTS SYSTEM ████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .achievements import (Achievement, AchievementManager, LeaderboardEntry,
                           LeaderboardManager, UnlockedAchievement,
                           get_achievements, get_leaderboard,
                           unlock_achievement)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ AI & OPPONENTS █████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .ai_opponents import (AIGameMaster, AIOpponent, AIOpponentManager,
                           AIPersonality, AIResponse, Difficulty,
                           get_game_master, get_npc_dialogue)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ ANALYTICS ██████████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .analytics import (GameAnalytics, GameEvent, PlayerAnalytics,
                        SessionMetrics, get_analytics, get_summary)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ CONSCIOUSNESS INTEGRATION ██████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .consciousness_integration import (ConsciousnessGameBridge,
                                        ConsciousnessGameEvent,
                                        ConsciousnessStage, ConsciousnessState,
                                        TempleFloor, award_cp,
                                        get_consciousness_bridge,
                                        get_modifiers, sync_consciousness)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ CYBER TERMINAL █████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .cyber_terminal import (CommandResult, CyberTerminal, TerminalMode,
                             TerminalState, start_terminal)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ DYNAMIC GAME MASTER ████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .dynamic_game_master import (DynamicEvent, DynamicGameMaster, EventType,
                                  GamePhase, GameSession, PlayerProfile)
from .dynamic_game_master import get_game_master as get_dynamic_game_master
# ═══════════════════════════════════════════════════════════════════════════════
# ██ FACTION SYSTEM █████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .faction_system import (AgentFactionMembership, Faction, FactionAlignment,
                             FactionMission, FactionSystem, MissionType,
                             get_faction_system)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ GAME PIPELINE ORCHESTRATION ████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .game_pipeline import (GameEventBus, GameModule, GamePipeline,
                            ModuleStatus, PipelineEvent, get_capability,
                            get_game_module, get_pipeline)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ GAME STATE & PERSISTENCE ███████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .game_state import (FactionStanding, GameState, GameStateManager,
                         PlayerProgress, get_game_manager, load_game,
                         save_game)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ HACKING MECHANICS ██████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .hacking_mechanics import (ExploitResult, ExploitType, HackingController,
                                Port, ScanResult, Trace, TraceStatus,
                                get_hacking_controller)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ HACKING QUESTS █████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .hacking_quests import (HackingQuestTemplate,
                             generate_culture_ship_narrative, get_quest_by_id,
                             get_quest_chain, get_quest_index,
                             get_quests_by_difficulty, get_quests_by_tier,
                             list_all_quests)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ HOUSE OF LEAVES (EXPLORATION) ██████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .house_of_leaves import (Direction, HouseOfLeaves, MazeRoom, PlayerState,
                              RoomType, TempleOfKnowledgeManager)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ MINI-GAMES █████████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .mini_games import GameResult, MiniGameScore, create_game, list_games
# ═══════════════════════════════════════════════════════════════════════════════
# ██ MULTIPLAYER FACTIONS ███████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .multiplayer_factions import (FactionManager, FactionMember, FactionRank,
                                   FactionState, FactionType, RelationType,
                                   Territory, get_faction_manager)
from .multiplayer_factions import get_leaderboard as get_faction_leaderboard
# ═══════════════════════════════════════════════════════════════════════════════
# ██ NARRATIVE ENGINE ███████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .narrative_engine import (NarrativeContext, NarrativeEngine,
                               NarrativeTheme, NarrativeTone)
from .narrative_engine import get_engine as get_narrative_engine
from .narrative_engine import (narrate_achievement, narrate_level_up,
                               narrate_quest_complete, narrate_quest_start)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ PROCEDURAL QUESTS ██████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .procedural_quests import (GeneratedQuest, ProceduralQuestGenerator,
                                QuestTemplate, generate_daily, generate_quest)
from .procedural_quests import get_generator as get_quest_generator
# ═══════════════════════════════════════════════════════════════════════════════
# ██ SKILL TREE █████████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .skill_tree import (RosettaTier, SkillTree, SkillTreeState,
                         UnlockableSkill, get_skill_tree)
# ═══════════════════════════════════════════════════════════════════════════════
# ██ TERMINAL UI ████████████████████████████████████████████████████████████████
# ═══════════════════════════════════════════════════════════════════════════════
from .terminal_ui import TerminalUI, ThemeColors, UITheme, get_ui, show_quest

__all__ = [
    # ════════════════════════════════════════════════════════════════════════════
    # ██ AI & OPPONENTS ██████████████████████████████████████████████████████████
    # ════════════════════════════════════════════════════════════════════════════
    "AIGameMaster",
    "AIOpponent",
    "AIOpponentManager",
    "AIPersonality",
    "AIResponse",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ ACHIEVEMENTS ████████████████████████████████████████████████████████████
    # ════════════════════════════════════════════════════════════════════════════
    "Achievement",
    "AchievementManager",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ FACTION SYSTEM ██████════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "AgentFactionMembership",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ CYBER TERMINAL ██████████████════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "CommandResult",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ CONSCIOUSNESS ███████████████████████████████████████████████████████████
    # ════════════════════════════════════════════════════════════════════════════
    "ConsciousnessGameBridge",
    "ConsciousnessGameEvent",
    "ConsciousnessStage",
    "ConsciousnessState",
    "CyberTerminal",
    "Difficulty",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ HOUSE OF LEAVES (EXPLORATION) ███████════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "Direction",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ DYNAMIC GAME MASTER █████════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "DynamicEvent",
    "DynamicGameMaster",
    "EventType",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ HACKING MECHANICS ███════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "ExploitResult",
    "ExploitType",
    "Faction",
    "FactionAlignment",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ MULTIPLAYER FACTIONS ████════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "FactionManager",
    "FactionMember",
    "FactionMission",
    "FactionRank",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ GAME STATE ██████════════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "FactionStanding",
    "FactionState",
    "FactionSystem",
    "FactionType",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ ANALYTICS ███████████████████████████████████████████████████████████████
    # ════════════════════════════════════════════════════════════════════════════
    "GameAnalytics",
    "GameEvent",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ GAME PIPELINE ███████════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "GameEventBus",
    "GameModule",
    "GamePhase",
    "GamePipeline",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ MINI-GAMES ██████════════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "GameResult",
    "GameSession",
    "GameState",
    "GameStateManager",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ PROCEDURAL QUESTS ███════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "GeneratedQuest",
    "HackingController",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ HACKING QUESTS ██████════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "HackingQuestTemplate",
    "HouseOfLeaves",
    "LeaderboardEntry",
    "LeaderboardManager",
    "MazeRoom",
    "MiniGameScore",
    "MissionType",
    "ModuleStatus",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ NARRATIVE ENGINE ████════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "NarrativeContext",
    "NarrativeEngine",
    "NarrativeTheme",
    "NarrativeTone",
    "PipelineEvent",
    "PlayerAnalytics",
    "PlayerProfile",
    "PlayerProgress",
    "PlayerState",
    "Port",
    "ProceduralQuestGenerator",
    "QuestTemplate",
    "RelationType",
    "RoomType",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ SKILL TREE ██████════════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "RosettaTier",
    "ScanResult",
    "SessionMetrics",
    "SkillTree",
    "SkillTreeState",
    "TempleFloor",
    "TempleOfKnowledgeManager",
    "TerminalMode",
    "TerminalState",
    # ════════════════════════════════════════════════════════════════════════════
    # ██ TERMINAL UI █████════════════════════════════════════════════════════════
    # ════════════════════════════════════════════════════════════════════════════
    "TerminalUI",
    "Territory",
    "ThemeColors",
    "Trace",
    "TraceStatus",
    "UITheme",
    "UnlockableSkill",
    "UnlockedAchievement",
    "award_cp",
    "create_game",
    "generate_culture_ship_narrative",
    "generate_daily",
    "generate_quest",
    "get_achievements",
    "get_analytics",
    "get_capability",
    "get_consciousness_bridge",
    "get_dynamic_game_master",
    "get_faction_leaderboard",
    "get_faction_manager",
    "get_faction_system",
    "get_game_manager",
    "get_game_master",
    "get_game_module",
    "get_hacking_controller",
    "get_leaderboard",
    "get_modifiers",
    "get_narrative_engine",
    "get_npc_dialogue",
    "get_pipeline",
    "get_quest_by_id",
    "get_quest_chain",
    "get_quest_generator",
    "get_quest_index",
    "get_quests_by_difficulty",
    "get_quests_by_tier",
    "get_skill_tree",
    "get_summary",
    "get_ui",
    "list_all_quests",
    "list_games",
    "load_game",
    "narrate_achievement",
    "narrate_level_up",
    "narrate_quest_complete",
    "narrate_quest_start",
    "save_game",
    "show_quest",
    "start_terminal",
    "sync_consciousness",
    "unlock_achievement",
]
