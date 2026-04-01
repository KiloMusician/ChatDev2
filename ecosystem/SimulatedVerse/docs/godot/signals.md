# Signals

Signals are Godot's observer pattern implementation.

## Defining Signals
```gdscript
signal health_changed(new_health)
signal player_died
```

## Emitting Signals
```gdscript
func take_damage(amount):
    health -= amount
    emit_signal("health_changed", health)
    if health <= 0:
        emit_signal("player_died")
```

## Connecting Signals
```gdscript
func _ready():
    player.connect("health_changed", self, "_on_health_changed")
    player.connect("player_died", self, "_on_player_died")
```
