extends Node2D

var spawn_count = 0

func _ready():
    print("[TestSpawn] Ready to spawn nodes via bridge commands")

func _input(event):
    if event is InputEventKey and event.pressed:
        match event.keycode:
            KEY_F1:
                # Send hello message to bridge
                var bridge = get_node("../XiNuSyQBridge")
                if bridge:
                    bridge.send_hello()
            KEY_F2:
                # Spawn a test node locally
                spawn_test_node()

func spawn_test_node():
    var new_node = ColorRect.new()
    new_node.size = Vector2(50, 50)
    new_node.color = Color(randf(), randf(), randf())
    new_node.position = Vector2(randf() * 800, randf() * 600)
    new_node.name = "SpawnedRect_" + str(spawn_count)
    spawn_count += 1
    
    add_child(new_node)
    print("[TestSpawn] Spawned: ", new_node.name)
    
    # Auto-remove after 5 seconds
    get_tree().create_timer(5.0).timeout.connect(func(): new_node.queue_free())