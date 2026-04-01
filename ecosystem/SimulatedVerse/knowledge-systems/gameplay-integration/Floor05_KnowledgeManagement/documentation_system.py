"""
🗃️ Floor 05: Knowledge Management
Documentation, tutorials, FAQs, and living knowledge systems
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from enum import Enum
import time

class DocumentType(Enum):
    TUTORIAL = "tutorial"
    FAQ = "faq"
    REFERENCE = "reference"
    GUIDE = "guide"
    LORE = "lore"
    TECHNICAL = "technical"

class KnowledgeLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class KnowledgeDocument:
    id: str
    title: str
    content: str
    doc_type: DocumentType
    level: KnowledgeLevel
    tags: Set[str]
    prerequisites: List[str] = None
    last_updated: float = None
    view_count: int = 0
    helpfulness_score: float = 0.0
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []
        if self.last_updated is None:
            self.last_updated = time.time()

class KnowledgeLibrary:
    """Centralized knowledge management system"""
    
    def __init__(self):
        self.documents: Dict[str, KnowledgeDocument] = {}
        self.tags_index: Dict[str, Set[str]] = {}
        self.search_history: List[str] = []
        self.learning_paths: Dict[str, List[str]] = {}
        
        # Initialize with core documentation
        self._create_core_documentation()
    
    def _create_core_documentation(self):
        """Create essential documentation"""
        core_docs = [
            KnowledgeDocument(
                "getting_started",
                "Getting Started with CoreLink Foundation",
                """
# 🚀 Getting Started with CoreLink Foundation

Welcome to your autonomous development ecosystem! This guide will help you understand the basic concepts and get you productive quickly.

## Core Concepts

### 1. The Three Pillars
- **Temple of Knowledge**: Optimization tiers and learning systems
- **House of Leaves**: Modular architecture and infinite expansion
- **Oldest House**: Anomaly containment and safe experimentation

### 2. ASCII Interface
Your primary interaction is through beautiful ASCII/Unicode interfaces:
- Real-time braille micro-pixel graphics
- TouchDesigner-style node patching
- Roguelike exploration maps
- Live data visualization

### 3. Colony Simulation
Manage a growing colony while building your development ecosystem:
- Resource management (food, power, oxygen)
- Colonist mood and skill development
- Research tree progression
- Base defense and expansion

## Quick Start

1. **Run the ASCII Interface**: `python ui_ascii/nu_ascii_app.py`
2. **Start Node Dashboard**: `node index.js`
3. **Explore the Temple**: Navigate floors 1-10 for different optimization levels
4. **Check Colony Status**: Monitor your colonists and resources

## Navigation

- Use **WASD** or arrow keys for movement
- **Tab** toggles menus
- **Space** pauses/resumes
- **M** cycles display modes
- **1-5** selects different effect modes

## Next Steps

Read the Intermediate Guide for deeper system understanding.
                """,
                DocumentType.TUTORIAL,
                KnowledgeLevel.BEGINNER,
                {"startup", "basics", "interface", "colony"}
            ),
            
            KnowledgeDocument(
                "ascii_interface_guide",
                "ASCII Interface Deep Dive",
                """
# 🎨 ASCII Interface Deep Dive

The CoreLink Foundation uses a sophisticated ASCII/Unicode interface that provides rich visual feedback without GUI dependencies.

## Interface Components

### Braille Micro-Pixels
- 2×4 dot matrix using Unicode Braille (U+2800)
- Allows for high-resolution graphics in terminal
- Real-time animations at 20+ FPS

### Color System
- Truecolor ANSI support with graceful fallback
- 6 themed palettes: TouchDesigner, Cyberpunk, Terminal, Amber, Ice, Synthwave
- Adaptive rendering based on terminal capabilities

### Widget System
- **Viewport**: Main game/simulation display
- **Minimap**: Radar, heat maps, flow fields
- **Oscilloscope**: Real-time data visualization
- **Node Graph**: TouchDesigner-style patching
- **Tile Renderer**: FOV and lighting for exploration

