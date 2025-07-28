"""
Enhanced FastAPI application with comprehensive OpenAPI documentation,
async LocalAI integration, and observability features.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from loguru import logger

from .config import config
from .models import (
    GenerateRequest,
    GenerateResponse,
    AskRequest,
    AskResponse,
    ModelInfo,
    HealthCheck,
    LivenessCheck,
    ReadinessCheck,
    ErrorResponse,
)
from .localai_client import localai_client

# Configure logging
logger.remove()
logger.add(
    sink=lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=config.log_level,
)

# Create FastAPI app with comprehensive OpenAPI configuration
app = FastAPI(
    title="🤖 Selfrag LLM API",
    description="""
    **Production-ready FastAPI template for LLM applications with LocalAI backend**
    
    This API provides a clean, scalable foundation for building AI-powered applications with:
    
    * 🚀 **High Performance**: Async operations and connection pooling
    * 🔒 **Production Ready**: Security best practices and error handling
    * 🎯 **Developer Friendly**: Comprehensive documentation and examples
    * 🔧 **Extensible**: Database-ready architecture for PostgreSQL/Qdrant
    
    ## Features
    
    - **Text Generation**: Create content with customizable parameters
    - **Conversational AI**: Ask questions and get intelligent responses  
    - **Model Management**: List and switch between available models
    - **Streaming Support**: Real-time text generation with Server-Sent Events
    - **Health Monitoring**: Liveness and readiness probes for orchestration
    
    ## Getting Started
    
    1. Ensure LocalAI is running and models are available
    2. Use the `/generate` endpoint for text completion
    3. Use the `/ask` endpoint for conversational interactions
    4. Monitor service health via `/health`, `/health/live`, `/health/ready`
    """,
    version="1.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Text Generation",
            "description": "Generate text content using LLM models with customizable parameters",
        },
        {
            "name": "Conversational AI",
            "description": "Interactive question-answering with context awareness",
        },
        {
            "name": "Model Management",
            "description": "Discover and manage available LLM models",
        },
        {
            "name": "Health & Monitoring",
            "description": "Service health checks and readiness probes for container orchestration",
        },
        {"name": "System Info", "description": "API information and service metadata"},
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Enhanced request logging middleware."""
    start_time = time.time()

    # Extract endpoint for logging (remove query params and path params)
    endpoint = request.url.path
    method = request.method

    try:
        response = await call_next(request)
        status_code = response.status_code

        # Log request
        logger.info(
            f"{method} {endpoint} - "
            f"Status: {status_code} - "
            f"Time: {time.time() - start_time:.3f}s"
        )

        return response

    except Exception as e:
        logger.error(
            f"{method} {endpoint} - Error: {str(e)} - Time: {time.time() - start_time:.3f}s"
        )
        raise


# API Routes
@app.get(
    "/",
    tags=["System Info"],
    summary="API Information",
    description="Get comprehensive information about the API, available endpoints, and features",
)
async def root():
    """Root endpoint with comprehensive API information and feature overview."""
    return {
        "name": "🤖 Selfrag LLM API",
        "version": "1.0.0",
        "description": "Production-ready FastAPI template for LLM applications",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoints": {
            "generate": {
                "method": "POST",
                "path": "/generate",
                "description": "Generate text with customizable parameters",
                "features": ["streaming", "temperature_control", "model_selection"],
            },
            "ask": {
                "method": "POST",
                "path": "/ask",
                "description": "Ask conversational questions",
                "features": ["context_awareness", "temperature_control"],
            },
            "models": {
                "method": "GET",
                "path": "/models",
                "description": "List available models with details",
            },
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Comprehensive health check",
            },
        },
        "features": {
            "async_processing": "Non-blocking I/O operations",
            "streaming_support": "Real-time text generation",
            "health_monitoring": "Kubernetes-ready health checks",
            "database_ready": "Prepared for PostgreSQL/Qdrant integration",
            "frontend_agnostic": "Works with React, Vue, Svelte, vanilla JS",
            "production_ready": "Security best practices and error handling",
        },
        "documentation": {
            "interactive_docs": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json",
        },
    }


