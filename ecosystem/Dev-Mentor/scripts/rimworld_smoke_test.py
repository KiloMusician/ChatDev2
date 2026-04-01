from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import textwrap
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
RIMWORLD_EXE = Path(
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/RimWorld/RimWorldWin64.exe"
)
LIVE_MODS_CONFIG = Path(
    "/mnt/c/Users/keath/AppData/LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml"
)
TMP_ROOT = REPO_ROOT / "tmp" / "rimworld_smoke"
DEFAULT_TIMEOUT_SECONDS = 180
RIMWORLD_DATA_DIR = Path(
    "/mnt/c/Program Files (x86)/Steam/steamapps/common/RimWorld/Data"
)
WORKSHOP_MODS_DIR = Path(
    "/mnt/c/Program Files (x86)/Steam/steamapps/workshop/content/294100"
)
MOD_CACHE_PATH = TMP_ROOT / "installed_mods_cache.json"

LOAD_BEFORE_CORE = ("ilyvion.loadingprogress",)
PERF_BASE_INSERTS = ("brrainz.harmony",)
PERF_OPTIONAL = {
    "loadingprogress": "ilyvion.loadingprogress",
    "performanceoptimizer": "taranchuk.performanceoptimizer",
    "rocketman": "krkr.rocketman",
    "dubsperformanceanalyzer": "dubwise.dubsperformanceanalyzer.steam",
    "frameratecontrol": "notfood.frameratecontrol",
}
AI_CHAT_TERMS = (
    "cj.rimtalk",
    "rimtalk.",
    "zruic.expand.",
    "brrainz.rimgpt",
    "yancy.rimchat",
    "cj.rimind",
    "com.antediluvian.compterm",
    "albion.aiuplift",
    "cyanobot.talkingisnteverything",
    "mlie.tpwalkietalkie",
    "flyingkiwis.agents",
)
SEVERE_PATTERNS = (
    "Could not execute post-long-event action. Exception:",
    "XML error:",
    "Config error in ",
    "Type PatchOperationSequence is not a Def type or could not be found",
    "NullReferenceException",
    "TypeLoadException",
    "ReflectionTypeLoadException",
    "System.Collections.Generic.KeyNotFoundException",
)
WARN_PATTERNS = (
    "Tried loading mod with the same packageId multiple times:",
    "needs to have <downloadUrl> and/or <steamWorkshopUrl> specified.",
    "Key binding conflict:",
)


@dataclass
class SmokeResult:
    profile: str
    mods: list[str]
    returncode: int
    duration_seconds: float
    severe_hits: list[str]
    warn_hits: list[str]
    log_path: str
    status: str


@dataclass
class ModMeta:
    package_id: str
    name: str
    source_path: str
    load_after: list[str]
    load_before: list[str]
    incompatible_with: list[str]
    dependencies: list[str]


def parse_mods_config(path: Path) -> tuple[str, list[str], list[str]]:
    text = path.read_text(errors="ignore")
    version_match = re.search(r"<version>(.*?)</version>", text, re.I | re.S)
    version = version_match.group(1).strip() if version_match else "1.6"
    active_mods = re.findall(r"<activeMods>\s*(.*?)\s*</activeMods>", text, re.I | re.S)
    known_expansions = re.findall(
        r"<knownExpansions>\s*(.*?)\s*</knownExpansions>", text, re.I | re.S
    )

    active = (
        re.findall(r"<li>(.*?)</li>", active_mods[0], re.I | re.S)
        if active_mods
        else []
    )
    expansions = (
        re.findall(r"<li>(.*?)</li>", known_expansions[0], re.I | re.S)
        if known_expansions
        else []
    )
    return (
        version,
        [item.strip() for item in active],
        [item.strip() for item in expansions],
    )


def _child_text(root: ET.Element, tag_name: str) -> str:
    for child in list(root):
        if child.tag.lower() == tag_name.lower():
            return (child.text or "").strip()
    return ""


def _child_li_values(root: ET.Element, tag_name: str) -> list[str]:
    values: list[str] = []
    for child in list(root):
        if child.tag.lower() != tag_name.lower():
            continue
        for node in child.iter():
            if node.tag.lower() == "li" and (node.text or "").strip():
                values.append((node.text or "").strip())
    return dedupe_preserve_order(values)


