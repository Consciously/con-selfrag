# Simplified Dockerfile following YAGNI principles
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1000 llmuser && \
    adduser -D -s /bin/sh -u 1000 -G llmuser llmuser

# Install system dependencies with fallback mirrors
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

# Copy dependency files first (for Docker layer caching)
COPY --chown=llmuser:llmuser pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
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
