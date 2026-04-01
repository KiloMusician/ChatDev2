extends Control

# ── Tray menu item IDs ────────────────────────────────────────────────────────
const TRAY_SHOW_HIDE      := 1
const TRAY_REFRESH        := 2
const TRAY_GAMING         := 10
const TRAY_CODING         := 11
const TRAY_BALANCED       := 12
const TRAY_RIMWORLD       := 13
const TRAY_HEAVY_GAMING   := 14
const TRAY_DOCTOR         := 20
const TRAY_EXPORT         := 21
const TRAY_OPTIMIZE       := 30
const TRAY_OPTIMIZE_FORCE := 31
const TRAY_QUIT           := 99

# ── Node refs — existing status grid ─────────────────────────────────────────
@onready var keeper_bridge: KeeperBridge   = $KeeperBridge
@onready var tray: StatusIndicator         = $Tray
@onready var tray_menu: PopupMenu          = $TrayMenu
@onready var refresh_timer: Timer          = $RefreshTimer

@onready var mode_value: Label             = $Margin/Root/StatusGrid/ModeCard/VBox/ModeValue
@onready var recommendation_value: Label   = $Margin/Root/StatusGrid/RecommendationCard/VBox/RecommendationValue
@onready var cpu_value: Label              = $Margin/Root/StatusGrid/CpuCard/VBox/CpuValue
@onready var risk_value: Label             = $Margin/Root/StatusGrid/RiskCard/VBox/RiskValue
@onready var workload_value: Label         = $Margin/Root/WorkloadPanel/WorkloadBox/WorkloadValue
@onready var findings_text: RichTextLabel  = $Margin/Root/Body/FindingsPanel/FindingsBox/FindingsText
@onready var details_text: RichTextLabel   = $Margin/Root/Body/DetailsPanel/DetailsBox/DetailsText

# ── Node refs — buttons ───────────────────────────────────────────────────────
@onready var refresh_button: Button        = $Margin/Root/Buttons/RefreshButton
@onready var gaming_button: Button         = $Margin/Root/Buttons/GamingButton
@onready var coding_button: Button         = $Margin/Root/Buttons/CodingButton
@onready var balanced_button: Button       = $Margin/Root/Buttons/BalancedButton
@onready var doctor_button: Button         = $Margin/Root/Buttons/DoctorButton
@onready var export_button: Button         = $Margin/Root/Buttons/ExportButton

# ── Node refs — brain panel ───────────────────────────────────────────────────
@onready var score_label: Label            = $Margin/Root/BrainPanel/BrainBox/BrainHeader/ScoreLabel
@onready var status_badge: Label           = $Margin/Root/BrainPanel/BrainBox/BrainHeader/StatusBadge
@onready var score_bar: ProgressBar        = $Margin/Root/BrainPanel/BrainBox/ScoreBar
@onready var advisor_label: Label          = $Margin/Root/BrainPanel/BrainBox/AdvisorRow/AdvisorInfo/AdvisorLabel
@onready var why_label: Label              = $Margin/Root/BrainPanel/BrainBox/AdvisorRow/AdvisorInfo/WhyLabel
@onready var optimize_button: Button       = $Margin/Root/BrainPanel/BrainBox/AdvisorRow/BrainButtons/OptimizeButton
@onready var force_button: Button          = $Margin/Root/BrainPanel/BrainBox/AdvisorRow/BrainButtons/ForceButton

var last_snapshot: Dictionary = {}
var tray_enabled := false

# ── Lifecycle ─────────────────────────────────────────────────────────────────

func _ready() -> void:
    get_tree().set_auto_accept_quit(false)
    _wire_buttons()
    _configure_tray()
    refresh_timer.timeout.connect(_refresh_snapshot)
    _refresh_snapshot()

func _notification(what: int) -> void:
    if what == NOTIFICATION_WM_CLOSE_REQUEST:
        if tray_enabled:
            _hide_to_tray()
        else:
            get_tree().quit()

# ── Button wiring ─────────────────────────────────────────────────────────────

