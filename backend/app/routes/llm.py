"""
LLM interaction routes for text generation, question answering, and model management.

This module provides the core LLM functionality endpoints that integrate with LocalAI
to enable inference and embedding tasks in a testable, explainable way.
"""

import time
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..localai_client import localai_client
from ..logging_utils import get_logger
from ..models import (
    AskRequest,
    AskResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    ModelInfo,
)

# Initialize logger and router
logger = get_logger(__name__)
router = APIRouter(tags=["LLM"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "LLM service error"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
    summary="Generate text using LLM",
    description="""
    **Generate text using the configured LLM model.**
    
    This endpoint provides text generation capabilities using LocalAI with OpenAI-compatible API.
    Supports various parameters for controlling generation behavior including temperature and model selection.
    
    **Use Cases:**
    - Code generation and completion
    - Creative writing assistance  
    - Text summarization and rewriting
    - Technical documentation generation
    
    **Performance Notes:**
    - Generation time varies by prompt complexity and model size
    - Streaming is available for real-time generation (see /generate/stream)
    - Default timeout is 30 seconds
    """,
)
async def generate_text(request: GenerateRequest) -> GenerateResponse:
    """Generate text using the LLM with comprehensive error handling and logging."""
    start_time = time.time()
    
    logger.info(
        "Text generation request received",
        extra={
            "prompt_length": len(request.prompt),
            "model": request.model or "default",
            "temperature": request.temperature,
            "stream": request.stream,
        }
    )
    
    try:
        # Validate request
        if not request.prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Check if streaming is requested (redirect to streaming endpoint)
        if request.stream:
            logger.warning("Streaming requested but not supported in this endpoint. Use /generate/stream instead.")
            raise HTTPException(
                status_code=400,
                detail="Streaming not supported in this endpoint. Use /generate/stream for streaming responses."
            )
        
        # Generate text using LocalAI
        response = await localai_client.generate(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            stream=False
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(
            "Text generation completed successfully",
            extra={
                "model": response.model,
                "response_length": len(response.response),
                "processing_time_ms": int(processing_time * 1000),
                "done": response.done,
            }
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "Text generation failed",
            extra={
                "error": str(e),
                "processing_time_ms": int(processing_time * 1000),
                "prompt_length": len(request.prompt),
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Text generation failed: {str(e)}"
        ) from e


@router.post(
    "/generate/stream",
    response_class=StreamingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "LLM service error"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
    summary="Generate streaming text using LLM",
    description="""
    **Generate streaming text using the configured LLM model.**
    
    This endpoint provides real-time text generation with streaming responses.
    Text is generated and sent as it becomes available, enabling real-time user experiences.
    
    **Response Format:**
    - Content-Type: text/plain
    - Streaming chunks of generated text
    - Connection closes when generation is complete
    
    **Use Cases:**
    - Interactive chat interfaces
    - Real-time code completion
    - Live content generation
    - Progressive text display
    """,
)
async def generate_text_stream(request: GenerateRequest):
    """Generate streaming text using the LLM."""
    logger.info(
        "Streaming text generation request received",
        extra={
            "prompt_length": len(request.prompt),
            "model": request.model or "default",
            "temperature": request.temperature,
        }
    )
    
    try:
        # Validate request
        if not request.prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Create async generator for streaming
        async def generate_stream():
            try:
                async for chunk in localai_client.generate_stream(
                    prompt=request.prompt,
                    model=request.model,
                    temperature=request.temperature
                ):
                    yield chunk
                    
                logger.info("Streaming text generation completed")
                    
            except Exception as e:
                logger.error(
                    "Streaming text generation failed",
                    extra={"error": str(e)},
                    exc_info=True
                )
                yield f"\n\nError: {str(e)}"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Streaming setup failed",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Streaming generation failed: {str(e)}"
        ) from e


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "LLM service error"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
    summary="Ask a conversational question",
    description="""
    **Ask a conversational question using chat completions.**
    
    This endpoint provides conversational AI capabilities using the chat completions API.
    Optimized for question-answering, explanations, and interactive conversations.
    
    **Key Features:**
    - Context-aware responses
    - Conversational tone and style
    - Optimized for Q&A interactions
    - Support for follow-up questions
    
    **Use Cases:**
    - Technical support and help
    - Educational explanations
    - Interactive tutorials
    - General knowledge queries
    
    **Differences from /generate:**
    - Uses chat completions instead of text completions
    - Better for conversational interactions
    - Maintains conversational context
    - Optimized response formatting
    """,
)
async def ask_question(request: AskRequest) -> AskResponse:
    """Ask a conversational question with comprehensive error handling and logging."""
    start_time = time.time()
    
    logger.info(
        "Question request received",
        extra={
            "question_length": len(request.question),
            "model": request.model or "default",
            "temperature": request.temperature,
        }
    )
    
    try:
        # Validate request
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Ask question using LocalAI
        response = await localai_client.ask(
            question=request.question,
            model=request.model,
            temperature=request.temperature
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        logger.info(
            "Question answered successfully",
            extra={
                "model": response.model,
                "answer_length": len(response.answer),
                "processing_time_ms": int(processing_time * 1000),
                "context_used": response.context_used,
            }
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "Question processing failed",
            extra={
                "error": str(e),
                "processing_time_ms": int(processing_time * 1000),
                "question_length": len(request.question),
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Question processing failed: {str(e)}"
        ) from e


@router.get(
    "/models",
    response_model=list[ModelInfo],
    responses={
        500: {"model": ErrorResponse, "description": "Failed to retrieve models"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
    summary="List available LLM models",
    description="""
    **List all available LLM models from LocalAI.**
    
    This endpoint provides information about all models available in the LocalAI instance.
    Useful for discovering available models and their capabilities.
    
    **Response Information:**
    - Model names and identifiers
    - Model sizes (when available)
    - Model digests for verification
    - Additional model details and capabilities
    
    **Use Cases:**
    - Model discovery and selection
    - System capability assessment
    - Model availability verification
    - Integration testing
    """,
)
async def list_models() -> list[ModelInfo]:
    """List all available models with comprehensive error handling."""
    logger.info("Models list request received")
    
    try:
        models = await localai_client.list_models()
        
        logger.info(
            "Models listed successfully",
            extra={
                "model_count": len(models),
                "models": [model.name for model in models],
            }
        )
        
        return models
        
    except Exception as e:
        logger.error(
            "Failed to list models",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve models: {str(e)}"
        ) from e


@router.get(
    "/health",
    responses={
        200: {"description": "LLM service is healthy"},
        503: {"description": "LLM service is unhealthy"},
    },
    summary="Check LLM service health",
    description="""
    **Check the health and availability of the LLM service.**
    
    This endpoint performs a comprehensive health check of the LocalAI service
    by attempting to connect and retrieve basic information.
    
    **Health Check Process:**
    1. Connection test to LocalAI
    2. Basic API functionality test
    3. Model availability verification
    
    **Response Codes:**
    - 200: Service is healthy and responsive
    - 503: Service is unavailable or unhealthy
    """,
)
async def health_check() -> dict[str, Any]:
    """Check LLM service health with detailed status information."""
    logger.info("LLM health check requested")
    
    try:
        is_healthy = await localai_client.health_check()
        
        if is_healthy:
            logger.info("LLM service health check passed")
            return {
                "status": "healthy",
                "service": "LocalAI",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "message": "LLM service is operational"
            }
        else:
            logger.warning("LLM service health check failed")
            raise HTTPException(
                status_code=503,
                detail="LLM service is not responding"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "LLM health check error",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=503,
            detail=f"LLM health check failed: {str(e)}"
        ) from e
