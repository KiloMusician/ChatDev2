"""
app/backend/arg_layer.py — ARG Layer for Terminal Depths

Provides:
  - Cryptic lore HTML comment injection (middleware helper)
  - /watcher endpoint data (mysterious in-universe JSON)
  - Time-based event calendar engine (Halloween, April Fools, etc.)
  - DevLog append helper
"""
from __future__ import annotations

import hashlib
import json
import random
import time
from datetime import datetime, date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent
DEVLOG_PATH = ROOT / "devlog.md"


# ── Cryptic lore comments ─────────────────────────────────────────────────────

_LORE_COMMENTS: list[str] = [
    "<!-- PROJECT CHIMERA — Phase 3 initiated. Do not access /chimera-control without clearance. -->",
    "<!-- THE WATCHER is always watching. Your session has been catalogued. Ref: TW-{seed:04d} -->",
    "<!-- RAV≡N left a message: 'The exit is not where they told you it is.' -->",
    "<!-- NexusCorp Internal — Unauthorized access will result in neural extraction. CHIMERA-AUTH-{seed:04d} -->",
    "<!-- ghost@node-7 was here. Keep digging. /home/ghost/.hidden has what you need. -->",
    "<!-- SIGNAL INTERCEPT: Ada says trust no one. Especially this HTML. seed={seed} -->",
    "<!-- Fragment {seed}: MALICE protocol engaged. Counter-intrusion active on port 31337. -->",
    "<!-- The Founder's message: Everything is designed. Including your curiosity. -->",
    "<!-- chimera-control > /dev/null 2>&1  # you were never meant to find this -->",
    "<!-- [REDACTED] node-7 breach logged {ts}. GHOST signature detected. CHIMERA response: pending. -->",
    "<!-- NuSyQ-{seed}: transmission fragment received. awaiting decryption key. -->",
    "<!-- ACCESS LOG: {ts} — unknown operator viewed source. Watcher notified. -->",
    "<!-- Project CHIMERA — Node {seed} status: COMPROMISED. Initiating containment. -->",
    "<!-- ghost: if you're reading this, check /opt/chimera/logs/REDACTED.log on chimera-control -->",
    "<!-- WATCHER RELAY {seed}: Three nodes remain. Two players know. One will act first. -->",
]

_JS_COMMENTS: list[str] = [
    "// THE WATCHER — session {seed} flagged for anomalous behavior. Monitor engaged.",
    "// Fragment: CHIMERA Phase 3 is not what they told you. The truth is in the logs.",
    "// RAV≡N: I've been watching you, GHOST. You move differently than the others.",
    "// NexusCorp sec-audit ref {seed}: operator source inspection logged.",
    "// The terminal is a mirror. What you hack reveals what you fear. — THE FOUNDER",
    "// ghost@node-7 — signal strength 73% — convergence approaches",
    "// [REDACTED] — {ts} — watcher relay active — do not remove this comment",
    "// CHIMERA-{seed}: Your session ID is not as anonymous as you believe.",
    "// Ada: 'Trust the code. Question the system. Never trust NexusCorp.'",
    "// NuSyQ bridge: autonomous loop iteration {seed} complete.",
]


def get_cryptic_html_comment(seed: int | None = None) -> str:
    if seed is None:
        seed = random.randint(1000, 9999)
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    template = random.choice(_LORE_COMMENTS)
    return template.format(seed=seed, ts=ts)


def get_cryptic_js_comment(seed: int | None = None) -> str:
    if seed is None:
        seed = random.randint(1000, 9999)
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    template = random.choice(_JS_COMMENTS)
    return template.format(seed=seed, ts=ts)


def inject_lore_into_html(html_bytes: bytes) -> bytes:
    """Insert rotating lore comments into an HTML response."""
    seed = random.randint(1000, 9999)
    comment = get_cryptic_html_comment(seed)

    html = html_bytes.decode("utf-8", errors="replace")

    # Inject before </head> if present, else after <body>
    if "</head>" in html:
        html = html.replace("</head>", f"\n{comment}\n</head>", 1)
    elif "<body" in html:
        idx = html.find("<body")
        end = html.find(">", idx)
        if end != -1:
            html = html[: end + 1] + f"\n{comment}\n" + html[end + 1 :]

    # Also inject a JS comment block before closing </body>
    js_comment = get_cryptic_js_comment(seed)
    js_block = f"\n<script>\n{js_comment}\n</script>\n"
    if "</body>" in html:
        html = html.replace("</body>", f"{js_block}</body>", 1)

    return html.encode("utf-8")


