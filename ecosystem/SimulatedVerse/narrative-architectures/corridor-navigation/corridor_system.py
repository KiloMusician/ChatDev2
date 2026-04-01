"""
🏠 House of Leaves: Corridor System
Infinite branching modular architecture with dynamic pathways
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import os
import ast
import time

class ModuleState(Enum):
    STABLE = "stable"          # 🟢 Fully implemented and tested
    DEVELOPING = "developing"  # 🟡 Work in progress
    BROKEN = "broken"         # 🔴 Needs immediate attention
    PLACEHOLDER = "placeholder" # ⚪ Stub waiting for implementation
    EXPERIMENTAL = "experimental" # 🔵 Prototype or research code

class CorridorType(Enum):
    MAIN_HALLWAY = "main_hallway"      # Core system pathways
    SIDE_PASSAGE = "side_passage"      # Feature modules
    SECRET_ROOM = "secret_room"        # Experimental modules
    DEAD_END = "dead_end"              # Broken/incomplete modules
    SPIRAL_STAIR = "spiral_stair"      # Recursive modules
    HIDDEN_DOOR = "hidden_door"        # Easter eggs and dev tools

@dataclass
class ModuleCorridor:
    id: str
    name: str
    path: str
    corridor_type: CorridorType
    state: ModuleState
    connections: List[str]  # Connected corridor IDs
    description: str
    last_modified: float
    file_count: int = 0
    function_count: int = 0
    complexity_score: float = 0.0
    test_coverage: float = 0.0
    dependencies: Set[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()

class HouseArchitect:
    """Manages the infinite corridor system"""
    
    def __init__(self, root_path: str = "."):
        self.root_path = root_path
        self.corridors: Dict[str, ModuleCorridor] = {}
        self.corridor_map: Dict[str, Set[str]] = {}  # Adjacency map
        self.dead_ends: Set[str] = set()
        self.healing_queue: List[str] = []
        
        # Scan and build initial corridor structure
        self.scan_filesystem()
        self.build_corridor_connections()
        self.identify_dead_ends()
    
    def scan_filesystem(self):
        """Scan filesystem to create corridor structure"""
        for root, dirs, files in os.walk(self.root_path):
            # Skip hidden directories and common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and 
                      d not in ['__pycache__', 'node_modules', '.git']]
            
            # Create corridor for each directory
            rel_path = os.path.relpath(root, self.root_path)
            if rel_path == '.':
                corridor_id = 'root'
                corridor_name = 'Root Entrance'
            else:
                corridor_id = rel_path.replace(os.sep, '_')
                corridor_name = os.path.basename(root).replace('_', ' ').title()
            
            # Determine corridor type based on path and contents
            corridor_type = self._classify_corridor(root, files)
            
            # Analyze module state
            state = self._analyze_module_state(root, files)
            
            # Count files and analyze complexity
            py_files = [f for f in files if f.endswith('.py')]
            js_files = [f for f in files if f.endswith('.js')]
            code_files = py_files + js_files
            
            complexity = self._calculate_complexity(root, code_files)
            
            corridor = ModuleCorridor(
                id=corridor_id,
                name=corridor_name,
                path=rel_path,
                corridor_type=corridor_type,
                state=state,
                connections=[],
                description=f"Module containing {len(code_files)} code files",
                last_modified=self._get_last_modified(root),
                file_count=len(files),
                function_count=complexity.get('functions', 0),
                complexity_score=complexity.get('score', 0.0),
                test_coverage=self._estimate_test_coverage(root, files)
            )
            
            self.corridors[corridor_id] = corridor
    
    def _classify_corridor(self, path: str, files: List[str]) -> CorridorType:
        """Classify corridor type based on path and contents"""
        path_lower = path.lower()
        
        # Main system directories
        if any(core in path_lower for core in ['core', 'main', 'src', 'lib']):
            return CorridorType.MAIN_HALLWAY
        
        # Test and experimental directories
        if any(exp in path_lower for exp in ['test', 'experimental', 'prototype', 'draft']):
            return CorridorType.EXPERIMENTAL
        
        # Utility and tool directories
        if any(util in path_lower for util in ['util', 'tool', 'helper', 'debug']):
            return CorridorType.HIDDEN_DOOR
        
        # Check for recursive patterns
        if 'recursive' in path_lower or any('self' in f for f in files):
            return CorridorType.SPIRAL_STAIR
        
        # Check for dead ends (empty or broken)
        if not files or all(f.startswith('.') for f in files):
            return CorridorType.DEAD_END
        
        # Default to side passage
        return CorridorType.SIDE_PASSAGE
    
    def _analyze_module_state(self, path: str, files: List[str]) -> ModuleState:
        """Analyze the current state of a module"""
        code_files = [f for f in files if f.endswith(('.py', '.js', '.ts'))]
        
        if not code_files:
            if files:
                return ModuleState.PLACEHOLDER
            else:
                return ModuleState.BROKEN
        
        # Check for common indicators
        has_tests = any('test' in f.lower() for f in files)
        has_readme = any(f.lower().startswith('readme') for f in files)
        
        # Simple heuristic based on file patterns
        if has_tests and has_readme and len(code_files) > 1:
            return ModuleState.STABLE
        elif 'experimental' in path.lower() or 'prototype' in path.lower():
            return ModuleState.EXPERIMENTAL
        elif len(code_files) >= 3:
            return ModuleState.DEVELOPING
        else:
            return ModuleState.PLACEHOLDER
    
    def _calculate_complexity(self, path: str, code_files: List[str]) -> Dict[str, float]:
        """Calculate complexity metrics for a module"""
        total_functions = 0
        total_lines = 0
        total_complexity = 0.0
        
        for filename in code_files:
            file_path = os.path.join(path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    if filename.endswith('.py'):
                        # Simple Python AST analysis
                        try:
                            tree = ast.parse(content)
                            functions = [node for node in ast.walk(tree) 
                                       if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
                            total_functions += len(functions)
                            
                            # Simple complexity: lines per function
                            if functions:
                                total_complexity += lines / len(functions)
                        except:
                            pass
                    
                    elif filename.endswith(('.js', '.ts')):
                        # Simple JavaScript function counting
                        function_keywords = content.count('function ') + content.count('=>')
                        total_functions += function_keywords
                        if function_keywords > 0:
                            total_complexity += lines / function_keywords
            
            except Exception:
                continue
        
        return {
            'functions': total_functions,
            'lines': total_lines,
            'score': total_complexity / max(1, total_functions)
        }
    
    def _get_last_modified(self, path: str) -> float:
        """Get the last modification time of a directory"""
        try:
            return os.path.getmtime(path)
        except:
            return time.time()
    
    def _estimate_test_coverage(self, path: str, files: List[str]) -> float:
        """Estimate test coverage based on file patterns"""
        code_files = [f for f in files if f.endswith(('.py', '.js', '.ts')) 
                     and not f.startswith('test_')]
        test_files = [f for f in files if 'test' in f.lower()]
        
        if not code_files:
            return 0.0
        
        # Simple heuristic: test files / code files
        return min(1.0, len(test_files) / len(code_files))
    
    def build_corridor_connections(self):
        """Build connections between corridors based on file system hierarchy"""
        for corridor_id, corridor in self.corridors.items():
            # Connect to parent directory
            if corridor.path != '.' and os.sep in corridor.path:
                parent_path = os.path.dirname(corridor.path)
                parent_id = parent_path.replace(os.sep, '_') if parent_path != '.' else 'root'
                
                if parent_id in self.corridors:
                    corridor.connections.append(parent_id)
                    if corridor_id not in self.corridor_map:
                        self.corridor_map[corridor_id] = set()
                    if parent_id not in self.corridor_map:
                        self.corridor_map[parent_id] = set()
                    
                    self.corridor_map[corridor_id].add(parent_id)
                    self.corridor_map[parent_id].add(corridor_id)
            
            # Connect to subdirectories
            for other_id, other_corridor in self.corridors.items():
                if other_id != corridor_id:
                    if (other_corridor.path.startswith(corridor.path + os.sep) and
                        other_corridor.path.count(os.sep) == corridor.path.count(os.sep) + 1):
                        corridor.connections.append(other_id)
                        
                        if corridor_id not in self.corridor_map:
                            self.corridor_map[corridor_id] = set()
                        if other_id not in self.corridor_map:
                            self.corridor_map[other_id] = set()
                        
                        self.corridor_map[corridor_id].add(other_id)
                        self.corridor_map[other_id].add(corridor_id)
    
    def identify_dead_ends(self):
        """Identify corridors that are dead ends and need healing"""
        for corridor_id, corridor in self.corridors.items():
            is_dead_end = (
                corridor.state == ModuleState.BROKEN or
                corridor.corridor_type == CorridorType.DEAD_END or
                (corridor.file_count == 0 and len(corridor.connections) <= 1)
            )
            
            if is_dead_end:
                self.dead_ends.add(corridor_id)
                if corridor_id not in self.healing_queue:
                    self.healing_queue.append(corridor_id)
    
    def find_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Find path between two corridors using BFS"""
        if start_id not in self.corridors or end_id not in self.corridors:
            return None
        
        if start_id == end_id:
            return [start_id]
        
        visited = set()
        queue = [(start_id, [start_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            for neighbor_id in self.corridor_map.get(current_id, []):
                if neighbor_id == end_id:
                    return path + [neighbor_id]
                
                if neighbor_id not in visited:
                    queue.append((neighbor_id, path + [neighbor_id]))
        
        return None
    
    def get_corridor_ascii_map(self, center_id: str = 'root', radius: int = 3) -> str:
        """Generate ASCII map of corridors around a center point"""
        if center_id not in self.corridors:
            return "Invalid corridor ID"
        
        # Get corridors within radius
        visited = set()
        current_level = {center_id}
        all_corridors = {center_id}
        
        for _ in range(radius):
            next_level = set()
            for corridor_id in current_level:
                for neighbor_id in self.corridor_map.get(corridor_id, []):
                    if neighbor_id not in visited:
                        next_level.add(neighbor_id)
                        all_corridors.add(neighbor_id)
            
            visited.update(current_level)
            current_level = next_level
        
        # Generate ASCII representation
        lines = ["🏠 HOUSE OF LEAVES - CORRIDOR MAP", "═" * 40]
        
        # State icons
        state_icons = {
            ModuleState.STABLE: "🟢",
            ModuleState.DEVELOPING: "🟡", 
            ModuleState.BROKEN: "🔴",
            ModuleState.PLACEHOLDER: "⚪",
            ModuleState.EXPERIMENTAL: "🔵"
        }
        
        # Corridor type symbols
        type_symbols = {
            CorridorType.MAIN_HALLWAY: "═══",
            CorridorType.SIDE_PASSAGE: "───",
            CorridorType.SECRET_ROOM: "···",
            CorridorType.DEAD_END: "   ",
            CorridorType.SPIRAL_STAIR: "~~~",
            CorridorType.HIDDEN_DOOR: "???"
        }
        
        for corridor_id in sorted(all_corridors):
            corridor = self.corridors[corridor_id]
            icon = state_icons[corridor.state]
            symbol = type_symbols[corridor.corridor_type]
            
            # Connection indicators
            len(self.corridor_map.get(corridor_id, []))
            
            line = f"{icon} {symbol} {corridor.name}"
            if corridor_id == center_id:
                line += " [YOU ARE HERE]"
            if corridor_id in self.dead_ends:
                line += " [DEAD END]"
            
            lines.append(line)
            
            # Show connections
            for connected_id in sorted(self.corridor_map.get(corridor_id, []))[:3]:
                if connected_id in all_corridors:
                    connected_corridor = self.corridors[connected_id]
                    lines.append(f"  ├─ {connected_corridor.name}")
        
        # Add legend
        lines.extend([
            "",
            "📍 LEGEND:",
            "🟢 Stable  🟡 Developing  🔴 Broken  ⚪ Placeholder  🔵 Experimental",
            "═══ Main Hallway  ─── Side Passage  ··· Secret Room",
            "~~~ Spiral Stair   ??? Hidden Door",
            "",
            f"💊 Dead ends to heal: {len(self.dead_ends)}",
            f"🏗️ Total corridors: {len(self.corridors)}"
        ])
        
        return "\n".join(lines)
    
    def propose_healing(self, corridor_id: str) -> Dict[str, str]:
        """Propose healing actions for a dead end corridor"""
        if corridor_id not in self.corridors:
            return {"error": "Corridor not found"}
        
        corridor = self.corridors[corridor_id]
        proposals = []
        
        if corridor.state == ModuleState.BROKEN:
            proposals.append("Add basic module structure with __init__.py or index.js")
            proposals.append("Create placeholder functions with docstrings")
            proposals.append("Add basic tests to verify functionality")
        
        elif corridor.state == ModuleState.PLACEHOLDER:
            proposals.append("Implement core functionality based on module name")
            proposals.append("Add comprehensive documentation")
            proposals.append("Connect to related modules")
        
        elif corridor.file_count == 0:
            proposals.append("Create initial module files")
            proposals.append("Add README with module purpose")
            proposals.append("Establish connection patterns")
        
        return {
            "corridor": corridor.name,
            "current_state": corridor.state.value,
            "healing_actions": proposals
        }