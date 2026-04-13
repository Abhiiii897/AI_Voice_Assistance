#!/usr/bin/env python3
"""
RAG Search Module for the Audio RAG Support Assistant

Provides semantic search over ingested technical manuals using Gemini embeddings.
Used at runtime during agent conversations.

Usage:
    from rag_search import RAGSearcher
    
    searcher = RAGSearcher()
    results = searcher.search("How to troubleshoot spindle errors?", top_k=3)
"""

import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
import chromadb
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class SearchResult:
    """Represents a single search result from the vector database"""
    text: str
    source: str
    chunk_index: int
    total_chunks: int
    similarity_score: float  # 0.0 to 1.0 (higher is better)
    metadata: Dict
    
    def __str__(self):
        return f"SearchResult(source={self.source}, similarity={self.similarity_score:.2%})"


# ============================================================================
# RAG Searcher
# ============================================================================

class RAGSearcher:
    """
    Semantic search over technical manuals using local SentenceTransformer embeddings and ChromaDB.
    
    Example:
        searcher = RAGSearcher()
        results = searcher.search("spindle troubleshooting", top_k=3)
        
        for result in results:
            print(f"Source: {result.source}")
            print(f"Text: {result.text}")
    """
    
    def __init__(
        self,
        collection_name: str = "support_manuals_minilm",
        vectordb_path: str = "data/vectordb",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize RAG searcher with local embeddings.
        
        Args:
            collection_name: Name of ChromaDB collection to search
            vectordb_path: Path to ChromaDB storage
            model_name: SentenceTransformer model name
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize Embedding Model
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB
        self.vectordb_path = vectordb_path
        self.collection_name = collection_name
        
        logger.info(f"Initializing RAG searcher...")
        logger.info(f"  Collection: {collection_name}")
        logger.info(f"  Vector DB: {vectordb_path}")
        logger.info(f"  Embedding model: {model_name}")
        
        try:
            self.chroma_client = chromadb.PersistentClient(path=vectordb_path)
            self.collection = self.chroma_client.get_collection(collection_name)
            
            doc_count = self.collection.count()
            logger.info(f"✓ Connected to collection with {doc_count} chunks")
            
        except Exception as e:
            logger.warning(f"ChromaDB collection '{collection_name}' not found: {e}")
            logger.info(f"  (Run ingest_docs.py to create and populate the collection)")
            self.collection = None
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """
        Embed a search query using local model.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector or None on failure
        """
        try:
            embedding = self.model.encode([query])[0].tolist()
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return None
    
    def search(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query (can be full conversation text or extracted keywords)
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"machine_type": "CNC Router"})
            
        Returns:
            List of SearchResult objects, sorted by relevance
        """
        # Check if collection is initialized
        if self.collection is None:
            logger.warning("Vector database not initialized yet - no indexed documents")
            return []
        
        logger.info(f"Searching for: '{query[:100]}...'")
        logger.info(f"Top K: {top_k}")
        
        # Embed query
        query_embedding = self.embed_query(query)
        
        if not query_embedding:
            logger.error("Failed to embed query, returning empty results")
            return []
        
        # Search ChromaDB
        try:
            query_params = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"]
            }
            
            # Add metadata filter if provided
            if filter_metadata:
                query_params["where"] = filter_metadata
                logger.info(f"Filter: {filter_metadata}")
            
            results = self.collection.query(**query_params)
            
            # Parse results
            search_results = []
            
            for doc, metadata, distance in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                # Convert distance to similarity score (0.0 to 1.0)
                # Cosine distance ranges from 0 (identical) to 2 (opposite)
                similarity = max(0.0, 1.0 - (distance / 2.0))
                
                search_results.append(SearchResult(
                    text=doc,
                    source=metadata.get('source', 'Unknown'),
                    chunk_index=metadata.get('chunk_index', 0),
                    total_chunks=metadata.get('total_chunks', 0),
                    similarity_score=similarity,
                    metadata=metadata
                ))
            
            logger.info(f"✓ Found {len(search_results)} results")
            
            # Log top result for debugging
            if search_results:
                top_result = search_results[0]
                logger.info(f"Top result: {top_result.source} (similarity: {top_result.similarity_score:.2%})")
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def format_results_for_llm(
        self,
        results: List[SearchResult],
        max_chars: int = 3000
    ) -> str:
        """
        Format search results as context for LLM prompt.
        
        Args:
            results: List of SearchResult objects
            max_chars: Maximum characters to include (to stay within token limits)
            
        Returns:
            Formatted string with results
        """
        if not results:
            return "No relevant documentation found."
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results, 1):
            # Format single result
            result_text = f"""
