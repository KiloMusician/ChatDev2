"""
🌿 NuSyQ-Hub Documentation Integration for Rooftop Garden
Temple of Knowledge Floor 06 - External Documentation Sources

Integrates with NuSyQ-hub to autonomously discover, process,
and integrate external documentation sources into our knowledge base.

Features:
- Automatic discovery of NuSyQ-hub documentation
- Intelligent filtering and relevance scoring
- Conflict-aware integration with existing knowledge
- Leisurely processing aligned with garden philosophy
"""

import asyncio
import aiohttp
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import os

# Import existing infrastructure
from autonomous_custodians import (
    CustodianPersonality, RooftopGardenOrchestrator
)
from ..Floor05_KnowledgeManagement.documentation_system import (
    KnowledgeLibrary, KnowledgeDocument, DocumentType, KnowledgeLevel
)

@dataclass
class ExternalDocumentSource:
    """Configuration for external documentation source"""
    name: str
    base_url: str
    auth_token: Optional[str] = None
    documentation_paths: List[str] = field(default_factory=list)
    processing_priority: float = 1.0
    last_sync: Optional[float] = None
    
class NuSyQHubDocumentationIntegrator:
    """
    Integrates documentation from NuSyQ-hub repository with
    peaceful, conflict-aware processing suitable for garden environment.
    """
    
    def __init__(self, garden_orchestrator: RooftopGardenOrchestrator):
        self.garden = garden_orchestrator
        self.library = garden_orchestrator.library
        self.processed_docs: Set[str] = set()
        self.integration_stats = {
            "docs_discovered": 0,
            "docs_integrated": 0,
            "conflicts_detected": 0,
            "last_sync": None
        }
        
        # NuSyQ-hub configuration
        self.hub_config = self._load_hub_configuration()
    
    def _load_hub_configuration(self) -> ExternalDocumentSource:
        """Load NuSyQ-hub configuration from environment or defaults"""
        return ExternalDocumentSource(
            name="NuSyQ-Hub",
            base_url=os.getenv("NUSYQ_HUB_URL", "https://github.com/your-org/NuSyQ-hub"),
            auth_token=os.getenv("GH_FINE_GRAINED_PAT"),
            documentation_paths=[
                "docs/", "README.md", "guides/", "templates/",
                "examples/", "architecture/", "tutorials/"
            ],
            processing_priority=0.8  # Slightly lower than internal docs
        )
    
    async def discover_hub_documentation(self) -> List[Dict[str, Any]]:
        """
        Discover available documentation in NuSyQ-hub repository.
        Uses GitHub API to find documentation files.
        """
        print("🔍 Discovering documentation in NuSyQ-hub...")
        
        if not self.hub_config.auth_token:
            print("⚠️  No GitHub token available - using mock discovery for demo")
            return self._mock_hub_documentation()
        
        discovered_docs = []
        
        try:
            async with aiohttp.ClientSession() as session:
                for doc_path in self.hub_config.documentation_paths:
                    docs_in_path = await self._fetch_github_directory(session, doc_path)
                    discovered_docs.extend(docs_in_path)
                    
                    # Be gentle with API
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"🚨 Error discovering hub documentation: {e}")
            print("📚 Using mock documentation for demonstration")
            return self._mock_hub_documentation()
        
        self.integration_stats["docs_discovered"] = len(discovered_docs)
        print(f"📖 Discovered {len(discovered_docs)} documentation files in NuSyQ-hub")
        
        return discovered_docs
    
    async def _fetch_github_directory(self, session: aiohttp.ClientSession, path: str) -> List[Dict[str, Any]]:
        """Fetch directory contents from GitHub API"""
        # Parse GitHub URL to get owner/repo
        url_parts = self.hub_config.base_url.replace("https://github.com/", "").split("/")
        if len(url_parts) < 2:
            return []
        
        owner, repo = url_parts[0], url_parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        
        headers = {
            "Authorization": f"token {self.hub_config.auth_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        try:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    contents = await response.json()
                    
                    docs = []
                    for item in contents:
                        if self._is_documentation_file(item["name"]):
                            docs.append({
                                "name": item["name"],
                                "path": item["path"],
                                "download_url": item["download_url"],
                                "size": item["size"],
                                "sha": item["sha"]
                            })
                    
                    return docs
                else:
                    print(f"⚠️  GitHub API error for {path}: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"🚨 Error fetching {path}: {e}")
            return []
    
    def _is_documentation_file(self, filename: str) -> bool:
        """Check if file is likely documentation"""
        doc_extensions = [".md", ".rst", ".txt", ".adoc"]
        doc_keywords = ["readme", "guide", "tutorial", "doc", "help", "faq"]
        
        filename_lower = filename.lower()
        
        # Check extension
        if any(filename_lower.endswith(ext) for ext in doc_extensions):
            return True
        
        # Check keywords
        if any(keyword in filename_lower for keyword in doc_keywords):
            return True
        
        return False
    
    def _mock_hub_documentation(self) -> List[Dict[str, Any]]:
        """Mock NuSyQ-hub documentation for demonstration"""
        return [
            {
                "name": "Advanced_Templates.md",
                "path": "docs/Advanced_Templates.md", 
                "content": """# Advanced Template System

The NuSyQ-hub provides sophisticated templates for rapid development:

## Component Templates
- React component scaffolds with TypeScript
- Vue.js component templates
- Angular module templates

## Service Templates  
- Express.js API services
- FastAPI Python services
- Go microservice templates

## Workflow Templates
- GitHub Actions CI/CD
- Docker containerization
- Kubernetes deployment

## Best Practices
- Code organization patterns
- Testing framework setup
- Documentation generation
""",
                "size": 1024,
                "sha": "abc123"
            },
            {
                "name": "Scaffolding_Guide.md",
                "path": "guides/Scaffolding_Guide.md",
                "content": """# Project Scaffolding Guide

Automated project generation with intelligent defaults:

## Quick Start
```bash
nusyq scaffold create --type react-app
nusyq scaffold create --type api-service
nusyq scaffold create --type fullstack
```

## Customization
- Project structure customization
- Dependency selection
- Configuration templates
- Environment setup

## Integration
- Git repository initialization
- CI/CD pipeline setup
- Documentation generation
- Testing framework integration
""",
                "size": 856,
                "sha": "def456"
            },
            {
                "name": "GitHub_Automation.md", 
                "path": "docs/GitHub_Automation.md",
                "content": """# GitHub Workflow Automation

Complete automation for development workflows:

## Automated Workflows
- Pull request creation
- Code review automation
- Branch management
- Release generation

## Quality Gates
- Automated testing
- Code coverage requirements
- Security scanning
- Performance benchmarks

## Team Collaboration
- Review assignment
- Status notifications
- Progress tracking
- Metrics collection
""",
                "size": 734,
                "sha": "ghi789"
            }
        ]
    
    async def integrate_hub_documentation_leisurely(self):
        """
        Integrate hub documentation using garden's leisurely approach.
        Creates a special custodian for external documentation processing.
        """
        print("🌿 Creating Hub Documentation Custodian...")
        
        # Create specialized custodian for hub integration
        hub_custodian = self.garden.create_custodian(
            "HubBridge", 
            CustodianPersonality.METHODICAL
        )
        
        # Discover available documentation
        hub_docs = await self.discover_hub_documentation()
        
        if not hub_docs:
            print("📚 No hub documentation found - continuing with internal knowledge")
            return
        
        print(f"🔗 Processing {len(hub_docs)} hub documents leisurely...")
        
        for doc_info in hub_docs:
            if not hub_custodian.is_active:
                break
            
            await self._process_hub_document_gently(doc_info)
            
            # Natural pause between documents (garden philosophy)
            await asyncio.sleep(random.uniform(5, 15))
        
        print("✨ Hub documentation integration complete")
    
    async def _process_hub_document_gently(self, doc_info: Dict[str, Any]):
        """Process a single hub document with conflict detection"""
        doc_name = doc_info["name"]
        doc_content = doc_info.get("content", "")
        
        # Skip if already processed
        doc_hash = hashlib.md5(doc_content.encode()).hexdigest()
        if doc_hash in self.processed_docs:
            return
        
        print(f"📖 Gently processing hub document: {doc_name}")
        
        # Determine document type and level
        doc_type = self._classify_document_type(doc_name, doc_content)
        doc_level = self._determine_knowledge_level(doc_content)
        
        # Check for conflicts with existing knowledge
        conflicts = await self._check_integration_conflicts(doc_name, doc_content)
        
        if conflicts:
            print(f"⚠️  Detected conflicts for {doc_name}: {len(conflicts)} potential issues")
            await self._handle_integration_conflicts(doc_name, conflicts)
        
        # Create knowledge document
        hub_doc = KnowledgeDocument(
            id=f"hub_{doc_name.lower().replace('.', '_')}",
            title=f"Hub: {doc_name.replace('.md', '').replace('_', ' ')}",
            content=doc_content,
            doc_type=doc_type,
            level=doc_level,
            tags=self._extract_tags(doc_content) | {"hub_source", "external"}
        )
        
        # Add to library with special marking
        self.library.add_document(hub_doc)
        self.processed_docs.add(doc_hash)
        self.integration_stats["docs_integrated"] += 1
        
        print(f"✅ Integrated hub document: {hub_doc.title}")
    
    def _classify_document_type(self, filename: str, content: str) -> DocumentType:
        """Classify document type based on name and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        if "tutorial" in filename_lower or "getting started" in content_lower:
            return DocumentType.TUTORIAL
        elif "guide" in filename_lower or "how to" in content_lower:
            return DocumentType.GUIDE
        elif "faq" in filename_lower or "frequently asked" in content_lower:
            return DocumentType.FAQ
        elif "api" in filename_lower or "reference" in content_lower:
            return DocumentType.REFERENCE
        elif "readme" in filename_lower:
            return DocumentType.GUIDE
        else:
            return DocumentType.TECHNICAL
    
    def _determine_knowledge_level(self, content: str) -> KnowledgeLevel:
        """Determine knowledge level based on content complexity"""
        content_lower = content.lower()
        
        beginner_indicators = ["getting started", "introduction", "basic", "simple"]
        advanced_indicators = ["advanced", "complex", "sophisticated", "enterprise"]
        
        if any(indicator in content_lower for indicator in beginner_indicators):
            return KnowledgeLevel.BEGINNER
        elif any(indicator in content_lower for indicator in advanced_indicators):
            return KnowledgeLevel.ADVANCED
        else:
            return KnowledgeLevel.INTERMEDIATE
    
    def _extract_tags(self, content: str) -> Set[str]:
        """Extract relevant tags from document content"""
        tag_keywords = {
            "template": ["template", "scaffold", "generator"],
            "automation": ["automation", "workflow", "ci/cd", "pipeline"],
            "github": ["github", "git", "repository", "pull request"],
            "development": ["development", "coding", "programming"],
            "documentation": ["documentation", "docs", "guide"],
            "testing": ["testing", "test", "coverage", "quality"],
            "deployment": ["deployment", "deploy", "production", "release"]
        }
        
        content_lower = content.lower()
        extracted_tags = set()
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                extracted_tags.add(tag)
        
        return extracted_tags
    
    async def _check_integration_conflicts(self, doc_name: str, content: str) -> List[str]:
        """Check for potential conflicts with existing documentation"""
        conflicts = []
        
        # Look for documents with similar titles or content
        content_lower = content.lower()
        
        for existing_id, existing_doc in self.library.documents.items():
            # Skip hub documents to avoid self-conflicts
            if "hub_" in existing_id:
                continue
            
            existing_content_lower = existing_doc.content.lower()
            
            # Check for contradictory information
            if self._detect_contradiction(content_lower, existing_content_lower):
                conflicts.append(f"Potential contradiction with {existing_doc.title}")
            
            # Check for significant overlap
            if self._detect_overlap(content_lower, existing_content_lower) > 0.7:
                conflicts.append(f"High content overlap with {existing_doc.title}")
        
        return conflicts
    
    def _detect_contradiction(self, content1: str, content2: str) -> bool:
        """Simple contradiction detection (would be more sophisticated in reality)"""
        # Look for contradictory statements about the same concepts
        contradiction_patterns = [
            ("recommended", "not recommended"),
            ("should", "should not"),
            ("best practice", "avoid"),
            ("deprecated", "recommended")
        ]
        
        for positive, negative in contradiction_patterns:
            if positive in content1 and negative in content2:
                return True
            if negative in content1 and positive in content2:
                return True
        
        return False
    
    def _detect_overlap(self, content1: str, content2: str) -> float:
        """Calculate content overlap percentage"""
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _handle_integration_conflicts(self, doc_name: str, conflicts: List[str]):
        """Handle detected conflicts during integration"""
        self.integration_stats["conflicts_detected"] += len(conflicts)
        
        print(f"🤔 Contemplating conflicts for {doc_name}:")
        for conflict in conflicts:
            print(f"   • {conflict}")
        
        # In a real implementation, this would:
        # 1. Alert human reviewers
        # 2. Create conflict resolution tasks
        # 3. Suggest document updates
        # 4. Track conflict resolution progress
        
        # For now, just log and continue
        print("📝 Conflicts noted for future resolution")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get current status of hub integration"""
        return {
            "hub_config": {
                "source": self.hub_config.name,
                "base_url": self.hub_config.base_url,
                "has_auth": bool(self.hub_config.auth_token),
                "paths_monitored": len(self.hub_config.documentation_paths)
            },
            "statistics": self.integration_stats,
            "processed_documents": len(self.processed_docs),
            "last_sync": self.integration_stats.get("last_sync", "Never")
        }

# Integration with main garden system
async def start_hub_integration_garden():
    """Start the complete garden with hub integration"""
    print("🌱 Initializing Rooftop Garden with NuSyQ-Hub Integration...")
    
    # Create knowledge library
    library = KnowledgeLibrary()
    
    # Create garden orchestrator
    garden = RooftopGardenOrchestrator(library)
    
    # Create hub integrator
    hub_integrator = NuSyQHubDocumentationIntegrator(garden)
    
    # Create standard custodians
    garden.create_custodian("Sage", CustodianPersonality.CONTEMPLATIVE)
    garden.create_custodian("Harmony", CustodianPersonality.HARMONIOUS)
    garden.create_custodian("Quest", CustodianPersonality.CURIOUS)
    
    print("🔗 Starting hub documentation integration...")
    await hub_integrator.integrate_hub_documentation_leisurely()
    
    print("🌿 Starting garden activities with integrated knowledge...")
    
    # Start garden with hub-integrated knowledge
    try:
        asyncio.create_task(garden.start_garden_activities())
        await asyncio.sleep(180)  # 3 minutes demo
        await garden.stop_garden_activities()
        
        print("\n📊 Integration Summary:")
        status = hub_integrator.get_integration_status()
        print(f"   Hub Documents Discovered: {status['statistics']['docs_discovered']}")
        print(f"   Documents Integrated: {status['statistics']['docs_integrated']}")
        print(f"   Conflicts Detected: {status['statistics']['conflicts_detected']}")
        
    except KeyboardInterrupt:
        await garden.stop_garden_activities()
        print("\n🌅 Garden day with hub integration peacefully concluded")

if __name__ == "__main__":
    asyncio.run(start_hub_integration_garden())