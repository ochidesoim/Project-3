"""
LumenOrb v2.0 - Engineering Knowledge Base
RAG (Retrieval Augmented Generation) system for mechanical engineering documents
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
import hashlib

# Optional dependencies - will work without them but with limited features
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("⚠️ chromadb not installed - RAG features disabled. Install with: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ sentence-transformers not installed - Using basic search. Install with: pip install sentence-transformers")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyPDF2 not installed - PDF ingestion disabled. Install with: pip install pypdf2")


class EngineeringKnowledgeBase:
    """
    Knowledge base for mechanical engineering documents with semantic search.
    
    Features:
    - Ingest PDF/TXT documents
    - Create vector embeddings for semantic search
    - Query with natural language
    - Provide context for AI prompts
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the knowledge base.
        
        Args:
            data_dir: Directory to store the vector database
        """
        self.data_dir = data_dir or Path("data/knowledge_base")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model
        self.embedder = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Loaded embedding model: all-MiniLM-L6-v2")
            except Exception as e:
                print(f"⚠️ Could not load embedding model: {e}")
        
        # Initialize ChromaDB
        self.collection = None
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=str(self.data_dir / "chroma"),
                    anonymized_telemetry=False
                ))
                self.collection = self.client.get_or_create_collection(
                    name="engineering_docs",
                    metadata={"description": "Mechanical engineering knowledge base"}
                )
                print(f"✅ ChromaDB initialized with {self.collection.count()} documents")
            except Exception as e:
                print(f"⚠️ Could not initialize ChromaDB: {e}")
        
        # Fallback: Simple document store
        self.documents: List[Dict[str, Any]] = []
        self._load_simple_store()
    
    def _load_simple_store(self):
        """Load documents from simple JSON store (fallback)."""
        store_path = self.data_dir / "documents.json"
        if store_path.exists():
            try:
                with open(store_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                print(f"✅ Loaded {len(self.documents)} documents from simple store")
            except Exception as e:
                print(f"⚠️ Could not load document store: {e}")
    
    def _save_simple_store(self):
        """Save documents to simple JSON store."""
        store_path = self.data_dir / "documents.json"
        with open(store_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2)
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from a PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not installed")
        
        text = ""
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def _generate_id(self, text: str) -> str:
        """Generate a unique ID for a text chunk."""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def ingest_document(self, file_path: Path, metadata: Optional[Dict] = None) -> int:
        """
        Ingest a document into the knowledge base.
        
        Args:
            file_path: Path to PDF or TXT file
            metadata: Optional metadata (source, topic, etc.)
            
        Returns:
            Number of chunks added
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text
        if file_path.suffix.lower() == '.pdf':
            text = self._extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() in ['.txt', '.md']:
            text = file_path.read_text(encoding='utf-8')
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        # Chunk the text
        chunks = self._chunk_text(text)
        
        # Prepare metadata
        base_metadata = {
            "source": str(file_path),
            "filename": file_path.name,
            **(metadata or {})
        }
        
        # Add to ChromaDB if available
        if self.collection and self.embedder:
            ids = [self._generate_id(chunk) for chunk in chunks]
            embeddings = self.embedder.encode(chunks).tolist()
            metadatas = [base_metadata] * len(chunks)
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            print(f"✅ Added {len(chunks)} chunks to ChromaDB from {file_path.name}")
        
        # Also add to simple store (fallback)
        for chunk in chunks:
            self.documents.append({
                "id": self._generate_id(chunk),
                "text": chunk,
                "metadata": base_metadata
            })
        self._save_simple_store()
        
        return len(chunks)
    
    def query(self, query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the knowledge base with semantic search.
        
        Args:
            query_text: Natural language query
            n_results: Number of results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        results = []
        
        # Try ChromaDB first
        if self.collection and self.embedder:
            try:
                query_embedding = self.embedder.encode([query_text]).tolist()
                chroma_results = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=n_results
                )
                
                for i, doc in enumerate(chroma_results['documents'][0]):
                    results.append({
                        "text": doc,
                        "metadata": chroma_results['metadatas'][0][i] if chroma_results['metadatas'] else {},
                        "distance": chroma_results['distances'][0][i] if chroma_results['distances'] else 0
                    })
                return results
            except Exception as e:
                print(f"⚠️ ChromaDB query failed: {e}, falling back to simple search")
        
        # Fallback: Simple keyword search
        query_words = set(query_text.lower().split())
        scored_docs = []
        
        for doc in self.documents:
            doc_words = set(doc['text'].lower().split())
            overlap = len(query_words & doc_words)
            if overlap > 0:
                scored_docs.append((overlap, doc))
        
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        
        for score, doc in scored_docs[:n_results]:
            results.append({
                "text": doc['text'],
                "metadata": doc['metadata'],
                "score": score
            })
        
        return results
    
    def get_context_for_prompt(self, query: str, max_tokens: int = 1000) -> str:
        """
        Get relevant context to inject into an AI prompt.
        
        Args:
            query: The user's query
            max_tokens: Maximum context length (rough estimate)
            
        Returns:
            Formatted context string
        """
        results = self.query(query, n_results=3)
        
        if not results:
            return ""
        
        context_parts = ["=== RELEVANT ENGINEERING KNOWLEDGE ==="]
        total_length = 0
        
        for result in results:
            text = result['text']
            source = result['metadata'].get('filename', 'Unknown')
            
            chunk = f"\n[Source: {source}]\n{text}\n"
            
            if total_length + len(chunk.split()) > max_tokens:
                break
            
            context_parts.append(chunk)
            total_length += len(chunk.split())
        
        return "\n".join(context_parts)
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all ingested documents."""
        sources = {}
        for doc in self.documents:
            source = doc['metadata'].get('source', 'Unknown')
            if source not in sources:
                sources[source] = 0
            sources[source] += 1
        
        return [{"source": s, "chunks": c} for s, c in sources.items()]
    
    def clear(self):
        """Clear all documents from the knowledge base."""
        self.documents = []
        self._save_simple_store()
        
        if self.collection:
            # Delete and recreate collection
            self.client.delete_collection("engineering_docs")
            self.collection = self.client.create_collection(
                name="engineering_docs",
                metadata={"description": "Mechanical engineering knowledge base"}
            )
        
        print("✅ Knowledge base cleared")


# Built-in engineering knowledge (always available)
BUILTIN_KNOWLEDGE = """
## Common Mechanical Engineering Formulas

### Stress and Strain
- Tensile Stress: σ = F/A (Force / Area)
- Strain: ε = ΔL/L (Change in length / Original length)
- Young's Modulus: E = σ/ε
- Shear Stress: τ = F/A (tangential force / area)

### Beam Bending
- Bending Moment: M = F × d
- Bending Stress: σ = My/I (Moment × distance from neutral axis / Moment of inertia)
- Deflection (cantilever): δ = FL³/3EI

### Pressure Vessels
- Hoop Stress (thin wall): σ = pr/t (pressure × radius / thickness)
- Longitudinal Stress: σ = pr/2t
- Thick wall (Lamé): σr = A - B/r², σθ = A + B/r²

### Gear Design
- Gear Ratio: i = N₂/N₁ = ω₁/ω₂ = d₂/d₁
- Module: m = d/N (pitch diameter / number of teeth)
- Circular Pitch: p = πm
- Pressure Angle: typically 20° standard

### Heat Transfer
- Conduction: Q = kA(ΔT)/L
- Convection: Q = hA(ΔT)
- Radiation: Q = εσA(T₁⁴ - T₂⁴)
- Gyroid lattice increases surface area by ~400%

### Shaft Design
- Torsional Stress: τ = Tr/J
- Power: P = 2πNT/60 (N in RPM, T in Nm)
- Critical Speed: ωc = √(k/m)
"""


def get_builtin_context(query: str) -> str:
    """
    Get relevant context from built-in engineering knowledge.
    Simple keyword matching for the built-in database.
    """
    query_lower = query.lower()
    
    keywords = {
        "stress": ["Stress and Strain", "Beam Bending", "Pressure Vessels"],
        "strain": ["Stress and Strain"],
        "beam": ["Beam Bending"],
        "pressure": ["Pressure Vessels"],
        "vessel": ["Pressure Vessels"],
        "gear": ["Gear Design"],
        "heat": ["Heat Transfer"],
        "thermal": ["Heat Transfer"],
        "cooling": ["Heat Transfer"],
        "lattice": ["Heat Transfer"],
        "gyroid": ["Heat Transfer"],
        "shaft": ["Shaft Design"],
        "torque": ["Shaft Design"],
        "torsion": ["Shaft Design"],
    }
    
    sections_to_include = set()
    for keyword, sections in keywords.items():
        if keyword in query_lower:
            sections_to_include.update(sections)
    
    if not sections_to_include:
        return ""
    
    # Extract relevant sections
    lines = BUILTIN_KNOWLEDGE.split('\n')
    result = []
    current_section = None
    include_current = False
    
    for line in lines:
        if line.startswith('### '):
            current_section = line[4:].strip()
            include_current = current_section in sections_to_include
        
        if include_current:
            result.append(line)
    
    return '\n'.join(result)
