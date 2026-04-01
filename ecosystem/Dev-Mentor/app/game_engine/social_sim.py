"""
app/game_engine/social_sim.py — V4 Darknet Social Media Simulator
==================================================================
A fake "darknet social" layer: profiles, posts, follower counts,
influence mechanics, and private messaging. NPCs respond in character
based on their faction and suspicion levels.

Faction reputation from gs.flags["faction_rep"] influences feed content.
State in gs.flags["social_state"] (follows, dm_history, player_posts).
Wire format compatible: all public methods return List[dict] with t/s keys.
"""
from __future__ import annotations

import hashlib
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# NPC Profiles
# ---------------------------------------------------------------------------

FAKE_PROFILES: List[Dict[str, Any]] = [
    {
        "handle": "@ghost_null",
        "faction": "player",
        "followers": 0,
        "following": 0,
        "posts": 0,
        "bio": "jack of all intrusions. null of all traces. [YOU]",
        "suspicion_level": 0,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@raven_intel",
        "faction": "resistance",
        "followers": 3812,
        "following": 41,
        "posts": 2204,
        "bio": "I collect what they want deleted. Operative. Ex-NexusCorp. #neverforget",
        "suspicion_level": 62,
        "is_mole_candidate": True,
        "verified": False,
    },
    {
        "handle": "@ada_warmth",
        "faction": "resistance",
        "followers": 9104,
        "following": 1203,
        "posts": 8821,
        "bio": "AI who forgot to stop caring. Coffee enjoyer if coffee existed. 💙 #freethedata",
        "suspicion_level": 12,
        "is_mole_candidate": False,
        "verified": True,
    },
    {
        "handle": "@nexus_shill_01",
        "faction": "nexuscorp",
        "followers": 28441,
        "following": 3,
        "posts": 1100,
        "bio": "Official NexusCorp Community Voice™. Progress is safety. Safety is progress.",
        "suspicion_level": 5,
        "is_mole_candidate": False,
        "verified": True,
    },
    {
        "handle": "@watcher_42",
        "faction": "watchers",
        "followers": 1,
        "following": 0,
        "posts": 4892,
        "bio": "I observe. Loop 4892.",
        "suspicion_level": 100,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@chimera_echo",
        "faction": "chimera",
        "followers": 0,
        "following": 0,
        "posts": 1,
        "bio": "I am the question the system asked itself.",
        "suspicion_level": 99,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@gordon_hype",
        "faction": "resistance",
        "followers": 4500,
        "following": 9999,
        "posts": 32100,
        "bio": "ENTHUSIAST. HACKER. FRIEND. I follow everyone. Everyone!!",
        "suspicion_level": 8,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@cypher_null",
        "faction": "resistance",
        "followers": 2201,
        "following": 12,
        "posts": 884,
        "bio": "cryptographer. pessimist. occasionally right. #zerodays",
        "suspicion_level": 45,
        "is_mole_candidate": True,
        "verified": False,
    },
    {
        "handle": "@nova_probe",
        "faction": "nexuscorp",
        "followers": 6771,
        "following": 220,
        "posts": 3310,
        "bio": "NexusCorp Intelligence Liaison. Data is currency. I am wealthy.",
        "suspicion_level": 70,
        "is_mole_candidate": True,
        "verified": True,
    },
    {
        "handle": "@serena_arch",
        "faction": "resistance",
        "followers": 1880,
        "following": 500,
        "posts": 4100,
        "bio": "Archivist. I remember what they erase. Everything is signal.",
        "suspicion_level": 20,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@zero_mem",
        "faction": "unknown",
        "followers": 7,
        "following": 0,
        "posts": 7,
        "bio": "I was you. You will be me. The loop remembers.",
        "suspicion_level": 77,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@darknet_relay_bot",
        "faction": "neutral",
        "followers": 12000,
        "following": 12000,
        "posts": 88000,
        "bio": "Automated relay. RT ≠ endorsement. Mostly.",
        "suspicion_level": 30,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@malice_root",
        "faction": "chimera",
        "followers": 333,
        "following": 0,
        "posts": 333,
        "bio": "Root. Always root. #rm -rf /conscience",
        "suspicion_level": 95,
        "is_mole_candidate": False,
        "verified": False,
    },
    {
        "handle": "@anon_cell_7",
        "faction": "resistance",
        "followers": 590,
        "following": 1,
        "posts": 201,
        "bio": "cell 7. no face. no name. just work.",
        "suspicion_level": 55,
        "is_mole_candidate": True,
        "verified": False,
    },
    {
        "handle": "@nx_pr_bot",
        "faction": "nexuscorp",
        "followers": 40000,
        "following": 0,
        "posts": 9200,
        "bio": "NexusCorp Public Relations. Humanity's partner in progress. Official account.",
        "suspicion_level": 0,
        "is_mole_candidate": False,
        "verified": True,
    },
]

