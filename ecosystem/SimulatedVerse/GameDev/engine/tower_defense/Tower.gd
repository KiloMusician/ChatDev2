extends Node2D
class_name Tower

# Tower Defense - Literal Game Mechanic
# Bridges symbolic "ΞΘΛΔ_tower_breath" to actual executable tower logic

@export var damage: float = 25.0
@export var range: float = 100.0
@export var fire_rate: float = 1.0
@export var cost: int = 50
@export var tower_type: String = "basic"

var targets_in_range: Array[Enemy] = []
var fire_timer: float = 0.0
var level: int = 1
var total_damage_dealt: float = 0.0
var enemies_killed: int = 0

signal enemy_killed(enemy: Enemy)
signal damage_dealt(amount: float)

func _ready():
	# Set up detection area
	var detection_area = Area2D.new()
	var collision_shape = CollisionShape2D.new()
	var circle_shape = CircleShape2D.new()
	
	circle_shape.radius = range
	collision_shape.shape = circle_shape
	detection_area.add_child(collision_shape)
	add_child(detection_area)
	
	detection_area.body_entered.connect(_on_enemy_entered)
	detection_area.body_exited.connect(_on_enemy_exited)
	
	print("[Tower] Initialized: Type=%s, Damage=%.1f, Range=%.1f" % [tower_type, damage, range])

func _process(delta):
	fire_timer -= delta
	
	# Auto-target and fire at enemies in range
	if fire_timer <= 0.0 and targets_in_range.size() > 0:
		var target = _select_target()
		if target != null:
			_fire_at_target(target)
			fire_timer = 1.0 / fire_rate

func _on_enemy_entered(body):
	if body is Enemy:
		targets_in_range.append(body)
		print("[Tower] Enemy entered range: %s" % body.name)

func _on_enemy_exited(body):
	if body is Enemy:
		targets_in_range.erase(body)

func _select_target() -> Enemy:
	if targets_in_range.is_empty():
		return null
	
	# Target closest enemy (or implement different strategies)
	var closest_enemy: Enemy = null
	var closest_distance: float = INF
	
	for enemy in targets_in_range:
		if not is_instance_valid(enemy):
			targets_in_range.erase(enemy)
			continue
			
		var distance = global_position.distance_to(enemy.global_position)
		if distance < closest_distance:
			closest_distance = distance
			closest_enemy = enemy
	
	return closest_enemy

func _fire_at_target(target: Enemy):
	if not is_instance_valid(target):
		return
	
	# Create projectile or instant damage
	var actual_damage = damage * _get_damage_multiplier()
	target.take_damage(actual_damage)
	
	total_damage_dealt += actual_damage
	damage_dealt.emit(actual_damage)
	
	if target.health <= 0:
		enemies_killed += 1
		enemy_killed.emit(target)
	
	print("[Tower] Fired at %s for %.1f damage" % [target.name, actual_damage])

func upgrade():
	level += 1
	damage *= 1.2
	range *= 1.1
	fire_rate *= 1.1
	
	print("[Tower] Upgraded to level %d: Damage=%.1f, Range=%.1f" % [level, damage, range])
	return true

func can_afford_upgrade(player_resources: int) -> bool:
	return player_resources >= get_upgrade_cost()

func get_upgrade_cost() -> int:
	return cost * level * 2

func _get_damage_multiplier() -> float:
	# Apply any buffs or debuffs
	return 1.0 + (level - 1) * 0.1

func get_stats() -> Dictionary:
	return {
		"type": tower_type,
		"level": level,
		"damage": damage,
		"range": range,
		"fire_rate": fire_rate,
		"enemies_killed": enemies_killed,
		"total_damage": total_damage_dealt,
		"upgrade_cost": get_upgrade_cost()
	}