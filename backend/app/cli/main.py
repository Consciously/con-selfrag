"""
Main CLI application entry point for Selfrag.

Provides comprehensive command-line interface for:
- Document ingestion and management
- Knowledge base querying
- System health monitoring
- Configuration management
- Development utilities
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.live import Live
from rich.progress import Progress, TaskID
import httpx

from ..config import config
from ..services.ingest_service import IngestService
from ..services.query_service import QueryService
from ..logging_utils import get_logger

# Initialize console and logger
console = Console()
logger = get_logger(__name__)

# API client for CLI operations
class SelfrageAPIClient:
    """HTTP client for interacting with Selfrag API."""
    
    def __init__(self, base_url: str = None, timeout: float = 30.0):
        self.base_url = base_url or f"http://{config.host}:{config.port}"
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
                "metadata": metadata or {"source": file_path}
            }
            
            response = await self.client.post(f"{self.base_url}/ingest", json=payload)
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
            
            response = await self.client.post(f"{self.base_url}/query", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Main CLI group
@click.group(name="selfrag")
@click.option("--api-url", default=None, help="API base URL")
@click.option("--timeout", default=30.0, help="Request timeout in seconds")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, api_url: str, timeout: float, verbose: bool):
    """
    Selfrag CLI - Personal Knowledge System
    
    A command-line interface for managing your local knowledge system.
    Supports document ingestion, semantic search, and system monitoring.
    """
    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['api_url'] = api_url
    ctx.obj['timeout'] = timeout
    ctx.obj['verbose'] = verbose
    
    if verbose:
        console.print("[dim]Selfrag CLI initialized[/dim]")


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health and service status."""
    
    async def check_health():
        client = SelfrageAPIClient(ctx.obj['api_url'], ctx.obj['timeout'])
        
        with console.status("[bold blue]Checking system health..."):
            result = await client.health_check()
        
        await client.close()
        
        if result.get("status") == "ready":
            console.print("✅ [bold green]System is healthy[/bold green]")
            
            # Display service status
            services = result.get("services", {})
            table = Table(title="Service Status")
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Response Time", style="yellow")
            
            for service_name, service_info in services.items():
                status = service_info.get("status", "unknown")
                response_time = service_info.get("response_time", "N/A")
                
                status_style = "green" if status == "healthy" else "red"
                table.add_row(
                    service_name.title(),
                    f"[{status_style}]{status}[/{status_style}]",
                    f"{response_time}"
                )
            
            console.print(table)
        else:
            console.print("❌ [bold red]System has issues[/bold red]")
            if "error" in result:
                console.print(f"Error: {result['error']}")
    
    asyncio.run(check_health())


