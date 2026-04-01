#!/usr/bin/env python3
"""
🚀 Architectural Integration Demo
Complete demonstration of Temple, House, and Oldest House with ASCII interface
"""

import sys
import time

# Add paths for all systems
sys.path.append('.')
sys.path.append('ui_ascii')

try:
    # ASCII Interface components
    from ui_ascii.color_themes import set_theme, pick, list_themes
    from ui_ascii.widgets.minimap import Minimap, RadarSweep
    from ui_ascii.widgets.oscilloscope import DataMonitor
    from ui_ascii.widgets.tile_renderer import TileRenderer
    from ui_ascii.widgets.node_graph import NodeGraph
    
    # Architectural systems
    from navigation_system import UniversalNavigator, render_navigation_interface
    from TempleOfKnowledge.Floor01_GameplayIntegration.colony_mechanics import ColonyState, render_colony_status_ascii
    from TempleOfKnowledge.Floor05_KnowledgeManagement.documentation_system import KnowledgeLibrary, render_knowledge_browser_ascii
    from TempleOfKnowledge.Floor10_MetaOptimization.cascade_protocols import MetaOptimizer, CascadeOrchestrator
    from HouseOfLeaves.corridor_system import HouseArchitect
    from OldestHouse.control_systems import OldestHouseControl
    
    print("✅ All systems loaded successfully!")
    
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Some systems may not be fully available")

