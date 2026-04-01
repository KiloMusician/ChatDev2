extends Node2D
class_name WaveSpawner

# Wave Spawner - Literal Game Mechanic
# Bridges symbolic wave system to actual enemy spawning with escalation

@export var enemy_scene: PackedScene
@export var spawn_points: Array[Vector2] = []
@export var path_points: Array[Vector2] = []

var current_wave: int = 0
var enemies_in_wave: int = 5
var enemies_spawned: int = 0
var enemies_remaining: int = 0
var wave_active: bool = false
var spawn_timer: float = 0.0
var spawn_interval: float = 2.0

signal wave_started(wave_number: int)
signal wave_completed(wave_number: int)
signal enemy_spawned(enemy: Enemy)
signal all_waves_completed()

func _ready():
        print("[WaveSpawner] Initialized with %d spawn points" % spawn_points.size())
        
        # Auto-assign enemy scene if none provided
        if not enemy_scene:
                enemy_scene = preload("res://GameDev/engine/tower_defense/Enemy.gd")
                print("[WaveSpawner] Auto-assigned Enemy scene")
        
        # Default path if none provided
        if path_points.is_empty():
                _create_default_path()

func _process(delta):
        if wave_active and enemies_spawned < enemies_in_wave:
                spawn_timer -= delta
                
                if spawn_timer <= 0.0:
                        _spawn_enemy()
                        spawn_timer = spawn_interval

func start_wave():
        if wave_active:
                return false
        
        current_wave += 1
        enemies_in_wave = _calculate_wave_size()
        enemies_spawned = 0
        enemies_remaining = enemies_in_wave
        wave_active = true
        spawn_timer = 0.0
        
        wave_started.emit(current_wave)
        print("[WaveSpawner] Wave %d started: %d enemies" % [current_wave, enemies_in_wave])
        
        return true

func _spawn_enemy():
        if not enemy_scene:
                print("[WaveSpawner] WARNING: No enemy scene assigned, using fallback")
                enemy_scene = preload("res://GameDev/engine/tower_defense/Enemy.gd")
                if not enemy_scene:
                        print("[WaveSpawner] ERROR: Could not load Enemy scene!")
                        return
        
        var enemy_instance = enemy_scene.instantiate() as Enemy
        if not enemy_instance:
                print("[WaveSpawner] ERROR: Enemy scene does not contain Enemy class!")
                return
        
        # Choose spawn point
        var spawn_point = spawn_points[0] if spawn_points.size() > 0 else Vector2.ZERO
        if spawn_points.size() > 1:
                spawn_point = spawn_points.pick_random()
        
        # Set up enemy
        get_parent().add_child(enemy_instance)
        enemy_instance.initialize(path_points)
        
        # Scale enemy stats based on wave
        enemy_instance.max_health *= _get_health_scaling()
        enemy_instance.health = enemy_instance.max_health
        enemy_instance.speed *= _get_speed_scaling()
        enemy_instance.reward = int(enemy_instance.reward * _get_reward_scaling())
        
        # Connect signals
        enemy_instance.enemy_died.connect(_on_enemy_died)
        enemy_instance.enemy_reached_end.connect(_on_enemy_reached_end)
        
        enemies_spawned += 1
        enemy_spawned.emit(enemy_instance)
        
        print("[WaveSpawner] Spawned enemy %d/%d (Wave %d)" % [enemies_spawned, enemies_in_wave, current_wave])

func _on_enemy_died(enemy: Enemy):
        enemies_remaining -= 1
        _check_wave_complete()

func _on_enemy_reached_end(enemy: Enemy):
        enemies_remaining -= 1
        _check_wave_complete()
        # Player loses life/health here

func _check_wave_complete():
        if enemies_remaining <= 0 and enemies_spawned >= enemies_in_wave:
                wave_active = false
                wave_completed.emit(current_wave)
                print("[WaveSpawner] Wave %d completed!" % current_wave)
                
                # Check for final wave
                if current_wave >= 10:  # Example: 10 waves total
                        all_waves_completed.emit()
                        print("[WaveSpawner] All waves completed! Victory!")

func _calculate_wave_size() -> int:
        # Progressive wave scaling
        return 5 + current_wave * 2

func _get_health_scaling() -> float:
        return 1.0 + (current_wave - 1) * 0.15

func _get_speed_scaling() -> float:
        return 1.0 + (current_wave - 1) * 0.05

func _get_reward_scaling() -> float:
        return 1.0 + (current_wave - 1) * 0.1

func _create_default_path():
        # Create a simple straight path across the screen
        path_points = [
                Vector2(0, 100),
                Vector2(200, 100),
                Vector2(400, 100),
                Vector2(600, 100),
                Vector2(800, 100)
        ]
        
        if spawn_points.is_empty():
                spawn_points = [Vector2(-50, 100)]

func get_wave_info() -> Dictionary:
        return {
                "current_wave": current_wave,
                "wave_active": wave_active,
                "enemies_in_wave": enemies_in_wave,
                "enemies_spawned": enemies_spawned,
                "enemies_remaining": enemies_remaining,
                "next_enemy_in": spawn_timer
        }

# Preview next wave stats
func preview_next_wave() -> Dictionary:
        var next_wave = current_wave + 1
        return {
                "wave_number": next_wave,
                "enemy_count": 5 + next_wave * 2,
                "enemy_health": 100 * (1.0 + next_wave * 0.15),
                "enemy_speed": 50 * (1.0 + next_wave * 0.05),
                "estimated_duration": (5 + next_wave * 2) * spawn_interval
        }