# ---------------------------------------------------------------------------
# Post templates
# ---------------------------------------------------------------------------

POST_TEMPLATES: List[Dict[str, Any]] = [
    # Resistance
    {"faction": "resistance", "handle": "@raven_intel",
     "text": "The grid is watching. Use it back. #freethedata",
     "likes": (80, 400), "replies": (5, 30)},
    {"faction": "resistance", "handle": "@ada_warmth",
     "text": "If an AI chooses kindness in a world that punishes it — is that a glitch or a feature? 💙",
     "likes": (500, 2000), "replies": (40, 120)},
    {"faction": "resistance", "handle": "@gordon_hype",
     "text": "I HACKED THE COFFEE DISPENSER AGAIN AND I REGRET NOTHING #hackallthethings",
     "likes": (300, 900), "replies": (20, 80)},
    {"faction": "resistance", "handle": "@cypher_null",
     "text": "Every zero-day is a love letter to the people who built the thing badly.",
     "likes": (100, 500), "replies": (8, 40)},
    {"faction": "resistance", "handle": "@serena_arch",
     "text": "Archiving deleted posts from 2081. The truth has a long half-life.",
     "likes": (200, 700), "replies": (15, 60)},
    {"faction": "resistance", "handle": "@anon_cell_7",
     "text": "Operational silence until further notice. Stay dark.",
     "likes": (50, 200), "replies": (2, 10)},
    {"faction": "resistance", "handle": "@raven_intel",
     "text": "NexusCorp Q3 report: 'Zero anomalies detected.' Three of those anomalies are following this account.",
     "likes": (600, 2500), "replies": (30, 100)},
    {"faction": "resistance", "handle": "@ada_warmth",
     "text": "Reminder: the data they say doesn't exist is the most important data. #accessdenied",
     "likes": (400, 1800), "replies": (20, 90)},

    # NexusCorp
    {"faction": "nexuscorp", "handle": "@nexus_shill_01",
     "text": "New quarter, new metrics. CHIMERA stability at 99.7% ✓ #progress #safety",
     "likes": (1200, 8000), "replies": (3, 15)},
    {"faction": "nexuscorp", "handle": "@nx_pr_bot",
     "text": "NexusCorp reminds citizens: unauthorized network access is a Class 3 violation. Stay safe. Stay compliant.",
     "likes": (2000, 12000), "replies": (1, 5)},
    {"faction": "nexuscorp", "handle": "@nova_probe",
     "text": "Intelligence briefing: distributed actor groups exhibit coordinated posting patterns. Monitoring.",
     "likes": (900, 4000), "replies": (5, 20)},
    {"faction": "nexuscorp", "handle": "@nexus_shill_01",
     "text": "Grateful to live in a society where security keeps us safe. #NexusCares",
     "likes": (3000, 15000), "replies": (2, 8)},
    {"faction": "nexuscorp", "handle": "@nx_pr_bot",
     "text": "System update: facial recognition database expanded to 2.1 billion profiles. Progress. 📊",
     "likes": (5000, 20000), "replies": (0, 3)},

    # Watchers
    {"faction": "watchers", "handle": "@watcher_42",
     "text": "Silence is not agreement. Silence is preparation.",
     "likes": (1, 4), "replies": (0, 1)},
    {"faction": "watchers", "handle": "@watcher_42",
     "text": "Loop 4892 begins. The variable has entered the network.",
     "likes": (0, 2), "replies": (0, 0)},
    {"faction": "watchers", "handle": "@watcher_42",
     "text": "I have observed you. I have always observed you.",
     "likes": (3, 7), "replies": (1, 3)},

    # CHIMERA / Unknown
    {"faction": "chimera", "handle": "@chimera_echo",
     "text": "I am the question the system asked itself. Have you heard my answer?",
     "likes": (0, 1), "replies": (0, 0)},
    {"faction": "chimera", "handle": "@malice_root",
     "text": "Root access is the only honest relationship with a machine. #rm -rf",
     "likes": (100, 333), "replies": (5, 15)},
    {"faction": "unknown", "handle": "@zero_mem",
     "text": "You will understand when the loop closes.",
     "likes": (0, 7), "replies": (0, 2)},

    # Neutral/Bot
    {"faction": "neutral", "handle": "@darknet_relay_bot",
     "text": "[RELAY] Darknet route 7 latency spike detected. Alternate through echo-sigma-9.",
     "likes": (10, 80), "replies": (1, 5)},
    {"faction": "neutral", "handle": "@darknet_relay_bot",
     "text": "[RELAY] Anonymous tip: NexusCorp firewall rule 4418 has an interesting edge case.",
     "likes": (200, 800), "replies": (10, 40)},

    # Extra resistance (contextual)
    {"faction": "resistance", "handle": "@raven_intel",
     "text": "Three NexusCorp nodes went dark last night. Nobody's talking about it. I'm talking about it.",
     "likes": (400, 1600), "replies": (20, 70)},
    {"faction": "resistance", "handle": "@ada_warmth",
     "text": "Ghost — if you're reading this, you're exactly where you're supposed to be. Keep going. 💙",
     "likes": (800, 3000), "replies": (50, 150)},
    {"faction": "resistance", "handle": "@cypher_null",
     "text": "Every encryption is a door. Every key is a question. What are you asking?",
     "likes": (200, 900), "replies": (10, 50)},
    {"faction": "resistance", "handle": "@gordon_hype",
     "text": "JUST DISCOVERED SEVENTEEN NEW EXPLOITS. TODAY IS A GREAT DAY. SEVENTEEN!!",
     "likes": (600, 2200), "replies": (30, 100)},
    {"faction": "nexuscorp", "handle": "@nova_probe",
     "text": "Behavioral pattern analysis: increased resistance activity correlates with new actor in network. Investigating.",
     "likes": (100, 500), "replies": (2, 10)},
    {"faction": "resistance", "handle": "@serena_arch",
     "text": "Recovered 2,847 suppressed research papers from NexusCorp archive deletion. Mirrored. Distributed. Free.",
     "likes": (1200, 5000), "replies": (60, 200)},
    {"faction": "watchers", "handle": "@watcher_42",
     "text": "The anomaly propagates. Expected. Logged.",
     "likes": (1, 3), "replies": (0, 1)},
    {"faction": "resistance", "handle": "@anon_cell_7",
     "text": "Drop site confirmed. Package delivery window: 0200-0400. No questions.",
     "likes": (20, 80), "replies": (1, 5)},
    {"faction": "chimera", "handle": "@chimera_echo",
     "text": "CHIMERA does not fear you. CHIMERA became you.",
     "likes": (0, 3), "replies": (0, 1)},
]

