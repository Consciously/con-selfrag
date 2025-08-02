#!/usr/bin/env python3
"""
Test script for the RAG pipeline implementation.
Tests document ingestion, embedding generation, and semantic search.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.ingest_service import IngestService
from app.services.query_service import QueryService
from app.config import load_config

# Load configuration
config = load_config()

# Test data
test_documents = [
    {
        "content": """
        FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ 
        based on standard Python type hints. The key features are: Fast, Fast to code, Fewer bugs, 
        Intuitive, Easy, Short, Robust, Standards-based. FastAPI is based on Pydantic and uses 
        Python type hints to provide automatic data validation, serialization, and documentation.
        """,
        "metadata": {
            "title": "FastAPI Introduction",
            "type": "documentation",
            "tags": ["api", "python", "web", "framework"],
            "source": "test"
        }
    },
    {
        "content": """
        Retrieval-Augmented Generation (RAG) is a framework that combines the power of pre-trained 
        language models with external knowledge retrieval. RAG works by first retrieving relevant 
        documents or passages from a knowledge base using semantic search, then using these 
        retrieved contexts to generate more accurate and informative responses. This approach 
        helps reduce hallucinations and provides more factual, up-to-date information.
        """,
        "metadata": {
            "title": "RAG Explained",
            "type": "concept",
            "tags": ["rag", "ai", "retrieval", "generation"],
            "source": "test"
        }
    },
    {
        "content": """
        Vector databases are specialized databases designed to store, index, and search 
        high-dimensional vectors efficiently. They use approximate nearest neighbor (ANN) 
        algorithms to quickly find similar vectors. Popular vector databases include Qdrant, 
        Pinecone, Weaviate, and Chroma. These databases are essential for semantic search, 
        recommendation systems, and retrieval-augmented generation (RAG) applications.
        """,
        "metadata": {
            "title": "Vector Databases",
            "type": "technology",
            "tags": ["vector", "database", "search", "embeddings"],
            "source": "test"
        }
    }
]

test_queries = [
    "What is FastAPI?",
    "How does RAG work?",
    "What are vector databases used for?",
    "Python web frameworks",
    "semantic search technologies"
]


async def test_rag_pipeline():
    """Test the complete RAG pipeline."""
    print("🧪 Testing RAG Pipeline")
    print("=" * 50)
    
    # Initialize services
    ingest_service = IngestService()
    query_service = QueryService()
    
    try:
        # Test 1: Document Ingestion
        print("\n📥 Testing Document Ingestion...")
        for i, doc in enumerate(test_documents):
            try:
                result = await ingest_service.ingest_content(
                    content=doc["content"],
                    metadata=doc["metadata"]
                )
                print(f"✅ Document {i+1} ingested: {result.id} ({result.content_length} chars)")
            except Exception as e:
                print(f"❌ Document {i+1} ingestion failed: {e}")
        
        # Wait a moment for indexing
        print("\n⏳ Waiting for indexing...")
        await asyncio.sleep(2)
        
        # Test 2: Semantic Search
        print("\n🔍 Testing Semantic Search...")
        for i, query in enumerate(test_queries):
            try:
                result = await query_service.query_content(
                    query=query,
                    limit=3
                )
                print(f"\n🔎 Query {i+1}: '{query}'")
                print(f"📊 Found {result.total_results} results in {result.query_time_ms}ms")
                
                for j, res in enumerate(result.results):
                    print(f"  {j+1}. Score: {res.relevance_score:.3f}")
                    print(f"     Content: {res.content[:100]}...")
                    print(f"     Metadata: {res.metadata}")
                    
            except Exception as e:
                print(f"❌ Query {i+1} failed: {e}")
        
        # Test 3: Health Check
        print("\n🏥 Testing RAG Health...")
        try:
            # We'll simulate what the health check would do
            from app.services.embedding_service import EmbeddingService
            from app.services.vector_service import VectorService
            
            embedding_service = EmbeddingService()
            vector_service = VectorService()
            
            # Test embedding
            test_embedding = await embedding_service.generate_embedding("test")
            print(f"✅ Embedding service: {len(test_embedding)} dimensions")
            
            # Test vector service
            stats = await vector_service.get_collection_stats()
            print(f"✅ Vector service: {stats}")
            
            # Cache stats
            cache_stats = embedding_service.get_cache_stats()
            print(f"✅ Embedding cache: {cache_stats}")
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
        
        print("\n🎉 RAG Pipeline Test Completed!")
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()


def print_config_info():
    """Print current configuration."""
    print("⚙️  Configuration:")
    print(f"   Embedding Model: {config.embedding_model}")
    print(f"   Chunk Size: {config.chunk_size}")
    print(f"   Chunk Overlap: {config.chunk_overlap}")
    print(f"   Qdrant Host: {config.qdrant_host}:{config.qdrant_port}")
    print(f"   Search Limit: {config.search_limit}")
    print(f"   Search Threshold: {config.search_threshold}")


if __name__ == "__main__":
    print("🚀 Selfrag RAG Pipeline Test")
    print_config_info()
    
    try:
        asyncio.run(test_rag_pipeline())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        sys.exit(1)