## Advanced Features

### Reactive Updates
All interface elements update in real-time using event-driven architecture.

### Mouse Support
Full mouse interaction for node editing, map navigation, and menu selection.

### Keyboard Shortcuts
Extensive keyboard shortcuts for power users.

## Customization

Change themes dynamically:
```python
from ui_ascii.color_themes import set_theme
set_theme("cyberpunk")  # Switch to cyberpunk aesthetic
```
                """,
                DocumentType.GUIDE,
                KnowledgeLevel.INTERMEDIATE,
                {"interface", "ascii", "graphics", "customization"}
            ),
            
            KnowledgeDocument(
                "faq_common_issues",
                "Frequently Asked Questions",
                """
# ❓ Frequently Asked Questions

## Installation & Setup

**Q: The ASCII interface looks broken or misaligned**
A: Check your terminal's Unicode support. Use a modern terminal like Replit console, VSCode terminal, or iTerm2.

**Q: Colors aren't displaying correctly**
A: Set your COLORTERM environment variable: `export COLORTERM=truecolor`

**Q: Performance is slow**
A: Reduce the frame rate in settings or switch to a simpler color theme.

## Gameplay

**Q: My colonists are unhappy**
A: Check resource levels - low food or power affects mood. Ensure basic needs are met.

**Q: How do I unlock new technologies?**
A: Generate Research points by assigning colonists to researcher jobs. Technologies unlock automatically when you have enough points.

**Q: What do the different building types do?**
A: Shelters house colonists, farms produce food, workshops generate materials, labs create research points.

## Technical

**Q: How do I add new features?**
A: Use the Temple of Knowledge navigation system to find the appropriate floor for your feature type.

**Q: Can I run this on mobile?**
A: The ASCII interface works on any terminal, including mobile SSH clients.

