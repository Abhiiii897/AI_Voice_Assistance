#!/usr/bin/env python3
"""
Test script for validating document ingestion and search functionality.

Usage:
    # Test ingestion with a single file
    python test_ingestion.py --file data/manuals/sample.pdf
    
    # Test search functionality
    python test_ingestion.py --search "How to troubleshoot spindle errors"
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict

from google import genai
import chromadb
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Test Ingestion
# ============================================================================

def test_single_file_ingestion(file_path: str):
    """
    Test ingestion pipeline with a single file.
    
    Args:
        file_path: Path to test file
    """
    logger.info(f"\n{'='*80}")
    logger.info("TESTING SINGLE FILE INGESTION")
    logger.info(f"{'='*80}\n")
    
    # Import from ingest_docs
    try:
        from ingest_docs import (
            extract_text,
            clean_text,
            chunk_document,
            EmbeddingClient,
            init_chromadb
        )
    except ImportError:
        logger.error("Could not import from ingest_docs.py")
        logger.error("Make sure ingest_docs.py is in the same directory")
        sys.exit(1)
    
    # Load API key
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        logger.error("GOOGLE_API_KEY not found!")
        sys.exit(1)
    
    try:
        # Step 1: Extract text
        logger.info("Step 1: Extracting text...")
        text = extract_text(file_path)
        logger.info(f"✓ Extracted {len(text)} characters")
        logger.info(f"Preview: {text[:200]}...")
        
        # Step 2: Clean text
        logger.info("\nStep 2: Cleaning text...")
        cleaned = clean_text(text)
        logger.info(f"✓ Cleaned text: {len(cleaned)} characters")
        
        # Step 3: Chunk
        logger.info("\nStep 3: Chunking document...")
        chunks = chunk_document(cleaned)
        logger.info(f"✓ Created {len(chunks)} chunks")
        
        # Show chunk statistics
        chunk_sizes = [len(c) / 4 for c in chunks]  # Estimate tokens
        logger.info(f"Chunk size stats:")
        logger.info(f"  Min: {min(chunk_sizes):.0f} tokens")
        logger.info(f"  Max: {max(chunk_sizes):.0f} tokens")
        logger.info(f"  Avg: {sum(chunk_sizes)/len(chunk_sizes):.0f} tokens")
        
        # Show first chunk
        logger.info(f"\nFirst chunk preview:")
        logger.info(f"{chunks[0][:300]}...")
        
        # Step 4: Test embedding
        logger.info("\nStep 4: Testing embedding...")
        embedding_client = EmbeddingClient(google_api_key, output_dim=768)
        
        test_embedding = embedding_client.embed_text(chunks[0])
        
        if test_embedding:
            logger.info(f"✓ Embedding successful!")
            logger.info(f"  Dimension: {len(test_embedding)}")
            logger.info(f"  Sample values: {test_embedding[:5]}")
        else:
            logger.error("✗ Embedding failed!")
            return
        
        # Step 5: Test ChromaDB storage
        logger.info("\nStep 5: Testing ChromaDB storage...")
        chroma_client = init_chromadb("data/vectordb_test")
        collection = chroma_client.get_or_create_collection("test_collection")
        
        collection.add(
            ids=["test_chunk_0"],
            documents=[chunks[0]],
            embeddings=[test_embedding],
            metadatas=[{
                "source": file_path,
                "chunk_index": 0
            }]
        )
        
        logger.info(f"✓ Stored in ChromaDB")
        logger.info(f"  Collection count: {collection.count()}")
        
        # Step 6: Test retrieval
        logger.info("\nStep 6: Testing search...")
        query_embedding = embedding_client.embed_text("troubleshooting")
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=1
        )
        
        logger.info(f"✓ Search successful!")
        logger.info(f"  Retrieved: {results['documents'][0][0][:200]}...")
        
        logger.info(f"\n{'='*80}")
        logger.info("✓ ALL TESTS PASSED!")
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# Test Search
# ============================================================================

def test_search(query: str, collection_name: str = "support_manuals", top_k: int = 3):
    """
    Test semantic search functionality.

    Args:
        query: Search query
        collection_name: ChromaDB collection to search
        top_k: Number of results to return
    """
    logger.info(f"\n{'='*80}")
    logger.info("TESTING SEMANTIC SEARCH")
    logger.info(f"{'='*80}\n")
    logger.info(f"Query: '{query}'")
    logger.info(f"Collection: {collection_name}")
    logger.info(f"Top K: {top_k}\n")
    
    # Load API key
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        logger.error("GOOGLE_API_KEY not found!")
        sys.exit(1)
    
    try:
        # Initialize clients
        from ingest_docs import EmbeddingClient, init_chromadb
        
        embedding_client = EmbeddingClient(google_api_key, output_dim=768)
        chroma_client = init_chromadb("data/vectordb")
        
        # Get collection
        collection = chroma_client.get_collection(collection_name)
        logger.info(f"Collection '{collection_name}' has {collection.count()} chunks\n")
        
        # Embed query
        logger.info("Embedding query...")
        query_embedding = embedding_client.embed_text(query)
        
        if not query_embedding:
            logger.error("Failed to embed query!")
            return
        
        logger.info("✓ Query embedded\n")
        
        # Search
        logger.info(f"Searching for top {top_k} results...")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Display results
        logger.info(f"\n{'='*80}")
        logger.info("SEARCH RESULTS")
        logger.info(f"{'='*80}\n")
        
        for i, (doc, metadata, distance) in enumerate(
            zip(results['documents'][0], results['metadatas'][0], results['distances'][0]),
            1
        ):
            logger.info(f"Result {i}:")
            logger.info(f"  Source: {metadata.get('source', 'Unknown')}")
            logger.info(f"  Chunk: {metadata.get('chunk_index', '?')}/{metadata.get('total_chunks', '?')}")
            logger.info(f"  Distance: {distance:.4f}")
            logger.info(f"  Content preview:")
            logger.info(f"  {doc[:300]}...")
            logger.info("")
        
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"Search test failed: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# Validate Installation
# ============================================================================

def validate_installation():
    """Check if all required packages are installed"""
    logger.info(f"\n{'='*80}")
    logger.info("VALIDATING INSTALLATION")
    logger.info(f"{'='*80}\n")
    
    required_packages = [
        "pypdf",
        "python-docx",
        "google-generativeai",
        "chromadb",
        "langchain",
        "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "python-docx":
                import docx
            elif package == "google-generativeai":
                from google import genai
            elif package == "langchain":
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            else:
                __import__(package.replace("-", "_"))
            
            logger.info(f"✓ {package}")
        except ImportError:
            logger.error(f"✗ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    logger.info("")
    
    # Check environment variables
    load_dotenv()
    
    if os.getenv("GOOGLE_API_KEY"):
        logger.info("✓ GOOGLE_API_KEY is set")
    else:
        logger.error("✗ GOOGLE_API_KEY is NOT set")
        missing_packages.append("GOOGLE_API_KEY")
    
    logger.info(f"\n{'='*80}")
    
    if missing_packages:
        logger.error("❌ VALIDATION FAILED")
        logger.error("Missing components:")
        for item in missing_packages:
            logger.error(f"  - {item}")
        logger.error("\nInstall missing packages with:")
        logger.error("  pip install pypdf python-docx google-generativeai chromadb langchain python-dotenv")
        return False
    else:
        logger.info("✅ ALL VALIDATIONS PASSED")
        return True


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Test document ingestion and search"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate installation and dependencies"
    )
    parser.add_argument(
        "--file",
        help="Test ingestion with a single file"
    )
    parser.add_argument(
        "--search",
        help="Test search with a query"
    )
    parser.add_argument(
        "--collection",
        default="support_manuals",
        help="Collection name for search (default: support_manuals)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of search results (default: 3)"
    )
    
    args = parser.parse_args()
    
    # Default: validate
    if not any([args.validate, args.file, args.search]):
        args.validate = True
    
    if args.validate:
        if not validate_installation():
            sys.exit(1)
    
    if args.file:
        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        test_single_file_ingestion(args.file)
    
    if args.search:
        test_search(args.search, args.collection, args.top_k)


if __name__ == "__main__":
    main()
