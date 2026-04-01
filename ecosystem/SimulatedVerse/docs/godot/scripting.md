# GDScript Scripting

GDScript is Godot's built-in scripting language.

## Basic Syntax
```gdscript
extends Node

func _ready():
    print("Hello World")

func _process(delta):
    # Called every frame
    pass
```

## Variables
```gdscript
var health = 100
var player_name = "Player"
var is_alive = true
```

## Functions
```gdscript
func take_damage(amount):
    health -= amount
    if health <= 0:
        die()

func die():
    queue_free()
```
