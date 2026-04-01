# Idle Merge Plan — GodotProjectZero (branch preview)

Goal: vendor a minimal `template/` slice from TinyTakinTeller/GodotProjectZero
into `res://modules/df_template` under the GameDev Godot project and expose a
safe `IncrementalBridge` autoload for our UI and gameplay code.

What this preview adds:

- `res/modules/df_template/IncrementalBridge.gd` — bridge adapter (autoload)
- `.github/workflows/godot-idle-smoke.yml` — non-blocking CI smoke
- `THIRD_PARTY.md` — vendor/submodule instructions

Next steps for full integration:

1. Add upstream as submodule: `external/GodotProjectZero`
2. Robocopy `template/` →
   `SimulatedVerse/GameDev/engine/godot/res/modules/df_template/` (selective
   copy)
3. Audit InputMap, Groups, and autoload names
4. Run headless boot smoke in CI and adjust paths
5. Create `THIRD_PARTY.md` entries per-vendored asset

Vendor checklist & copy script (branch-only preview)

When you're ready to vendor the template slice after adding the submodule, run
the following from the repository root (PowerShell):

```powershell
# ensure submodule is present
git submodule update --init --recursive

# create the namespaced module dir (adjust if your godot root differs)
mkdir -Force ".\SimulatedVerse\GameDev\engine\godot\res\modules\df_template"

# copy the template slice into the namespaced module
robocopy external\GodotProjectZero\template SimulatedVerse\GameDev\engine\godot\res\modules\df_template /E

# optionally copy supporting helpers if the template needs them
robocopy external\GodotProjectZero\global SimulatedVerse\GameDev\engine\godot\res\modules\df_template\_global /E
robocopy external\GodotProjectZero\resources SimulatedVerse\GameDev\engine\godot\res\modules\df_template\_resources /E
robocopy external\GodotProjectZero\scenes SimulatedVerse\GameDev\engine\godot\res\modules\df_template\_scenes /E
```

Expected template files to verify after copy (examples; upstream may differ):

- `template/main.tscn` or `template/_scenes/MinimalIncremental.tscn`
- `template/scripts/idle_logic.gd` or similar core engine script(s)
- `template/resources/*.tres` data resources (growth curves, cost tables)
- `template/assets/*` (art/sfx — note licenses in `THIRD_PARTY.md`)

Run a quick existence check after the copy:

```powershell
gci .\SimulatedVerse\GameDev\engine\godot\res\modules\df_template -Recurse -Include *.tscn,*.gd,*.tres,*.res | Select-Object FullName
```

If those files are present, proceed with InputMap / Groups audit (see earlier
section).
