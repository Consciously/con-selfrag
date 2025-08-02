# Selfrag CLI Module

The Selfrag CLI provides a comprehensive command-line interface for managing your personal knowledge system. It supports document ingestion, semantic search, health monitoring, and interactive querying.

## Installation

### Option 1: Use the standalone script (Recommended for testing)

```bash
# Navigate to the backend directory
cd backend

# Test the CLI directly
python selfrag_cli.py --help
```

### Option 2: Install as a package command

```bash
# Install the package with CLI dependencies
cd backend
pip install -e .

# Use the installed command
selfrag --help
```

## Available Commands

### Health Check

Check the status of all Selfrag services:

```bash
# Basic health check
python selfrag_cli.py health

# With custom API URL
python selfrag_cli.py --api-url http://localhost:8080 health
```

### Document Ingestion

Ingest documents into your knowledge base:

```bash
# Ingest a single file
python selfrag_cli.py ingest document.txt --title "My Document"

# Ingest multiple files with metadata
python selfrag_cli.py ingest *.md --tags "documentation,important" --type "docs"

# Ingest text directly
echo "Machine learning is fascinating" | python selfrag_cli.py ingest --title "ML Note"

# Ingest with custom metadata
python selfrag_cli.py ingest research.pdf --title "AI Research" --tags "ai,research" --source "academic"
```

### Knowledge Base Querying

Search your knowledge base using semantic search:

```bash
# Basic query
python selfrag_cli.py query "machine learning algorithms"

# Limit results and set threshold
python selfrag_cli.py query "API documentation" --limit 5 --threshold 0.7

# JSON output for scripting
python selfrag_cli.py query "docker setup" --format json
```

### Interactive Chat Mode

Start an interactive session for exploring your knowledge:

```bash
# Start chat mode
python selfrag_cli.py chat

# In chat mode, you can:
selfrag> What is machine learning?
selfrag> How do I set up Docker?
selfrag> quit
```

### Statistics and Monitoring

View RAG pipeline statistics:

```bash
# Show collection stats
python selfrag_cli.py stats
```

## Configuration

### Environment Variables

The CLI respects the same environment variables as the backend:

```bash
export LOCALAI_HOST=localhost
export LOCALAI_PORT=8080
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
```

### API URL Override

You can specify a custom API URL for all commands:

```bash
python selfrag_cli.py --api-url http://remote-server:8080 health
```

## Advanced Usage

### Batch Processing

Ingest multiple documents with automation:

```bash
# Process all markdown files in a directory
find docs/ -name "*.md" -exec python selfrag_cli.py ingest {} --type documentation \;

# Ingest with timestamped metadata
python selfrag_cli.py ingest report.txt --tags "$(date +%Y-%m),monthly-report"
```

### Scripting Integration

Use the CLI in shell scripts:

```bash
#!/bin/bash
# check_knowledge.sh

# Check if system is healthy
if python selfrag_cli.py health > /dev/null 2>&1; then
    echo "System healthy, proceeding with ingestion..."
    python selfrag_cli.py ingest new_document.txt
else
    echo "System unhealthy, aborting..."
    exit 1
fi
```

### JSON Processing

Process CLI output with jq:

```bash
# Get document IDs from query results
python selfrag_cli.py query "machine learning" --format json | jq '.[].metadata.id'

# Count results
python selfrag_cli.py query "API" --format json | jq 'length'
```

## Troubleshooting

### Common Issues

**Connection Errors:**

```bash
# Check if the API is running
curl http://localhost:8080/health

# Use custom timeout for slow responses
python selfrag_cli.py --timeout 60 health
```

**File Encoding Issues:**

```bash
# Ensure files are UTF-8 encoded
file -i document.txt

# Convert if necessary
iconv -f ISO-8859-1 -t UTF-8 document.txt > document_utf8.txt
```

**Large File Processing:**

```bash
# For large files, increase timeout
python selfrag_cli.py --timeout 120 ingest large_document.txt
```

### Debug Mode

Enable verbose output for debugging:

```bash
# The CLI will show detailed error messages
python selfrag_cli.py query "test" --api-url http://wrong-url:8080
```

## Examples

### Complete Workflow Example

```bash
# 1. Check system health
python selfrag_cli.py health

# 2. Ingest documentation
python selfrag_cli.py ingest README.md --title "Project Documentation" --tags "docs,setup"

# 3. Ingest code files with context
python selfrag_cli.py ingest src/main.py --title "Main Application" --type "code" --tags "python,core"

# 4. Query for specific information
python selfrag_cli.py query "how to setup the project"

# 5. Interactive exploration
python selfrag_cli.py chat
```

### Academic Research Workflow

```bash
# Ingest research papers
python selfrag_cli.py ingest papers/*.pdf --type "research" --tags "academic,$(date +%Y)"

# Query for specific topics
python selfrag_cli.py query "transformer architecture" --limit 3

# Export results for analysis
python selfrag_cli.py query "machine learning" --format json > ml_results.json
```

### Documentation Management

```bash
# Ingest all documentation
find docs/ -name "*.md" | head -10 | xargs -I {} python selfrag_cli.py ingest {} --type documentation

# Quick lookup
python selfrag_cli.py query "API endpoints"

# Interactive help
python selfrag_cli.py chat
```

## Integration with Other Tools

### With Git Hooks

```bash
# .git/hooks/post-commit
#!/bin/bash
# Auto-ingest changed files
git diff --name-only HEAD~1 HEAD | grep -E '\.(md|txt|py)$' | \
    xargs -I {} python selfrag_cli.py ingest {} --tags "git-commit,$(date +%Y-%m-%d)"
```

### With Cron Jobs

```bash
# Daily knowledge base backup
0 2 * * * cd /path/to/selfrag && python selfrag_cli.py stats > daily_stats.log
```

### With Text Editors

Add to your editor's configuration to ingest files on save:

```vim
" Vim integration
autocmd BufWritePost *.md !python /path/to/selfrag_cli.py ingest % --type documentation
```

## Performance Tips

1. **Batch Processing**: Use multiple file arguments instead of single file calls
2. **Appropriate Thresholds**: Set similarity thresholds based on your content quality
3. **Metadata Strategy**: Use consistent tags and metadata for better organization
4. **Regular Health Checks**: Monitor system health before large operations

## Future Enhancements

The CLI is designed to grow with the Selfrag project:

- **Memory Module Integration**: Context-aware queries
- **Agent Commands**: Task execution and planning
- **Tool Integration**: External tool connections
- **Advanced Export**: Multiple output formats
- **Configuration Management**: Profile-based settings
