# Multi-stage Dockerfile for development and production
FROM python:3.12-alpine AS dev

# Set working directory
WORKDIR /app

# Install system dependencies and development tools
RUN apk update --no-cache && \
    apk add --no-cache \
    curl \
    bash \
    gcc \
    musl-dev \
    linux-headers \
    || \
    (apk add --no-cache --repository http://dl-3.alpinelinux.org/alpine/v3.22/main \
    curl \
    bash \
    gcc \
    musl-dev \
    linux-headers) || \
    (apk add --no-cache --repository http://dl-4.alpinelinux.org/alpine/v3.22/main \
    curl \
    bash \
    gcc \
    musl-dev \
    linux-headers)

# Copy dependency files
COPY pyproject.toml README.md ./

# Install all dependencies including dev tools
RUN pip install --no-cache-dir -e ".[dev]" && \
    pip install --no-cache-dir uv

# Copy application code
COPY app/ ./app/
COPY test_*.py ./

# Development stage complete - includes all dev tools

# Runtime stage - slim production image
FROM python:3.12-alpine AS runtime

# Create non-root user for security
RUN addgroup -g 1000 llmuser && \
    adduser -D -s /bin/sh -u 1000 -G llmuser llmuser

# Install minimal runtime dependencies
RUN apk update --no-cache && \
    apk add --no-cache \
    curl \
    bash || \
    (apk add --no-cache --repository http://dl-3.alpinelinux.org/alpine/v3.22/main \
    curl \
    bash) || \
    (apk add --no-cache --repository http://dl-4.alpinelinux.org/alpine/v3.22/main \
    curl \
    bash)

WORKDIR /app

# Copy only production dependencies from dev stage
COPY --from=dev /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dev /usr/local/bin /usr/local/bin
COPY --chown=llmuser:llmuser pyproject.toml README.md ./
COPY --chown=llmuser:llmuser app/ ./app/

# Switch to non-root user
USER llmuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