func _wire_buttons() -> void:
    refresh_button.pressed.connect(_refresh_snapshot)
    gaming_button.pressed.connect(func() -> void: _apply_mode("gaming"))
    coding_button.pressed.connect(func() -> void: _apply_mode("coding"))
    balanced_button.pressed.connect(func() -> void: _apply_mode("balanced"))
    doctor_button.pressed.connect(_refresh_doctor)
    export_button.pressed.connect(_export_report)
    optimize_button.pressed.connect(func() -> void: _apply_optimize(false))
    force_button.pressed.connect(func() -> void: _apply_optimize(true))

# ── Tray ──────────────────────────────────────────────────────────────────────

func _configure_tray() -> void:
    tray_enabled = DisplayServer.has_feature(DisplayServer.FEATURE_STATUS_INDICATOR)
    tray.visible = tray_enabled
    if not tray_enabled:
        return

    tray_menu.clear()
    tray_menu.add_item("Show / Hide Keeper", TRAY_SHOW_HIDE)
    tray_menu.add_separator()
    tray_menu.add_item("Refresh", TRAY_REFRESH)
    tray_menu.add_separator()
    tray_menu.add_item("Gaming Mode", TRAY_GAMING)
    tray_menu.add_item("Coding Mode", TRAY_CODING)
    tray_menu.add_item("Balanced Mode", TRAY_BALANCED)
    tray_menu.add_item("RimWorld-Mod Mode", TRAY_RIMWORLD)
    tray_menu.add_item("Heavy Gaming Mode", TRAY_HEAVY_GAMING)
    tray_menu.add_separator()
    tray_menu.add_item("Optimize (safe gate)", TRAY_OPTIMIZE)
    tray_menu.add_item("Optimize -Force", TRAY_OPTIMIZE_FORCE)
    tray_menu.add_separator()
    tray_menu.add_item("Doctor", TRAY_DOCTOR)
    tray_menu.add_item("Export HTML", TRAY_EXPORT)
    tray_menu.add_separator()
    tray_menu.add_item("Quit", TRAY_QUIT)
    tray_menu.id_pressed.connect(_on_tray_menu_id_pressed)
    tray.menu = tray_menu.get_path()
    tray.tooltip = "Keeper Shell"

func _on_tray_menu_id_pressed(id: int) -> void:
    match id:
        TRAY_SHOW_HIDE:
            if get_window().visible:
                _hide_to_tray()
            else:
                _show_window()
        TRAY_REFRESH:
            _refresh_snapshot()
        TRAY_GAMING:
            _apply_mode("gaming")
        TRAY_CODING:
            _apply_mode("coding")
        TRAY_BALANCED:
            _apply_mode("balanced")
        TRAY_RIMWORLD:
            _apply_mode("rimworld-mod")
        TRAY_HEAVY_GAMING:
            _apply_mode("heavy-gaming")
        TRAY_OPTIMIZE:
            _apply_optimize(false)
        TRAY_OPTIMIZE_FORCE:
            _apply_optimize(true)
        TRAY_DOCTOR:
            _refresh_doctor()
        TRAY_EXPORT:
            _export_report()
        TRAY_QUIT:
            get_tree().quit()

func _hide_to_tray() -> void:
    get_window().hide()

func _show_window() -> void:
    get_window().show()
    get_window().move_to_foreground()
    get_window().grab_focus()

# ── Bridge actions ────────────────────────────────────────────────────────────

func _refresh_snapshot() -> void:
    var response := keeper_bridge.invoke("snapshot")
    if not response.get("ok", false):
        _show_error(response)
        return

    last_snapshot = response.get("data", {})
    _render_snapshot(last_snapshot)

func _refresh_doctor() -> void:
    var response := keeper_bridge.invoke("doctor")
    if not response.get("ok", false):
        _show_error(response)
        return

    _render_findings(response.get("data", {}))

func _apply_mode(mode_name: String) -> void:
    var response := keeper_bridge.invoke("mode", PackedStringArray([mode_name]))
    if not response.get("ok", false):
        _show_error(response)
        return
    _refresh_snapshot()

