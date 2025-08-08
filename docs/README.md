# SelfRAG Documentation Index

Welcome to the comprehensive documentation for CON-SelfRAG, a high-performance containerized Self-Reflective AI system.

## 📚 Documentation Overview

### 🚀 Getting Started

1. **[README](../README.md)** - Project overview and quick start
2. **[Comprehensive Guide](COMPREHENSIVE_GUIDE.md)** - Complete user manual with detailed examples
3. **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment and scaling

### 🖥️ User Interfaces

4. **[CLI Guide](CLI_GUIDE.md)** - Detailed command-line interface usage
5. **[API Reference](API_REFERENCE.md)** - REST API endpoints and examples
6. **[Backend API Docs](../backend/API_DOCUMENTATION.md)** - Technical API implementation details

### 🏗️ Architecture & Implementation

7. **[RAG Implementation](../backend/RAG_IMPLEMENTATION.md)** - Retrieval-Augmented Generation details
8. **[Performance Summary](../backend/RAG_COMPLETION_SUMMARY.md)** - Performance optimizations and caching

## 📖 Documentation by Use Case

### For End Users

- **Getting Started**: [README](../README.md) → [Quick Start Section](../README.md#quick-start)
- **CLI Usage**: [CLI Guide](CLI_GUIDE.md) → [Basic Commands](CLI_GUIDE.md#basic-commands)
- **Web Interface**: [Comprehensive Guide](COMPREHENSIVE_GUIDE.md#web-interface)

### For Developers

- **API Integration**: [API Reference](API_REFERENCE.md) → [Core Endpoints](API_REFERENCE.md#core-endpoints)
- **Backend Development**: [Backend API Docs](../backend/API_DOCUMENTATION.md)
- **Performance Tuning**: [Comprehensive Guide](COMPREHENSIVE_GUIDE.md#performance-features)

### For System Administrators

- **Production Deployment**: [Deployment Guide](DEPLOYMENT_GUIDE.md) → [Production Deployment](DEPLOYMENT_GUIDE.md#production-deployment)
- **Monitoring & Health**: [Comprehensive Guide](COMPREHENSIVE_GUIDE.md#monitoring--health)
- **Troubleshooting**: [CLI Guide](CLI_GUIDE.md#troubleshooting)

## 🔍 Quick Reference

### Essential Commands

```bash
# Health check
python selfrag_cli.py health

# Ingest documents
python selfrag_cli.py ingest document.txt --title "My Document"

# Search knowledge
python selfrag_cli.py query "machine learning" --limit 5

# Interactive chat
python selfrag_cli.py chat
```

### Key URLs

- **Main API**: http://localhost:8080
- **Interactive API Docs**: http://localhost:8080/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard
- **Health Check**: http://localhost:8080/health/readiness

### Essential Endpoints

```bash
# System health
curl http://localhost:8080/health/readiness

# Performance metrics
curl http://localhost:8080/health/metrics

# Cache analytics
curl http://localhost:8080/health/cache/analytics
```

## 📊 Document Status

| Document            | Status      | Last Updated | Audience   |
| ------------------- | ----------- | ------------ | ---------- |
| README              | ✅ Complete | Latest       | All Users  |
| Comprehensive Guide | ✅ Complete | Latest       | End Users  |
| CLI Guide           | ✅ Complete | Latest       | CLI Users  |
| API Reference       | ✅ Complete | Latest       | Developers |
| Deployment Guide    | ✅ Complete | Latest       | DevOps     |
| Backend API Docs    | ✅ Complete | Latest       | Developers |

## 🎯 Common Workflows

### First-Time Setup

1. [README](../README.md#quick-start) - Initial setup and installation
2. [CLI Guide](CLI_GUIDE.md#installation--setup) - CLI configuration
3. [Comprehensive Guide](COMPREHENSIVE_GUIDE.md#first-steps) - First document ingestion

### Daily Usage

1. [CLI Guide](CLI_GUIDE.md#document-management) - Ingesting new documents
2. [CLI Guide](CLI_GUIDE.md#search--query) - Searching your knowledge base
3. [CLI Guide](CLI_GUIDE.md#interactive-mode) - Interactive chat sessions

### Integration & Development

1. [API Reference](API_REFERENCE.md#authentication) - API authentication
2. [API Reference](API_REFERENCE.md#request-response-examples) - Integration examples
3. [Backend API Docs](../backend/API_DOCUMENTATION.md) - Implementation details

### Production Deployment

1. [Deployment Guide](DEPLOYMENT_GUIDE.md#production-deployment) - Production setup
2. [Deployment Guide](DEPLOYMENT_GUIDE.md#monitoring-and-maintenance) - Monitoring
3. [Comprehensive Guide](COMPREHENSIVE_GUIDE.md#troubleshooting) - Issue resolution

## 🔧 Support & Help

### Troubleshooting Resources

- **[CLI Troubleshooting](CLI_GUIDE.md#troubleshooting)** - Command-line issues
- **[API Troubleshooting](COMPREHENSIVE_GUIDE.md#troubleshooting)** - API and service issues
- **[Deployment Issues](DEPLOYMENT_GUIDE.md#troubleshooting-deployment)** - Production problems

### Getting Help

1. **Check the health status**: `python selfrag_cli.py health`
2. **Review logs**: `docker-compose logs -f`
3. **Consult the troubleshooting guides** above
4. **Check the interactive API docs**: http://localhost:8080/docs

### Performance Optimization

- **[Performance Features](COMPREHENSIVE_GUIDE.md#performance-features)** - Caching and optimization
- **[Performance Tuning](DEPLOYMENT_GUIDE.md#performance-tuning)** - Production optimization
- **[Monitoring](COMPREHENSIVE_GUIDE.md#monitoring--health)** - Performance monitoring

## 📝 Contributing to Documentation

To improve this documentation:

1. Identify gaps or unclear sections
2. Add examples and use cases
3. Update with new features
4. Maintain consistency across documents
5. Test all examples and commands

---

**Next Steps**: Start with the [README](../README.md) for project overview, then move to the [Comprehensive Guide](COMPREHENSIVE_GUIDE.md) for detailed usage instructions.
