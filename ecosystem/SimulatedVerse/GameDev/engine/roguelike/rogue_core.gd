extends Node2D
class_name RogueCore

# Roguelike Core - Literal Game Mechanic  
# Bridges symbolic dungeon_exploration_breath to actual turn-based movement and FOV

@export var dungeon_width: int = 50
@export var dungeon_height: int = 50
@export var fov_radius: int = 5

var player_pos: Vector2i = Vector2i(25, 25)
var dungeon_tiles: Array[Array] = []
var visible_tiles: Array[Vector2i] = []
var explored_tiles: Array[Vector2i] = []
var turn_count: int = 0

# Tile types
enum TileType { WALL, FLOOR, DOOR, STAIRS_UP, STAIRS_DOWN, CHEST, ENEMY }
var tile_chars = {
	TileType.WALL: "#",
	TileType.FLOOR: ".",
	TileType.DOOR: "+", 
	TileType.STAIRS_UP: "<",
	TileType.STAIRS_DOWN: ">",
	TileType.CHEST: "C",
	TileType.ENEMY: "E"
}

signal player_moved(old_pos: Vector2i, new_pos: Vector2i)
signal tile_discovered(pos: Vector2i, tile_type: TileType)
signal turn_completed(turn: int)
signal item_found(item_name: String)

func _ready():
	_generate_dungeon()
	_calculate_fov()
	print("[RogueCore] Dungeon generated: %dx%d, Player at (%d, %d)" % [dungeon_width, dungeon_height, player_pos.x, player_pos.y])

func _input(event):
	if event is InputEventKey and event.pressed:
		var moved = false
		var old_pos = player_pos
		
		match event.keycode:
			KEY_UP, KEY_W:
				moved = try_move(Vector2i(0, -1))
			KEY_DOWN, KEY_S:
				moved = try_move(Vector2i(0, 1))
			KEY_LEFT, KEY_A:
				moved = try_move(Vector2i(-1, 0))
			KEY_RIGHT, KEY_D:
				moved = try_move(Vector2i(1, 0))
		
		if moved:
			player_moved.emit(old_pos, player_pos)
			_calculate_fov()
			turn_count += 1
			turn_completed.emit(turn_count)

func try_move(direction: Vector2i) -> bool:
	var new_pos = player_pos + direction
	
	# Check bounds
	if new_pos.x < 0 or new_pos.x >= dungeon_width or new_pos.y < 0 or new_pos.y >= dungeon_height:
		return false
	
	# Check if tile is walkable
	var tile_type = dungeon_tiles[new_pos.y][new_pos.x]
	if tile_type == TileType.WALL:
		return false
	
	# Move player
	player_pos = new_pos
	
	# Handle special tiles
	match tile_type:
		TileType.CHEST:
			_open_chest(new_pos)
		TileType.STAIRS_DOWN:
			_descend_stairs()
		TileType.ENEMY:
			_encounter_enemy(new_pos)
	
	print("[RogueCore] Player moved to (%d, %d)" % [player_pos.x, player_pos.y])
	return true

func _generate_dungeon():
	"""Generate a simple dungeon with rooms and corridors"""
	# Initialize with walls
	dungeon_tiles = []
	for y in range(dungeon_height):
		var row = []
		for x in range(dungeon_width):
			row.append(TileType.WALL)
		dungeon_tiles.append(row)
	
	# Create rooms
	var room_count = 8
	var rooms: Array[Rect2i] = []
	
	for i in range(room_count):
		var room = _generate_random_room()
		if _is_room_valid(room, rooms):
			rooms.append(room)
			_carve_room(room)
	
	# Connect rooms with corridors
	for i in range(rooms.size() - 1):
		_carve_corridor(rooms[i].get_center(), rooms[i + 1].get_center())
	
	# Place special tiles
	_place_special_tiles(rooms)
	
	# Ensure player starting position is floor
	dungeon_tiles[player_pos.y][player_pos.x] = TileType.FLOOR

func _generate_random_room() -> Rect2i:
	var width = randi_range(5, 15)
	var height = randi_range(5, 15) 
	var x = randi_range(1, dungeon_width - width - 1)
	var y = randi_range(1, dungeon_height - height - 1)
	
	return Rect2i(x, y, width, height)

