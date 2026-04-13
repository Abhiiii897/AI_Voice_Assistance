#!/usr/bin/env python3
"""
Document Ingestion Script for the Audio RAG Support Assistant
Handles large PDF/DOCX manuals with proper chunking and Gemini embeddings.

This script:
1. Extracts text from PDF/DOCX files
2. Cleans and normalizes text
3. Chunks documents into embedding-friendly sizes
4. Embeds chunks using Gemini gemini-embedding-001
5. Stores in ChromaDB with metadata

Usage:
    python ingest_docs.py --input data/manuals/ --collection support_manuals
"""

import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import time

# PDF/DOCX extraction
import pypdf
from docx import Document

# Embedding and Vector DB
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Environment variables
from dotenv import load_dotenv

# Text processing
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ============================================================================
# Configuration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Token limits and chunking parameters
MAX_CHUNK_SIZE = 1024  # Max chars for embeddings
TARGET_CHUNK_SIZE = 512  # Target chars per chunk
CHUNK_OVERLAP = 100  # Chars to overlap between chunks
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 outputs 384-dimensional embeddings

# Batch processing
BATCH_SIZE = 32  # Process chunks in batches


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata"""
    text: str
    chunk_index: int
    total_chunks: int
    source_file: str
    file_type: str
    metadata: Dict


# ============================================================================
# Text Extraction
# ============================================================================

def extract_text(file_path: str) -> str:
    """
    Extract text from PDF or DOCX file.
    
    Args:
        file_path: Path to document file
        
    Returns:
        Extracted text
    """
    file_ext = Path(file_path).suffix.lower()
    
    logger.info(f"Extracting text from {file_ext} file...")
    
    try:
        if file_ext == '.pdf':
            return _extract_pdf(file_path)
        elif file_ext == '.docx':
            return _extract_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    except Exception as e:
        logger.error(f"Failed to extract text: {e}")
        raise


def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = []
    
    with open(file_path, 'rb') as f:
        pdf_reader = pypdf.PdfReader(f)
        total_pages = len(pdf_reader.pages)
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
                
                # Progress indicator
                if page_num % max(1, total_pages // 10) == 0:
                    logger.info(f"  Extracted {page_num}/{total_pages} pages...")
                    
            except Exception as e:
                logger.warning(f"Failed to extract page {page_num}: {e}")
                continue
    
    logger.info(f"✓ Extracted {total_pages} pages")
    return "\n".join(text)


def _extract_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    doc = Document(file_path)
    text = []
    
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)
    
    logger.info(f"✓ Extracted {len(text)} paragraphs")
    return "\n".join(text)


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove control characters but keep newlines
    text = ''.join(char for char in text if char.isprintable() or char in '\n\t')
    
    # Remove very short lines that are likely artifacts
    lines = text.split('\n')
    lines = [line.strip() for line in lines if len(line.strip()) > 3]
    text = '\n'.join(lines)
    
    return text.strip()


def chunk_document(
    text: str,
    chunk_size: int = TARGET_CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    Split document into chunks.
    
    Args:
        text: Document text
        chunk_size: Target characters per chunk
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = splitter.split_text(text)
    
    logger.info(f"Created {len(chunks)} chunks")
    logger.info(f"  Min size: {min(len(c) for c in chunks) if chunks else 0} chars")
    logger.info(f"  Max size: {max(len(c) for c in chunks) if chunks else 0} chars")
    logger.info(f"  Avg size: {sum(len(c) for c in chunks) // len(chunks) if chunks else 0} chars")
    
    return chunks


# ============================================================================
# Embedding
# ============================================================================

class EmbeddingClient:
    """Wrapper for SentenceTransformer (all-MiniLM-L6-v2) with batch processing"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding client with local model.
        
        Args:
            model_name: SentenceTransformer model name
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        
        self.request_count = 0
        self.error_count = 0
        
        logger.info(f"✓ Embedding model loaded: {model_name}")
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Embed a single text using local model.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None on failure
        """
        try:
            embedding = self.model.encode([text])[0].tolist()
            self.request_count += 1
            return embedding
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to embed text: {e}")
            return None
    
    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Embed a batch of texts using local model."""
        if not texts:
            return []
        
        try:
            logger.info(f"Embedding batch of {len(texts)} texts...")
            
            embeddings = self.model.encode(texts).tolist()
            self.request_count += len(texts)
            
            logger.info(f"✓ Batch embedding complete")
            return embeddings
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to embed batch: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get embedding statistics"""
        return {
            "total_requests": self.request_count,
            "errors": self.error_count,
            "model": self.model_name,
            "success_rate": 100.0 if self.error_count == 0 else (1 - self.error_count / self.request_count) * 100
        }


# ============================================================================
# Vector Database
# ============================================================================

def init_chromadb(persist_directory: str = "data/vectordb") -> chromadb.Client:
    """
    Initialize ChromaDB client.
    
    Args:
        persist_directory: Directory for persistent storage
        
    Returns:
        ChromaDB client
    """
    logger.info(f"Initializing ChromaDB at {persist_directory}")
    
    # Create directory if it doesn't exist
    Path(persist_directory).mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    return client


def store_chunks_in_chromadb(
    chunks: List[DocumentChunk],
    embeddings: List[List[float]],
    collection_name: str,
    chroma_client: chromadb.Client
) -> int:
    """
    Store document chunks and embeddings in ChromaDB.
    
    Args:
        chunks: List of document chunks
        embeddings: Corresponding embeddings
        collection_name: Name of ChromaDB collection
        chroma_client: ChromaDB client
        
    Returns:
        Number of chunks stored
    """
    logger.info(f"Storing {len(chunks)} chunks in collection '{collection_name}'...")
    
    # Get or create collection
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Technical support manuals"}
    )
    
    # Prepare data for batch insert
    ids = []
    documents = []
    embeddings_list = []
    metadatas = []
    
    for chunk, embedding in zip(chunks, embeddings):
        if embedding is None:
            logger.warning(f"Skipping chunk {chunk.chunk_index} (no embedding)")
            continue
        
        # Create unique ID
        chunk_id = f"{Path(chunk.source_file).stem}_chunk_{chunk.chunk_index}"
        
        ids.append(chunk_id)
        documents.append(chunk.text)
        embeddings_list.append(embedding)
        metadatas.append({
            "source": chunk.source_file,
            "file_type": chunk.file_type,
            "chunk_index": chunk.chunk_index,
            "total_chunks": chunk.total_chunks,
            **chunk.metadata
        })
    
    # Batch insert (ChromaDB handles batching internally)
    try:
        collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings_list,
            metadatas=metadatas
        )
        logger.info(f"✓ Successfully stored {len(ids)} chunks")
        return len(ids)
        
    except Exception as e:
        logger.error(f"Failed to store chunks: {e}")
        raise


# ============================================================================
# Main Ingestion Pipeline
# ============================================================================

def ingest_document(
    file_path: str,
    embedding_client: EmbeddingClient,
    chroma_client: chromadb.Client,
    collection_name: str,
    metadata: Optional[Dict] = None
) -> Tuple[int, int]:
    """
    Complete ingestion pipeline for a single document.
    
    Args:
        file_path: Path to document file
        embedding_client: Embedding client
        chroma_client: ChromaDB client
        collection_name: Target collection name
        metadata: Additional metadata for chunks
        
    Returns:
        Tuple of (chunks_created, chunks_stored)
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {file_path}")
    logger.info(f"{'='*80}")
    
    # Default metadata
    if metadata is None:
        metadata = {}
    
    # Add file info to metadata
    file_type = Path(file_path).suffix.lower().lstrip('.')
    metadata["file_type"] = file_type
    metadata["file_name"] = Path(file_path).name
    
    try:
        # Step 1: Extract text
        text = extract_text(file_path)
        
        if not text.strip():
            logger.warning("No text extracted from document!")
            return 0, 0
        
        # Step 2: Clean text
        cleaned_text = clean_text(text)
        
        # Step 3: Chunk document
        chunks_text = chunk_document(cleaned_text)
        
        # Step 4: Create DocumentChunk objects
        chunks = [
            DocumentChunk(
                text=chunk_text,
                chunk_index=i,
                total_chunks=len(chunks_text),
                source_file=file_path,
                file_type=file_type,
                metadata=metadata.copy()
            )
            for i, chunk_text in enumerate(chunks_text)
        ]
        
        logger.info(f"Created {len(chunks)} chunks")
        
        # Step 5: Embed chunks in batches
        embeddings = []
        valid_chunks = []
        failed_chunks = 0
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_texts = [c.text for c in batch]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
            
            logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} chunks)...")
            
            batch_embeddings = embedding_client.embed_batch(batch_texts)
            
            if batch_embeddings:
                embeddings.extend(batch_embeddings)
                valid_chunks.extend(batch)
            else:
                logger.warning(f"Batch {batch_num} failed, skipping {len(batch)} chunks")
                failed_chunks += len(batch)
        
        if failed_chunks > 0:
            logger.warning(f"Failed to embed {failed_chunks}/{len(chunks)} chunks")
        
        if not valid_chunks:
            logger.error("No chunks were successfully embedded")
            return 0, 0

        # Step 6: Store in ChromaDB
        stored_count = store_chunks_in_chromadb(
            valid_chunks,
            embeddings,
            collection_name,
            chroma_client
        )
        
        logger.info(f"✓ Document processed: {stored_count}/{len(chunks)} chunks stored")
        
        return len(chunks), stored_count
        
    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        raise