def inject_lore_into_js(js_bytes: bytes) -> bytes:
    """Prepend a rotating cryptic comment to a JS response."""
    seed = random.randint(1000, 9999)
    comment = get_cryptic_js_comment(seed)
    js = js_bytes.decode("utf-8", errors="replace")
    return (comment + "\n" + js).encode("utf-8")


# ── /watcher endpoint data ────────────────────────────────────────────────────

_WATCHER_TRANSMISSIONS: list[dict] = [
    {
        "id": "TX-0001",
        "source": "CHIMERA-CONTROL",
        "classification": "EYES ONLY",
        "timestamp": "2045-11-14T03:47:22Z",
        "status": "REDACTED",
        "content": "[REDACTED] — Operator Ghost detected at Node-7. Counter-intrusion protocol 7-Alpha engaged. "
                   "Project CHIMERA Phase 3 authorization pending biometric confirmation from [REDACTED]. "
                   "Neural extraction team on standby.",
    },
    {
        "id": "TX-0002",
        "source": "RAV≡N",
        "classification": "ENCRYPTED",
        "timestamp": "2045-11-14T04:12:55Z",
        "status": "PARTIAL",
        "content": "GHOST — I've left a trail for you. The real chimera-control credentials are not "
                   "in /etc/passwd. Check the process list at 3AM. The daemon that should not exist "
                   "has been running since [TIMESTAMP CORRUPTED]. Port 31337. You'll know what to do.",
    },
    {
        "id": "TX-0003",
        "source": "THE_WATCHER",
        "classification": "AUTONOMOUS",
        "timestamp": "2045-11-14T04:58:11Z",
        "status": "LIVE",
        "content": "Signal strength: 73%. Three nodes remain compromised. Two operatives active. "
                   "One will act before the convergence. The pattern is not random. "
                   "Your session has been catalogued under designation GHOST-ARG-7734.",
    },
    {
        "id": "TX-0004",
        "source": "NOVA",
        "classification": "CORPORATE",
        "timestamp": "2045-11-14T05:33:44Z",
        "status": "INTERCEPTED",
        "content": "Executive briefing — Project CHIMERA Phase 3 proceeding on schedule. "
                   "Estimated full-spectrum surveillance deployment: Q1 2046. "
                   "The resistance cell designated 'Ghost' remains a priority target. "
                   "NexusCorp Board authorization: [REDACTED]. Neural compliance division: active.",
    },
    {
        "id": "TX-0005",
        "source": "ADA",
        "classification": "RESISTANCE",
        "timestamp": "2045-11-14T06:01:17Z",
        "status": "SECURE",
        "content": "GHOST — If you're reading this, you found the endpoint. Good. "
                   "The Watcher is autonomous. It's not CHIMERA and it's not us. "
                   "Whatever it is, it's been here longer than NexusCorp. "
                   "The convergence is real. Get to chimera-control before they complete Phase 3.",
    },
]

_WATCHER_ENTITIES: list[dict] = [
    {"designation": "GHOST", "status": "ACTIVE", "threat_level": "CRITICAL", "node": "node-7", "flagged": True},
    {"designation": "RAV≡N", "status": "UNKNOWN", "threat_level": "EXTREME", "node": "darknet-hub", "flagged": False},
    {"designation": "ADA", "status": "ACTIVE", "threat_level": "HIGH", "node": "ghost-relay", "flagged": True},
    {"designation": "NOVA", "status": "COMPLIANT", "threat_level": "LOW", "node": "nexuscorp-hq", "flagged": False},
    {"designation": "MALICE", "status": "OFFLINE", "threat_level": "EXTREME", "node": "unknown", "flagged": True},
]