**Q: How do I backup my progress?**
A: Colony data is automatically saved. Use the export function in the menu.
                """,
                DocumentType.FAQ,
                KnowledgeLevel.BEGINNER,
                {"faq", "troubleshooting", "help", "common"}
            )
        ]
        
        for doc in core_docs:
            self.add_document(doc)
    
    def add_document(self, doc: KnowledgeDocument):
        """Add a document to the library"""
        self.documents[doc.id] = doc
        
        # Update tags index
        for tag in doc.tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = set()
            self.tags_index[tag].add(doc.id)
    
    def search(self, query: str, doc_type: Optional[DocumentType] = None, 
               level: Optional[KnowledgeLevel] = None) -> List[KnowledgeDocument]:
        """Search documents by query"""
        self.search_history.append(query)
        query_lower = query.lower()
        results = []
        
        for doc in self.documents.values():
            # Type filter
            if doc_type and doc.doc_type != doc_type:
                continue
            
            # Level filter  
            if level and doc.level != level:
                continue
            
            # Text search
            if (query_lower in doc.title.lower() or 
                query_lower in doc.content.lower() or
                any(query_lower in tag for tag in doc.tags)):
                results.append(doc)
        
        # Sort by relevance (simple scoring)
        results.sort(key=lambda d: d.helpfulness_score, reverse=True)
        return results
    
    def get_learning_path(self, topic: str) -> List[str]:
        """Get recommended learning path for a topic"""
        if topic in self.learning_paths:
            return self.learning_paths[topic]
        
        # Generate learning path based on available documents
        beginner_docs = []
        intermediate_docs = []
        advanced_docs = []
        
        for doc in self.documents.values():
            if topic in doc.tags:
                if doc.level == KnowledgeLevel.BEGINNER:
                    beginner_docs.append(doc.id)
                elif doc.level == KnowledgeLevel.INTERMEDIATE:
                    intermediate_docs.append(doc.id)
                elif doc.level == KnowledgeLevel.ADVANCED:
                    advanced_docs.append(doc.id)
        
        path = beginner_docs + intermediate_docs + advanced_docs
        self.learning_paths[topic] = path
        return path
    
    def get_document_dependencies(self, doc_id: str) -> List[str]:
        """Get documents that should be read before this one"""
        if doc_id not in self.documents:
            return []
        
        doc = self.documents[doc_id]
        dependencies = []
        
        for prereq in doc.prerequisites:
            if prereq in self.documents:
                dependencies.append(prereq)
        
        return dependencies
    
    def mark_viewed(self, doc_id: str):
        """Mark document as viewed"""
        if doc_id in self.documents:
            self.documents[doc_id].view_count += 1
    
    def rate_helpfulness(self, doc_id: str, rating: float):
        """Rate document helpfulness (0.0 to 1.0)"""
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            # Simple moving average
            doc.helpfulness_score = (doc.helpfulness_score + rating) / 2

class TutorialSystem:
    """Interactive tutorial system"""
    
    def __init__(self, knowledge_library: KnowledgeLibrary):
        self.library = knowledge_library
        self.active_tutorial: Optional[str] = None
        self.tutorial_progress: Dict[str, int] = {}
        self.completed_tutorials: Set[str] = set()
    
    def start_tutorial(self, tutorial_id: str) -> bool:
        """Start an interactive tutorial"""
        if tutorial_id not in self.library.documents:
            return False
        
        doc = self.library.documents[tutorial_id]
        if doc.doc_type != DocumentType.TUTORIAL:
            return False
        
        self.active_tutorial = tutorial_id
        self.tutorial_progress[tutorial_id] = 0
        return True
    
    def advance_tutorial(self) -> Optional[str]:
        """Advance to next step of active tutorial"""
        if not self.active_tutorial:
            return None
        
        current_step = self.tutorial_progress.get(self.active_tutorial, 0)
        self.tutorial_progress[self.active_tutorial] = current_step + 1
        
        # Check if tutorial is complete
        doc = self.library.documents[self.active_tutorial]
        total_steps = len(doc.content.split("##")) - 1  # Count sections
        
        if current_step >= total_steps:
            self.completed_tutorials.add(self.active_tutorial)
            self.active_tutorial = None
            return "Tutorial completed!"
        
        return f"Step {current_step + 1} of {total_steps}"

# ASCII rendering for knowledge system
def render_knowledge_browser_ascii(library: KnowledgeLibrary, 
                                 search_query: str = "") -> str:
    """Render knowledge browser for ASCII interface"""
    lines = [
        "🗃️  KNOWLEDGE LIBRARY",
        "═" * 40
    ]
    
    if search_query:
        results = library.search(search_query)
        lines.append(f"📖 Search results for '{search_query}':")
        lines.append("")
        
        for i, doc in enumerate(results[:5]):  # Show top 5
            icon = {"tutorial": "📚", "faq": "❓", "guide": "📖", 
                   "reference": "📋", "lore": "📜", "technical": "🔧"}
            doc_icon = icon.get(doc.doc_type.value, "📄")
            
            lines.append(f"{i+1}. {doc_icon} {doc.title}")
            lines.append(f"   Level: {doc.level.value} | Views: {doc.view_count}")
            lines.append("")
    else:
        # Show categories
        lines.extend([
            "📚 CATEGORIES:",
            "",
            "1. 🚀 Getting Started",
            "2. 🎨 Interface Guides", 
            "3. 🎮 Gameplay Help",
            "4. 🔧 Technical Reference",
            "5. 📜 Lore & Background",
            "6. ❓ FAQ & Troubleshooting",
            "",
            "💡 Recent searches:"
        ])
        
        recent = library.search_history[-3:] if library.search_history else ["No recent searches"]
        for query in recent:
            lines.append(f"   • {query}")
    
    lines.extend([
        "",
        "🔍 Type search query or select category",
        "📖 [Enter] to read selected document"
    ])
    
    return "\n".join(lines)