[Document {i}]
Source: {result.source}
Relevance: {result.similarity_score:.1%}

{result.text}
---
"""
            
            result_length = len(result_text)
            
            # Check if adding this result would exceed limit
            if current_length + result_length > max_chars and i > 1:
                context_parts.append(f"\n[... {len(results) - i + 1} more results omitted due to length ...]")
                break
            
            context_parts.append(result_text)
            current_length += result_length
        
        return "\n".join(context_parts)
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the vector database collection.
        
        Returns:
            Dictionary with collection stats
        """
        try:
            count = self.collection.count()
            
            # Sample a few documents to get metadata
            sample = self.collection.peek(limit=10)
            
            # Count unique sources
            sources = set()
            if sample and 'metadatas' in sample:
                for metadata in sample['metadatas']:
                    if 'source' in metadata:
                        sources.add(metadata['source'])
            
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "sample_sources": list(sources)[:5],
                "vectordb_path": self.vectordb_path
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# ============================================================================
# Helper Functions
# ============================================================================

def extract_search_query_from_conversation(
    conversation_text: str,
    max_length: int = 500
) -> str:
    """
    Extract a focused search query from full conversation text.
    
    For better search results, you may want to:
    - Extract just the last user question
    - Use an LLM to reformulate the question
    - Extract key technical terms
    
    Args:
        conversation_text: Full conversation history
        max_length: Maximum query length
        
    Returns:
        Processed query string
    """
    # Simple approach: use last portion of conversation
    # For production, consider using LLM to extract key query
    
    if len(conversation_text) <= max_length:
        return conversation_text
    
    # Take the last N characters (usually the most recent context)
    return conversation_text[-max_length:]


def build_rag_context(
    conversation_text: str,
    searcher: RAGSearcher,
    top_k: int = 3,
    include_stats: bool = False
) -> Dict:
    """
    Build RAG context for LLM suggestion generation.
    
    This is what you'll call from your orchestrator when processing conversations.
    
    Args:
        conversation_text: Full conversation transcript
        searcher: Initialized RAGSearcher instance
        top_k: Number of document chunks to retrieve
        include_stats: Whether to include search statistics
        
    Returns:
        Dictionary with context and metadata
    """
    # Extract focused query
    search_query = extract_search_query_from_conversation(conversation_text)
    
    # Search for relevant chunks
    results = searcher.search(search_query, top_k=top_k)
    
    # Format for LLM
    formatted_context = searcher.format_results_for_llm(results)
    
    # Build return object
    context = {
        "search_query": search_query,
        "num_results": len(results),
        "formatted_context": formatted_context,
        "results": results  # Raw results if needed
    }
    
    if include_stats:
        context["stats"] = searcher.get_collection_stats()
    
    return context


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Example usage of RAG searcher"""
    
    # Initialize searcher
    searcher = RAGSearcher(
        collection_name="support_manuals",
        vectordb_path="data/vectordb"
    )
    
    # Print collection stats
    stats = searcher.get_collection_stats()
    print("\n" + "="*80)
    print("COLLECTION STATISTICS")
    print("="*80)
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Sample sources: {', '.join(stats['sample_sources'])}")
    print()
    
    # Example search
    query = "How to troubleshoot spindle motor errors?"
    
    print("="*80)
    print(f"SEARCH: {query}")
    print("="*80)
    
    results = searcher.search(query, top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"  Source: {result.source}")
        print(f"  Similarity: {result.similarity_score:.2%}")
        print(f"  Chunk: {result.chunk_index + 1}/{result.total_chunks}")
        print(f"  Preview: {result.text[:200]}...")
    
    print("\n" + "="*80)
    print("FORMATTED FOR LLM")
    print("="*80)
    
    formatted = searcher.format_results_for_llm(results)
    print(formatted)


if __name__ == "__main__":
    main()
