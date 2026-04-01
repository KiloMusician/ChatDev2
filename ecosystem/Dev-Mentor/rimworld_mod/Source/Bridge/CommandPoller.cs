using System;
using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Threading;
using RimWorld;
using Verse;

namespace TerminalKeeper.EventBridge;

internal static class CommandPoller
{
    private static readonly ConcurrentQueue<string> Incoming = new();
    private static volatile bool _polling;
    private static int _lastPollTick;

    public static void Tick()
    {
        DrainIncoming();

        var ticks = Find.TickManager?.TicksGame ?? 0;
        if (_polling || ticks - _lastPollTick < BridgeSettings.CommandPollIntervalTicks)
        {
            return;
        }

        _lastPollTick = ticks;
        _polling = true;

        ThreadPool.QueueUserWorkItem(_ =>
        {
            try
            {
                var command = FetchNextCommand();
                if (!string.IsNullOrWhiteSpace(command))
                {
                    Incoming.Enqueue(command);
                }
            }
            catch (Exception ex)
            {
                Log.Warning($"[TKEB] Command poll failed: {ex.Message}");
            }
            finally
            {
                _polling = false;
            }
        });
    }

    private static void DrainIncoming()
    {
        while (Incoming.TryDequeue(out var command))
        {
            Messages.Message($"[TKEB] Command received: {command}", MessageTypeDefOf.NeutralEvent, false);
            EventDispatcher.QueueEvent("command_received",
                $"{{\"command\":\"{BridgeJson.Escape(command)}\"}}");
        }
    }

    private static string? FetchNextCommand()
    {
        var request = (HttpWebRequest)WebRequest.Create(BridgeSettings.ServerBaseUrl.TrimEnd('/') + "/api/commands/next");
        request.Method = "GET";
        request.Timeout = 2000;

        try
        {
            using var response = (HttpWebResponse)request.GetResponse();
            if (response.StatusCode != HttpStatusCode.OK)
            {
                return null;
            }

            using var reader = new StreamReader(response.GetResponseStream() ?? Stream.Null);
            return reader.ReadToEnd();
        }
        catch (WebException ex) when (ex.Response is HttpWebResponse httpResponse &&
                                      httpResponse.StatusCode == HttpStatusCode.NoContent)
        {
            return null;
        }
    }
}