@cli.command()
@click.argument("file_paths", nargs=-1, required=True)
@click.option("--title", help="Document title")
@click.option("--tags", help="Comma-separated tags")
@click.option("--type", "doc_type", help="Document type")
@click.option("--source", help="Document source")
@click.option("--batch", is_flag=True, help="Process files in batch mode")
@click.pass_context
def ingest(ctx, file_paths: tuple, title: str, tags: str, doc_type: str, source: str, batch: bool):
    """
    Ingest documents into the knowledge base.
    
    Supports text files, markdown, and other readable formats.
    Automatically chunks documents and generates embeddings.
    
    Examples:
        selfrag ingest document.txt --title "My Document" --tags "important,work"
        selfrag ingest *.md --batch --type "documentation"
    """
    
    async def ingest_files():
        client = SelfrageAPIClient(ctx.obj['api_url'], ctx.obj['timeout'])
        
        # Prepare metadata
        metadata = {}
        if title:
            metadata["title"] = title
        if tags:
            metadata["tags"] = [t.strip() for t in tags.split(",")]
        if doc_type:
            metadata["type"] = doc_type
        if source:
            metadata["source"] = source
        
        results = []
        
        if batch:
            with Progress() as progress:
                task = progress.add_task("[cyan]Ingesting files...", total=len(file_paths))
                
                for file_path in file_paths:
                    if not Path(file_path).exists():
                        console.print(f"❌ File not found: {file_path}")
                        continue
                    
                    # Add filename to metadata for batch processing
                    file_metadata = metadata.copy()
                    file_metadata["filename"] = Path(file_path).name
                    if not title:
                        file_metadata["title"] = Path(file_path).stem
                    
                    result = await client.ingest_file(file_path, file_metadata)
                    results.append((file_path, result))
                    
                    progress.update(task, advance=1)
        else:
            for file_path in file_paths:
                if not Path(file_path).exists():
                    console.print(f"❌ File not found: {file_path}")
                    continue
                
                with console.status(f"[bold blue]Ingesting {file_path}..."):
                    result = await client.ingest_file(file_path, metadata)
                    results.append((file_path, result))
        
        await client.close()
        
        # Display results
        success_count = 0
        error_count = 0
        
        for file_path, result in results:
            if result.get("status") == "success":
                success_count += 1
                doc_id = result.get("id", "unknown")
                chunks = result.get("chunks_created", 0)
                console.print(f"✅ [green]{file_path}[/green] → ID: {doc_id} ({chunks} chunks)")
            else:
                error_count += 1
                error_msg = result.get("error", "Unknown error")
                console.print(f"❌ [red]{file_path}[/red] → Error: {error_msg}")
        
        # Summary
        console.print(f"\n📊 Summary: {success_count} succeeded, {error_count} failed")
    
    asyncio.run(ingest_files())


@cli.command()
@click.argument("query_text")
@click.option("--limit", "-l", default=10, help="Maximum number of results")
@click.option("--format", "output_format", default="table", 
              type=click.Choice(["table", "json", "simple"]), help="Output format")
@click.option("--threshold", default=0.5, help="Minimum similarity score")
@click.pass_context
def query(ctx, query_text: str, limit: int, output_format: str, threshold: float):
    """
    Query the knowledge base using semantic search.
    
    Searches through ingested documents using vector similarity.
    Returns relevant chunks with similarity scores and metadata.
    
    Examples:
        selfrag query "machine learning algorithms"
        selfrag query "API documentation" --limit 5 --format json
    """
    
    async def search_knowledge():
        client = SelfrageAPIClient(ctx.obj['api_url'], ctx.obj['timeout'])
        
        with console.status(f"[bold blue]Searching for: {query_text}..."):
            result = await client.query(query_text, limit)
        
        await client.close()
        
        if result.get("status") == "error":
            console.print(f"❌ Query failed: {result.get('error')}")
            return
        
        results = result.get("results", [])
        if not results:
            console.print("🔍 No results found")
            return
        
        # Filter by threshold
        filtered_results = [r for r in results if r.get("score", 0) >= threshold]
        
        if not filtered_results:
            console.print(f"🔍 No results above similarity threshold {threshold}")
            return
        
        if output_format == "json":
            console.print(json.dumps(filtered_results, indent=2))
        elif output_format == "simple":
            for i, result in enumerate(filtered_results, 1):
                score = result.get("score", 0)
                content = result.get("content", "")[:200] + "..."
                console.print(f"{i}. [yellow]Score: {score:.3f}[/yellow]")
                console.print(f"   {content}\n")
        else:  # table format
            table = Table(title=f"Search Results for: {query_text}")
            table.add_column("Rank", width=4)
            table.add_column("Score", width=8)
            table.add_column("Content", min_width=40)
            table.add_column("Source", width=20)
            
            for i, result in enumerate(filtered_results, 1):
                score = result.get("score", 0)
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                source = metadata.get("source", "unknown")
                
                # Truncate content for table display
                display_content = content[:100] + "..." if len(content) > 100 else content
                
                table.add_row(
                    str(i),
                    f"{score:.3f}",
                    display_content,
                    source
                )
            
            console.print(table)
            console.print(f"\n📊 Found {len(filtered_results)} results (threshold: {threshold})")
    
    asyncio.run(search_knowledge())


@cli.command()
@click.option("--format", "output_format", default="table", 
              type=click.Choice(["table", "json"]), help="Output format")