func _apply_optimize(force: bool) -> void:
    var extra := PackedStringArray()
    if force:
        extra.append("-Force")
    var response := keeper_bridge.invoke("optimize", extra)
    if not response.get("ok", false):
        _show_error(response)
        return

    var data: Dictionary = response.get("data", {})
    var status_str: String = str(data.get("status", "unknown")).to_upper()
    var action_str: String = str(data.get("action", data.get("recommended", "none")))
    var reason_str: String = str(data.get("reason", data.get("why", "")))
    var applied = data.get("applied", null)

    var lines := PackedStringArray()
    lines.append("[b]Optimize: %s[/b]" % status_str)
    lines.append("Action: %s" % action_str)
    if not reason_str.is_empty():
        lines.append(reason_str)
    if applied != null and applied is Dictionary:
        var count = applied.get("count", applied.get("freed_mb", ""))
        if str(count) != "":
            lines.append("Result: %s" % str(count))
    details_text.text = "\n".join(lines)
    _refresh_snapshot()

func _export_report() -> void:
    var response := keeper_bridge.invoke("export", PackedStringArray(["-Html"]))
    if not response.get("ok", false):
        _show_error(response)
        return

    var data: Dictionary = response.get("data", {})
    var path := str(data.get("report_path", data.get("html_path", "created")))
    details_text.text = "[b]Export complete[/b]\n" + path

# ── Render ────────────────────────────────────────────────────────────────────

func _render_snapshot(snapshot: Dictionary) -> void:
    var health: Dictionary         = snapshot.get("health", {})
    var doctor: Dictionary         = snapshot.get("doctor", {})
    var recommendation: Dictionary = snapshot.get("recommendation", {})
    var steam: Dictionary          = snapshot.get("steam", {})
    var brain: Dictionary          = snapshot.get("brain", {})

    var mode_name    := str(health.get("mode", snapshot.get("current_state", {}).get("mode", "idle")))
    var cpu_percent  := str(health.get("cpu_percent", "n/a"))
    var free_mem     := str(health.get("free_mem_mb", "n/a"))
    var total_mem    := str(health.get("total_mem_mb", "n/a"))
    var docker_active := bool(health.get("docker_active", false))
    var wsl_active   := bool(health.get("wsl_active", false))

    mode_value.text           = mode_name
    recommendation_value.text = str(recommendation.get("recommended_mode", "unknown"))
    cpu_value.text            = "%s%% / %s MB free of %s MB" % [cpu_percent, free_mem, total_mem]
    risk_value.text           = str(doctor.get("risk_level", "unknown")).to_upper()

    var active_games: Array = steam.get("active_games", [])
    var game_names := PackedStringArray()
    for item in active_games:
        if item is Dictionary:
            game_names.append(str(item.get("GameName", item.get("ProcessName", "Unknown"))))

    var workload_lines := PackedStringArray()
    workload_lines.append("Docker: %s" % ("active" if docker_active else "idle"))
    workload_lines.append("WSL: %s" % ("active" if wsl_active else "idle"))
    workload_lines.append("Steam games: %s" % (", ".join(game_names) if game_names.size() > 0 else "none"))
    var offenders: Array = health.get("top_offenders", [])
    workload_lines.append("Top offenders: %s" % (", ".join(PackedStringArray(offenders)) if offenders.size() > 0 else "none"))
    workload_value.text = "\n".join(workload_lines)

    _render_brain(brain)
    _render_findings(doctor)
    _render_details(snapshot)

    if tray_enabled:
        var brain_score_str := ""
        if brain.has("score") and brain["score"] is Dictionary:
            brain_score_str = " | Score %s" % str(brain["score"].get("score", "--"))
        tray.tooltip = "Keeper Shell | %s | Risk %s%s" % [
            mode_name,
            str(doctor.get("risk_level", "unknown")).to_upper(),
            brain_score_str
        ]