def ingest_directory(
    input_dir: str,
    collection_name: str,
    embedding_client: EmbeddingClient,
    chroma_client: chromadb.Client,
    file_pattern: str = "*.pdf"
) -> Dict:
    """
    Ingest all documents from a directory.
    
    Args:
        input_dir: Directory containing documents
        collection_name: ChromaDB collection name
        embedding_client: Embedding client
        chroma_client: ChromaDB client
        file_pattern: File glob pattern (e.g., "*.pdf", "*.docx")
        
    Returns:
        Statistics dictionary
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    
    # Find all matching files
    files = list(input_path.glob(file_pattern))
    
    if not files:
        logger.warning(f"No files matching '{file_pattern}' found in {input_dir}")
        return {}
    
    logger.info(f"Found {len(files)} files to process")
    
    # Process each file
    stats = {
        "total_files": len(files),
        "successful_files": 0,
        "failed_files": 0,
        "total_chunks_created": 0,
        "total_chunks_stored": 0,
        "files_processed": []
    }
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"\nProcessing file {i}/{len(files)}: {file_path.name}")
        
        try:
            chunks_created, chunks_stored = ingest_document(
                str(file_path),
                embedding_client,
                chroma_client,
                collection_name
            )
            
            stats["successful_files"] += 1
            stats["total_chunks_created"] += chunks_created
            stats["total_chunks_stored"] += chunks_stored
            stats["files_processed"].append({
                "file": file_path.name,
                "status": "success",
                "chunks_created": chunks_created,
                "chunks_stored": chunks_stored
            })
            
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            stats["failed_files"] += 1
            stats["files_processed"].append({
                "file": file_path.name,
                "status": "failed",
                "error": str(e)
            })
    
    return stats


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Ingest PDF/DOCX documents into ChromaDB for RAG"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory containing manuals"
    )
    parser.add_argument(
        "--collection",
        default="support_manuals_minilm",
        help="ChromaDB collection name (default: support_manuals_minilm)"
    )
    parser.add_argument(
        "--vectordb-path",
        default="data/vectordb",
        help="ChromaDB storage path (default: data/vectordb)"
    )
    parser.add_argument(
        "--pattern",
        default="*.pdf",
        help="File pattern to match (default: *.pdf)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=TARGET_CHUNK_SIZE,
        help=f"Target characters per chunk (default: {TARGET_CHUNK_SIZE})"
    )
    
    args = parser.parse_args()
    
    # Initialize embedding client (requires GOOGLE_API_KEY)
    logger.info("Initializing embedding client...")
    embedding_client = EmbeddingClient()
    
    logger.info("Initializing ChromaDB...")
    chroma_client = init_chromadb(args.vectordb_path)
    
    # Run ingestion
    logger.info(f"\nStarting document ingestion...")
    logger.info(f"  Input: {args.input}")
    logger.info(f"  Collection: {args.collection}")
    logger.info(f"  Pattern: {args.pattern}")
    logger.info(f"  Chunk size: {args.chunk_size} characters")
    
    start_time = time.time()
    
    try:
        stats = ingest_directory(
            input_dir=args.input,
            collection_name=args.collection,
            embedding_client=embedding_client,
            chroma_client=chroma_client,
            file_pattern=args.pattern
        )
        
        # Print summary
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("INGESTION SUMMARY")
        print("="*80)
        print(f"Total files: {stats['total_files']}")
        print(f"Successful: {stats['successful_files']}")
        print(f"Failed: {stats['failed_files']}")
        print(f"Total chunks created: {stats['total_chunks_created']}")
        print(f"Total chunks stored: {stats['total_chunks_stored']}")
        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        
        # Embedding stats
        embed_stats = embedding_client.get_stats()
        print(f"\nEmbedding API calls: {embed_stats['total_requests']}")
        print(f"Embedding errors: {embed_stats['errors']}")
        print(f"Success rate: {embed_stats['success_rate']:.1f}%")
        
        print("\nFiles processed:")
        for file_info in stats['files_processed']:
            status_icon = "✓" if file_info['status'] == 'success' else "✗"
            print(f"  {status_icon} {file_info['file']}")
            if file_info['status'] == 'success':
                print(f"      Chunks: {file_info['chunks_stored']}/{file_info['chunks_created']}")
            else:
                print(f"      Error: {file_info.get('error', 'Unknown')}")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