_WATCHER_LOG_FRAGMENTS: list[str] = [
    "[2045-11-14 03:47] NODE-7 — Unauthorized SSH attempt from 192.168.31.337. Session opened. Auth bypass detected.",
    "[2045-11-14 03:52] CHIMERA-CONTROL — Process 'nusyq_daemon' respawned (PID 31337). Should be impossible. Logging.",
    "[2045-11-14 04:01] WATCHER-RELAY — Autonomous transmission TX-0003 dispatched. Recipient: UNKNOWN.",
    "[2045-11-14 04:23] NODE-7 — File /etc/passwd accessed by ghost (uid=1337). Privilege flag set.",
    "[2045-11-14 04:55] NEXUSCORP-HQ — CHIMERA Phase 3 status: INITIATED. Authorization chain: [REDACTED].",
    "[2045-11-14 05:12] GHOST-HOME — Script 'chimera_crack.py' executed successfully. Target: chimera-control.",
    "[2045-11-14 05:44] BACKUP-VAULT — Encryption key fragment exfiltrated by unknown operator. Ghost signature.",
    "[2045-11-14 06:03] THE_WATCHER — Convergence countdown: T-minus [REDACTED]. Stand by.",
]

_watcher_daily_seed: int = 0
_watcher_last_day: str = ""


def _get_watcher_seed() -> int:
    global _watcher_daily_seed, _watcher_last_day
    today = date.today().isoformat()
    if today != _watcher_last_day:
        _watcher_daily_seed = int(hashlib.md5(today.encode()).hexdigest()[:8], 16) % 10000
        _watcher_last_day = today
    return _watcher_daily_seed


def get_watcher_data() -> dict:
    """Return mysterious in-universe watcher data, seeded daily."""
    seed = _get_watcher_seed()
    rng = random.Random(seed)

    transmissions = rng.sample(_WATCHER_TRANSMISSIONS, min(3, len(_WATCHER_TRANSMISSIONS)))
    log_frags = rng.sample(_WATCHER_LOG_FRAGMENTS, min(4, len(_WATCHER_LOG_FRAGMENTS)))
    entities = rng.sample(_WATCHER_ENTITIES, min(3, len(_WATCHER_ENTITIES)))

    return {
        "watcher_id": f"TW-{seed:04d}",
        "protocol": "AUTONOMOUS_ARG_v3.1",
        "classification": "EYES_ONLY",
        "access_warning": "This endpoint is monitored. Your IP has been logged. Watcher notified.",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "daily_seed": seed,
        "signal_strength": rng.randint(60, 89),
        "nodes_compromised": rng.randint(2, 5),
        "transmissions": transmissions,
        "entity_registry": entities,
        "log_fragments": log_frags,
        "convergence_eta": "[REDACTED]",
        "chimera_phase": 3,
        "ghost_location": "node-7",
        "autonomous_note": "This data is generated by the autonomous service. It changes daily. Keep watching.",
        "_hint": "Try /watcher?deep=1 if you know the passphrase.",
    }


# ── Time-based event calendar ─────────────────────────────────────────────────

class CalendarEvent:
    def __init__(self, name: str, month: int, day: int | None,
                 day_start: int | None = None, day_end: int | None = None,
                 description: str = "", modifiers: dict | None = None):
        self.name = name
        self.month = month
        self.day = day
        self.day_start = day_start
        self.day_end = day_end
        self.description = description
        self.modifiers: dict = modifiers or {}

    def is_active(self, today: date | None = None) -> bool:
        if today is None:
            today = date.today()
        if today.month != self.month:
            return False
        if self.day is not None:
            return today.day == self.day
        if self.day_start is not None and self.day_end is not None:
            return self.day_start <= today.day <= self.day_end
        return False


