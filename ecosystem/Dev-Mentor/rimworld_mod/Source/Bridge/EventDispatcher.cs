using System;
using System.Collections.Concurrent;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using Verse;

namespace TerminalKeeper.EventBridge;

internal static class EventDispatcher
{
    private static readonly ConcurrentQueue<string> Pending = new();
    private static volatile bool _sending;
    private static int _lastFlushTick;

    public static void QueueEvent(string eventType, string payloadJson)
    {
        var ticks = Find.TickManager?.TicksGame ?? 0;
        var body = $"{{\"eventType\":\"{BridgeJson.Escape(eventType)}\",\"ticks\":\"{ticks}\",\"payload\":{payloadJson}}}";
        Pending.Enqueue(body);
    }

    public static void Tick()
    {
        var ticks = Find.TickManager?.TicksGame ?? 0;
        if (_sending || Pending.IsEmpty)
        {
            return;
        }

        if (ticks - _lastFlushTick < BridgeSettings.EventFlushIntervalTicks)
        {
            return;
        }

        _lastFlushTick = ticks;

        if (!Pending.TryDequeue(out var body))
        {
            return;
        }

        _sending = true;
        ThreadPool.QueueUserWorkItem(_ =>
        {
            try
            {
                PostJson("/api/events", body);
            }
            catch (Exception ex)
            {
                Log.Warning($"[TKEB] Event post failed: {ex.Message}");
                Pending.Enqueue(body);
            }
            finally
            {
                _sending = false;
            }
        });
    }

    private static void PostJson(string path, string body)
    {
        var request = (HttpWebRequest)WebRequest.Create(BridgeSettings.ServerBaseUrl.TrimEnd('/') + path);
        request.Method = "POST";
        request.ContentType = "application/json";
        request.Timeout = 2000;

        var bytes = Encoding.UTF8.GetBytes(body);
        request.ContentLength = bytes.Length;

        using (var stream = request.GetRequestStream())
        {
            stream.Write(bytes, 0, bytes.Length);
        }

        using var response = (HttpWebResponse)request.GetResponse();
        using var reader = new StreamReader(response.GetResponseStream() ?? Stream.Null);
        _ = reader.ReadToEnd();
    }
}
