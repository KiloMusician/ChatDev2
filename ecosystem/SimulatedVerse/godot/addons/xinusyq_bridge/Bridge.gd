extends Node

var ws := WebSocketPeer.new()
var connected := false
var retry_timer := 0.0
var latency_ms := 0.0
var last_ping := 0

@export var ws_url := "ws://127.0.0.1:8765"

func _ready():
    print("[XiNuSyQ Bridge] Initializing bridge connection...")
    connect_to_hub()

func connect_to_hub():
    var err = ws.connect_to_url(ws_url)
    if err == OK:
        connected = true
        print("[XiNuSyQ Bridge] Connection established to ", ws_url)
    else:
        connected = false
        print("[XiNuSyQ Bridge] Connection failed: ", err)

func _process(delta):
    if not connected:
        retry_timer += delta
        if retry_timer > 2.0:
            retry_timer = 0.0
            print("[XiNuSyQ Bridge] Retrying connection...")
            connect_to_hub()
        return

    ws.poll()
    while ws.get_available_packet_count() > 0:
        var raw = ws.get_packet().get_string_from_utf8()
        var msg = {}
        if raw.length() > 0:
            msg = JSON.parse_string(raw) if JSON.is_valid(raw) else {}
        if "type" in msg:
            match msg.type:
                "hello_ack":
                    print("[XiNuSyQ Bridge] Received hello_ack: ", msg.get("id", "unknown"))
                "apply_actions":
                    _apply_actions(msg)
                "system_status":
                    print("[XiNuSyQ Bridge] System status: ", msg.get("payload", {}))
                _:
                    print("[XiNuSyQ Bridge] Unknown message type: ", msg.type)

    # send heartbeat + minimal state
    if OS.get_ticks_msec() - last_ping > 1000:
        last_ping = OS.get_ticks_msec()
        var payload = {
            "fps": Engine.get_frames_per_second(),
            "entities": get_tree().get_node_count(),
            "memory_mb": OS.get_static_memory_usage_by_type().size(),
            "scene": get_tree().current_scene.name if get_tree().current_scene else "none"
        }
        var pkt = {"type":"state","payload":payload}
        ws.send_text(JSON.stringify(pkt))

func _apply_actions(msg):
    # Example action: spawn a node or load a scene
    # Actions are file-based (no eval) so it's safe for agents.
    # msg.actions = [{"op":"load_scene","path":"res://scenes/Test.tscn"}]
    if not msg.has("actions"): 
        return
        
    print("[XiNuSyQ Bridge] Applying ", msg.actions.size(), " actions")
    
    for a in msg.actions:
        match a.get("op", ""):
            "load_scene":
                var scene_path = a.get("path", "")
                if scene_path and ResourceLoader.exists(scene_path):
                    var s = load(scene_path)
                    if s:
                        var inst = s.instantiate()
                        get_tree().get_root().add_child(inst)
                        print("[XiNuSyQ Bridge] Loaded scene: ", scene_path)
                else:
                    print("[XiNuSyQ Bridge] Scene not found: ", scene_path)
            "spawn_node":
                var node_type = a.get("type", "Node")
                var node_name = a.get("name", "SpawnedNode")
                var new_node = Node.new()
                new_node.name = node_name
                get_tree().get_root().add_child(new_node)
                print("[XiNuSyQ Bridge] Spawned node: ", node_name)
            "send_message":
                var message = a.get("message", "Hello from XiNuSyQ!")
                print("[XiNuSyQ Bridge] Message: ", message)
            _:
                print("[XiNuSyQ Bridge] Unknown action: ", a.get("op", ""))

func send_hello():
    if connected:
        var hello_msg = {
            "type": "hello",
            "id": "godot_" + str(OS.get_ticks_msec()),
            "version": "4.0",
            "project": ProjectSettings.get_setting("application/config/name", "Unknown")
        }
        ws.send_text(JSON.stringify(hello_msg))

func _notification(what):
    if what == NOTIFICATION_WM_CLOSE_REQUEST:
        if connected:
            ws.close()
        get_tree().quit()