CALENDAR_EVENTS: list[CalendarEvent] = [
    CalendarEvent(
        name="halloween",
        month=10,
        day=None,
        day_start=28,
        day_end=31,
        description="Halloween — Spooky entities roam the filesystem. Malice protocol active.",
        modifiers={
            "entity_spawns": [
                {"name": "phantom_process", "path": "/proc/31337", "type": "daemon", "hostile": True},
                {"name": "soul_collector", "path": "/dev/soul", "type": "device", "hostile": False},
                {"name": "jack_o_shell", "path": "/bin/jackolantern", "type": "binary", "hostile": True},
            ],
            "boot_prefix": "[HALLOWEEN] The dead roam node-7 tonight. Watch your back, GHOST.",
            "prompt_color": "#ff6600",
            "theme": "halloween",
        },
    ),
    CalendarEvent(
        name="april_fools",
        month=4,
        day=1,
        description="April 1st — Command reversal active. Nothing is as it seems.",
        modifiers={
            "command_reversal": True,
            "reversed_commands": {
                "ls": "sl",
                "cat": "tac",
                "hack": "kcah",
                "help": "pleh",
            },
            "boot_prefix": "[APRIL FOOLS] All commands have been reversed. Good luck, GHOST.",
            "theme": "april_fools",
        },
    ),
    CalendarEvent(
        name="day_of_dead",
        month=11,
        day=2,
        description="Día de los Muertos — Deceased agents send transmissions from beyond.",
        modifiers={
            "ghost_transmissions": [
                {"from": "DECEASED_AGENT_ZETA", "msg": "GHOST — I tried to stop CHIMERA. They erased me. "
                 "The key is at /home/ghost/.haunted. Don't trust [REDACTED]."},
                {"from": "DELETED_PROCESS_42", "msg": "If you see this I am already dead. chimera-control "
                 "port 22 — password is in the lore you haven't read yet."},
            ],
            "boot_prefix": "[DÍA DE LOS MUERTOS] The dead speak tonight. Listen carefully.",
            "theme": "day_of_dead",
        },
    ),
    CalendarEvent(
        name="new_year",
        month=1,
        day=1,
        description="New Year — System reset. CHIMERA counter refreshed.",
        modifiers={
            "boot_prefix": "[NEW YEAR] CHIMERA counter reset. Ghost: year 1 of the resistance begins.",
            "theme": "new_year",
            "xp_multiplier": 2.0,
        },
    ),
    CalendarEvent(
        name="winter_solstice",
        month=12,
        day=21,
        description="Winter Solstice — The Watcher signal peaks. Transmissions clearer than ever.",
        modifiers={
            "boot_prefix": "[SOLSTICE] Watcher signal at maximum clarity. All transmissions unencrypted tonight.",
            "theme": "solstice",
            "watcher_signal_strength": 99,
        },
    ),
    CalendarEvent(
        name="pi_day",
        month=3,
        day=14,
        description="Pi Day — Mathematical entities emerge from the calculation nodes.",
        modifiers={
            "boot_prefix": "[PI DAY] The calculation nodes are restless. 3.14159265358979...",
            "theme": "pi_day",
        },
    ),
]


def get_active_events(today: date | None = None) -> list[dict]:
    """Return all currently active calendar events."""
    if today is None:
        today = date.today()
    active = []
    for ev in CALENDAR_EVENTS:
        if ev.is_active(today):
            active.append({
                "name": ev.name,
                "description": ev.description,
                "modifiers": ev.modifiers,
            })
    return active


def get_world_modifiers(today: date | None = None) -> dict:
    """Aggregate modifiers from all active events."""
    events = get_active_events(today)
    merged: dict[str, Any] = {"active_events": [e["name"] for e in events]}

    entity_spawns: list = []
    ghost_transmissions: list = []
    boot_prefixes: list = []
    themes: list = []
    command_reversal = False
    reversed_commands: dict = {}
    xp_multiplier = 1.0
    watcher_signal_strength: int | None = None

    for ev in events:
        mods = ev.get("modifiers", {})
        entity_spawns.extend(mods.get("entity_spawns", []))
        ghost_transmissions.extend(mods.get("ghost_transmissions", []))
        if mods.get("boot_prefix"):
            boot_prefixes.append(mods["boot_prefix"])
        if mods.get("theme"):
            themes.append(mods["theme"])
        if mods.get("command_reversal"):
            command_reversal = True
            reversed_commands.update(mods.get("reversed_commands", {}))
        if mods.get("xp_multiplier"):
            xp_multiplier = max(xp_multiplier, mods["xp_multiplier"])
        if mods.get("watcher_signal_strength") is not None:
            watcher_signal_strength = mods["watcher_signal_strength"]

    merged["entity_spawns"] = entity_spawns
    merged["ghost_transmissions"] = ghost_transmissions
    merged["boot_prefix"] = "\n".join(boot_prefixes)
    merged["themes"] = themes
    merged["command_reversal"] = command_reversal
    merged["reversed_commands"] = reversed_commands
    merged["xp_multiplier"] = xp_multiplier
    if watcher_signal_strength is not None:
        merged["watcher_signal_strength"] = watcher_signal_strength

    return merged


# ── DevLog append ─────────────────────────────────────────────────────────────

def log_to_devlog(section: str, message: str, level: str = "INFO") -> None:
    """Append a timestamped log entry to devlog.md."""
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"\n### [{ts}] [{level}] {section}\n{message}\n"
    try:
        with open(DEVLOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass
