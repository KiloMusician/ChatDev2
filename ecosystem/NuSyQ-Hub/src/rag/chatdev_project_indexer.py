"""ChatDev Project Auto-Indexer - RAG Integration for Project Context.

Automatically indexes ChatDev project outputs (metadata, documentation, code,
test results) into a vector store for semantic retrieval during future agent tasks.

Inspired by:
- ChatOllama's project context retrieval
- LangChain's document loaders and embedding system

OmniTag: {
    "purpose": "Semantic indexing of ChatDev projects for RAG",
    "dependencies": ["chroma", "embeddings", "quest_system"],
    "context": "Vector storage, semantic search, project metadata",
    "evolution_stage": "v1.0"
}
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Module-level constants
README_FILENAME = "README.md"


@dataclass
class ProjectMetadata:
    """Metadata about a ChatDev project."""

    project_name: str
    project_path: str
    created_at: str
    completed_at: str | None = None
    status: str = "in_progress"  # in_progress, completed, failed
    task_description: str = ""
    model_used: str = ""
    agents: list[str] | None = None  # CEO, CTO, Programmer, etc.

    def __post_init__(self):
        """Implement __post_init__."""
        if self.agents is None:
            self.agents = []


@dataclass
class ProjectDocument:
    """A document chunk from a ChatDev project ready for indexing."""

    doc_id: str
    project_name: str
    source_type: str  # metadata, readme, code, test, review
    content: str
    metadata: dict[str, Any]
    created_at: str | None = None

    def __post_init__(self):
        """Implement __post_init__."""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class ChatDevProjectIndexer:
    """Indexes ChatDev projects to vector store for RAG."""

    def __init__(
        self,
        chatdev_root: Path | None = None,
        vector_store_type: str | None = None,
        embedding_model: str | None = None,
        vector_store_config: dict[str, Any] | None = None,
        embedding_config: dict[str, Any] | None = None,
    ):
        """Initialize project indexer with multi-store/model support.

        Args:
            chatdev_root: Path to ChatDev workspace
            vector_store_type: Type of vector store (chroma, faiss, pinecone, qdrant, etc.)
            embedding_model: Embedding model name (OpenAI, HuggingFace, etc.)
            vector_store_config: Extra config for vector store
            embedding_config: Extra config for embedding model
        """
        self.chatdev_root = chatdev_root or self._get_default_chatdev_root()
        self.vector_store_type = vector_store_type or os.environ.get("RAG_VECTOR_STORE", "chroma")
        self.embedding_model = embedding_model or os.environ.get(
            "RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2"
        )
        self.vector_store_config = vector_store_config or {}
        self.embedding_config = embedding_config or {}
        self.indexed_projects: dict[str, ProjectMetadata] = {}
        self.documents: list[ProjectDocument] = []

        # Initialize vector store handler
        self.vector_store = None
        self.collection = None
        if self._has_vector_store_available():
            self._initialize_vector_store()

    def _has_vector_store_available(self) -> bool:
        """Check if vector store dependencies are available for selected backend."""
        try:
            if self.vector_store_type == "chroma":
                __import__("chromadb")
                return True
            elif self.vector_store_type == "faiss":
                __import__("faiss")
                return True
            elif self.vector_store_type == "pinecone":
                __import__("pinecone")
                return True
            elif self.vector_store_type == "qdrant":
                __import__("qdrant_client")
                return True
            else:
                logger.warning(f"Unknown vector store type: {self.vector_store_type}")
                return False
        except ImportError:
            logger.warning(f"{self.vector_store_type} not installed, indexing disabled")
            return False

    def _initialize_vector_store(self) -> None:
        """Initialize vector store connection for selected backend."""
        try:
            if self.vector_store_type == "chroma":
                import chromadb

                self.vector_store = chromadb.Client()
                self.collection = self.vector_store.get_or_create_collection(
                    name="chatdev_projects", metadata={"usage": "ChatDev project semantic search"}
                )
                logger.info("✅ Vector store initialized (Chroma)")
            elif self.vector_store_type == "faiss":
                import faiss

                # Placeholder: actual FAISS integration needed
                logger.info("✅ Vector store initialized (FAISS, stub)")
            elif self.vector_store_type == "pinecone":
                import pinecone

                # Placeholder: actual Pinecone integration needed
                logger.info("✅ Vector store initialized (Pinecone, stub)")
            elif self.vector_store_type == "qdrant":
                import qdrant_client

                # Placeholder: actual Qdrant integration needed
                logger.info("✅ Vector store initialized (Qdrant, stub)")
            else:
                logger.warning(f"Unknown vector store type: {self.vector_store_type}")
        except ImportError:
            logger.warning(f"{self.vector_store_type} not available, vector store disabled")
            self.vector_store = None

    def _get_embedding_model(self):
        """Return an embedding callable or model name string.

        Resolution order:
        1. sentence-transformers (local, offline)
        2. HuggingFace MCP bridge (requires HF_TOKEN env var)
        3. OpenAI embeddings (requires OPENAI_API_KEY)
        4. Ollama embeddings (requires local Ollama)
        5. Fall back to raw model name string (caller must handle)
        """
        model = self.embedding_model  # e.g. "all-MiniLM-L6-v2" or "text-embedding-ada-002"

        # 1. sentence-transformers (fully local)
        try:
            from sentence_transformers import \
                SentenceTransformer  # type: ignore[import]

            return SentenceTransformer(model)
        except ImportError:
            pass

        # 2. HuggingFace bridge (MCP)
        if os.environ.get("HF_TOKEN"):
            try:
                from src.integrations.huggingface_bridge import \
                    get_huggingface_bridge

                return get_huggingface_bridge()
            except ImportError:
                pass

        # 3. OpenAI embeddings
        if os.environ.get("OPENAI_API_KEY"):
            try:
                from openai import OpenAI  # type: ignore[import]

                client = OpenAI()

                def openai_embed(texts: list[str]) -> list[list[float]]:
                    resp = client.embeddings.create(model=model, input=texts)
                    return [e.embedding for e in resp.data]

                return openai_embed
            except ImportError:
                pass

        # 4. Ollama embeddings (local, no API key)
        try:
            import json as _json
            import urllib.request

            def ollama_embed(texts: list[str]) -> list[list[float]]:
                results = []
                for text in texts:
                    payload = _json.dumps({"model": model, "prompt": text}).encode()
                    req = urllib.request.Request(
                        "http://127.0.0.1:11434/api/embeddings",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=10) as r:
                        results.append(_json.loads(r.read())["embedding"])
                return results

            return ollama_embed
        except Exception:
            pass

        # 5. Return model name string — caller must handle
        logger.warning(
            "No embedding backend available (sentence-transformers/HF/OpenAI/Ollama). Returning model name string: %s",
            model,
        )
        return model

    def _get_default_chatdev_root(self) -> Path:
        """Get default ChatDev root directory."""
        return Path("C:/Users/keath/NuSyQ/ChatDev")

    def _has_vector_store_available(self) -> bool:
        """Check if vector store dependencies are available."""
        try:
            # Test if chromadb can be imported
            __import__("chromadb")
            return True
        except ImportError:
            logger.warning("Chroma not installed, indexing disabled")
            return False

    def _initialize_vector_store(self) -> None:
        """Initialize vector store connection."""
        try:
            import chromadb

            # Create Chroma client
            self.vector_store = chromadb.Client()

            # Create or get collection for ChatDev projects
            self.collection = self.vector_store.get_or_create_collection(
                name="chatdev_projects", metadata={"usage": "ChatDev project semantic search"}
            )

            logger.info("✅ Vector store initialized (Chroma)")
        except ImportError:
            logger.warning("Chroma not available, vector store disabled")
            self.vector_store = None

    def index_project(
        self, project_path: Path, project_metadata: dict[str, Any] | None = None
    ) -> bool:
        """Index a ChatDev project.

        Args:
            project_path: Path to project directory
            project_metadata: Optional metadata overrides

        Returns:
            True if successful
        """
        try:
            project_name = project_path.name

            logger.info(f"📝 Indexing project: {project_name}")

            # Discover and load documents
            documents = self._load_project_documents(project_path)

            if not documents:
                logger.warning(f"No documents found in {project_name}")
                return False

            # Index documents
            self._index_documents(project_name, documents)

            # Store project metadata
            metadata = ProjectMetadata(
                project_name=project_name,
                project_path=str(project_path),
                created_at=datetime.now().isoformat(),
                **(project_metadata or {}),
            )
            self.indexed_projects[project_name] = metadata

            logger.info(f"✅ Indexed {len(documents)} documents from {project_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to index project: {e}")
            return False

    def _load_project_documents(self, project_path: Path) -> list[ProjectDocument]:
        """Load documents from a ChatDev project.

        Args:
            project_path: Path to project

        Returns:
            List of ProjectDocument objects
        """
        documents = []
        project_name = project_path.name

        # Skip very large directories
        try:
            total_size = sum(f.stat().st_size for f in project_path.rglob("*") if f.is_file())
            if total_size > 100_000_000:  # Skip if > 100MB
                logger.warning(
                    f"Skipping {project_name}: too large ({total_size / 1_000_000:.1f}MB)"
                )
                return documents
        except Exception:
            logger.debug("Suppressed Exception", exc_info=True)

        # Load project metadata/README
        readme_path = project_path / README_FILENAME
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding="utf-8")
                doc = ProjectDocument(
                    doc_id=f"{project_name}_readme",
                    project_name=project_name,
                    source_type="readme",
                    content=content,
                    metadata={"file": README_FILENAME},
                )
                documents.append(doc)
            except Exception as e:
                logger.debug(f"Failed to load README: {e}")

        # Load generated code files (limit to top-level and immediate subdirs)
        py_count = 0
        for py_file in project_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            # Skip node_modules, .git, etc.
            if any(part in py_file.parts for part in ["node_modules", ".git", "__pycache__"]):
                continue

            # Limit to 20 Python files per project
            if py_count >= 20:
                break

            try:
                content = py_file.read_text(encoding="utf-8")

                # Skip very large individual files
                if len(content) > 50000:
                    logger.debug(f"Skipping large file: {py_file.name}")
                    continue

                doc = ProjectDocument(
                    doc_id=f"{project_name}_{py_file.stem}",
                    project_name=project_name,
                    source_type="code",
                    content=content[:10000],  # Truncate to first 10k chars
                    metadata={"file": str(py_file.relative_to(project_path))},
                )
                documents.append(doc)
                py_count += 1
            except Exception as e:
                logger.debug(f"Failed to load {py_file}: {e}")

        # Load test results if available
        test_results_path = project_path / "test_results.json"
        if test_results_path.exists():
            try:
                with open(test_results_path, encoding="utf-8") as f:
                    test_data = json.load(f)

                doc = ProjectDocument(
                    doc_id=f"{project_name}_test_results",
                    project_name=project_name,
                    source_type="test",
                    content=json.dumps(test_data, indent=2)[:5000],
                    metadata={"file": "test_results.json"},
                )
                documents.append(doc)
            except Exception as e:
                logger.debug(f"Failed to load test results: {e}")

        # Load review/analysis if available
        review_path = project_path / "review.md"
        if review_path.exists():
            try:
                content = review_path.read_text(encoding="utf-8")
                doc = ProjectDocument(
                    doc_id=f"{project_name}_review",
                    project_name=project_name,
                    source_type="review",
                    content=content[:5000],
                    metadata={"file": "review.md"},
                )
                documents.append(doc)
            except Exception as e:
                logger.debug(f"Failed to load review: {e}")

        self.documents.extend(documents)
        return documents

    def _chunk_text(self, text: str, chunk_size: int = 3000, _overlap: int = 300) -> list[str]:
        """Chunk text for indexing.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        # For performance, just return single chunk truncated
        return [text[:chunk_size]]

    def _index_documents(self, _project_name: str, documents: list[ProjectDocument]) -> None:
        """Index documents to vector store.

        Args:
            project_name: Project name
            documents: Documents to index
        """
        if not self.vector_store:
            logger.warning("Vector store not available, skipping indexing")
            return

        try:
            # Prepare data for Chroma
            ids = []
            documents_text = []
            metadatas = []

            for doc in documents:
                ids.append(doc.doc_id)
                documents_text.append(doc.content)
                metadatas.append(
                    {
                        "project_name": doc.project_name,
                        "source_type": doc.source_type,
                        "created_at": doc.created_at,
                        **doc.metadata,
                    }
                )

            # Add to collection
            self.collection.add(ids=ids, documents=documents_text, metadatas=metadatas)

            logger.info(f"✅ Added {len(documents)} documents to vector store")

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")

    def search_projects(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search indexed projects by semantic similarity.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of matching documents with scores
        """
        if not self.vector_store:
            logger.warning("Vector store not available")
            return []

        try:
            results = self.collection.query(query_texts=[query], n_results=top_k)

            # Format results
            formatted = []
            for i, doc_id in enumerate(results["ids"][0]):
                formatted.append(
                    {
                        "doc_id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else None,
                    }
                )

            return formatted

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def index_workspace(self, start_fresh: bool = False) -> int:
        """Index all ChatDev projects in workspace.

        Args:
            start_fresh: Clear existing index

        Returns:
            Number of projects indexed
        """
        if start_fresh:
            self.indexed_projects.clear()
            self.documents.clear()

        indexed_count = 0

        if not self.chatdev_root.exists():
            logger.warning(f"ChatDev root not found: {self.chatdev_root}")
            return 0

        # Find all project folders
        for item in self.chatdev_root.iterdir():
            if not item.is_dir():
                continue

            # Look for ChatDev project indicators
            if self._is_chatdev_project(item) and self.index_project(item):
                indexed_count += 1

        logger.info(f"✅ Indexed {indexed_count} projects from workspace")
        return indexed_count

    def _is_chatdev_project(self, path: Path) -> bool:
        """Check if directory is a ChatDev project.

        Args:
            path: Directory path

        Returns:
            True if ChatDev project
        """
        # ChatDev projects have specific naming pattern or structure
        has_readme = (path / README_FILENAME).exists()
        has_code = any(path.glob("*.py"))

        return has_readme or has_code

    def export_index_manifest(self) -> dict[str, Any]:
        """Export index manifest for persistence.

        Returns:
            Manifest dict
        """
        return {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "indexed_projects": len(self.indexed_projects),
            "total_documents": len(self.documents),
            "projects": {name: asdict(meta) for name, meta in self.indexed_projects.items()},
            "vector_store_type": self.vector_store_type,
            "embedding_model": self.embedding_model,
        }

    def save_manifest(self, output_path: Path | None = None) -> bool:
        """Save index manifest to file.

        Args:
            output_path: Path to save manifest

        Returns:
            True if successful
        """
        try:
            output_path = output_path or Path("config/chatdev_index_manifest.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)

            manifest = self.export_index_manifest()

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            logger.info(f"✅ Saved manifest to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
            return False


# Global instance
_indexer: ChatDevProjectIndexer | None = None


def get_chatdev_project_indexer() -> ChatDevProjectIndexer:
    """Get global ChatDev project indexer instance.

    Returns:
        ChatDevProjectIndexer instance
    """
    global _indexer
    if _indexer is None:
        _indexer = ChatDevProjectIndexer()
    return _indexer


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    indexer = get_chatdev_project_indexer()

    logger.info("ChatDev Project Indexer")
    logger.info("=" * 60)

    # Index workspace
    logger.info(f"\n📂 ChatDev root: {indexer.chatdev_root}")
    count = indexer.index_workspace()
    logger.info(f"✅ Indexed {count} projects")

    # Show indexed projects
    if indexer.indexed_projects:
        logger.info(f"\n📋 Indexed Projects ({len(indexer.indexed_projects)}):")
        for name in indexer.indexed_projects:
            logger.info(f"  • {name}")

    # Show statistics
    logger.info("\n📊 Statistics:")
    logger.info(f"  Total documents: {len(indexer.documents)}")
    logger.info(f"  Vector store: {indexer.vector_store_type}")
    logger.info(f"  Embedding model: {indexer.embedding_model}")

    # Save manifest
    logger.info("\n💾 Saving manifest...")
    indexer.save_manifest()

    # Example search
    if indexer.vector_store:
        logger.info("\n🔍 Example search (if vector store available):")
        results = indexer.search_projects("API endpoints and HTTP methods")
        for result in results[:3]:
            logger.info(f"  • {result['doc_id']}")