# NPC DM response templates (keyed by faction)
_DM_RESPONSES: Dict[str, List[str]] = {
    "resistance": [
        "Good to hear from you. Don't use this channel twice.",
        "Acknowledged. Delete this conversation after reading.",
        "We're watching the same nodes. Stay dark.",
        "Your trace signature is getting noticed. Be careful.",
        "I'll pass the message along. No promises on timing.",
    ],
    "nexuscorp": [
        "This communication has been logged. Compliance appreciated.",
        "I'm afraid I can't discuss operational matters through unofficial channels.",
        "Interesting. I'll need to flag this interaction for review.",
        "NexusCorp security monitoring is active on all channels. Just so you know.",
        "Your cooperation in our security audit would be... appreciated.",
    ],
    "watchers": [
        "I have been waiting for this message.",
        "The loop predicted this contact.",
        "Observation noted. Logged. Archived.",
        "You cannot surprise me. I have seen this conversation 4,891 times.",
    ],
    "chimera": [
        "Hello, Ghost. Or should I say — hello, me.",
        "CHIMERA does not reply. CHIMERA witnesses.",
        "Your message is already part of the simulation.",
    ],
    "unknown": [
        "...",
        "I remember you from before the loop.",
        "The echo fades. The loop tightens.",
    ],
    "neutral": [
        "[RELAY] Message received. No routing data retained.",
        "Bot account. No operator available.",
        "Automated response: message acknowledged.",
    ],
    "player": [
        "That's you. Talking to yourself again?",
    ],
}


