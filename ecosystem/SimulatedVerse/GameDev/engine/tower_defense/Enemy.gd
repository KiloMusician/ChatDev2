extends CharacterBody2D
class_name Enemy

# Enemy - Literal Game Mechanic
# Bridges symbolic enemy spawning to actual pathfinding and health systems

@export var max_health: float = 100.0
@export var speed: float = 50.0
@export var reward: int = 10
@export var enemy_type: String = "basic"

var health: float
var path_points: Array[Vector2] = []
var current_path_index: int = 0
var is_alive: bool = true

signal enemy_died(enemy: Enemy)
signal enemy_reached_end(enemy: Enemy)
signal health_changed(current: float, max: float)

func _ready():
	health = max_health
	print("[Enemy] Spawned: Type=%s, Health=%.1f, Speed=%.1f" % [enemy_type, health, speed])

func initialize(spawn_path: Array[Vector2]):
	path_points = spawn_path.duplicate()
	if path_points.size() > 0:
		global_position = path_points[0]
		current_path_index = 1

func _physics_process(delta):
	if not is_alive or path_points.is_empty():
		return
	
	# Move along path
	if current_path_index < path_points.size():
		var target_point = path_points[current_path_index]
		var direction = (target_point - global_position).normalized()
		
		velocity = direction * speed
		move_and_slide()
		
		# Check if reached current waypoint
		if global_position.distance_to(target_point) < 5.0:
			current_path_index += 1
			
			if current_path_index >= path_points.size():
				# Reached end of path
				_reach_end()
	else:
		_reach_end()

func take_damage(amount: float):
	if not is_alive:
		return
	
	health -= amount
	health_changed.emit(health, max_health)
	
	print("[Enemy] %s took %.1f damage (%.1f/%.1f HP)" % [name, amount, health, max_health])
	
	if health <= 0:
		_die()

func _die():
	is_alive = false
	enemy_died.emit(self)
	print("[Enemy] %s died, reward: %d" % [name, reward])
	
	# Death animation or effects could go here
	queue_free()

func _reach_end():
	is_alive = false
	enemy_reached_end.emit(self)
	print("[Enemy] %s reached the end!" % name)
	queue_free()

func get_health_percentage() -> float:
	return health / max_health

func get_stats() -> Dictionary:
	return {
		"type": enemy_type,
		"health": health,
		"max_health": max_health,
		"speed": speed,
		"reward": reward,
		"position": global_position,
		"alive": is_alive,
		"progress": float(current_path_index) / float(path_points.size())
	}

# Buff/debuff system for future expansion
func apply_slow(duration: float, slow_factor: float = 0.5):
	var original_speed = speed
	speed *= slow_factor
	
	await get_tree().create_timer(duration).timeout
	speed = original_speed
	print("[Enemy] %s slow effect ended" % name)

func apply_poison(duration: float, damage_per_second: float):
	var poison_timer = 0.0
	while poison_timer < duration and is_alive:
		await get_tree().process_frame
		poison_timer += get_process_delta_time()
		
		if int(poison_timer) % 1 == 0:  # Once per second
			take_damage(damage_per_second)