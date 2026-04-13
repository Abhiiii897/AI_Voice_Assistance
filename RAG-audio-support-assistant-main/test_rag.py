#!/usr/bin/env python3
"""
Test script to validate RAG search with BGE-M3 embeddings
Run this after ingestion is complete
"""

import chromadb
from rag_search import RAGSearcher
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_search():
    """Test RAG search functionality"""
    
    print("\n" + "=" * 80)
    print("RAG SEARCH TEST - BGE-M3 Embeddings")
    print("=" * 80)
    
    try:
        # Initialize RAG searcher
        logger.info("Initializing RAG searcher...")
        searcher = RAGSearcher()
        
        # Test queries
        test_queries = [
            "Tell me about Rover",
            "spindle error",
            "maintenance procedure",
            "How to troubleshoot",
        ]
        
        print("\n" + "-" * 80)
        print("TEST RESULTS:")
        print("-" * 80)
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = searcher.search(query, top_k=2)
            
            if results:
                print(f"  ✓ Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"    [{i}] {result.source} (similarity: {result.similarity_score:.2%})")
                    # Show snippet
                    snippet = result.text[:100].replace('\n', ' ')
                    print(f"        → {snippet}...")
            else:
                print(f"  ✗ No results found")
        
        print("\n" + "=" * 80)
        print("✓ RAG Search test completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import sys
    success = test_rag_search()
    sys.exit(0 if success else 1)