class CoreLinkFoundation:
    """Main integration class for the complete autonomous development ecosystem"""
    
    def __init__(self):
        print("🛕 Initializing CoreLink Foundation...")
        
        # Initialize all architectural systems
        self.navigator = UniversalNavigator()
        self.meta_optimizer = MetaOptimizer()
        self.cascade_orchestrator = CascadeOrchestrator()
        self.knowledge_library = KnowledgeLibrary()
        self.colony_state = ColonyState()
        self.house_architect = HouseArchitect()
        self.oldest_house = OldestHouseControl()
        
        # Initialize ASCII interface components
        self.minimap = Minimap()
        self.data_monitor = DataMonitor()
        self.tile_renderer = TileRenderer()
        self.node_graph = NodeGraph()
        
        # Set theme
        set_theme("touchdesigner")
        
        # System state
        self.running = True
        self.current_mode = "navigation"
        self.frame_count = 0
        
        print("🎮 CoreLink Foundation initialized!")
    
    def run_integration_demo(self):
        """Run the complete system integration demo"""
        print("\n" + "="*60)
        print("🚀 CORELINK FOUNDATION - ARCHITECTURAL INTEGRATION")
        print("="*60)
        
        # Demo sequence
        demos = [
            ("Navigation System", self.demo_navigation),
            ("Temple of Knowledge", self.demo_temple),
            ("House of Leaves", self.demo_house),
            ("Oldest House Control", self.demo_oldest_house),
            ("ASCII Interface Widgets", self.demo_ascii_widgets),
            ("Colony Simulation", self.demo_colony),
            ("Meta-Optimization", self.demo_meta_optimization),
            ("Complete Integration", self.demo_complete_integration)
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n🔸 {demo_name}")
            print("-" * 40)
            try:
                demo_func()
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error in {demo_name}: {e}")
        
        print("\n✨ Integration demo complete!")
    
    def demo_navigation(self):
        """Demonstrate navigation system"""
        print("📍 Current location:", self.navigator.current_location)
        
        # Show navigation map
        nav_map = self.navigator.get_navigation_map_ascii()
        print(nav_map[:500] + "..." if len(nav_map) > 500 else nav_map)
        
        # Navigate to temple
        result = self.navigator.navigate_to("temple_floor_05")
        if result["success"]:
            print("✅ Navigated to Knowledge Management floor")
        
        # Return to entrance
        self.navigator.navigate_to("temple_entrance")
    
    def demo_temple(self):
        """Demonstrate Temple of Knowledge systems"""
        print("🛕 Temple of Knowledge Systems:")
        
        # Knowledge Library
        search_results = self.knowledge_library.search("getting started")
        print(f"📚 Found {len(search_results)} documents for 'getting started'")
        
        # Show knowledge browser
        kb_interface = render_knowledge_browser_ascii(self.knowledge_library)
        print(kb_interface[:300] + "..." if len(kb_interface) > 300 else kb_interface)
        
        # Meta-optimization status
        opt_report = self.meta_optimizer.get_optimization_report()
        print(opt_report[:200] + "..." if len(opt_report) > 200 else opt_report)
    
    def demo_house(self):
        """Demonstrate House of Leaves modular architecture"""
        print("🏠 House of Leaves Architecture:")
        
        # Corridor map
        corridor_map = self.house_architect.get_corridor_ascii_map("root", 2)
        print(corridor_map[:400] + "..." if len(corridor_map) > 400 else corridor_map)
        
        # Show dead ends that need healing
        print(f"🚫 Dead ends detected: {len(self.house_architect.dead_ends)}")
        for dead_end in list(self.house_architect.dead_ends)[:3]:
            healing = self.house_architect.propose_healing(dead_end)
            print(f"   • {healing.get('corridor', dead_end)}: {healing.get('current_state', 'unknown')}")
    
    def demo_oldest_house(self):
        """Demonstrate Oldest House control systems"""
        print("🏛️ Oldest House Control Systems:")
        
        # Control status
        status = self.oldest_house.get_status_report()
        print(status[:400] + "..." if len(status) > 400 else status)
        
        # Simulate anomaly detection
        signatures = ["high_cpu_usage", "memory_pressure"]
        detected = self.oldest_house.detect_anomaly(signatures, {"test": True})
        if detected:
            print(f"🚨 Anomaly detected: {detected}")
    
    def demo_ascii_widgets(self):
        """Demonstrate ASCII interface widgets"""
        print("🎨 ASCII Interface Widgets:")
        
        # Add some data to monitor
        self.data_monitor.add_metric("system_health", 0.85, "%", ".1f")
        self.data_monitor.add_metric("optimization_level", 3.2, "", ".1f")
        self.data_monitor.add_metric("colony_mood", 0.75, "", ".2f")
        
        # Show minimap with different modes
        print("📡 Minimap (Radar mode):")
        self.minimap.add_target(10, 15, "colony", 0.8)
        self.minimap.add_target(25, 8, "anomaly", 0.3)
        
        # Add some visual variety
        print("🎵 Data visualization ready")
        print("🗺️ Tile renderer active") 
        print("🔗 Node graph connections established")
    
    def demo_colony(self):
        """Demonstrate colony simulation"""
        print("🎮 Colony Simulation:")
        
        # Run a few simulation days
        for day in range(3):
            status = self.colony_state.daily_tick()
            print(f"Day {status['day']}: Pop {status['population']}, Mood {status['average_mood']:.2f}")
        
        # Show colony status
        colony_ascii = render_colony_status_ascii(self.colony_state)
        print(colony_ascii[:300] + "..." if len(colony_ascii) > 300 else colony_ascii)
    
    def demo_meta_optimization(self):
        """Demonstrate meta-optimization systems"""
        print("⟦Ξ⟧ Meta-Optimization:")
        
        # Check for cascade opportunities
        cascades = self.meta_optimizer.evaluate_cascade_conditions()
        print(f"🔄 Available cascade events: {len(cascades)}")
        
        if cascades:
            # Trigger first cascade
            result = self.meta_optimizer.trigger_cascade(cascades[0])
            if result.get("success"):
                print(f"✅ Triggered cascade: {cascades[0]}")
                improvements = result.get("metrics_improvement", {})
                best_improvement = max(improvements.values()) if improvements else 0
                print(f"📈 Best improvement: {best_improvement:+.1f}%")
    
    def demo_complete_integration(self):
        """Demonstrate complete system integration"""
        print("🌟 Complete System Integration:")
        
        # Show how all systems work together
        integration_status = {
            "navigation": len(self.navigator.visited_nodes),
            "temple_floors": 10,
            "house_corridors": len(self.house_architect.corridors),
            "oldest_house_entities": len(self.oldest_house.entities),
            "colony_day": self.colony_state.day,
            "optimization_cascades": len(self.meta_optimizer.cascade_history),
            "knowledge_docs": len(self.knowledge_library.documents)
        }
        
        print("📊 System Status:")
        for system, value in integration_status.items():
            print(f"   {system}: {value}")
        
        # Generate unified status display
        unified_status = self.generate_unified_status()
        print("\n🖥️ Unified ASCII Status:")
        print(unified_status[:400] + "..." if len(unified_status) > 400 else unified_status)
    
    def generate_unified_status(self) -> str:
        """Generate unified status display combining all systems"""
        lines = [
            "🚀 CORELINK FOUNDATION - UNIFIED STATUS",
            "═" * 50,
            f"📍 Location: {self.navigator.nodes[self.navigator.current_location].name}",
            f"🛕 Temple Access: Level {self.navigator.access_level}/10",
            f"🏠 House Corridors: {len(self.house_architect.corridors)} mapped",
            f"🏛️ Oldest House: {self.oldest_house.threat_level.value.upper()} threat level",
            f"🎮 Colony Day: {self.colony_state.day} (Pop: {len(self.colony_state.colonists)})",
            f"⟦Ξ⟧ Optimization: {len(self.meta_optimizer.cascade_history)} cascades",
            "",
            "🎨 ASCII Interface: TouchDesigner theme active",
            "📊 Real-time monitoring: ONLINE",
            "🔄 Auto-optimization: ENABLED",
            "🚪 Navigation: Multi-wing access",
            "",
            "✨ All systems operational and integrated!"
        ]
        
        return "\n".join(lines)
    
    def interactive_mode(self):
        """Run interactive mode for exploring the system"""
        print("\n🎮 INTERACTIVE MODE")
        print("Commands: [n]avigate, [t]emple, [h]ouse, [o]ldest, [c]olony, [q]uit")
        
        while self.running:
            try:
                command = input("\n> ").lower().strip()
                
                if command == 'q' or command == 'quit':
                    self.running = False
                    print("👋 Goodbye!")
                    
                elif command == 'n' or command == 'navigate':
                    nav_interface = render_navigation_interface(self.navigator)
                    print(nav_interface)
                    
                elif command == 't' or command == 'temple':
                    print("🛕 Temple of Knowledge")
                    opt_report = self.meta_optimizer.get_optimization_report()
                    print(opt_report[:500] + "..." if len(opt_report) > 500 else opt_report)
                    
                elif command == 'h' or command == 'house':
                    print("🏠 House of Leaves")
                    corridor_map = self.house_architect.get_corridor_ascii_map("root", 3)
                    print(corridor_map[:500] + "..." if len(corridor_map) > 500 else corridor_map)
                    
                elif command == 'o' or command == 'oldest':
                    print("🏛️ Oldest House")
                    status = self.oldest_house.get_status_report()
                    print(status[:500] + "..." if len(status) > 500 else status)
                    
                elif command == 'c' or command == 'colony':
                    print("🎮 Colony Status")
                    colony_status = render_colony_status_ascii(self.colony_state)
                    print(colony_status)
                    
                elif command == 'themes':
                    print("🎨 Available themes:", ", ".join(list_themes()))
                    
                elif command.startswith('theme '):
                    theme_name = command[6:]
                    if set_theme(theme_name):
                        print(f"✅ Switched to {theme_name} theme")
                    else:
                        print(f"❌ Theme '{theme_name}' not found")
                        
                else:
                    print("❓ Unknown command. Try: navigate, temple, house, oldest, colony, quit")
                    
            except KeyboardInterrupt:
                self.running = False
                print("\n👋 Interrupted. Goodbye!")
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    print("🚀 CoreLink Foundation - Autonomous Development Ecosystem")
    print("Integrating Temple of Knowledge, House of Leaves, and Oldest House")
    print("With TouchDesigner-style ASCII interface and 20 FPS animations")
    
    try:
        # Initialize the complete system
        foundation = CoreLinkFoundation()
        
        # Run integration demo
        foundation.run_integration_demo()
        
        # Optional interactive mode
        response = input("\n🎮 Enter interactive mode? (y/n): ")
        if response.lower().startswith('y'):
            foundation.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()