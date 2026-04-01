extends Node

func _ready() -> void:
    # Smoke test to be run headless/CI: checks autoload presence
    if Engine.has_singleton("IncrementalBridge"):
        print("[Smoke] IncrementalBridge autoload present ✅")
    else:
        push_error("[Smoke] IncrementalBridge missing ❌")
