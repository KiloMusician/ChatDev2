"""
🔗 Node Graph Editor
TouchDesigner-style node patching system in ASCII
"""

from textual.widget import Widget
from textual.reactive import reactive
from textual import events
from rich.text import Text
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json

from ..palette import pick

class NodeType(Enum):
    INPUT = "input"
    PROCESS = "process"
    OUTPUT = "output"
    GENERATOR = "generator"
    FILTER = "filter"
    ANALYZER = "analyzer"

@dataclass
class NodePort:
    name: str
    type: str  # "input" or "output"
    data_type: str  # "audio", "visual", "data", "control"
    connected_to: Set[str] = None
    
    def __post_init__(self):
        if self.connected_to is None:
            self.connected_to = set()

@dataclass
class Node:
    id: str
    name: str
    node_type: NodeType
    x: int
    y: int
    width: int = 12
    height: int = 6
    inputs: List[NodePort] = None
    outputs: List[NodePort] = None
    parameters: Dict = None
    active: bool = True
    
    def __post_init__(self):
        if self.inputs is None:
            self.inputs = []
        if self.outputs is None:
            self.outputs = []
        if self.parameters is None:
            self.parameters = {}

@dataclass
class Connection:
    from_node: str
    from_port: str
    to_node: str
    to_port: str
    data_type: str

