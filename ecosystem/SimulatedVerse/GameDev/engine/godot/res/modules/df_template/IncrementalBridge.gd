extends Node
class_name IncrementalBridge

signal resource_changed(id: StringName, value: float)
signal tick(delta: float)

var _engine := null

func _ready() -> void:
    # Try to discover template core manager or instantiate a minimal scene
    if has_node("/root/DF_Core"):
        _engine = get_node("/root/DF_Core")
    else:
        var scene := load("res://res/modules/df_template/_scenes/MinimalIncremental.tscn")
        if scene:
            var inst = scene.instantiate()
            inst.visible = false
            get_tree().root.add_child(inst)
            _engine = inst.get_node_or_null("DF_Core")
    if _engine and _engine.has_signal("resource_changed"):
        _engine.resource_changed.connect(func(id, v): resource_changed.emit(id, v))

func add_generator(conf: Dictionary) -> void:
    assert(_engine, "Template engine missing")
    if _engine.has_method("add_generator"):
        _engine.add_generator(conf)

func get_resource(id: StringName) -> float:
    assert(_engine, "Template engine missing")
    if _engine.has_method("get_resource"):
        return _engine.get_resource(id)
    return 0.0

func spend(id: StringName, amount: float) -> bool:
    assert(_engine, "Template engine missing")
    if _engine.has_method("spend"):
        return _engine.spend(id, amount)
    return false