def _dependency_values(root: ET.Element) -> list[str]:
    values: list[str] = []
    for child in list(root):
        if child.tag.lower() not in {"moddependencies", "moddependenciesbyversion"}:
            continue
        for node in child.iter():
            if node.tag.lower() == "packageid" and (node.text or "").strip():
                values.append((node.text or "").strip())
    return dedupe_preserve_order(values)


def parse_about_xml(path: Path) -> ModMeta | None:
    try:
        root = ET.fromstring(path.read_text(errors="ignore"))
    except ET.ParseError:
        return None

    package_id = _child_text(root, "packageId")
    if not package_id:
        return None

    return ModMeta(
        package_id=package_id.lower(),
        name=_child_text(root, "name") or package_id,
        source_path=str(path.parent.parent),
        load_after=[item.lower() for item in _child_li_values(root, "loadAfter")],
        load_before=[item.lower() for item in _child_li_values(root, "loadBefore")],
        incompatible_with=[
            item.lower() for item in _child_li_values(root, "incompatibleWith")
        ],
        dependencies=[item.lower() for item in _dependency_values(root)],
    )


def discover_installed_mods() -> tuple[dict[str, list[ModMeta]], list[str]]:
    if MOD_CACHE_PATH.exists():
        try:
            payload = json.loads(MOD_CACHE_PATH.read_text())
            installed = {
                pkg: [ModMeta(**meta) for meta in metas]
                for pkg, metas in payload.get("installed", {}).items()
            }
            duplicates = payload.get("duplicates", [])
            return installed, duplicates
        except Exception:
            pass

    installed: dict[str, list[ModMeta]] = {}
    roots = [path for path in (WORKSHOP_MODS_DIR, RIMWORLD_DATA_DIR) if path.exists()]
    for root in roots:
        try:
            child_names = [entry.name for entry in os.scandir(root) if entry.is_dir()]
        except FileNotFoundError:
            child_names = []

        for child_name in child_names:
            about = root / child_name / "About" / "About.xml"
            if not about.exists():
                continue
            meta = parse_about_xml(about)
            if not meta:
                continue
            installed.setdefault(meta.package_id, []).append(meta)

    duplicates = sorted([pkg for pkg, metas in installed.items() if len(metas) > 1])
    MOD_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    MOD_CACHE_PATH.write_text(
        json.dumps(
            {
                "installed": {
                    pkg: [meta.__dict__ for meta in metas]
                    for pkg, metas in installed.items()
                },
                "duplicates": duplicates,
            },
            indent=2,
        )
    )
    return installed, duplicates


def find_running_rimworld_pids() -> list[int]:
    proc = subprocess.run(
        ["cmd.exe", "/c", "tasklist | findstr /I RimWorldWin64.exe"],
        capture_output=True,
        text=True,
        check=False,
    )
    pids: list[int] = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].lower() == "rimworldwin64.exe":
            try:
                pids.append(int(parts[1]))
            except ValueError:
                continue
    return pids


def wait_for_rimworld_exit(timeout_seconds: int = 30) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if not find_running_rimworld_pids():
            return True
        time.sleep(1)
    return not find_running_rimworld_pids()


def build_mods_config(
    version: str, active_mods: Iterable[str], known_expansions: Iterable[str]
) -> str:
    active_lines = "\n".join(f"    <li>{mod}</li>" for mod in active_mods)
    expansion_lines = "\n".join(f"    <li>{exp}</li>" for exp in known_expansions)
    return textwrap.dedent(
        f"""\
        <?xml version="1.0" encoding="utf-8"?>
        <ModsConfigData>
          <version>{version}</version>
          <activeMods>
        {active_lines}
          </activeMods>
          <knownExpansions>
        {expansion_lines}
          </knownExpansions>
        </ModsConfigData>
        """
    )


