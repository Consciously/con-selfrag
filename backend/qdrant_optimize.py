#!/usr/bin/env python3
"""
Qdrant Collection Optimization Script

This script adds payload indexing on custom metadata fields to improve
retrieval speed on tag-filtered searches.

Usage:
    python qdrant_optimize.py
"""

import requests
import json
from typing import Dict, Any, List

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "documents"

def create_payload_index(field_name: str, field_type: str = "keyword") -> bool:
    """
    Create a payload index for the specified field.
    
    Args:
        field_name: Name of the field to index (e.g., 'document_type', 'tags', 'source')
        field_type: Type of index ('keyword', 'integer', 'float', 'bool', 'geo', 'text')
    
    Returns:
        True if successful, False otherwise
    """
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}/index"
    
    payload = {
        "field_name": field_name,
        "field_schema": field_type
    }
    
    try:
        response = requests.put(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Created index for field '{field_name}' (type: {field_type})")
            return True
        else:
            print(f"❌ Failed to create index for field '{field_name}': {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating index for field '{field_name}': {e}")
        return False

def check_collection_info() -> Dict[str, Any]:
    """Check current collection configuration."""
    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get collection info: {response.text}")
            return {}
    except Exception as e:
        print(f"❌ Error getting collection info: {e}")
        return {}

def optimize_qdrant_collection():
    """
    Optimize Qdrant collection by adding payload indexes for common metadata fields.
    
    This improves search performance for filtered queries on:
    - document_type: Type of document (e.g., 'documentation', 'code', 'article')
    - tags: Array of tags for categorization
    - source: Source of the document (e.g., 'user_input', 'file_upload', 'api')
    - chunk_index: Index of the chunk within the document
    - document_id: ID of the parent document
    """
    print("🔧 Optimizing Qdrant Collection for Performance")
    print("=" * 50)
    
    # Check current collection status
    print("📊 Current Collection Info:")
    info = check_collection_info()
    if info:
        result = info.get('result', {})
        config = result.get('config', {})
        payload_schema = result.get('payload_schema', {})
        
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Points Count: {result.get('points_count', 0)}")
        print(f"   Vector Size: {config.get('params', {}).get('vectors', {}).get('size', 'unknown')}")
        print(f"   Current Payload Schema: {json.dumps(payload_schema, indent=2) if payload_schema else 'None'}")
    print()
    
    # Define indexes to create for optimal performance
    indexes_to_create = [
        # Metadata field indexes for filtering
        ("document_type", "keyword"),  # For filtering by document type
        ("tags", "keyword"),           # For filtering by tags (array support)
        ("source", "keyword"),         # For filtering by source
        
        # Document structure indexes
        ("document_id", "keyword"),    # For filtering by parent document
        ("chunk_index", "integer"),    # For ordering chunks within documents
        
        # Performance indexes
        ("token_count", "integer"),    # For filtering by content size
        ("chunk_id", "keyword"),       # For exact chunk lookups
    ]
    
    print("🚀 Creating Payload Indexes:")
    success_count = 0
    
    for field_name, field_type in indexes_to_create:
        if create_payload_index(field_name, field_type):
            success_count += 1
    
    print()
    print("📈 Optimization Results:")
    print(f"   ✅ Successfully created {success_count}/{len(indexes_to_create)} indexes")
    
    if success_count == len(indexes_to_create):
        print("   🎉 Collection optimization completed successfully!")
        print()
        print("💡 Performance Benefits:")
        print("   • Faster tag-filtered searches")
        print("   • Improved document_type filtering")
        print("   • Enhanced source-based queries")
        print("   • Optimized chunk retrieval within documents")
        print("   • Better support for metadata-based filtering")
    else:
        print("   ⚠️  Some indexes may have failed to create")
        print("   💡 Check Qdrant logs for detailed error information")
    
    print()
    print("🔍 Usage Examples:")
    print("   # Filter by document type")
    print("   POST /query with filters: {'document_type': 'documentation'}")
    print()
    print("   # Filter by multiple tags")
    print("   POST /query with filters: {'tags': ['python', 'api']}")
    print()
    print("   # Filter by source")
    print("   POST /query with filters: {'source': 'file_upload'}")
    print()
    print("   # Combined filtering")
    print("   POST /query with filters: {'document_type': 'code', 'tags': ['fastapi']}")

if __name__ == "__main__":
    optimize_qdrant_collection()