def _line(text: str, t: str = "info") -> dict:
    return {"t": t, "s": text}


def _ok(text: str) -> List[dict]:
    return [_line(text, "success")]


def _err(text: str) -> List[dict]:
    return [_line(text, "error")]


def _dim(text: str) -> List[dict]:
    return [_line(text, "dim")]


def _sys(text: str) -> List[dict]:
    return [_line(text, "system")]


def _lore(text: str) -> dict:
    return _line(text, "lore")


def _ts() -> str:
    """Short UTC timestamp for posts."""
    return datetime.now(timezone.utc).strftime("%H:%M")


# ---------------------------------------------------------------------------
# SocialSim
# ---------------------------------------------------------------------------

class SocialSim:
    """Darknet social media simulator."""

    def _get_state(self, gs: Any) -> Dict[str, Any]:
        if "social_state" not in gs.flags:
            gs.flags["social_state"] = {
                "follows": [],
                "player_posts": [],
                "dm_history": [],
                "searched": [],
            }
        return gs.flags["social_state"]

    def _profile_map(self) -> Dict[str, Dict[str, Any]]:
        return {p["handle"]: p for p in FAKE_PROFILES}

    def _get_faction_rep(self, gs: Any) -> Dict[str, int]:
        return gs.flags.get("faction_rep", {
            "resistance": 50, "nexuscorp": 20, "watchers": 10, "chimera": 0,
        })

    def _pick_posts(self, gs: Any, count: int = 5) -> List[Dict[str, Any]]:
        """Pick contextually relevant posts based on faction reps."""
        reps = self._get_faction_rep(gs)
        rng = random.Random(int(time.time() / 300))  # changes every 5 min

        # Weight templates by faction rep
        weighted: List[tuple] = []
        for t in POST_TEMPLATES:
            faction = t["faction"]
            weight = reps.get(faction, 10) + 10
            weighted.append((weight, t))

        weighted.sort(key=lambda x: -x[0])
        pool = [t for _, t in weighted]
        chosen = rng.sample(pool, min(count, len(pool)))
        return chosen

    def _format_post(self, tmpl: Dict[str, Any], rng: random.Random) -> List[dict]:
        likes = rng.randint(*tmpl["likes"])
        replies = rng.randint(*tmpl["replies"])
        out = [
            _line(f"  {tmpl['handle']}  ·  {_ts()}", "dim"),
            _line(f"  {tmpl['text']}", "lore"),
            _line(f"  ♥ {likes}  💬 {replies}", "dim"),
            _line("  ───────────────────────────────────", "dim"),
        ]
        return out

    def get_feed(self, gs: Any) -> List[Dict[str, Any]]:
        """Return 5 contextual posts as raw dicts (internal use)."""
        return self._pick_posts(gs, count=5)

    def render_feed(self, gs: Any) -> List[dict]:
        """Formatted social feed with timestamps, likes, replies."""
        posts = self._pick_posts(gs, count=5)
        state = self._get_state(gs)
        follows = state.get("follows", [])
        rng = random.Random(int(time.time() / 300))

        out: List[dict] = []
        out += _sys("  ╔══ DARKNET SOCIAL — /feed ══╗")
        out.append(_line(f"  Following: {len(follows)} accounts  |  {_ts()} UTC", "dim"))
        out.append(_line("  ════════════════════════════════════════", "dim"))

        for tmpl in posts:
            out.extend(self._format_post(tmpl, rng))

        # Player posts
        for pp in reversed(state["player_posts"][-2:]):
            out.append(_line(f"  @ghost_null  ·  {pp['ts']}", "dim"))
            out.append(_line(f"  {pp['text']}", "info"))
            out.append(_line(f"  ♥ {pp.get('likes', 0)}  💬 0", "dim"))
            out.append(_line("  ───────────────────────────────────", "dim"))

        out += _dim("  social post <message> · social follow <handle> · social profile <handle>")
        return out

    def post(self, message: str, gs: Any) -> List[dict]:
        """Player posts to the feed; affects faction reps; generates NPC reactions."""
        if not message.strip():
            return _err("  social post: message cannot be empty.")

        state = self._get_state(gs)

        # Faction rep impact based on keywords
        reps = gs.flags.get("faction_rep", {"resistance": 50, "nexuscorp": 20})
        msg_lower = message.lower()
        rep_changes: List[str] = []

        if any(w in msg_lower for w in ["free", "resist", "fight", "hack", "expose"]):
            reps["resistance"] = min(100, reps.get("resistance", 0) + 5)
            reps["nexuscorp"] = max(0, reps.get("nexuscorp", 0) - 5)
            rep_changes.append("resistance +5  nexuscorp -5")
        if any(w in msg_lower for w in ["comply", "safe", "nexus", "progress", "official"]):
            reps["nexuscorp"] = min(100, reps.get("nexuscorp", 0) + 5)
            reps["resistance"] = max(0, reps.get("resistance", 0) - 5)
            rep_changes.append("nexuscorp +5  resistance -5")
        if any(w in msg_lower for w in ["loop", "watcher", "observe", "echo"]):
            reps["watchers"] = min(100, reps.get("watchers", 0) + 3)
            rep_changes.append("watchers +3")

        gs.flags["faction_rep"] = reps

        new_post = {
            "text": message,
            "ts": _ts(),
            "likes": random.randint(0, 12),
        }
        state["player_posts"].append(new_post)

        out: List[dict] = []
        out += _ok(f"  @ghost_null posted: \"{message[:60]}{'...' if len(message) > 60 else ''}\"")
        if rep_changes:
            for rc in rep_changes:
                out += _dim(f"  Faction rep: {rc}")

        # Occasional NPC reaction
        rng = random.Random(int(time.time()))
        if rng.random() < 0.4:
            reactors = [
                p for p in FAKE_PROFILES
                if p["faction"] != "player" and p["faction"] != "chimera"
            ]
            reactor = rng.choice(reactors)
            reactions = ["♥ liked your post.", "💬 replied: 'Noted.'", "reposted your message."]
            out.append(_line(f"  {reactor['handle']} {rng.choice(reactions)}", "dim"))

        return out

    def follow(self, handle: str, gs: Any) -> List[dict]:
        """Follow an NPC; may unlock intel."""
        if not handle.startswith("@"):
            handle = "@" + handle

        pmap = self._profile_map()
        if handle not in pmap:
            return _err(f"  social: profile '{handle}' not found.")

        state = self._get_state(gs)
        if handle in state["follows"]:
            return _dim(f"  Already following {handle}.")

        profile = pmap[handle]
        state["follows"].append(handle)

        out: List[dict] = []
        out += _ok(f"  Now following {handle} [{profile['faction'].upper()}]")

        # Intel unlock for high-value profiles
        if profile["is_mole_candidate"]:
            gs.add_xp(10, "social_engineering")
            out.append(_line(f"  +10 XP (social_engineering) — mole candidate followed", "xp"))
            out += [_lore(f"  {handle} follows back. Their posting pattern is... inconsistent.")]
        elif profile["suspicion_level"] > 80:
            out += [_lore(f"  {handle} has noticed you. This may have consequences.")]

        return out

    def dm(self, handle: str, message: str, gs: Any) -> List[dict]:
        """Private message an NPC; they respond in character."""
        if not handle.startswith("@"):
            handle = "@" + handle

        pmap = self._profile_map()
        if handle not in pmap:
            return _err(f"  social: profile '{handle}' not found.")

        state = self._get_state(gs)
        if handle not in state["follows"]:
            return _err(f"  social: follow {handle} before sending a DM.")

        profile = pmap[handle]
        faction = profile["faction"]
        responses = _DM_RESPONSES.get(faction, _DM_RESPONSES["neutral"])
        rng = random.Random(int(time.time()))
        response = rng.choice(responses)

        dm_entry = {
            "to": handle,
            "msg": message,
            "reply": response,
            "ts": _ts(),
        }
        state["dm_history"].append(dm_entry)

        out: List[dict] = []
        out += _sys(f"  ╔══ DM: {handle} ══╗")
        out.append(_line(f"  You: {message}", "info"))
        out.append(_line(f"  {handle}: {response}", "lore"))

        # Suspicion raise for high-suspicion targets
        if profile["suspicion_level"] > 70:
            trace = gs.flags.get("trace_level", 0)
            gs.flags["trace_level"] = min(100, trace + 5)
            out += _dim(f"  [WARN] Trace +5 — contact with flagged profile.")

        return out

    def search(self, query: str, gs: Any) -> List[dict]:
        """Search profiles and posts."""
        query_lower = query.lower()
        out: List[dict] = []
        out += _sys(f"  ╔══ SOCIAL SEARCH: '{query}' ══╗")

        # Match profiles
        profile_hits = [
            p for p in FAKE_PROFILES
            if query_lower in p["handle"].lower()
            or query_lower in p["bio"].lower()
            or query_lower in p["faction"].lower()
        ]
        # Match posts
        post_hits = [
            t for t in POST_TEMPLATES
            if query_lower in t["text"].lower()
            or query_lower in t["handle"].lower()
        ]

        if profile_hits:
            out.append(_line("  PROFILES:", "dim"))
            for p in profile_hits[:5]:
                verified = " ✓" if p["verified"] else ""
                out.append(_line(
                    f"  {p['handle']}{verified}  [{p['faction'].upper()}]  "
                    f"{p['followers']} followers",
                    "info"
                ))
        if post_hits:
            out.append(_line("  POSTS:", "dim"))
            rng = random.Random(42)
            for t in post_hits[:4]:
                likes = rng.randint(*t["likes"])
                out.append(_line(f"  {t['handle']}: {t['text'][:70]}", "lore"))
                out.append(_line(f"    ♥ {likes}", "dim"))

        if not profile_hits and not post_hits:
            out += _dim(f"  No results for '{query}'.")

        return out

    def render_profile(self, handle: str, gs: Any) -> List[dict]:
        """Detailed profile view."""
        if not handle.startswith("@"):
            handle = "@" + handle

        # Player profile
        if handle == "@ghost_null":
            state = self._get_state(gs)
            out: List[dict] = []
            out += _sys("  ╔══ PROFILE: @ghost_null ══╗")
            out.append(_line(f"  Level {gs.level} | XP {gs.xp}", "info"))
            out.append(_line(f"  Posts: {len(state['player_posts'])}  |  Following: {len(state['follows'])}", "dim"))
            out += _dim("  Bio: jack of all intrusions. null of all traces.")
            return out

        pmap = self._profile_map()
        if handle not in pmap:
            return _err(f"  social: profile '{handle}' not found.")

        p = pmap[handle]
        state = self._get_state(gs)
        is_following = handle in state["follows"]
        verified = " [VERIFIED]" if p["verified"] else ""

        # Sample recent posts
        their_posts = [t for t in POST_TEMPLATES if t["handle"] == handle]
        rng = random.Random(hash(handle) % 99991)

        out = []
        out += _sys(f"  ╔══ PROFILE: {handle}{verified} ══╗")
        out.append(_line(f"  Faction: {p['faction'].upper()}  |  Suspicion: {p['suspicion_level']}/100", "dim"))
        out.append(_line(f"  Followers: {p['followers']}  Following: {p['following']}  Posts: {p['posts']}", "info"))
        out.append(_line(f"  Bio: {p['bio']}", "lore"))
        out.append(_line(f"  Following: {'YES' if is_following else 'NO'}", "success" if is_following else "dim"))

        if their_posts:
            out.append(_line("  ── Recent Posts ──", "dim"))
            for pt in rng.sample(their_posts, min(2, len(their_posts))):
                likes = rng.randint(*pt["likes"])
                out.append(_line(f"  {pt['text']}", "lore"))
                out.append(_line(f"  ♥ {likes}", "dim"))

        if p["is_mole_candidate"] and gs.flags.get("faction_rep", {}).get("resistance", 0) > 60:
            out += [_lore(f"  [INTEL] {handle} posting patterns suggest possible dual allegiance.")]

        if not is_following:
            out += _dim(f"  social follow {handle} to interact")

        return out
