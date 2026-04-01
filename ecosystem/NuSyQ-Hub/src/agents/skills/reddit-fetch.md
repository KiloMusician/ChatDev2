---
name: reddit-fetch
description:
  Fetch content from Reddit via a CLI fallback when WebFetch is blocked. Adapted
  from claude-code-tips.
---

# Reddit Fetch (NuSyQ skill)

When WebFetch fails to access Reddit (blocked/403), use a CLI fallback (e.g.,
Gemini CLI) via tmux.

Usage (example):

```bash
tmux new-session -d -s gemini_fetch -x 200 -y 50
tmux send-keys -t gemini_fetch 'gemini' Enter
sleep 3
tmux send-keys -t gemini_fetch 'search reddit for "<query>"' Enter
sleep 20
tmux capture-pane -t gemini_fetch -p -S -500 > /tmp/reddit_output.txt
tmux kill-session -t gemini_fetch
```

Notes:

- Pick a unique session name and reuse it.
- Adjust waits based on model latency.
