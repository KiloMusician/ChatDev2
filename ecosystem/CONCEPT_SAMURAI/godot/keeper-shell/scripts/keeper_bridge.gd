extends Node
class_name KeeperBridge

const DEFAULT_COMMAND_TIMEOUT := true

var _pwsh_exe: String = ""

func _resolve_repo_root() -> String:
    var env_root := OS.get_environment("KEEPER_ROOT")
    if not env_root.is_empty():
        return env_root
    return ProjectSettings.globalize_path("res://../../")

func _resolve_bridge_path() -> String:
    var env_path := OS.get_environment("KEEPER_BRIDGE_PATH")
    if not env_path.is_empty():
        return env_path
    return _resolve_repo_root().path_join("tools").path_join("keeper-bridge.ps1")

func _resolve_powershell_executable() -> String:
    var preferred := OS.get_environment("KEEPER_PWSH_EXE")
    if not preferred.is_empty():
        return preferred
    if not _pwsh_exe.is_empty():
        return _pwsh_exe
    # Prefer PowerShell Core 7; fall back to Windows PowerShell 5.1
    var pf := OS.get_environment("PROGRAMFILES")
    if not pf.is_empty():
        var pwsh7 := pf + "\\PowerShell\\7\\pwsh.exe"
        if FileAccess.file_exists(pwsh7):
            _pwsh_exe = pwsh7
            return _pwsh_exe
    # Try LocalAppData (Windows Store install path)
    var local := OS.get_environment("LOCALAPPDATA")
    if not local.is_empty():
        var pwsh_store := local + "\\Microsoft\\WindowsApps\\pwsh.exe"
        if FileAccess.file_exists(pwsh_store):
            _pwsh_exe = pwsh_store
            return _pwsh_exe
    _pwsh_exe = "powershell.exe"
    return _pwsh_exe

func bridge_available() -> bool:
    return FileAccess.file_exists(_resolve_bridge_path())

func invoke(command: String, extra_args: PackedStringArray = PackedStringArray()) -> Dictionary:
    if not OS.has_feature("windows"):
        return {
            "ok": false,
            "error": "Keeper Shell currently expects to run on Windows."
        }

    var bridge_path := _resolve_bridge_path()
    if not FileAccess.file_exists(bridge_path):
        return {
            "ok": false,
            "error": "keeper-bridge.ps1 was not found.",
            "bridge_path": bridge_path
        }

    var args := PackedStringArray([
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        bridge_path,
        command
    ])
    for arg in extra_args:
        args.append(arg)

    var output := []
    var exit_code := OS.execute(_resolve_powershell_executable(), args, output, DEFAULT_COMMAND_TIMEOUT)
    var raw := "\n".join(output).strip_edges()

    if raw.is_empty():
        return {
            "ok": false,
            "error": "Bridge returned no output.",
            "exit_code": exit_code
        }

    var parsed = JSON.parse_string(raw)
    if parsed == null:
        return {
            "ok": false,
            "error": "Bridge returned non-JSON output.",
            "exit_code": exit_code,
            "raw": raw
        }

    if parsed is Dictionary:
        parsed["exit_code"] = exit_code
        return parsed

    return {
        "ok": false,
        "error": "Bridge returned an unexpected JSON payload.",
        "exit_code": exit_code,
        "raw": raw
    }
