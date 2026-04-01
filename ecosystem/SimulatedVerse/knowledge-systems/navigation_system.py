"""
🚪 Navigation System
Universal navigation between Temple of Knowledge, House of Leaves, and Oldest House
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

# Import the three architectural systems
try:
    from TempleOfKnowledge.Floor10_MetaOptimization.cascade_protocols import MetaOptimizer
    from TempleOfKnowledge.Floor05_KnowledgeManagement.documentation_system import KnowledgeLibrary
    from TempleOfKnowledge.Floor01_GameplayIntegration.colony_mechanics import ColonyState
    from HouseOfLeaves.corridor_system import HouseArchitect
    from OldestHouse.control_systems import OldestHouseControl
except ImportError:
    # Fallback for when modules aren't fully available
    MetaOptimizer = None
    KnowledgeLibrary = None
    ColonyState = None
    HouseArchitect = None
    OldestHouseControl = None

class ArchitecturalWing(Enum):
    TEMPLE = "temple"           # Temple of Knowledge
    HOUSE = "house"             # House of Leaves
    OLDEST = "oldest"           # Oldest House

class TransportType(Enum):
    ELEVATOR = "elevator"       # Vertical temple navigation
    CORRIDOR = "corridor"       # Horizontal house navigation  
    PORTAL = "portal"           # Cross-wing transportation
    EMERGENCY = "emergency"     # Emergency evacuation routes

@dataclass
class NavigationNode:
    id: str
    name: str
    wing: ArchitecturalWing
    coordinates: Tuple[int, int, int]  # x, y, z
    transport_types: List[TransportType]
    connections: List[str]  # Connected node IDs
    access_level: int = 1   # 1-10, higher requires clearance
    description: str = ""
    special_properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.special_properties is None:
            self.special_properties = {}

class UniversalNavigator:
    """Central navigation system connecting all three architectural wings"""
    
    def __init__(self):
        self.nodes: Dict[str, NavigationNode] = {}
        self.current_location = "temple_entrance"
        self.access_level = 1
        self.visited_nodes = set()
        self.navigation_history: List[str] = []
        
        # Initialize subsystems (with error handling)
        self.temple_optimizer = MetaOptimizer() if MetaOptimizer else None
        self.knowledge_library = KnowledgeLibrary() if KnowledgeLibrary else None
        self.colony_state = ColonyState() if ColonyState else None
        self.house_architect = HouseArchitect() if HouseArchitect else None
        self.oldest_house = OldestHouseControl() if OldestHouseControl else None
        
        # Build navigation network
        self._build_navigation_network()
    
    def _build_navigation_network(self):
        """Build the complete navigation network"""
        # Temple of Knowledge nodes (vertical floors)
        temple_nodes = [
            NavigationNode(
                "temple_entrance", "Temple Entrance", ArchitecturalWing.TEMPLE,
                (0, 0, 0), [TransportType.ELEVATOR, TransportType.PORTAL],
                ["temple_floor_01", "house_entrance", "oldest_entrance"],
                1, "Grand entrance with elevators to all floors"
            ),
            NavigationNode(
                "temple_floor_01", "Floor 01: Gameplay Integration", ArchitecturalWing.TEMPLE,
                (0, 0, 1), [TransportType.ELEVATOR],
                ["temple_entrance", "temple_floor_02"],
                1, "Colony mechanics and core game loops"
            ),
            NavigationNode(
                "temple_floor_05", "Floor 05: Knowledge Management", ArchitecturalWing.TEMPLE,
                (0, 0, 5), [TransportType.ELEVATOR],
                ["temple_floor_04", "temple_floor_06"],
                3, "Documentation systems and tutorials"
            ),
            NavigationNode(
                "temple_floor_10", "Floor 10: Meta-Optimization", ArchitecturalWing.TEMPLE,
                (0, 0, 10), [TransportType.ELEVATOR],
                ["temple_floor_09"],
                8, "Cascade protocols and self-improvement"
            )
        ]
        
        # House of Leaves nodes (branching corridors)
        house_nodes = [
            NavigationNode(
                "house_entrance", "House Entrance Hall", ArchitecturalWing.HOUSE,
                (10, 0, 0), [TransportType.CORRIDOR, TransportType.PORTAL],
                ["house_main_hallway", "temple_entrance", "oldest_entrance"],
                1, "Central hub with infinite corridor access"
            ),
            NavigationNode(
                "house_main_hallway", "Main Hallway", ArchitecturalWing.HOUSE,
                (15, 0, 0), [TransportType.CORRIDOR],
                ["house_entrance", "house_side_passage", "house_secret_room"],
                2, "Primary corridor with core system modules"
            ),
            NavigationNode(
                "house_secret_room", "Secret Development Room", ArchitecturalWing.HOUSE,
                (20, 5, 0), [TransportType.CORRIDOR],
                ["house_main_hallway"],
                5, "Hidden experimental modules and prototypes"
            ),
            NavigationNode(
                "house_spiral_stair", "Spiral Staircase", ArchitecturalWing.HOUSE,
                (25, 0, 0), [TransportType.CORRIDOR],
                ["house_main_hallway"],
                6, "Recursive modules and self-referential systems",
                {"recursive": True, "max_depth": 10}
            )
        ]
        
        # Oldest House nodes (containment facility)
        oldest_nodes = [
            NavigationNode(
                "oldest_entrance", "Director's Lobby", ArchitecturalWing.OLDEST,
                (0, 10, 0), [TransportType.PORTAL],
                ["oldest_directors_office", "temple_entrance", "house_entrance"],
                3, "Central command access point"
            ),
            NavigationNode(
                "oldest_directors_office", "Director's Office", ArchitecturalWing.OLDEST,
                (5, 10, 0), [TransportType.EMERGENCY],
                ["oldest_entrance", "oldest_containment", "oldest_research"],
                7, "Central command and oversight facility"
            ),
            NavigationNode(
                "oldest_containment", "Containment Sector", ArchitecturalWing.OLDEST,
                (10, 10, 0), [TransportType.EMERGENCY],
                ["oldest_directors_office"],
                8, "Anomaly containment cells and monitoring"
            ),
            NavigationNode(
                "oldest_research", "Research Laboratory", ArchitecturalWing.OLDEST,
                (0, 15, 0), [TransportType.EMERGENCY],
                ["oldest_directors_office"],
                5, "Safe experimentation and analysis facility"
            )
        ]
        
        # Register all nodes
        all_nodes = temple_nodes + house_nodes + oldest_nodes
        for node in all_nodes:
            self.nodes[node.id] = node
    
    def get_current_location_info(self) -> Dict[str, Any]:
        """Get detailed information about current location"""
        if self.current_location not in self.nodes:
            return {"error": "Unknown location"}
        
        node = self.nodes[self.current_location]
        
        # Get wing-specific context
        context = {}
        if node.wing == ArchitecturalWing.TEMPLE and self.temple_optimizer:
            context["optimization_status"] = self.temple_optimizer.get_optimization_report()
        elif node.wing == ArchitecturalWing.HOUSE and self.house_architect:
            context["corridor_map"] = self.house_architect.get_corridor_ascii_map()
        elif node.wing == ArchitecturalWing.OLDEST and self.oldest_house:
            context["control_status"] = self.oldest_house.get_status_report()
        
        return {
            "node": node,
            "available_exits": self._get_available_exits(node.id),
            "context": context,
            "access_granted": node.access_level <= self.access_level
        }
    
    def _get_available_exits(self, node_id: str) -> List[Dict[str, str]]:
        """Get available exits from current node"""
        if node_id not in self.nodes:
            return []
        
        node = self.nodes[node_id]
        exits = []
        
        for connection_id in node.connections:
            if connection_id in self.nodes:
                target = self.nodes[connection_id]
                exit_info = {
                    "id": connection_id,
                    "name": target.name,
                    "wing": target.wing.value,
                    "transport": self._get_transport_method(node, target),
                    "accessible": target.access_level <= self.access_level
                }
                exits.append(exit_info)
        
        return exits
    
    def _get_transport_method(self, from_node: NavigationNode, 
                            to_node: NavigationNode) -> str:
        """Determine transport method between nodes"""
        # Same wing
        if from_node.wing == to_node.wing:
            if from_node.wing == ArchitecturalWing.TEMPLE:
                return "elevator"
            elif from_node.wing == ArchitecturalWing.HOUSE:
                return "corridor"
            else:
                return "secured_passage"
        else:
            return "portal"
    
    def navigate_to(self, destination_id: str) -> Dict[str, Any]:
        """Navigate to a specific node"""
        if destination_id not in self.nodes:
            return {"success": False, "error": f"Unknown destination: {destination_id}"}
        
        destination = self.nodes[destination_id]
        
        # Check access level
        if destination.access_level > self.access_level:
            return {
                "success": False, 
                "error": f"Insufficient access level. Required: {destination.access_level}, Current: {self.access_level}"
            }
        
        # Check if destination is reachable from current location
        current_node = self.nodes[self.current_location]
        if destination_id not in current_node.connections:
            # Try to find a path
            path = self._find_path(self.current_location, destination_id)
            if not path:
                return {"success": False, "error": "No path available to destination"}
            
            # Navigate through path
            for step in path[1:]:  # Skip current location
                step_result = self.navigate_to(step)
                if not step_result["success"]:
                    return step_result
            
            return {"success": True, "path_taken": path}
        
        # Direct navigation
        previous_location = self.current_location
        self.current_location = destination_id
        self.visited_nodes.add(destination_id)
        self.navigation_history.append(destination_id)
        
        transport_method = self._get_transport_method(current_node, destination)
        
        return {
            "success": True,
            "from": previous_location,
            "to": destination_id,
            "transport": transport_method,
            "location_info": self.get_current_location_info()
        }
    
    def _find_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Find path between two nodes using BFS"""
        if start_id == end_id:
            return [start_id]
        
        visited = set()
        queue = [(start_id, [start_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            current_node = self.nodes[current_id]
            
            for connection_id in current_node.connections:
                if connection_id == end_id:
                    return path + [connection_id]
                
                if connection_id not in visited:
                    # Check access level for intermediate nodes
                    intermediate_node = self.nodes[connection_id]
                    if intermediate_node.access_level <= self.access_level:
                        queue.append((connection_id, path + [connection_id]))
        
        return None
    
    def get_navigation_map_ascii(self) -> str:
        """Generate ASCII map of entire navigation network"""
        lines = [
            "🚪 UNIVERSAL NAVIGATION MAP",
            "═" * 60
        ]
        
        # Wing sections
        wing_icons = {
            ArchitecturalWing.TEMPLE: "🛕",
            ArchitecturalWing.HOUSE: "🏠", 
            ArchitecturalWing.OLDEST: "🏛️"
        }
        
        for wing in ArchitecturalWing:
            lines.append(f"\n{wing_icons[wing]} {wing.value.upper()}:")
            
            wing_nodes = [node for node in self.nodes.values() if node.wing == wing]
            wing_nodes.sort(key=lambda n: n.coordinates[2])  # Sort by Z coordinate
            
            for node in wing_nodes:
                current_marker = " [YOU ARE HERE]" if node.id == self.current_location else ""
                visited_marker = "✓" if node.id in self.visited_nodes else " "
                access_marker = "🔒" if node.access_level > self.access_level else "🔓"
                
                lines.append(f"  {visited_marker} {access_marker} {node.name}{current_marker}")
                
                # Show connections
                connections = self._get_available_exits(node.id)
                for conn in connections[:2]:  # Show first 2 connections
                    transport_icon = {"elevator": "🛗", "corridor": "🚪", "portal": "🌀", "secured_passage": "🔐"}
                    icon = transport_icon.get(conn["transport"], "→")
                    lines.append(f"    {icon} → {conn['name']}")
        
        # Legend
        lines.extend([
            "",
            "📍 LEGEND:",
            "✓ Visited   🔓 Accessible   🔒 Restricted",
            "🛗 Elevator  🚪 Corridor    🌀 Portal",
            "",
            f"Access Level: {self.access_level}/10",
            f"Locations Visited: {len(self.visited_nodes)}/{len(self.nodes)}"
        ])
        
        return "\n".join(lines)
    
    def increase_access_level(self, new_level: int) -> bool:
        """Increase access level (security clearance)"""
        if new_level > self.access_level and new_level <= 10:
            self.access_level = new_level
            return True
        return False
    
    def get_wing_status(self, wing: ArchitecturalWing) -> Dict[str, Any]:
        """Get status for a specific architectural wing"""
        if wing == ArchitecturalWing.TEMPLE and self.temple_optimizer:
            return {
                "wing": "Temple of Knowledge",
                "status": "Active",
                "optimization_level": len(self.temple_optimizer.cascade_history),
                "available_floors": 10
            }
        
        elif wing == ArchitecturalWing.HOUSE and self.house_architect:
            return {
                "wing": "House of Leaves", 
                "status": "Expanding",
                "total_corridors": len(self.house_architect.corridors),
                "dead_ends": len(self.house_architect.dead_ends)
            }
        
        elif wing == ArchitecturalWing.OLDEST and self.oldest_house:
            active_breaches = len([b for b in self.oldest_house.active_breaches if not b.resolved])
            return {
                "wing": "Oldest House",
                "status": f"Threat Level {self.oldest_house.threat_level.value.upper()}",
                "contained_entities": len(self.oldest_house.entities),
                "active_breaches": active_breaches
            }
        
        else:
            return {"wing": wing.value, "status": "Unavailable"}

# Integration with ASCII interface
def render_navigation_interface(navigator: UniversalNavigator) -> str:
    """Render navigation interface for ASCII display"""
    location_info = navigator.get_current_location_info()
    
    lines = [
        "🚪 NAVIGATION CONSOLE",
        "═" * 40,
        f"📍 Current Location: {location_info['node'].name}",
        f"🏛️ Wing: {location_info['node'].wing.value.title()}",
        f"🔐 Access Level: {navigator.access_level}/10",
        "",
        "🚪 AVAILABLE EXITS:"
    ]
    
    exits = location_info["available_exits"]
    for i, exit_info in enumerate(exits, 1):
        access_icon = "🔓" if exit_info["accessible"] else "🔒"
        transport_icon = {"elevator": "🛗", "corridor": "🚪", "portal": "🌀"}.get(exit_info["transport"], "→")
        
        lines.append(f"{i}. {access_icon} {transport_icon} {exit_info['name']}")
    
    lines.extend([
        "",
        "⌨️ COMMANDS:",
        "[1-9] Navigate to exit",
        "[M] View full map", 
        "[S] Wing status",
        "[H] Navigation history"
    ])
    
    return "\n".join(lines)