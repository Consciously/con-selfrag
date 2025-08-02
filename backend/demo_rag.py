#!/usr/bin/env python3
"""
Quick demo script to showcase the RAG pipeline capabilities.
This script demonstrates the complete flow from ingestion to search.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the app directory to Python path  
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def demo():
    """Run a quick RAG pipeline demonstration."""
    print("🚀 Selfrag RAG Pipeline Demo")
    print("=" * 40)
    
    try:
        from app.services.ingest_service import IngestService
        from app.services.query_service import QueryService
        
        # Initialize services
        ingest_service = IngestService()
        query_service = QueryService()
        
        # Sample document about Selfrag itself
        selfrag_doc = """
        Selfrag is a personal knowledge system for tech-savvy solo users. It follows a 
        modular, service-oriented approach where specialized modules interact with each other. 
        Selfrag starts as a lightweight RAG system and grows alongside the user's needs.
        
        The system aims to return control over knowledge to the user - local, explainable, 
        and customizable. Instead of isolated tools, it creates a connected, modular system 
        that not only searches documents but also interprets, links, and reflects on them over time.
        
        Selfrag uses FastAPI for the backend, Qdrant for vector storage, and LocalAI for 
        language model capabilities. The architecture includes modules for coordination, 
        RAG processing, memory management, and agent functionality.
        """
        
        print("\n📝 Ingesting sample document...")
        result = await ingest_service.ingest_content(
            content=selfrag_doc,
            metadata={
                "title": "Selfrag Overview",
                "type": "documentation", 
                "tags": ["selfrag", "rag", "knowledge", "system"],
                "source": "demo"
            }
        )
        print(f"✅ Document ingested: {result.id}")
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Test queries
        queries = [
            "What is Selfrag?",
            "How does Selfrag work?", 
            "What technologies does Selfrag use?",
            "modular system architecture"
        ]
        
        print("\n🔍 Testing search queries...")
        for query in queries:
            print(f"\n🔎 Query: '{query}'")
            
            result = await query_service.query_content(query, limit=2)
            
            if result.results:
                for i, res in enumerate(result.results):
                    print(f"  📄 Result {i+1} (score: {res.relevance_score:.3f})")
                    print(f"     {res.content[:120]}...")
            else:
                print("  ❌ No results found")
        
        print("\n🎉 Demo completed successfully!")
        print("\n💡 Try these commands:")
        print("   python test_rag_pipeline.py  # Full test suite")
        print("   uvicorn app.main:app --reload # Start API server")
        print("   curl http://localhost:8000/docs # View API docs")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure to install dependencies: ./setup_rag.sh")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")

if __name__ == "__main__":
    asyncio.run(demo())
