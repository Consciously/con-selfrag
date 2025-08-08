# SelfRAG CLI User Guide

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Basic Commands](#basic-commands)
3. [Document Management](#document-management)
4. [Search & Query](#search--query)
5. [Interactive Mode](#interactive-mode)
6. [Configuration](#configuration)
7. [Examples & Workflows](#examples--workflows)
8. [Troubleshooting](#troubleshooting)

## Installation & Setup

### Prerequisites

- Docker Compose (for backend services)
- Python 3.8+ (for CLI)
- curl (for health checks)

### Quick Setup

```bash
# 1. Start the backend services
docker-compose up -d

# 2. Wait for services to be ready
./scripts/health-check.sh

# 3. Navigate to backend directory
cd backend

# 4. Test the CLI
python selfrag_cli.py health
```

### CLI Installation (Optional)

For system-wide access, you can create a symlink:

```bash
# Create symlink for easy access
ln -s $(pwd)/backend/selfrag_cli.py /usr/local/bin/selfrag
chmod +x /usr/local/bin/selfrag

# Now you can use 'selfrag' from anywhere
selfrag health
```

## Basic Commands

### Command Structure

```bash
python selfrag_cli.py [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

### Global Options

| Option      | Description               | Default                 |
| ----------- | ------------------------- | ----------------------- |
| `--api-url` | API base URL              | `http://localhost:8080` |
| `--timeout` | Request timeout (seconds) | `30`                    |

### Available Commands

| Command  | Description                              |
| -------- | ---------------------------------------- |
| `health` | Check system health and service status   |
| `ingest` | Ingest documents into the knowledge base |
| `query`  | Search the knowledge base                |
| `stats`  | Show RAG pipeline statistics             |
| `chat`   | Interactive chat mode                    |

## Document Management

### Basic Ingestion

#### Single File

```bash
# Ingest a single file
python selfrag_cli.py ingest document.txt
```

#### Multiple Files

```bash
# Ingest multiple files
python selfrag_cli.py ingest file1.txt file2.md file3.pdf

# Ingest all markdown files
python selfrag_cli.py ingest *.md

# Ingest all files in a directory
python selfrag_cli.py ingest documents/*.txt
```

### Advanced Ingestion with Metadata

#### Adding Metadata

```bash
# With title and tags
python selfrag_cli.py ingest document.txt \
  --title "Research Paper on AI" \
  --tags "ai,research,paper"

# With full metadata
python selfrag_cli.py ingest report.pdf \
  --title "Q4 Financial Report" \
  --tags "finance,quarterly,2024" \
  --type "report" \
  --source "finance-team"
```

#### Direct Text Ingestion

```bash
# Ingest text directly without a file
python selfrag_cli.py ingest \
  --text "Machine learning is transforming industries worldwide." \
  --title "ML Impact Note" \
  --tags "ml,industry,transformation"
```

### Metadata Options

| Option     | Description          | Example                             |
| ---------- | -------------------- | ----------------------------------- |
| `--title`  | Document title       | `"Research Paper"`                  |
| `--tags`   | Comma-separated tags | `"ai,research,important"`           |
| `--type`   | Document type        | `"article"`, `"report"`, `"note"`   |
| `--source` | Document source      | `"web"`, `"internal"`, `"research"` |

### Ingestion Examples

```bash
# Academic paper
python selfrag_cli.py ingest paper.pdf \
  --title "Deep Learning in Computer Vision" \
  --tags "deep-learning,computer-vision,academic" \
  --type "academic-paper" \
  --source "arxiv"

# Meeting notes
python selfrag_cli.py ingest meeting-notes.md \
  --title "Project Kickoff Meeting" \
  --tags "meeting,project,kickoff" \
  --type "notes" \
  --source "internal"

# Web article
python selfrag_cli.py ingest \
  --text "$(curl -s https://example.com/article)" \
  --title "Latest AI Trends" \
  --tags "ai,trends,web" \
  --type "article" \
  --source "web"
```

## Search & Query

### Basic Search

```bash
# Simple query
python selfrag_cli.py query "machine learning"

# Query with quotes for exact phrases
python selfrag_cli.py query "deep learning algorithms"
```

### Advanced Search Options

#### Limiting Results

```bash
# Limit to 5 results
python selfrag_cli.py query "neural networks" --limit 5

# Top 3 most relevant results
python selfrag_cli.py query "artificial intelligence" -l 3
```

#### Similarity Threshold

```bash
# Only show results with similarity > 0.7
python selfrag_cli.py query "machine learning" --threshold 0.7

# More strict threshold for precise results
python selfrag_cli.py query "deep learning" --threshold 0.8
```

#### Output Formats

```bash
# Human-readable table format (default)
python selfrag_cli.py query "AI applications"

# JSON format for scripting
python selfrag_cli.py query "neural networks" --format json

# JSON with specific fields
python selfrag_cli.py query "ML algorithms" \
  --format json \
  --limit 3 \
  --threshold 0.6
```

### Query Examples

#### Research Queries

```bash
# Find research papers
python selfrag_cli.py query "research methodology" \
  --threshold 0.7 \
  --limit 5

# Academic concepts
python selfrag_cli.py query "statistical significance" \
  --format json
```

#### Technical Documentation

```bash
# API documentation
python selfrag_cli.py query "authentication endpoint" \
  --threshold 0.6

# Configuration help
python selfrag_cli.py query "database configuration" \
  --limit 3
```

#### Meeting Notes and Business

```bash
# Find meeting notes
python selfrag_cli.py query "project timeline" \
  --threshold 0.5

# Business requirements
python selfrag_cli.py query "user requirements" \
  --limit 10
```

### Understanding Search Results

#### Result Format

```
🔍 Searching for: machine learning

📊 Found 3 results:

1. 🎯 Score: 0.847
   📄 ML Fundamentals                    # Document title
   📝 Machine learning algorithms...     # Content preview
   🏷️ Tags: algorithms, ml, fundamentals # Metadata tags

2. 🎯 Score: 0.723
   📄 Deep Learning Guide
   📝 Neural networks represent...
   🏷️ Tags: neural-networks, deep-learning

3. 🎯 Score: 0.692
   📄 Algorithm Comparison
   📝 Various machine learning...
   🏷️ Tags: comparison, algorithms
```

#### Score Interpretation

- **0.9-1.0**: Excellent match, highly relevant
- **0.8-0.9**: Very good match, relevant
- **0.7-0.8**: Good match, somewhat relevant
- **0.6-0.7**: Fair match, may be relevant
- **0.5-0.6**: Low match, possibly relevant
- **<0.5**: Poor match, likely not relevant

## Interactive Mode

### Starting Chat Mode

```bash
python selfrag_cli.py chat
```

### Chat Interface

```
🤖 SelfRAG Interactive Chat
Type 'quit' or 'exit' to leave

🔍 Query: what is machine learning?

🎯 Best match (score: 0.847):
📄 ML Fundamentals
📝 Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It encompasses various algorithms and techniques that allow systems to automatically learn and improve from data without being explicitly programmed for every scenario.

📊 Found 3 total results

🔍 Query: how does deep learning work?

🎯 Best match (score: 0.756):
📄 Deep Learning Guide
📝 Deep learning uses artificial neural networks with multiple layers to model and understand complex patterns in data. Each layer learns increasingly abstract representations of the input data...

📊 Found 2 total results

🔍 Query: quit
👋 Goodbye!
```

### Chat Commands

- **Regular text**: Search query
- **`quit`**, **`exit`**, **`q`**: Exit chat mode
- **Empty line**: Skip to next query
- **Ctrl+C**: Force exit

### Chat Features

- **Real-time search**: Instant results as you type
- **Context awareness**: Maintains search context
- **Top result focus**: Shows the most relevant result first
- **Result counting**: Displays total matches found
- **Clean interface**: Simplified output for readability

## Configuration

### Environment Variables

Set these in your shell or `.bashrc`:

```bash
# Default API URL
export SELFRAG_API_URL=http://localhost:8080

# Default timeout
export SELFRAG_TIMEOUT=60

# Add to PATH for easy access
export PATH=$PATH:/path/to/selfrag/backend
```

### Command Line Configuration

#### API URL Configuration

```bash
# Local development
python selfrag_cli.py --api-url http://localhost:8080 health

# Remote server
python selfrag_cli.py --api-url http://your-server:8080 health

# Different port
python selfrag_cli.py --api-url http://localhost:9000 health
```

#### Timeout Configuration

```bash
# Short timeout for quick operations
python selfrag_cli.py --timeout 10 health

# Long timeout for large ingestions
python selfrag_cli.py --timeout 120 ingest large-document.pdf

# Very long timeout for batch operations
python selfrag_cli.py --timeout 300 ingest *.pdf
```

### Configuration File (Optional)

Create `~/.selfrag/config`:

```ini
[DEFAULT]
api_url = http://localhost:8080
timeout = 30

[QUERY]
default_limit = 10
default_threshold = 0.5
default_format = table

[INGEST]
default_type = document
default_source = cli
```

## Examples & Workflows

### Academic Research Workflow

```bash
# 1. Ingest research papers
python selfrag_cli.py ingest papers/*.pdf \
  --tags "research,academic" \
  --type "paper" \
  --source "arxiv"

# 2. Search for specific concepts
python selfrag_cli.py query "neural network architectures" \
  --threshold 0.7 \
  --limit 5

# 3. Interactive exploration
python selfrag_cli.py chat
```

### Documentation Management

```bash
# 1. Ingest all documentation
python selfrag_cli.py ingest docs/*.md \
  --tags "documentation,reference" \
  --type "docs"

# 2. Quick API reference lookup
python selfrag_cli.py query "authentication API" \
  --threshold 0.6

# 3. Configuration help
python selfrag_cli.py query "database setup" \
  --format json | jq '.results[0].content'
```

### Knowledge Base Building

```bash
# 1. Batch ingest with metadata
for file in knowledge/*.txt; do
  title=$(basename "$file" .txt)
  python selfrag_cli.py ingest "$file" \
    --title "$title" \
    --tags "knowledge,reference" \
    --type "article"
done

# 2. Verify ingestion
python selfrag_cli.py stats

# 3. Test search quality
python selfrag_cli.py query "important concepts" \
  --threshold 0.8
```

### Daily Note-Taking

```bash
# 1. Quick note ingestion
echo "Today I learned about transformer architecture" | \
python selfrag_cli.py ingest \
  --text "$(cat)" \
  --title "Daily Learning - $(date +%Y-%m-%d)" \
  --tags "daily,learning,$(date +%Y-%m)"

# 2. Search recent notes
python selfrag_cli.py query "transformer" \
  --threshold 0.6

# 3. Review weekly learnings
python selfrag_cli.py query "$(date +%Y-%m)" \
  --limit 20
```

### Scripting with SelfRAG CLI

#### Bash Script Example

```bash
#!/bin/bash
# bulk_ingest.sh - Bulk ingest with metadata extraction

for file in "$@"; do
  # Extract metadata from filename
  filename=$(basename "$file")
  extension="${filename##*.}"
  title="${filename%.*}"

  # Determine type from extension
  case $extension in
    pdf) type="document" ;;
    md) type="documentation" ;;
    txt) type="note" ;;
    *) type="file" ;;
  esac

  echo "Ingesting: $file"
  python selfrag_cli.py ingest "$file" \
    --title "$title" \
    --type "$type" \
    --tags "bulk-import,$(date +%Y-%m)"
done
```

#### Python Script Example

```python
#!/usr/bin/env python3
# search_and_export.py - Search and export results

import subprocess
import json
import sys

def search_and_export(query, output_file):
    """Search SelfRAG and export results to file."""
    cmd = [
        'python', 'selfrag_cli.py',
        'query', query,
        '--format', 'json',
        '--limit', '50'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        data = json.loads(result.stdout)
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Results exported to {output_file}")
    else:
        print(f"Search failed: {result.stderr}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python search_and_export.py 'query' output.json")
        sys.exit(1)

    search_and_export(sys.argv[1], sys.argv[2])
```

## Troubleshooting

### Common Issues

#### Connection Refused

```bash
# Check if services are running
docker-compose ps

# Check service health
python selfrag_cli.py --api-url http://localhost:8080 health

# Restart services if needed
docker-compose restart
```

#### Timeout Errors

```bash
# Increase timeout for large operations
python selfrag_cli.py --timeout 120 ingest large-file.pdf

# Check service status
curl -w "Total time: %{time_total}s\n" http://localhost:8080/health/readiness
```

#### No Results Found

```bash
# Lower similarity threshold
python selfrag_cli.py query "your query" --threshold 0.3

# Check if documents are ingested
python selfrag_cli.py stats

# Verify document content
python selfrag_cli.py query "common words" --limit 20
```

#### Permission Errors

```bash
# Check file permissions
ls -la selfrag_cli.py

# Make executable
chmod +x selfrag_cli.py

# Run with python explicitly
python3 selfrag_cli.py health
```

### Debug Mode

Enable verbose output by modifying the CLI script:

```python
# Add debug flag to API client
client = SelfrageAPIClient(args.api_url, args.timeout, debug=True)
```

### Performance Issues

```bash
# Check system resources
docker stats

# Monitor API performance
curl -w "@curl-format.txt" http://localhost:8080/health/metrics

# Clear cache if needed
curl -X POST http://localhost:8080/health/cache/clear
```

### Getting Help

```bash
# General help
python selfrag_cli.py --help

# Command-specific help
python selfrag_cli.py ingest --help
python selfrag_cli.py query --help

# Check system status
python selfrag_cli.py health
```

---

This CLI guide provides comprehensive coverage of all SelfRAG CLI capabilities. For additional examples and updates, refer to the main project documentation.