class NodeGraph(Widget):
    """Node graph editor widget"""
    
    nodes = reactive({})
    connections = reactive([])
    selected_node = reactive(None)
    pan_x = reactive(0)
    pan_y = reactive(0)
    zoom = reactive(1.0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dragging_node = None
        self.drag_offset = (0, 0)
        self.connecting_from = None
        self.grid_size = 2
        
        # Initialize with some example nodes
        self.create_example_nodes()
    
    def create_example_nodes(self):
        """Create example nodes for demonstration"""
        nodes = {}
        
        # Audio input node
        audio_in = Node(
            id="audio_in",
            name="Audio In",
            node_type=NodeType.INPUT,
            x=5, y=5,
            outputs=[
                NodePort("audio", "output", "audio"),
                NodePort("level", "output", "control")
            ]
        )
        nodes["audio_in"] = audio_in
        
        # Oscilloscope analyzer
        scope = Node(
            id="scope",
            name="Scope",
            node_type=NodeType.ANALYZER,
            x=25, y=5,
            inputs=[
                NodePort("audio", "input", "audio")
            ],
            outputs=[
                NodePort("display", "output", "visual")
            ]
        )
        nodes["scope"] = scope
        
        # Spectrum analyzer
        spectrum = Node(
            id="spectrum",
            name="Spectrum",
            node_type=NodeType.ANALYZER,
            x=25, y=15,
            inputs=[
                NodePort("audio", "input", "audio")
            ],
            outputs=[
                NodePort("frequencies", "output", "data"),
                NodePort("visual", "output", "visual")
            ]
        )
        nodes["spectrum"] = spectrum
        
        # Visual mixer
        mixer = Node(
            id="mixer",
            name="Mixer",
            node_type=NodeType.PROCESS,
            x=45, y=10,
            inputs=[
                NodePort("input1", "input", "visual"),
                NodePort("input2", "input", "visual"),
                NodePort("blend", "input", "control")
            ],
            outputs=[
                NodePort("output", "output", "visual")
            ]
        )
        nodes["mixer"] = mixer
        
        # Display output
        display = Node(
            id="display",
            name="Display",
            node_type=NodeType.OUTPUT,
            x=65, y=10,
            inputs=[
                NodePort("visual", "input", "visual")
            ]
        )
        nodes["display"] = display
        
        self.nodes = nodes
        
        # Create some example connections
        connections = [
            Connection("audio_in", "audio", "scope", "audio", "audio"),
            Connection("audio_in", "audio", "spectrum", "audio", "audio"),
            Connection("scope", "display", "mixer", "input1", "visual"),
            Connection("spectrum", "visual", "mixer", "input2", "visual"),
            Connection("mixer", "output", "display", "visual", "visual")
        ]
        self.connections = connections
    
    def render(self):
        """Render the node graph"""
        width = max(80, self.size.width)
        height = max(24, self.size.height)
        
        # Create canvas
        canvas = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Draw grid
        self.draw_grid(canvas, width, height)
        
        # Draw connections first (behind nodes)
        self.draw_connections(canvas, width, height)
        
        # Draw nodes
        self.draw_nodes(canvas, width, height)
        
        # Convert canvas to text
        lines = []
        for row in canvas:
            lines.append("".join(row))
        
        # Add header and status
        header = "🔗 NODE GRAPH EDITOR"
        status = f"Nodes: {len(self.nodes)} | Connections: {len(self.connections)}"
        if self.selected_node:
            status += f" | Selected: {self.nodes[self.selected_node].name}"
        
        result_text = Text()
        result_text.append(header + "\n", style=pick("accent_a"))
        result_text.append("─" * width + "\n", style=pick("text_dim"))
        
        for line in lines:
            result_text.append(line + "\n", style=pick("text_bright"))
        
        result_text.append("─" * width + "\n", style=pick("text_dim"))
        result_text.append(status, style=pick("text_dim"))
        result_text.append("\n[Space] Add Node [Del] Delete [Tab] Connect", style=pick("text_dim"))
        
        return result_text
    
    def draw_grid(self, canvas: List[List[str]], width: int, height: int):
        """Draw background grid"""
        for y in range(0, height, self.grid_size):
            for x in range(0, width, self.grid_size):
                if x < width and y < height:
                    canvas[y][x] = '·'
    
    def draw_nodes(self, canvas: List[List[str]], width: int, height: int):
        """Draw all nodes"""
        for node in self.nodes.values():
            self.draw_node(canvas, node, width, height)
    
    def draw_node(self, canvas: List[List[str]], node: Node, width: int, height: int):
        """Draw a single node"""
        # Apply pan and zoom
        x = int((node.x + self.pan_x) * self.zoom)
        y = int((node.y + self.pan_y) * self.zoom)
        w = int(node.width * self.zoom)
        h = int(node.height * self.zoom)
        
        # Skip if outside visible area
        if x >= width or y >= height or x + w < 0 or y + h < 0:
            return
        
        # Choose style based on node type and state
        if node.id == self.selected_node:
            border_char = "█"
            fill_char = "▓"
        elif node.active:
            border_char = "▓"
            fill_char = "▒"
        else:
            border_char = "▒"
            fill_char = "░"
        
        # Draw node box
        for dy in range(h):
            for dx in range(w):
                canvas_x = x + dx
                canvas_y = y + dy
                
                if 0 <= canvas_x < width and 0 <= canvas_y < height:
                    if (dx == 0 or dx == w-1 or dy == 0 or dy == h-1):
                        canvas[canvas_y][canvas_x] = border_char
                    else:
                        canvas[canvas_y][canvas_x] = fill_char
        
        # Draw node name (if there's room)
        if w >= len(node.name) and h >= 2:
            name_x = x + (w - len(node.name)) // 2
            name_y = y + 1
            
            for i, char in enumerate(node.name):
                canvas_x = name_x + i
                if 0 <= canvas_x < width and 0 <= name_y < height:
                    canvas[name_y][canvas_x] = char
        
        # Draw input ports
        port_spacing = max(1, h // (len(node.inputs) + 1)) if node.inputs else 1
        for i, port in enumerate(node.inputs):
            port_y = y + (i + 1) * port_spacing
            port_x = x - 1
            
            if 0 <= port_x < width and 0 <= port_y < height:
                canvas[port_y][port_x] = '◄' if port.connected_to else '◁'
        
        # Draw output ports
        port_spacing = max(1, h // (len(node.outputs) + 1)) if node.outputs else 1
        for i, port in enumerate(node.outputs):
            port_y = y + (i + 1) * port_spacing
            port_x = x + w
            
            if 0 <= port_x < width and 0 <= port_y < height:
                canvas[port_y][port_x] = '►' if port.connected_to else '▷'
    
    def draw_connections(self, canvas: List[List[str]], width: int, height: int):
        """Draw all connections between nodes"""
        for conn in self.connections:
            self.draw_connection(canvas, conn, width, height)
    
    def draw_connection(self, canvas: List[List[str]], conn: Connection, width: int, height: int):
        """Draw a single connection"""
        from_node = self.nodes.get(conn.from_node)
        to_node = self.nodes.get(conn.to_node)
        
        if not from_node or not to_node:
            return
        
        # Calculate connection endpoints
        from_x = int((from_node.x + from_node.width + self.pan_x) * self.zoom)
        from_y = int((from_node.y + from_node.height // 2 + self.pan_y) * self.zoom)
        
        to_x = int((to_node.x - 1 + self.pan_x) * self.zoom)
        to_y = int((to_node.y + to_node.height // 2 + self.pan_y) * self.zoom)
        
        # Draw connection line
        self.draw_line(canvas, from_x, from_y, to_x, to_y, width, height, conn.data_type)
    
    def draw_line(self, canvas: List[List[str]], x1: int, y1: int, x2: int, y2: int, 
                  width: int, height: int, data_type: str):
        """Draw a line between two points"""
        # Choose line character based on data type
        line_chars = {
            "audio": "~",
            "visual": "=",
            "data": "-",
            "control": "·"
        }
        char = line_chars.get(data_type, "-")
        
        # Simple line drawing (Bresenham-like)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        
        while True:
            if 0 <= x < width and 0 <= y < height:
                if canvas[y][x] == ' ' or canvas[y][x] == '·':
                    canvas[y][x] = char
            
            if x == x2 and y == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def get_node_at_position(self, x: int, y: int) -> Optional[str]:
        """Get node ID at screen position"""
        for node_id, node in self.nodes.items():
            node_x = int((node.x + self.pan_x) * self.zoom)
            node_y = int((node.y + self.pan_y) * self.zoom)
            node_w = int(node.width * self.zoom)
            node_h = int(node.height * self.zoom)
            
            if (node_x <= x < node_x + node_w and 
                node_y <= y < node_y + node_h):
                return node_id
        return None
    
    async def on_mouse_down(self, event: events.MouseDown):
        """Handle mouse down for selection and dragging"""
        node_id = self.get_node_at_position(event.x, event.y)
        
        if node_id:
            self.selected_node = node_id
            node = self.nodes[node_id]
            
            self.dragging_node = node_id
            self.drag_offset = (
                event.x - int((node.x + self.pan_x) * self.zoom),
                event.y - int((node.y + self.pan_y) * self.zoom)
            )
        else:
            self.selected_node = None
            self.dragging_node = None
    
    async def on_mouse_move(self, event: events.MouseMove):
        """Handle mouse move for dragging"""
        if self.dragging_node and event.button == 1:  # Left button
            node = self.nodes[self.dragging_node]
            
            new_x = (event.x - self.drag_offset[0]) / self.zoom - self.pan_x
            new_y = (event.y - self.drag_offset[1]) / self.zoom - self.pan_y
            
            # Snap to grid
            node.x = int(new_x // self.grid_size) * self.grid_size
            node.y = int(new_y // self.grid_size) * self.grid_size
            
            self.refresh()
    
    async def on_mouse_up(self, event: events.MouseUp):
        """Handle mouse up to stop dragging"""
        self.dragging_node = None
    
    async def on_key(self, event: events.Key):
        """Handle keyboard input"""
        if event.key == "space":
            self.add_new_node()
        elif event.key == "delete" and self.selected_node:
            self.delete_node(self.selected_node)
        elif event.key == "tab":
            self.toggle_connection_mode()
        elif event.key == "escape":
            self.connecting_from = None
            self.selected_node = None
    
    def add_new_node(self):
        """Add a new node"""
        node_id = f"node_{len(self.nodes)}"
        new_node = Node(
            id=node_id,
            name=f"Node {len(self.nodes)}",
            node_type=NodeType.PROCESS,
            x=10 + len(self.nodes) * 15,
            y=10,
            inputs=[NodePort("in", "input", "data")],
            outputs=[NodePort("out", "output", "data")]
        )
        
        new_nodes = dict(self.nodes)
        new_nodes[node_id] = new_node
        self.nodes = new_nodes
        
        self.selected_node = node_id
    
    def delete_node(self, node_id: str):
        """Delete a node and its connections"""
        if node_id not in self.nodes:
            return
        
        # Remove connections involving this node
        new_connections = [
            conn for conn in self.connections
            if conn.from_node != node_id and conn.to_node != node_id
        ]
        self.connections = new_connections
        
        # Remove the node
        new_nodes = dict(self.nodes)
        del new_nodes[node_id]
        self.nodes = new_nodes
        
        self.selected_node = None
    
    def toggle_connection_mode(self):
        """Toggle connection creation mode"""
        if self.connecting_from is None and self.selected_node:
            self.connecting_from = self.selected_node
        else:
            if self.connecting_from and self.selected_node and self.connecting_from != self.selected_node:
                # Create connection
                self.create_connection(self.connecting_from, self.selected_node)
            self.connecting_from = None
    
    def create_connection(self, from_node_id: str, to_node_id: str):
        """Create a connection between two nodes"""
        from_node = self.nodes.get(from_node_id)
        to_node = self.nodes.get(to_node_id)
        
        if not from_node or not to_node:
            return
        
        # Find available ports
        from_port = None
        for port in from_node.outputs:
            if not port.connected_to:
                from_port = port
                break
        
        to_port = None
        for port in to_node.inputs:
            if not port.connected_to:
                to_port = port
                break
        
        if from_port and to_port:
            # Create connection
            connection = Connection(
                from_node_id, from_port.name,
                to_node_id, to_port.name,
                from_port.data_type
            )
            
            new_connections = list(self.connections)
            new_connections.append(connection)
            self.connections = new_connections
            
            # Update port connection status
            from_port.connected_to.add(f"{to_node_id}.{to_port.name}")
            to_port.connected_to.add(f"{from_node_id}.{from_port.name}")
    
    def save_graph(self, filename: str):
        """Save the node graph to a file"""
        graph_data = {
            "nodes": {
                node_id: {
                    "name": node.name,
                    "type": node.node_type.value,
                    "x": node.x,
                    "y": node.y,
                    "width": node.width,
                    "height": node.height,
                    "parameters": node.parameters
                }
                for node_id, node in self.nodes.items()
            },
            "connections": [
                {
                    "from": {"node": c.from_node, "port": c.from_port},
                    "to": {"node": c.to_node, "port": c.to_port},
                    "type": c.data_type
                }
                for c in self.connections
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(graph_data, f, indent=2)
    
    def load_graph(self, filename: str):
        """Load a node graph from a file"""
        try:
            with open(filename, 'r') as f:
                json.load(f)
            
            # Recreate nodes and connections from saved data
            # Implementation would go here
            pass
        except Exception as e:
            print(f"Error loading graph: {e}")