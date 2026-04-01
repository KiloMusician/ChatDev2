"""
services/mod_audit/conflict_rules.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Conflict detection for RimWorld mod lists.

Conflict sources (checked in order):
  1. About.xml `<incompatibleWith>` declarations
  2. Hardcoded known-bad pairs from ACTIVE_MODS_AUDIT.md and community data
  3. Duplicate packageId entries in the active list

Severity levels: critical | warning | info
"""
from __future__ import annotations

from typing import Any


# ── Hardcoded conflict database ───────────────────────────────────────────────
# Sourced from: ACTIVE_MODS_AUDIT.md + community RimWorld knowledge.
# Format: (pkg_a, pkg_b, severity, note)
_KNOWN_CONFLICTS: list[tuple[str, str, str, str]] = [
    # VBE / RimThemes — confirmed crash lead from ACTIVE_MODS_AUDIT.md
    (
        "vanillaexpanded.backgrounds",
        "rimthemes",
        "critical",
        "VBE.ModCompat.LoadRimThemesImages() throws during startup. "
        "Remove one or apply the community RimThemes-VBE patch.",
    ),

    # Doors Expanded duplicate packageId (seen in user's ModsConfig.xml)
    (
        "jecrell.doorsexpanded",
        "jecrell.doorsexpanded",
        "warning",
        "Duplicate packageId detected. Only the last loaded copy will be active; "
        "remove the duplicate entry from ModsConfig.xml.",
    ),

    # Deep Storage duplicate
    (
        "lwm.deepstorage",
        "lwm.deepstorage",
        "warning",
        "Duplicate Deep Storage entry. Remove the older or non-Workshop copy.",
    ),

    # JecsTools duplicate (dependency for many Jecrell mods)
    (
        "jecrell.jecstools",
        "jecrell.jecstools",
        "warning",
        "Duplicate JecsTools entry. This can cause Harmony patch conflicts.",
    ),

    # Vanilla Expanded Base Generation duplicate
    (
        "vanillaexpanded.basegeneration",
        "vanillaexpanded.basegeneration",
        "warning",
        "Duplicate VBE BaseGeneration. Map-gen patches may apply twice.",
    ),

    # VBE Skills duplicate
    (
        "vanillaexpanded.skills",
        "vanillaexpanded.skills",
        "warning",
        "Duplicate VBE Skills. Skill XP multipliers will stack incorrectly.",
    ),

    # More Trait Slots duplicate
    (
        "moretraitslots.kv.rw",
        "moretraitslots.kv.rw",
        "warning",
        "Duplicate More Trait Slots. Trait count limits may behave unexpectedly.",
    ),

    # Winston Wave duplicate
    (
        "vanillastorytellersexpanded.winstonwave",
        "vanillastorytellersexpanded.winstonwave",
        "warning",
        "Duplicate Winston Wave storyteller entry.",
    ),

    # Factional War Continued duplicate
    (
        "sr.modrimworld.factionalwarcontinued",
        "sr.modrimworld.factionalwarcontinued",
        "warning",
        "Duplicate Factional War Continued entry.",
    ),

    # Toggleable Overlays duplicate
    (
        "owlchemist.toggleableoverlays",
        "owlchemist.toggleableoverlays",
        "warning",
        "Duplicate Toggleable Overlays.",
    ),

    # Raid Extension duplicate
    (
        "sr.modrimworld.raidextension",
        "sr.modrimworld.raidextension",
        "warning",
        "Duplicate Raid Extension entry.",
    ),

    # RimGPT vs RimChat — both patch comms console; known keybind conflict
    (
        "rimgpt",
        "rimchat",
        "warning",
        "RimGPT and RimChat both patch the comms console and share a keybind "
        "(Command_OpenRimGPT). Test carefully; a patch exclusion in one mod's "
        "Patches/ folder may be needed.",
    ),

    # RimGPT keybind also conflicts with RimTalk
    (
        "rimgpt",
        "rimtalk",
        "info",
        "RimGPT and RimTalk both inject dialogue UI hooks. "
        "Shared OpenAI-provider settings may conflict. "
        "Prefer routing both through TerminalKeeper's local provider registry.",
    ),

    # VacskinGland config errors — mentioned in logs
    (
        "vanilaexpanded.genetics",
        "vanilaexpanded.vgeneticse",
        "info",
        "VacskinGland config errors observed in load logs. "
        "Ensure both mods are the same Workshop version.",
    ),

    # XML patch failure mods
    (
        "vanillaexpanded.vanillaexpandedextraembrasures",
        "oskarpotocki.vanillavehiclesexpanded",
        "info",
        "VanillaExpandedExtraEmbrasures.xml patch failure may interact with "
        "Vehicle Framework. Load VBE Embrasures after Vehicles.",
    ),
]

