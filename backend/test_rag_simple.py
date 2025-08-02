#!/usr/bin/env python3
"""
Simple RAG Pipeline Test
Tests the RAG services with their actual API methods
"""

import asyncio
import os
import sys
sys.path.append('/mnt/workspace/projects/con-selfrag/backend')

# Force CPU usage to avoid CUDA issues
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService  
from app.services.vector_service import VectorService
from app.services.ingest_service import IngestService
from app.services.query_service import QueryService

async def test_simple_rag():
    """Test the RAG pipeline with actual service APIs"""
    print("🚀 Starting Simple RAG Pipeline Test\n")
    
    # Initialize services
    print("📋 Initializing services...")
    doc_processor = DocumentProcessor()
    embedding_service = EmbeddingService()
    vector_service = VectorService()
    ingest_service = IngestService()
    query_service = QueryService()
    
    print("✅ Services initialized\n")
    
    # Test document processing
    print("📄 Testing document processing...")
    test_document = """
    Machine learning is a method of data analysis that automates analytical model building.
    
    It is a branch of artificial intelligence based on the idea that systems can learn from data,
    identify patterns and make decisions with minimal human intervention.
    
    Deep learning is a subset of machine learning that uses neural networks with three or more layers.
    These neural networks attempt to simulate the behavior of the human brain.
    """
    
    chunks = await doc_processor.process_document(test_document)
    print(f"✅ Document processed into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"   Chunk {i+1}: {chunk.content[:80]}...")
    print()
    
    # Test embedding generation
    print("🧠 Testing embedding generation...")
    texts = [chunk.content for chunk in chunks]
    embeddings = await embedding_service.generate_embeddings_batch(texts)
    print(f"✅ Generated {len(embeddings)} embeddings, dimension: {len(embeddings[0])}\n")
    
    # Test vector storage (using the actual API)
    print("💾 Testing vector storage...")
    
    # Ensure collection exists
    collection_exists = await vector_service.ensure_collection_exists()
    print(f"✅ Collection exists: {collection_exists}")
    
    # Store chunks using the actual API
    await vector_service.store_chunks(chunks, embeddings)
    print(f"✅ Stored {len(chunks)} chunks with embeddings\n")
    
    # Test similarity search
    print("🔍 Testing similarity search...")
    query_text = "What is deep learning?"
    query_embedding = await embedding_service.generate_embedding(query_text)
    
    search_results = await vector_service.search_similar(
        query_embedding=query_embedding,
        limit=3,
        score_threshold=0.0
    )
    
    print(f"Query: '{query_text}'")
    print(f"Found {len(search_results)} results:")
    for i, result in enumerate(search_results):
        print(f"   {i+1}. (Score: {result.score:.4f}) {result.content[:100]}...")
    print()
    
    # Test complete ingestion pipeline
    print("📤 Testing complete ingestion...")
    test_doc_2 = """
    Natural Language Processing (NLP) is a field of artificial intelligence that gives machines 
    the ability to read, understand and derive meaning from human languages.
    
    NLP combines computational linguistics with statistical, machine learning, and deep learning models.
    """
    
    await ingest_service.ingest_content(test_doc_2, {"source": "test", "document_id": "test_doc_2"})
    print("✅ Document ingested through complete pipeline\n")
    
    # Test query service
    print("🎯 Testing query service...")
    query_text = "Explain NLP and its relationship to AI"
    query_response = await query_service.query_content(query_text, limit=2)
    
    print(f"Query: '{query_text}'")
    print(f"Found {len(query_response.results)} results:")
    for i, result in enumerate(query_response.results):
        print(f"   {i+1}. (Score: {result.relevance_score:.4f}) {result.content[:100]}...")
    
    print(f"\n✅ RAG pipeline test completed successfully!")
    
    # Show collection stats
    print("\n📊 Collection statistics:")
    stats = await vector_service.get_collection_stats()
    print(f"   - Points count: {stats.get('points_count', 'N/A')}")
    print(f"   - Vectors count: {stats.get('vectors_count', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_simple_rag())