func _is_room_valid(room: Rect2i, existing_rooms: Array[Rect2i]) -> bool:
	for existing_room in existing_rooms:
		if room.intersects(existing_room):
			return false
	return true

func _carve_room(room: Rect2i):
	for y in range(room.position.y, room.position.y + room.size.y):
		for x in range(room.position.x, room.position.x + room.size.x):
			if x >= 0 and x < dungeon_width and y >= 0 and y < dungeon_height:
				dungeon_tiles[y][x] = TileType.FLOOR

func _carve_corridor(start: Vector2i, end: Vector2i):
	# Simple L-shaped corridor
	var current = start
	
	# Horizontal first
	while current.x != end.x:
		if current.x < end.x:
			current.x += 1
		else:
			current.x -= 1
		dungeon_tiles[current.y][current.x] = TileType.FLOOR
	
	# Then vertical
	while current.y != end.y:
		if current.y < end.y:
			current.y += 1
		else:
			current.y -= 1
		dungeon_tiles[current.y][current.x] = TileType.FLOOR

func _place_special_tiles(rooms: Array[Rect2i]):
	# Place chests in random rooms
	for i in range(min(3, rooms.size())):
		var room = rooms[randi_range(0, rooms.size())]
		var chest_pos = room.get_center()
		dungeon_tiles[chest_pos.y][chest_pos.x] = TileType.CHEST
	
	# Place stairs down in last room
	if rooms.size() > 0:
		var last_room = rooms[-1]
		var stairs_pos = last_room.get_center()
		dungeon_tiles[stairs_pos.y][stairs_pos.x] = TileType.STAIRS_DOWN

func _calculate_fov():
	"""Calculate field of view using simple circle algorithm"""
	visible_tiles.clear()
	
	for y in range(player_pos.y - fov_radius, player_pos.y + fov_radius + 1):
		for x in range(player_pos.x - fov_radius, player_pos.x + fov_radius + 1):
			if x >= 0 and x < dungeon_width and y >= 0 and y < dungeon_height:
				var distance = player_pos.distance_to(Vector2i(x, y))
				if distance <= fov_radius:
					var tile_pos = Vector2i(x, y)
					visible_tiles.append(tile_pos)
					
					if tile_pos not in explored_tiles:
						explored_tiles.append(tile_pos)
						tile_discovered.emit(tile_pos, dungeon_tiles[y][x])

func _open_chest(pos: Vector2i):
	dungeon_tiles[pos.y][pos.x] = TileType.FLOOR
	
	# Random loot
	var loot_items = ["Health Potion", "Magic Scroll", "Gold Coins", "Iron Key", "Strange Artifact"]
	var item = loot_items.pick_random()
	
	item_found.emit(item)
	print("[RogueCore] Found %s in chest!" % item)

func _descend_stairs():
	print("[RogueCore] Descended to next level")
	_generate_dungeon()  # New level
	_calculate_fov()

func _encounter_enemy(pos: Vector2i):
	print("[RogueCore] Enemy encountered!")
	# For now, just remove enemy. Combat system would go here.
	dungeon_tiles[pos.y][pos.x] = TileType.FLOOR

func get_visible_map() -> String:
	"""Generate ASCII representation of visible area"""
	var map_string = ""
	
	for y in range(player_pos.y - 10, player_pos.y + 11):
		for x in range(player_pos.x - 15, player_pos.x + 16):
			if x < 0 or x >= dungeon_width or y < 0 or y >= dungeon_height:
				map_string += " "
			elif Vector2i(x, y) == player_pos:
				map_string += "@"
			elif Vector2i(x, y) in visible_tiles:
				var tile_type = dungeon_tiles[y][x]
				map_string += tile_chars[tile_type]
			elif Vector2i(x, y) in explored_tiles:
				map_string += "."  # Previously seen
			else:
				map_string += " "  # Unknown
		map_string += "\n"
	
	return map_string

func get_stats() -> Dictionary:
	return {
		"player_position": player_pos,
		"turn_count": turn_count,
		"explored_tiles": explored_tiles.size(),
		"fov_radius": fov_radius,
		"dungeon_size": "%dx%d" % [dungeon_width, dungeon_height],
		"visible_tiles": visible_tiles.size()
	}