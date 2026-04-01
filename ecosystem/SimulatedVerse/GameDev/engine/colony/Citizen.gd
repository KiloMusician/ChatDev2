extends CharacterBody2D
class_name Citizen

# Colony Citizen - Literal Game Mechanic
# Bridges symbolic colonist breath to actual AI behavior and job system

@export var citizen_name: String = ""
@export var job: String = "unemployed"
@export var skill_level: int = 1
@export var happiness: float = 50.0
@export var energy: float = 100.0
@export var hunger: float = 0.0

var assigned_building: Node2D = null
var current_task: String = "idle"
var task_progress: float = 0.0
var work_efficiency: float = 1.0
var traits: Array[String] = []

# AI State Machine
enum AIState { IDLE, WORKING, EATING, SLEEPING, SOCIALIZING }
var current_state: AIState = AIState.IDLE
var state_timer: float = 0.0

signal task_completed(citizen: Citizen, task: String)
signal job_changed(citizen: Citizen, old_job: String, new_job: String)
signal happiness_changed(citizen: Citizen, new_happiness: float)

func _ready():
	if citizen_name.is_empty():
		citizen_name = _generate_random_name()
	
	_assign_random_traits()
	print("[Citizen] %s initialized: Job=%s, Happiness=%.1f" % [citizen_name, job, happiness])

func _process(delta):
	_update_needs(delta)
	_update_ai_state(delta)
	_execute_current_state(delta)

func _update_needs(delta):
	# Hunger increases over time
	hunger += delta * 0.1
	
	# Energy decreases during work, increases during sleep
	if current_state == AIState.WORKING:
		energy -= delta * 0.2
	elif current_state == AIState.SLEEPING:
		energy += delta * 0.5
		hunger -= delta * 0.1  # Sleeping reduces hunger slightly
	
	# Happiness affects work efficiency
	work_efficiency = 0.5 + (happiness / 100.0) * 0.5
	
	# Clamp values
	hunger = clampf(hunger, 0.0, 100.0)
	energy = clampf(energy, 0.0, 100.0)
	happiness = clampf(happiness, 0.0, 100.0)

func _update_ai_state(delta):
	state_timer += delta
	
	# State transition logic
	match current_state:
		AIState.IDLE:
			if hunger > 70.0:
				_change_state(AIState.EATING)
			elif energy < 30.0:
				_change_state(AIState.SLEEPING)
			elif job != "unemployed" and assigned_building:
				_change_state(AIState.WORKING)
		
		AIState.WORKING:
			if hunger > 80.0 or energy < 20.0:
				_change_state(AIState.IDLE)
			elif state_timer > 30.0:  # Work for 30 seconds, then break
				_change_state(AIState.SOCIALIZING)
		
		AIState.EATING:
			if state_timer > 5.0:  # 5 seconds to eat
				hunger -= 40.0
				_change_state(AIState.IDLE)
		
		AIState.SLEEPING:
			if energy > 80.0 or state_timer > 20.0:
				_change_state(AIState.IDLE)
		
		AIState.SOCIALIZING:
			if state_timer > 10.0:  # 10 seconds of socializing
				happiness += 10.0
				_change_state(AIState.IDLE)

func _execute_current_state(delta):
	match current_state:
		AIState.WORKING:
			_perform_work(delta)
		AIState.EATING:
			_animate_eating()
		AIState.SLEEPING:
			_animate_sleeping()
		AIState.SOCIALIZING:
			_animate_socializing()
		AIState.IDLE:
			_animate_idle()

func _change_state(new_state: AIState):
	current_state = new_state
	state_timer = 0.0
	print("[Citizen] %s changed state to %s" % [citizen_name, AIState.keys()[new_state]])

func assign_job(new_job: String, building: Node2D = null):
	var old_job = job
	job = new_job
	assigned_building = building
	
	# Job-specific skill bonuses
	match new_job:
		"farmer":
			if "green_thumb" in traits:
				skill_level += 1
		"miner":
			if "strong" in traits:
				skill_level += 1
		"researcher":
			if "intelligent" in traits:
				skill_level += 1
	
	job_changed.emit(self, old_job, new_job)
	print("[Citizen] %s assigned to %s job" % [citizen_name, new_job])

func _perform_work(delta):
	if not assigned_building:
		return
	
	task_progress += delta * work_efficiency * skill_level
	
	if task_progress >= 10.0:  # Task takes 10 seconds base time
		_complete_task()
		task_progress = 0.0

func _complete_task():
	var output_amount = skill_level * work_efficiency
	
	match job:
		"farmer":
			# Produce food
			task_completed.emit(self, "food_produced")
		"miner":
			# Produce materials
			task_completed.emit(self, "materials_produced")
		"researcher":
			# Produce research points
			task_completed.emit(self, "research_produced")
		"builder":
			# Advance construction
			task_completed.emit(self, "construction_progress")
	
	# Gain experience
	if randf() < 0.1:  # 10% chance to level up
		skill_level += 1
		happiness += 5.0
		print("[Citizen] %s leveled up! New skill level: %d" % [citizen_name, skill_level])

func _assign_random_traits():
	var possible_traits = ["hardworker", "lazy", "intelligent", "strong", "social", "green_thumb", "night_owl"]
	var num_traits = randi_range(1, 3)
	
	for i in range(num_traits):
		var trait = possible_traits.pick_random()
		if trait not in traits:
			traits.append(trait)
	
	_apply_trait_effects()

func _apply_trait_effects():
	for trait in traits:
		match trait:
			"hardworker":
				work_efficiency += 0.2
			"lazy":
				work_efficiency -= 0.1
			"intelligent":
				if job == "researcher":
					work_efficiency += 0.3
			"social":
				happiness += 10.0
			"night_owl":
				# Could work better at night
				pass

func _generate_random_name() -> String:
	var first_names = ["Alex", "Casey", "Jordan", "Riley", "Sage", "Quinn", "Avery", "Blake"]
	var last_names = ["Smith", "Chen", "Garcia", "Johnson", "Kim", "Patel", "Brown", "Davis"]
	
	return first_names.pick_random() + " " + last_names.pick_random()

func _animate_working():
	# Placeholder for work animation
	pass

func _animate_eating():
	# Placeholder for eating animation
	pass

func _animate_sleeping():
	# Placeholder for sleeping animation
	pass

func _animate_socializing():
	# Placeholder for social animation
	pass

func _animate_idle():
	# Placeholder for idle animation
	pass

func get_stats() -> Dictionary:
	return {
		"name": citizen_name,
		"job": job,
		"skill_level": skill_level,
		"happiness": happiness,
		"energy": energy,
		"hunger": hunger,
		"work_efficiency": work_efficiency,
		"traits": traits,
		"current_state": AIState.keys()[current_state],
		"task_progress": task_progress
	}

func get_productivity() -> float:
	return skill_level * work_efficiency * (happiness / 100.0)