def dedupe_preserve_order(mods: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for mod in mods:
        if mod not in seen:
            ordered.append(mod)
            seen.add(mod)
    return ordered


def remove_mods(mods: Iterable[str], removals: set[str]) -> list[str]:
    return [mod for mod in mods if mod not in removals]


def insert_before_first_ludeon(mods: list[str], inserts: list[str]) -> list[str]:
    ordered = dedupe_preserve_order(inserts)
    if not ordered:
        return mods[:]
    out = [mod for mod in mods if mod not in ordered]
    idx = next(
        (i for i, mod in enumerate(out) if mod.startswith("ludeon.rimworld")), len(out)
    )
    for mod in reversed(ordered):
        out.insert(idx, mod)
    return out


def insert_after(mods: list[str], anchor: str, inserts: list[str]) -> list[str]:
    ordered = dedupe_preserve_order(inserts)
    out = [mod for mod in mods if mod not in ordered]
    try:
        idx = out.index(anchor) + 1
    except ValueError:
        idx = len(out)
    for mod in reversed(ordered):
        out.insert(idx, mod)
    return out


def insert_after_last_ludeon(mods: list[str], inserts: list[str]) -> list[str]:
    ordered = dedupe_preserve_order(inserts)
    out = [mod for mod in mods if mod not in ordered]
    ludeon_indices = [
        i for i, mod in enumerate(out) if mod.startswith("ludeon.rimworld")
    ]
    idx = (ludeon_indices[-1] + 1) if ludeon_indices else len(out)
    for mod in reversed(ordered):
        out.insert(idx, mod)
    return out


def core_profile_mods(active_mods: list[str]) -> list[str]:
    return [
        mod
        for mod in active_mods
        if mod.startswith("ludeon.rimworld") or mod == "brrainz.harmony"
    ]


def perf_profile_mods(active_mods: list[str], *optional_keys: str) -> list[str]:
    base = [mod for mod in active_mods if mod.startswith("ludeon.rimworld")]
    profile = insert_before_first_ludeon(base, list(PERF_BASE_INSERTS))
    wants_rocketman = "rocketman" in optional_keys

    pre_core: list[str] = []
    post_harmony: list[str] = []
    last: list[str] = []
    for key in optional_keys:
        mod = PERF_OPTIONAL[key]
        if mod == "ilyvion.loadingprogress":
            pre_core.append(mod)
        elif mod == "krkr.rocketman":
            last.append(mod)
        else:
            post_harmony.append(mod)

    profile = insert_before_first_ludeon(profile, pre_core)
    profile = insert_after(profile, "brrainz.harmony", post_harmony)
    if wants_rocketman:
        profile = insert_after_last_ludeon(profile, ["unlimitedhugs.hugslib"])
    if last:
        profile = dedupe_preserve_order(
            [mod for mod in profile if mod not in last] + last
        )
    return profile


def ai_chat_profile_mods(active_mods: list[str]) -> list[str]:
    base = [mod for mod in active_mods if mod.startswith("ludeon.rimworld")]
    extras = [
        mod
        for mod in active_mods
        if mod == "brrainz.harmony"
        or mod == "unlimitedhugs.hugslib"
        or mod == "mlie.modmanager"
        or any(term in mod for term in AI_CHAT_TERMS)
    ]
    profile = dedupe_preserve_order(base + extras)
    return insert_before_first_ludeon(profile, list(LOAD_BEFORE_CORE))


def build_profiles(active_mods: list[str]) -> dict[str, list[str]]:
    current = dedupe_preserve_order(active_mods)
    current_no_themes = remove_mods(
        current, {"vanillaexpanded.backgrounds", "arandomkiwi.rimthemes"}
    )
    current_no_themes_lp = insert_before_first_ludeon(
        current_no_themes, list(LOAD_BEFORE_CORE)
    )
    mp_minimal = core_profile_mods(current)
    mp_minimal = insert_before_first_ludeon(mp_minimal, list(LOAD_BEFORE_CORE))
    mp_minimal = insert_after(
        mp_minimal,
        "brrainz.harmony",
        ["rwmt.Multiplayer", "rwmt.MultiplayerCompatibility"],
    )

    current_no_themes_lp_mp = insert_after(
        current_no_themes_lp,
        (
            "unlimitedhugs.hugslib"
            if "unlimitedhugs.hugslib" in current_no_themes_lp
            else "brrainz.harmony"
        ),
        ["rwmt.Multiplayer", "rwmt.MultiplayerCompatibility"],
    )

    return {
        "perf_core_dlc_harmony": perf_profile_mods(current),
        "perf_core_dlc_harmony_loadingprogress": perf_profile_mods(
            current, "loadingprogress"
        ),
        "perf_core_dlc_harmony_loadingprogress_performanceoptimizer": perf_profile_mods(
            current, "loadingprogress", "performanceoptimizer"
        ),
        "perf_core_dlc_harmony_loadingprogress_rocketman": perf_profile_mods(
            current, "loadingprogress", "rocketman"
        ),
        "perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman": perf_profile_mods(
            current, "loadingprogress", "performanceoptimizer", "rocketman"
        ),
        "perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman_dubsanalyzer": perf_profile_mods(
            current,
            "loadingprogress",
            "performanceoptimizer",
            "rocketman",
            "dubsperformanceanalyzer",
        ),
        "perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman_frameratecontrol": perf_profile_mods(
            current,
            "loadingprogress",
            "performanceoptimizer",
            "rocketman",
            "frameratecontrol",
        ),
        "current_active": current,
        "current_no_vbe_rimthemes": current_no_themes,
        "current_no_vbe_rimthemes_plus_loadingprogress": current_no_themes_lp,
        "multiplayer_minimal": mp_minimal,
        "current_no_vbe_rimthemes_plus_loadingprogress_plus_multiplayer": current_no_themes_lp_mp,
        "ai_chat_minimal": ai_chat_profile_mods(current),
    }


def run_profile(
    profile_name: str,
    version: str,
    known_expansions: list[str],
    mods: list[str],
    timeout_seconds: int,
) -> SmokeResult:
    profile_root = TMP_ROOT / profile_name / str(int(time.time() * 1000))
    (profile_root / "Config").mkdir(parents=True, exist_ok=True)
    log_path = profile_root / "Player.log"
    mods_config = profile_root / "Config" / "ModsConfig.xml"
    mods_config.write_text(build_mods_config(version, mods, known_expansions))
    live_backup = profile_root / "live_ModsConfig.backup.xml"
    shutil.copy2(LIVE_MODS_CONFIG, live_backup)
    shutil.copy2(mods_config, LIVE_MODS_CONFIG)

    exe_win = str(RIMWORLD_EXE).replace("/mnt/c", "C:").replace("/", "\\")
    log_path_win = str(log_path).replace("/mnt/c", "C:").replace("/", "\\")
    ps_command = (
        f"& '{exe_win}' -logfile '{log_path_win}' -quicktest -disable-compute-shaders"
    )

    t0 = time.time()
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = proc.returncode
    except subprocess.TimeoutExpired:
        shutil.copy2(live_backup, LIVE_MODS_CONFIG)
        return SmokeResult(
            profile=profile_name,
            mods=mods,
            returncode=124,
            duration_seconds=round(time.time() - t0, 2),
            severe_hits=["Timed out waiting for RimWorld quicktest"],
            warn_hits=[],
            log_path=str(log_path),
            status="timeout",
        )
    finally:
        if live_backup.exists():
            shutil.copy2(live_backup, LIVE_MODS_CONFIG)

    duration = round(time.time() - t0, 2)
    severe_hits: list[str] = []
    warn_hits: list[str] = []
    if log_path.exists():
        lines = log_path.read_text(errors="ignore").splitlines()
        for line in lines:
            if any(pattern in line for pattern in SEVERE_PATTERNS):
                severe_hits.append(line.strip())
            elif any(pattern in line for pattern in WARN_PATTERNS):
                warn_hits.append(line.strip())
        severe_hits = dedupe_preserve_order(severe_hits)
        warn_hits = dedupe_preserve_order(warn_hits)

    status = "pass"
    if returncode != 0 or severe_hits:
        status = "fail"
    elif warn_hits:
        status = "warn"

    return SmokeResult(
        profile=profile_name,
        mods=mods,
        returncode=returncode,
        duration_seconds=duration,
        severe_hits=severe_hits,
        warn_hits=warn_hits,
        log_path=str(log_path),
        status=status,
    )


def validate_profile_static(
    profile_name: str,
    mods: list[str],
    installed: dict[str, list[ModMeta]],
    duplicate_installed_ids: list[str],
) -> SmokeResult:
    t0 = time.time()
    severe_hits: list[str] = []
    warn_hits: list[str] = []
    normalized = [mod.lower() for mod in mods]
    positions = {mod: idx for idx, mod in enumerate(normalized)}

    for mod in normalized:
        if mod not in installed:
            severe_hits.append(
                f"Missing installed mod metadata for active packageId: {mod}"
            )
            continue
        if mod in duplicate_installed_ids:
            paths = ", ".join(meta.source_path for meta in installed[mod])
            warn_hits.append(
                f"Duplicate installed packageId detected for active mod {mod}: {paths}"
            )

    for mod in normalized:
        metas = installed.get(mod)
        if not metas:
            continue
        meta = metas[0]

        for dep in meta.dependencies:
            if dep not in positions:
                severe_hits.append(f"{mod} missing dependency {dep}")

        for other in meta.incompatible_with:
            if other in positions:
                severe_hits.append(f"{mod} is incompatible with active mod {other}")

        for other in meta.load_after:
            if other in positions and positions[mod] < positions[other]:
                warn_hits.append(f"{mod} should load after {other}")

        for other in meta.load_before:
            if other in positions and positions[mod] > positions[other]:
                warn_hits.append(f"{mod} should load before {other}")

    severe_hits = dedupe_preserve_order(severe_hits)
    warn_hits = dedupe_preserve_order(warn_hits)
    status = "pass"
    returncode = 0
    if severe_hits:
        status = "fail"
        returncode = 2
    elif warn_hits:
        status = "warn"

    report_path = TMP_ROOT / profile_name / f"static_{int(time.time() * 1000)}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "profile": profile_name,
                "mods": mods,
                "severe_hits": severe_hits,
                "warn_hits": warn_hits,
            },
            indent=2,
        )
    )

    return SmokeResult(
        profile=profile_name,
        mods=mods,
        returncode=returncode,
        duration_seconds=round(time.time() - t0, 2),
        severe_hits=severe_hits,
        warn_hits=warn_hits,
        log_path=str(report_path),
        status=status,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", action="append", help="Specific profile(s) to run")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    parser.add_argument(
        "--launch",
        action="store_true",
        help="Launch RimWorld quicktest instead of static validation",
    )
    args = parser.parse_args()

    if not LIVE_MODS_CONFIG.exists():
        raise SystemExit(f"Missing live ModsConfig: {LIVE_MODS_CONFIG}")
    if not RIMWORLD_EXE.exists():
        raise SystemExit(f"Missing RimWorld executable: {RIMWORLD_EXE}")

    version, active_mods, known_expansions = parse_mods_config(LIVE_MODS_CONFIG)
    profiles = build_profiles(active_mods)
    selected = args.profile or list(profiles.keys())
    installed, duplicate_installed_ids = discover_installed_mods()

    results = []
    if args.launch:
        running_pids = find_running_rimworld_pids()
        if running_pids:
            raise SystemExit(
                f"Refusing to launch RimWorld while already running. Active PIDs: {running_pids}"
            )

    for name in selected:
        if name not in profiles:
            raise SystemExit(f"Unknown profile: {name}")
        if args.launch:
            result = run_profile(
                name,
                version,
                known_expansions,
                profiles[name],
                timeout_seconds=args.timeout,
            )
            if not wait_for_rimworld_exit():
                raise SystemExit(
                    "RimWorld quicktest did not fully exit; aborting remaining profiles."
                )
        else:
            result = validate_profile_static(
                name, profiles[name], installed, duplicate_installed_ids
            )
        results.append(result)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "launch" if args.launch else "static",
        "results": [
            {
                "profile": r.profile,
                "status": r.status,
                "returncode": r.returncode,
                "duration_seconds": r.duration_seconds,
                "mod_count": len(r.mods),
                "severe_hits": r.severe_hits,
                "warn_hit_count": len(r.warn_hits),
                "log_path": r.log_path,
            }
            for r in results
        ],
    }
    report_path = TMP_ROOT / "report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2))

    if args.json:
        print(json.dumps(payload, indent=2))
        return

    print(json.dumps(payload, indent=2))
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
