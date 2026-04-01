using Verse;

namespace TerminalKeeper.EventBridge;

public sealed class BridgeController : GameComponent
{
    public BridgeController(Game game)
    {
    }

    public override void GameComponentTick()
    {
        EventDispatcher.Tick();
        CommandPoller.Tick();
    }

    public override void StartedNewGame()
    {
        EventDispatcher.QueueEvent("game_started", "{\"mode\":\"new_game\"}");
    }

    public override void LoadedGame()
    {
        EventDispatcher.QueueEvent("game_started", "{\"mode\":\"loaded_game\"}");
    }
}
