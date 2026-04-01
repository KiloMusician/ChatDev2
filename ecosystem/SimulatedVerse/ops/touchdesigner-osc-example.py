# TouchDesigner OSC Integration Example
# Add this code to a Text DAT in TouchDesigner to receive ΞNuSyQ state

from pythonosc import udp_client, osc
from pythonosc.dispatcher import Dispatcher
from pythonosc.server import osc
import threading

# Configuration
OSC_RECEIVE_PORT = 9001  # TouchDesigner receives on this port
OSC_SEND_HOST = "127.0.0.1"
OSC_SEND_PORT = 9000     # Send back to ΞNuSyQ bridge

# Create OSC client for sending messages back to ΞNuSyQ
client = udp_client.SimpleUDPClient(OSC_SEND_HOST, OSC_SEND_PORT)

def xinusyq_state_handler(unused_addr, fps, entities):
    """Handle incoming state updates from ΞNuSyQ/Godot bridge"""
    print(f"ΞNuSyQ State - FPS: {fps}, Entities: {entities}")
    
    # Example: Map to TouchDesigner parameters
    # op('fps_meter')['value'] = fps
    # op('entity_count')['value'] = entities
    
    # Example: Send visual feedback back to bridge
    if fps < 30:
        client.send_message("/xinusyq/performance", ["low_fps", fps])
    
    # Example: Trigger visual effects based on entity count
    if entities > 10:
        client.send_message("/xinusyq/fx", ["swarm_mode", entities])

def setup_osc_receiver():
    """Setup OSC message dispatcher"""
    dispatcher = Dispatcher()
    dispatcher.map("/xinusyq/state", xinusyq_state_handler)
    
    # Start OSC server in background thread
    server = osc.ThreadingOSCUDPServer(("127.0.0.1", OSC_RECEIVE_PORT), dispatcher)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"TouchDesigner OSC receiver listening on port {OSC_RECEIVE_PORT}")

# Call this in TouchDesigner initialization
setup_osc_receiver()

# Example TouchDesigner node setup:
# 1. Add this code to a Text DAT
# 2. Create CHOPs for 'fps_meter' and 'entity_count'
# 3. Use these values to drive visuals, audio, or other parameters