#!/usr/bin/env python3
"""
Complete RAG Pipeline Test
Tests the entire document ingestion and query pipeline
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

async def test_complete_rag():
    """Test the complete RAG pipeline"""
    print("🚀 Starting Complete RAG Pipeline Test\n")
    
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
    Artificial Intelligence (AI) has revolutionized many industries and continues to evolve rapidly.
    
    Machine learning is a subset of AI that enables computers to learn from data without being explicitly programmed.
    Deep learning, a subset of machine learning, uses neural networks with multiple layers to model complex patterns.
    
    Natural Language Processing (NLP) is a branch of AI that helps computers understand and generate human language.
    Large Language Models (LLMs) like GPT have shown remarkable capabilities in text generation and comprehension.
    
    Computer vision allows machines to interpret visual information from the world around them.
    Applications include autonomous vehicles, medical imaging, and facial recognition systems.
    """
    
    chunks = await doc_processor.process_document(test_document)
    print(f"✅ Document processed into {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
        print(f"   Chunk {i+1}: {chunk.content[:100]}...")
    print()
    
    # Test embedding generation
    print("🧠 Testing embedding generation...")
    texts = [chunk.content for chunk in chunks]
    embeddings = await embedding_service.generate_embeddings_batch(texts)
    print(f"✅ Generated {len(embeddings)} embeddings, dimension: {len(embeddings[0])}\n")
    
    # Test vector storage
    print("💾 Testing vector storage...")
    collection_name = "test_rag_collection"
    
    # Clean up any existing collection
    await vector_service.delete_collection(collection_name)
    
    # Create collection and store vectors
    await vector_service.create_collection(collection_name, len(embeddings[0]))
    
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append({
            'id': i,
            'vector': embedding,
            'payload': {
                'content': chunk.content,
                'chunk_id': chunk.chunk_id,
                'document_id': 'test_doc_1'
            }
        })
    
    await vector_service.store_vectors(collection_name, points)
    print(f"✅ Stored {len(points)} vectors in collection '{collection_name}'\n")
    
    # Test complete ingestion service
    print("📤 Testing complete ingestion pipeline...")
    test_doc_2 = """
    Python is a high-level programming language known for its simplicity and readability.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    
    FastAPI is a modern web framework for building APIs with Python.
    It provides automatic API documentation and high performance through async/await support.
    
    Docker containers provide a lightweight way to package applications and their dependencies.
    Container orchestration platforms like Kubernetes help manage containerized applications at scale.
    """
    
    await ingest_service.ingest_document("test_doc_2", test_doc_2, {"source": "test"})
    print("✅ Document ingested through complete pipeline\n")
    
    # Test semantic search
    print("🔍 Testing semantic search...")
    search_queries = [
        "What is machine learning?",
        "How does FastAPI work?",
        "Tell me about Docker containers"
    ]
    
    for query in search_queries:
        print(f"Query: '{query}'")
        results = await query_service.search(query, collection_name="documents", limit=2)
        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            print(f"   {i+1}. (Score: {result.score:.4f}) {result.content[:100]}...")
        print()
    
    # Test end-to-end RAG query
    print("🎯 Testing end-to-end RAG query...")
    rag_query = "Explain the relationship between AI, machine learning, and deep learning"
    search_results = await query_service.search(rag_query, collection_name="documents", limit=3)
    
    print(f"RAG Query: '{rag_query}'")
    print(f"Retrieved {len(search_results)} relevant chunks:")
    
    context_chunks = []
    for i, result in enumerate(search_results):
        print(f"   {i+1}. (Score: {result.score:.4f}) {result.content[:150]}...")
        context_chunks.append(result.content)
    
    # Prepare context for LLM (would be sent to LocalAI in real usage)
    context = "\n\n".join(context_chunks)
    prompt = f"""
    Based on the following context, answer the question: {rag_query}
    
    Context:
    {context}
    
    Answer:
    """
    
    print(f"\n📝 RAG prompt prepared (length: {len(prompt)} chars)")
    print("✅ RAG pipeline test completed successfully!")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    await vector_service.delete_collection(collection_name)
    await vector_service.delete_collection("documents")
    print("✅ Cleanup completed")

if __name__ == "__main__":
    asyncio.run(test_complete_rag())
