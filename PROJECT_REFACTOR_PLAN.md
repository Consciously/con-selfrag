# Project Refactor Plan - Simplified Template Structure

## Proposed New Structure

```
con-llm-container-base/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app with clean routes
│   │   ├── config.py            # Simplified configuration
│   │   ├── models.py            # Pydantic models/types
│   │   ├── ollama_client.py     # Direct Ollama integration
│   │   └── database/            # Database preparation (empty for now)
│   │       ├── __init__.py
│   │       ├── connection.py    # DB connection placeholder
│   │       └── models.py        # DB models placeholder
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.lock
├── frontend/                    # Frontend placeholder
│   ├── README.md               # Frontend setup instructions
│   └── .gitkeep
├── shared/
│   └── types.py                # Shared types between frontend/backend
├── docker-compose.yml          # Single compose file
├── .env.example
├── .gitignore
├── README.md
└── docs/
    ├── API.md                  # API documentation
    ├── DATABASE.md             # Database integration guide
    └── DEPLOYMENT.md           # Deployment guide
```

## Key Simplifications

### 1. Remove Redundant Directories
- Remove root-level `api/`, `app/`, `dist/`, `docker/`, `scripts/`
- Consolidate into clean `backend/` structure
- Remove duplicate Docker configurations

### 2. Simplify Backend Architecture
- Remove factory patterns (YAGNI - only one implementation)
- Flatten configuration structure
- Reduce error hierarchy to 3 types max
- Direct Ollama client integration
- Remove unused model parameters (keep only temperature)

### 3. Database Preparation
- Add `backend/app/database/` structure
- Placeholder files for PostgreSQL and Qdrant integration
- Clear separation for future database layer

### 4. Frontend Preparation
- Simple `frontend/` directory with setup instructions
- Clear API contract via shared types
- Agnostic approach - can be React, Vue, Svelte, etc.

### 5. Minimal Dependencies
```toml
[dependencies]
fastapi = ">=0.104.0"
ollama = ">=0.3.0"
loguru = ">=0.7.0"
pydantic = ">=2.0.0"
uvicorn = ">=0.24.0"
# Database dependencies (commented out for now)
# asyncpg = ">=0.29.0"        # PostgreSQL
# qdrant-client = ">=1.7.0"   # Qdrant vector DB
```

## Implementation Steps

1. Create new simplified backend structure
2. Migrate essential code with simplifications
3. Remove redundant files and directories
4. Add database preparation structure
5. Update documentation
6. Test and validate

## Benefits

- **50% reduction in file count**
- **Clear separation of concerns**
- **Easy to extend with databases**
- **Simple frontend integration**
- **Production-ready template**
- **Follows SOLID principles without over-engineering**