# Mods known to be AI/LLM surfaces — used to produce integration hints
_AI_SURFACE_MODS: set[str] = {
    "rimtalk",
    "rimgpt",
    "rimchat",
    "rimind",
    "rimnet.terminal",
    "aiuplifting",
}


# ── Public API ────────────────────────────────────────────────────────────────

def check_conflicts(mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Run all conflict checks against the supplied mod list.
    Returns a list of ConflictWarning dicts sorted by severity.
    """
    known_ids = {m["package_id"] for m in mods}
    results: list[dict[str, Any]] = []

    # 1. About.xml incompatibleWith declarations
    for mod in mods:
        for bad in mod.get("incompatible_with", []):
            if bad in known_ids:
                results.append({
                    "severity":  "critical",
                    "mod_a":     mod["package_id"],
                    "mod_b":     bad,
                    "source":    "about_xml",
                    "message":   (
                        f"'{mod['display_name']}' declares '{bad}' as incompatible "
                        "in its About.xml."
                    ),
                    "fix":       f"Remove '{bad}' from your mod list.",
                })

    # 2. Hardcoded known-bad pairs
    for a, b, severity, note in _KNOWN_CONFLICTS:
        a_present = a in known_ids
        b_present = b in known_ids

        if a == b:
            # Self-conflict = duplicate detection
            count = sum(1 for m in mods if m["package_id"] == a)
            if count > 1:
                results.append({
                    "severity":  severity,
                    "mod_a":     a,
                    "mod_b":     b,
                    "source":    "known_duplicates",
                    "message":   f"Duplicate entry detected for '{a}' ({count}×). {note}",
                    "fix":       "Keep only one entry; remove duplicates from ModsConfig.xml.",
                })
        elif a_present and b_present:
            results.append({
                "severity":  severity,
                "mod_a":     a,
                "mod_b":     b,
                "source":    "known_conflicts",
                "message":   note,
                "fix":       _default_fix(a, b, severity),
            })

    # Sort: critical first, then warning, then info
    _sev_order = {"critical": 0, "warning": 1, "info": 2}
    results.sort(key=lambda r: _sev_order.get(r["severity"], 9))
    return results


def detect_ai_surface_mods(mods: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return mods in the active list that are known AI/LLM surfaces."""
    found = []
    for mod in mods:
        pid = mod["package_id"]
        if any(surface in pid for surface in _AI_SURFACE_MODS):
            found.append({
                "package_id":   pid,
                "display_name": mod.get("display_name", pid),
                "integration_note": _ai_integration_note(pid),
            })
    return found


def _ai_integration_note(pid: str) -> str:
    notes = {
        "rimtalk":        (
            "Best first target for local LLM routing. Has provider-selection layer, "
            "OpenAI-compatible client, Gemini, Player2, and model-fetching. "
            "TerminalKeeper can inject its Ollama/LM-Studio endpoint here."
        ),
        "rimgpt":         (
            "Direct prompt UX surface. Replace or extend with TerminalKeeper's "
            "local model provider via OpenAI-compatible endpoint."
        ),
        "rimchat":        (
            "Filesystem-backed prompt files (Prompt/Default/*.json). "
            "Patches comms console. Good seam for persona injection."
        ),
        "rimind":         (
            "Resilient multi-provider routing with cooldowns and failure counts. "
            "Reference implementation for quota-aware provider rotation."
        ),
        "rimnet.terminal":(
            "Terminal-flavoured interaction surface. Compatible with TerminalKeeper "
            "themes. Use as secondary REPL surface for non-Lattice colonists."
        ),
        "aiuplifting":    (
            "AI Uplifting mod — check for research/hediff surfaces that can be "
            "linked to TerminalKeeper XP milestones."
        ),
    }
    for key, note in notes.items():
        if key in pid:
            return note
    return "AI/LLM surface mod — investigate for TerminalKeeper integration."


def _default_fix(a: str, b: str, severity: str) -> str:
    if severity == "critical":
        return f"Remove '{a}' or '{b}' from your mod list before loading a save."
    if severity == "warning":
        return "Load in a fresh save to test stability, or check for community patches."
    return "Monitor for issues; may be safely ignored on stable playthroughs."