func _render_brain(brain: Dictionary) -> void:
    var score_data: Dictionary  = brain.get("score", {})
    var advisor_data: Dictionary = brain.get("advisor", {})

    var score_val: int    = int(score_data.get("score", 0))
    var status_str: String = str(score_data.get("status", "ok"))
    var recommended: String = str(advisor_data.get("recommended", "none"))
    var why: String        = str(advisor_data.get("why", ""))
    var confidence: float  = float(advisor_data.get("confidence", 0.0))
    var safe: bool         = bool(advisor_data.get("safe_to_apply", false))

    score_label.text = "Score: %d" % score_val
    status_badge.text = status_str.to_upper()
    score_bar.value = score_val

    if recommended != "none" and not recommended.is_empty():
        var safe_tag := " [safe]" if safe else " [needs -Force]"
        advisor_label.text = "Recommended: %s  (%.0f%%%s)" % [recommended, confidence * 100.0, safe_tag]
    else:
        advisor_label.text = "No action recommended"
    why_label.text = why

    var has_action := recommended != "none" and not recommended.is_empty()
    optimize_button.disabled = not has_action
    force_button.disabled    = not has_action

    # Color status badge
    status_badge.remove_theme_color_override("font_color")
    match status_str:
        "critical": status_badge.add_theme_color_override("font_color", Color(1.0, 0.25, 0.25))
        "warning":  status_badge.add_theme_color_override("font_color", Color(1.0, 0.8,  0.1))
        "info":     status_badge.add_theme_color_override("font_color", Color(0.4, 0.8,  1.0))
        "ok":       status_badge.add_theme_color_override("font_color", Color(0.3, 1.0,  0.45))

func _render_findings(doctor: Dictionary) -> void:
    var findings: Array = doctor.get("findings", [])
    if findings.is_empty():
        findings_text.text = "[b]No urgent findings.[/b]"
        return

    var lines := PackedStringArray(["[b]Doctor findings[/b]"])
    for finding in findings:
        lines.append("- %s" % str(finding))
    findings_text.text = "\n".join(lines)

func _render_details(snapshot: Dictionary) -> void:
    var health: Dictionary         = snapshot.get("health", {})
    var recommendation: Dictionary = snapshot.get("recommendation", {})
    var automation: Dictionary     = snapshot.get("automation", {})
    var steam: Dictionary          = snapshot.get("steam", {})
    var brain: Dictionary          = snapshot.get("brain", {})
    var score_data: Dictionary     = brain.get("score", {})

    var lines := PackedStringArray()
    lines.append("[b]Offline-first[/b]")
    lines.append("Bridge-backed UI surface. No internet required.")
    lines.append("")

    # Brain signals
    if score_data.size() > 0:
        var signals: Dictionary = score_data.get("signals", {})
        lines.append("[b]Pressure Signals[/b]")
        lines.append("Disk:       %.1f%%" % (float(signals.get("diskPressure", 0)) * 100.0))
        lines.append("CPU:        %.1f%%" % (float(signals.get("cpuPressure",  0)) * 100.0))
        lines.append("RAM:        %.1f%%" % (float(signals.get("ramPressure",  0)) * 100.0))
        lines.append("Contention: %.1f%%" % (float(signals.get("backgroundContention", 0)) * 100.0))
        var issues: Array = score_data.get("issues", [])
        if issues.size() > 0:
            lines.append("")
            lines.append("[b]Issues[/b]")
            for issue in issues:
                lines.append("- %s" % str(issue))
        lines.append("")

    lines.append("[b]Recommendation[/b]")
    lines.append(str(recommendation.get("recommended_mode", "unknown")).to_upper())
    for reason in recommendation.get("reasons", []):
        lines.append("- %s" % str(reason))
    lines.append("")
    lines.append("[b]Automation[/b]")
    lines.append("Target mode: %s" % str(automation.get("target_mode", "unknown")))
    lines.append("Should apply: %s" % str(automation.get("should_apply", false)))
    lines.append("")
    lines.append("[b]Power / Audio[/b]")
    lines.append("Power plan: %s" % str(health.get("power_plan_raw", "unknown")))
    lines.append("Game Mode: %s" % str(health.get("game_mode_enabled", false)))
    lines.append("Sound devices: %s" % ", ".join(PackedStringArray(health.get("sound_devices", []))))
    lines.append("")
    lines.append("[b]Steam[/b]")
    lines.append("Libraries: %s" % ", ".join(PackedStringArray(steam.get("library_roots", []))))
    details_text.text = "\n".join(lines)

func _show_error(response: Dictionary) -> void:
    mode_value.text           = "error"
    recommendation_value.text = "check bridge"
    findings_text.text        = "[b]Bridge error[/b]\n%s" % str(response.get("error", "Unknown error"))
    details_text.text         = "[b]Response[/b]\n%s" % JSON.stringify(response, "  ")
