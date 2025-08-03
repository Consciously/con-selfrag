#!/usr/bin/env python3
"""
Selfrag CLI - Standalone Command Line Interface

A comprehensive CLI for the Selfrag personal knowledge system.
Can be run directly or installed as a package command.

Usage:
    python selfrag_cli.py health
    python selfrag_cli.py ingest document.txt
    python selfrag_cli.py query "machine learning"
"""

import asyncio
import json
import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import httpx

# Default configuration
DEFAULT_API_URL = "http://localhost:8080"
DEFAULT_TIMEOUT = 30.0


class SelfrageAPIClient:
    """HTTP client for interacting with Selfrag API."""
    
    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = await self.client.get(f"{self.base_url}/health/readiness")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest a document file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            payload = {
                "content": content,
                "metadata": metadata or {"source": file_path, "filename": Path(file_path).name}
            }
            
            response = await self.client.post(f"{self.base_url}/ingest/", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def ingest_text(self, content: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest text content directly."""
        try:
            payload = {
                "content": content,
                "metadata": metadata or {"source": "cli-text"}
            }
            
            response = await self.client.post(f"{self.base_url}/ingest/", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def query(self, query_text: str, limit: int = 10) -> Dict[str, Any]:
        """Query the knowledge base."""
        try:
            payload = {
                "query": query_text,
                "limit": limit
            }
            
            response = await self.client.post(f"{self.base_url}/query/", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG pipeline statistics."""
        try:
            response = await self.client.get(f"{self.base_url}/rag/collections/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


def print_success(message: str):
    """Print success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"❌ {message}", file=sys.stderr)


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """Print warning message."""
    print(f"⚠️  {message}")


async def cmd_health(args):
    """Check system health and service status."""
    client = SelfrageAPIClient(args.api_url, args.timeout)
    
    print("🔍 Checking system health...")
    result = await client.health_check()
    await client.close()
    
    if result.get("status") == "ready":
        print_success("System is healthy")
        
        # Display service status
        services = result.get("services", {})
        if services:
            print("\n📊 Service Status:")
            for service_name, service_info in services.items():
                status = service_info.get("status", "unknown")
                response_time = service_info.get("response_time", "N/A")
                
                status_icon = "✅" if status == "healthy" else "❌"
                print(f"  {status_icon} {service_name.title()}: {status} ({response_time})")
    else:
        print_error("System has issues")
        if "error" in result:
            print_error(f"Error: {result['error']}")


async def cmd_ingest(args):
    """Ingest documents into the knowledge base."""
    client = SelfrageAPIClient(args.api_url, args.timeout)
    
    # Prepare metadata
    metadata = {}
    if args.title:
        metadata["title"] = args.title
    if args.tags:
        metadata["tags"] = [tag.strip() for tag in args.tags.split(",")]
    if args.type:
        metadata["type"] = args.type
    if args.source:
        metadata["source"] = args.source
    
    results = []
    
    # Handle text input from stdin
    if args.text or (not args.files and not sys.stdin.isatty()):
        if args.text:
            content = args.text
        else:
            content = sys.stdin.read()
        
        print("📝 Ingesting text content...")
        result = await client.ingest_text(content, metadata)
        results.append(("stdin", result))
    
    # Handle file inputs
    for file_path in args.files:
        if not Path(file_path).exists():
            print_error(f"File not found: {file_path}")
            continue
        
        print(f"📝 Ingesting {file_path}...")
        
        # Add filename to metadata
        file_metadata = metadata.copy()
        file_metadata["filename"] = Path(file_path).name
        if not args.title:
            file_metadata["title"] = Path(file_path).stem
        
        result = await client.ingest_file(file_path, file_metadata)
        results.append((file_path, result))
    
    await client.close()
    
    # Display results
    success_count = 0
    error_count = 0
    
    print("\n📊 Ingestion Results:")
    for source, result in results:
        if result.get("status") == "success":
            success_count += 1
            doc_id = result.get("id", "unknown")
            chunks = result.get("chunks_created", 0)
            print_success(f"{source} → ID: {doc_id} ({chunks} chunks)")
        else:
            error_count += 1
            error_msg = result.get("error", "Unknown error")
            print_error(f"{source} → {error_msg}")
    
    print(f"\n📈 Summary: {success_count} succeeded, {error_count} failed")


async def cmd_query(args):
    """Query the knowledge base using semantic search."""
    client = SelfrageAPIClient(args.api_url, args.timeout)
    
    print(f"🔍 Searching for: {args.query}")
    result = await client.query(args.query, args.limit)
    await client.close()
    
    if result.get("status") == "error":
        print_error(f"Query failed: {result.get('error')}")
        return
    
    results = result.get("results", [])
    if not results:
        print_info("No results found")
        return
    
    # Filter by threshold
    filtered_results = [r for r in results if r.get("score", 0) >= args.threshold]
    
    if not filtered_results:
        print_info(f"No results above similarity threshold {args.threshold}")
        return
    
    if args.format == "json":
        print(json.dumps(filtered_results, indent=2))
    else:
        print(f"\n📊 Found {len(filtered_results)} results:\n")
        
        for i, result_item in enumerate(filtered_results, 1):
            score = result_item.get("score", 0)
            content = result_item.get("content", "")
            metadata = result_item.get("metadata", {})
            source = metadata.get("source", "unknown")
            title = metadata.get("title", "")
            
            print(f"{i}. Score: {score:.3f}")
            if title:
                print(f"   Title: {title}")
            print(f"   Source: {source}")
            
            # Truncate content for display
            if len(content) > 200:
                display_content = content[:200] + "..."
            else:
                display_content = content
            
            print(f"   Content: {display_content}")
            print()


async def cmd_stats(args):
    """Show RAG pipeline statistics."""
    client = SelfrageAPIClient(args.api_url, args.timeout)
    
    print("📊 Fetching RAG statistics...")
    result = await client.get_rag_stats()
    await client.close()
    
    if result.get("status") == "error":
        print_error(f"Failed to get stats: {result.get('error')}")
        return
    
    # The API returns a flat structure with collection stats
    print("\n📈 RAG Pipeline Statistics:")
    print(f"  Documents: {result.get('points_count', 0)}")  # Points represent document chunks
    print(f"  Chunks: {result.get('points_count', 0)}")     # Each point is a chunk
    print(f"  Vectors: {result.get('vectors_count', 0)}")
    print(f"  Collection: {result.get('status', 'unknown')}")
    print(f"  Vector Size: {result.get('vector_size', 0)} dimensions")


async def cmd_chat(args):
    """Interactive chat mode for querying the knowledge base."""
    client = SelfrageAPIClient(args.api_url, args.timeout)
    
    print("💬 Selfrag Interactive Chat")
    print("Ask questions about your knowledge base.")
    print("Type 'quit', 'exit', or press Ctrl+C to leave.\n")
    
    try:
        while True:
            try:
                query_text = input("selfrag> ").strip()
            except EOFError:
                break
            
            if query_text.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query_text:
                continue
            
            print("🔍 Searching...")
            result = await client.query(query_text, limit=3)
            
            if result.get("status") == "error":
                print_error(f"Error: {result.get('error')}")
                continue
            
            results = result.get("results", [])
            if not results:
                print_info("No results found")
                continue
            
            # Display top result
            top_result = results[0]
            score = top_result.get("score", 0)
            content = top_result.get("content", "")
            metadata = top_result.get("metadata", {})
            
            print(f"\n🎯 Best match (score: {score:.3f}):")
            if metadata.get("title"):
                print(f"📄 {metadata['title']}")
            print(f"📝 {content[:300]}{'...' if len(content) > 300 else ''}")
            
            if len(results) > 1:
                print(f"\n📊 Found {len(results)} total results")
            print()
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    await client.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Selfrag CLI - Personal Knowledge System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s health
    %(prog)s ingest document.txt --title "My Document"
    %(prog)s ingest *.md --tags "docs,important"
    %(prog)s query "machine learning algorithms"
    %(prog)s chat
        """
    )
    
    # Global options
    parser.add_argument("--api-url", default=DEFAULT_API_URL, 
                       help=f"API base URL (default: {DEFAULT_API_URL})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                       help=f"Request timeout in seconds (default: {DEFAULT_TIMEOUT})")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Health command
    health_parser = subparsers.add_parser("health", help="Check system health")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument("files", nargs="*", help="Files to ingest")
    ingest_parser.add_argument("--text", help="Text content to ingest directly")
    ingest_parser.add_argument("--title", help="Document title")
    ingest_parser.add_argument("--tags", help="Comma-separated tags")
    ingest_parser.add_argument("--type", help="Document type")
    ingest_parser.add_argument("--source", help="Document source")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge base")
    query_parser.add_argument("query", help="Search query")
    query_parser.add_argument("--limit", "-l", type=int, default=10,
                             help="Maximum number of results (default: 10)")
    query_parser.add_argument("--threshold", type=float, default=0.5,
                             help="Minimum similarity score (default: 0.5)")
    query_parser.add_argument("--format", choices=["table", "json"], default="table",
                             help="Output format (default: table)")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show RAG statistics")
    
    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Interactive chat mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Run the appropriate command
    try:
        if args.command == "health":
            asyncio.run(cmd_health(args))
        elif args.command == "ingest":
            asyncio.run(cmd_ingest(args))
        elif args.command == "query":
            asyncio.run(cmd_query(args))
        elif args.command == "stats":
            asyncio.run(cmd_stats(args))
        elif args.command == "chat":
            asyncio.run(cmd_chat(args))
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