@app.get(
    "/health",
    response_model=HealthCheck,
    tags=["Health & Monitoring"],
    summary="Comprehensive Health Check",
    description="Get detailed health status including LocalAI connectivity and service readiness",
)
async def health_check():
    """Comprehensive health check with detailed service status."""
    try:
        # Direct await since health_check is already async
        localai_healthy = await localai_client.health_check()

        return HealthCheck(
            status="healthy" if localai_healthy else "degraded",
            localai_connected=localai_healthy,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheck(
            status="unhealthy",
            localai_connected=False,
            timestamp=datetime.utcnow().isoformat() + "Z",
            version="1.0.0",
        )


@app.get(
    "/health/live",
    response_model=LivenessCheck,
    tags=["Health & Monitoring"],
    summary="Liveness Probe",
    description="Kubernetes liveness probe - checks if the service is alive and responding",
)
async def liveness_check():
    """Liveness probe for container orchestration."""
    return LivenessCheck(alive=True, timestamp=datetime.utcnow().isoformat() + "Z")


@app.get(
    "/health/ready",
    response_model=ReadinessCheck,
    tags=["Health & Monitoring"],
    summary="Readiness Probe",
    description="Kubernetes readiness probe - checks if the service is ready to handle requests",
)
async def readiness_check():
    """Readiness probe for container orchestration."""
    try:
        # Direct await since health_check is already async
        localai_ready = await localai_client.health_check()
        dependencies_ready = localai_ready  # Add more dependency checks as needed

        return ReadinessCheck(
            ready=localai_ready and dependencies_ready,
            localai_ready=localai_ready,
            dependencies_ready=dependencies_ready,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return ReadinessCheck(
            ready=False,
            localai_ready=False,
            dependencies_ready=False,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )


@app.post(
    "/generate",
    response_model=GenerateResponse,
    tags=["Text Generation"],
    summary="Generate Text Content",
    description="""
    Generate text using LocalAI LLM models with comprehensive customization options.
    
    **Features:**
    - **Streaming Support**: Enable real-time text generation with Server-Sent Events
    - **Temperature Control**: Adjust creativity from deterministic (0.0) to highly creative (2.0)
    - **Model Selection**: Choose from available models or use the default
    - **Async Processing**: Non-blocking operations for high performance
    
    **Streaming Response Format:**
    When `stream=true`, responses are sent as Server-Sent Events:
    ```
    data: {"chunk": "Generated text chunk"}
    data: {"done": true}
    ```
    """,
    responses={
        200: {
            "description": "Successfully generated text",
            "content": {
                "application/json": {
                    "example": {
                        "response": "Here's a comprehensive explanation of quantum computing...",
                        "model": "llama2",
                        "done": True,
                        "total_duration": 1234567890,
                    }
                }
            },
        },
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Generation failed", "model": ErrorResponse},
    },
)
async def generate_text(request: GenerateRequest):
    """Generate text using LocalAI with async processing and comprehensive error handling."""
    start_time = time.time()
    model_name = request.model or config.default_model

    try:
        if request.stream:
            # Return streaming response
            async def stream_generator():
                try:
                    # Use asyncio.to_thread for blocking LocalAI stream call
                    stream_iter = await asyncio.to_thread(
                        localai_client.generate_stream,
                        prompt=request.prompt,
                        model=model_name,
                        temperature=request.temperature or 0.7,
                    )

                    async for chunk in stream_iter:
                        # Format as Server-Sent Events
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"

                    # Send completion signal
                    yield f"data: {json.dumps({'done': True})}\n\n"

                except Exception as e:
                    logger.error(f"Streaming generation error: {str(e)}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                },
            )
        else:
            # Return complete response using async processing
            response = await asyncio.to_thread(
                localai_client.generate,
                prompt=request.prompt,
                model=model_name,
                temperature=request.temperature or 0.7,
            )

            return response

    except Exception as e:
        logger.error(f"Text generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "GenerationError",
                "message": "Text generation failed",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e


@app.post(
    "/ask",
    response_model=AskResponse,
    tags=["Conversational AI"],
    summary="Ask Conversational Question",
    description="""
    Ask intelligent questions and receive contextual answers from the AI assistant.
    
    **Features:**
    - **Context Awareness**: Maintains conversational context for better responses
    - **Temperature Control**: Adjust response creativity and consistency
    - **Model Selection**: Choose the best model for your use case
    - **Async Processing**: Non-blocking operations for optimal performance
    
    **Use Cases:**
    - Technical Q&A and troubleshooting
    - Educational explanations and tutorials
    - Creative writing assistance
    - Code review and programming help
    """,
    responses={
        200: {
            "description": "Successfully answered question",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "Docker containers provide process isolation, consistent environments, and easy deployment across different systems...",
                        "model": "llama2",
                        "context_used": False,
                    }
                }
            },
        },
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Question processing failed", "model": ErrorResponse},
    },
)
async def ask_question(request: AskRequest):
    """Ask a conversational question with async processing and enhanced context."""
    start_time = time.time()
    model_name = request.model or config.default_model

    try:
        # Use asyncio.to_thread for blocking LocalAI call
        response = await asyncio.to_thread(
            localai_client.ask,
            question=request.question,
            model=model_name,
            temperature=request.temperature or 0.7,
        )

        return response

    except Exception as e:
        logger.error(f"Question processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "QuestionProcessingError",
                "message": "Question processing failed",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e


@app.get(
    "/models",
    tags=["Model Management"],
    summary="List Available Models",
    description="""
    Retrieve comprehensive information about all available LLM models.
    
    **Response includes:**
    - Model names and identifiers
    - Model sizes and resource requirements
    - Capabilities and parameter counts
    - Verification digests for integrity checking
    
    **Use this endpoint to:**
    - Discover available models for your use case
    - Check model availability before making requests
    - Monitor model inventory and updates
    """,
    responses={
        200: {
            "description": "Successfully retrieved model list",
            "content": {
                "application/json": {
                    "example": {
                        "models": [
                            {
                                "name": "llama2",
                                "size": 3825819519,
                                "digest": "sha256:1a838c2d3e4f5a6b",
                                "details": {
                                    "format": "gguf",
                                    "family": "llama",
                                    "parameter_size": "7B",
                                },
                            }
                        ],
                        "count": 1,
                        "timestamp": "2024-01-15T10:30:00Z",
                    }
                }
            },
        },
        500: {"description": "Failed to retrieve models", "model": ErrorResponse},
    },
)
async def list_models():
    """List available models with comprehensive details and async processing."""
    try:
        # Use asyncio.to_thread for blocking LocalAI call
        models = await asyncio.to_thread(localai_client.list_models)

        return {
            "models": [model.dict() for model in models],
            "count": len(models),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    except Exception as e:
        logger.error(f"Model listing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ModelListingError",
                "message": "Failed to list models",
                "detail": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        ) from e


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Starting Enhanced LocalAI LLM API Template")
    logger.info(f"📊 Health checks available at /health, /health/live, /health/ready")
    logger.info(f"📚 Interactive docs at http://{config.host}:{config.port}/docs")
    logger.info(f"🔗 LocalAI endpoint: {config.localai_base_url}")
    logger.info(f"🤖 Default model: {config.default_model}")

    uvicorn.run(
        app, host=config.host, port=config.port, log_level=config.log_level.lower()
    )
