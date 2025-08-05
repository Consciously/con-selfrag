# Multi-stage Dockerfile for development and production
FROM python:3.12-slim AS dev

# Set working directory
WORKDIR /app

# Install system dependencies and development tools for ML packages
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    gcc \
    g++ \
    make \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml README.md ./

# Install all dependencies including dev tools
# Install in specific order to handle dependencies better
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir numpy && \
    pip install --no-cache-dir -e ".[dev]" && \
    pip install --no-cache-dir uv

# Copy application code
COPY app/ ./app/
COPY test_*.py ./
COPY alembic.ini ./
COPY migrations/ ./migrations/

# Development stage complete - includes all dev tools

# Runtime stage - slim production image
FROM python:3.12-slim AS runtime

# Create non-root user for security
RUN groupadd -g 1000 llmuser && \
    useradd -r -u 1000 -g llmuser llmuser

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only production dependencies from dev stage
COPY --from=dev /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dev /usr/local/bin /usr/local/bin
COPY --chown=llmuser:llmuser pyproject.toml README.md ./
COPY --chown=llmuser:llmuser app/ ./app/
COPY --chown=llmuser:llmuser alembic.ini ./
COPY --chown=llmuser:llmuser migrations/ ./migrations/

# Create cache directory for sentence-transformers models
RUN mkdir -p /app/.cache/huggingface && \
    chown -R llmuser:llmuser /app/.cache

# Set environment variables for model caching
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers

# Switch to non-root user
USER llmuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
