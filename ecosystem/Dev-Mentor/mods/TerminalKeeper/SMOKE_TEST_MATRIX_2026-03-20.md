# RimWorld Smoke Test Matrix - 2026-03-20

## Scope

Focused startup smoke tests for a clean development baseline built from:

- `brrainz.harmony`
- core RimWorld
- all installed DLCs:
  - `ludeon.rimworld.royalty`
  - `ludeon.rimworld.ideology`
  - `ludeon.rimworld.biotech`
  - `ludeon.rimworld.anomaly`
  - `ludeon.rimworld.odyssey`
- `ilyvion.loadingprogress` ("Better Loading")
- `taranchuk.performanceoptimizer` ("Performance Enhancer" assumption)
- `krkr.rocketman`
- optional diagnostics:
  - `dubwise.dubsperformanceanalyzer.steam`
  - `notfood.frameratecontrol`

Tests were run with `scripts/rimworld_smoke_test.py` using `-quicktest` and a temporary swap of the live `ModsConfig.xml`, restoring the original config after every launch.

## Important Notes

- `-savedatafolder` alone was not sufficient to isolate the active mod list. The runner now swaps the live [`ModsConfig.xml`](/mnt/c/Users/keath/AppData/LocalLow/Ludeon%20Studios/RimWorld%20by%20Ludeon%20Studios/Config/ModsConfig.xml#L1) for each profile and restores it afterward.
- Workshop metadata warnings from inactive or duplicate installed mods still appear in logs because RimWorld scans installed workshop metadata at startup.
- Those metadata warnings are not the same thing as active-mod initialization failures.
- `RocketMan` was placed last in the load order, matching its workshop guidance.

## Package IDs

- `brrainz.harmony`
- `ilyvion.loadingprogress`
- `taranchuk.performanceoptimizer`
- `krkr.rocketman`
- `dubwise.dubsperformanceanalyzer.steam`
- `notfood.frameratecontrol`

## Results

All tested profiles passed quicktest startup without severe hits.

| Profile | Mods | Duration | Result |
|---|---:|---:|---|
| `perf_core_dlc_harmony` | 7 | 2.21s | pass |
| `perf_core_dlc_harmony_loadingprogress` | 8 | 2.50s | pass |
| `perf_core_dlc_harmony_loadingprogress_performanceoptimizer` | 9 | 3.33s | pass |
| `perf_core_dlc_harmony_loadingprogress_rocketman` | 9 | 3.31s | pass |
| `perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman` | 10 | 7.14s | pass |
| `perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman_dubsanalyzer` | 11 | 5.05s | pass |
| `perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman_frameratecontrol` | 11 | 2.82s | pass |

## Recommended Development Baselines

### Baseline A: Safest clean dev stack

- `brrainz.harmony`
- `ilyvion.loadingprogress`
- all DLCs

Use this when validating pure TerminalKeeper scaffolding with the fewest moving parts.

### Baseline B: Recommended performance-aware dev stack

- `brrainz.harmony`
- `ilyvion.loadingprogress`
- `taranchuk.performanceoptimizer`
- all DLCs

Use this as the default modding/dev baseline if you want a stable startup surface plus lightweight optimization.

### Baseline C: Aggressive performance baseline

- `brrainz.harmony`
- `ilyvion.loadingprogress`
- `taranchuk.performanceoptimizer`
- all DLCs
- `krkr.rocketman` last

Use this when testing compatibility with heavier optimization patches. It passed, but it introduces the most patch surface.

## Recommendation For TerminalKeeper Work

Start TerminalKeeper compatibility work on **Baseline B**.

Why:

- it passed cleanly
- it keeps startup visibility from `Loading Progress`
- it includes one performance patch layer without stacking every optimizer at once
- it avoids immediately conflating TerminalKeeper bugs with RocketMan-specific behavior

After Baseline B is stable, expand to:

1. Baseline C with `RocketMan`
2. add AI/chat mods
3. add vehicles and social systems
4. reintroduce theme/UI mods later

## Known Separate Crash Lead

The earlier full-load startup failure still points to a theme compatibility problem, not these performance baselines:

- `vanillaexpanded.backgrounds`
- `arandomkiwi.rimthemes`

See [`ACTIVE_MODS_AUDIT.md`](/mnt/c/Users/keath/Dev-Mentor/mods/TerminalKeeper/ACTIVE_MODS_AUDIT.md#L1) for the `VBE.ModCompat.LoadRimThemesImages()` crash notes.

## Artifacts

- runner: [`scripts/rimworld_smoke_test.py`](/mnt/c/Users/keath/Dev-Mentor/scripts/rimworld_smoke_test.py#L1)
- report json: [`tmp/rimworld_smoke/report.json`](/mnt/c/Users/keath/Dev-Mentor/tmp/rimworld_smoke/report.json#L1)

Representative logs:

- [`perf_core_dlc_harmony`](/mnt/c/Users/keath/Dev-Mentor/tmp/rimworld_smoke/perf_core_dlc_harmony/1774017801385/Player.log)
- [`perf_core_dlc_harmony_loadingprogress_performanceoptimizer`](/mnt/c/Users/keath/Dev-Mentor/tmp/rimworld_smoke/perf_core_dlc_harmony_loadingprogress_performanceoptimizer/1774017806867/Player.log)
- [`perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman`](/mnt/c/Users/keath/Dev-Mentor/tmp/rimworld_smoke/perf_core_dlc_harmony_loadingprogress_performanceoptimizer_rocketman/1774017814933/Player.log)