@click.pass_context
def config_show(ctx, output_format: str):
    """Show current configuration settings."""
    
    config_dict = {
        "server": {
            "host": config.host,
            "port": config.port,
        },
        "localai": {
            "host": config.localai_host,
            "port": config.localai_port,
            "base_url": config.localai_base_url,
            "default_model": config.default_model,
            "timeout": config.localai_timeout,
        },
        "databases": {
            "postgres_url": config.postgres_url or "Not configured",
            "qdrant_host": config.qdrant_host,
            "qdrant_port": config.qdrant_port,
            "redis_host": config.redis_host,
            "redis_port": config.redis_port,
        },
        "rag": {
            "embedding_model": config.embedding_model,
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "search_limit": config.search_limit,
            "search_threshold": config.search_threshold,
        },
        "logging": {
            "log_level": config.log_level,
        }
    }
    
    if output_format == "json":
        console.print(json.dumps(config_dict, indent=2))
    else:
        for section, settings in config_dict.items():
            table = Table(title=f"{section.title()} Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in settings.items():
                table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)
            console.print()


@cli.command()
@click.option("--interactive", "-i", is_flag=True, help="Start interactive query mode")
@click.pass_context
def chat(ctx, interactive: bool):
    """
    Interactive chat mode for querying the knowledge base.
    
    Provides a conversational interface for exploring your knowledge system.
    """
    
    if not interactive:
        console.print("Use --interactive flag to start chat mode")
        return
    
    async def chat_session():
        client = SelfrageAPIClient(ctx.obj['api_url'], ctx.obj['timeout'])
        
        console.print(Panel.fit(
            "[bold cyan]Selfrag Interactive Chat[/bold cyan]\n"
            "Ask questions about your knowledge base.\n"
            "Type 'quit', 'exit', or press Ctrl+C to leave.",
            title="Welcome",
            border_style="blue"
        ))
        
        try:
            while True:
                query_text = console.input("\n[bold blue]selfrag>[/bold blue] ")
                
                if query_text.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query_text.strip():
                    continue
                
                with console.status("[bold blue]Searching..."):
                    result = await client.query(query_text, limit=5)
                
                if result.get("status") == "error":
                    console.print(f"❌ Error: {result.get('error')}")
                    continue
                
                results = result.get("results", [])
                if not results:
                    console.print("🔍 No results found")
                    continue
                
                # Display top result with context
                top_result = results[0]
                score = top_result.get("score", 0)
                content = top_result.get("content", "")
                metadata = top_result.get("metadata", {})
                
                console.print(f"\n[yellow]Best match (score: {score:.3f}):[/yellow]")
                console.print(Panel(content, title=metadata.get("title", "Result")))
                
                if len(results) > 1:
                    console.print(f"\n[dim]Found {len(results)} total results[/dim]")
        
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!")
        
        await client.close()
    
    asyncio.run(chat_session())


@cli.command()
@click.option("--output", "-o", help="Output file path")
@click.pass_context
def export_config(ctx, output: str):
    """Export current configuration to a file."""
    
    config_dict = {
        "server": {
            "host": config.host,
            "port": config.port,
        },
        "localai": {
            "host": config.localai_host,
            "port": config.localai_port,
            "default_model": config.default_model,
            "timeout": config.localai_timeout,
        },
        "databases": {
            "qdrant_host": config.qdrant_host,
            "qdrant_port": config.qdrant_port,
            "redis_host": config.redis_host,
            "redis_port": config.redis_port,
        },
        "rag": {
            "embedding_model": config.embedding_model,
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "search_limit": config.search_limit,
            "search_threshold": config.search_threshold,
        },
        "logging": {
            "log_level": config.log_level,
        }
    }
    
    output_path = output or "selfrag-config.json"
    
    try:
        with open(output_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        console.print(f"✅ Configuration exported to {output_path}")
    except Exception as e:
        console.print(f"❌ Failed to export configuration: {e}")


if __name__ == "__main__":
    cli()
