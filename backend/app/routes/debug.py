"""
Debug routes for testing LocalAI capabilities directly.

This module provides temporary test endpoints for manual verification of LocalAI
integration before wiring into main application endpoints. Includes verbose logging
for debugging and development purposes.
"""

import time
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..localai_client import localai_client
from ..logging_utils import get_logger
from ..models import AskRequest, AskResponse, ErrorResponse, GenerateRequest, GenerateResponse

# Initialize logger and router
logger = get_logger(__name__)
router = APIRouter(tags=["Debug"])


class DebugEmbedRequest:
    """Request model for embedding testing."""
    
    def __init__(self, text: str, model: str = None, verbose: bool = False):
        self.text = text
        self.model = model
        self.verbose = verbose


@router.post(
    "/ask",
    response_model=AskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "LocalAI service error"},
        503: {"model": ErrorResponse, "description": "LocalAI service unavailable"},
    },
    summary="Debug: Ask LocalAI a question directly",
    description="""
    **Debug endpoint for testing conversational AI capabilities.**
    
    This endpoint allows direct testing of LocalAI's question-answering capabilities
    with comprehensive logging for debugging purposes. Use this to verify end-to-end
    functionality before integrating into production endpoints.
    
    **Debug Features:**
    - Verbose request/response logging
    - Raw LocalAI response inspection
    - Performance timing metrics
    - Error details with stack traces
    
    **Use Cases:**
    - Manual testing of LocalAI integration
    - Debugging conversation flows
    - Performance benchmarking
    - Response quality assessment
    """,
)
async def debug_ask(
    request: AskRequest,
    verbose: bool = Query(default=False, description="Enable verbose logging for debugging")
) -> AskResponse:
    """Ask LocalAI a question directly with debug logging."""
    start_time = time.time()
    
    logger.info(
        "🔍 DEBUG: Ask request received",
        extra={
            "question": request.question,
            "question_length": len(request.question),
            "model": request.model or "default",
            "temperature": request.temperature,
            "verbose": verbose,
            "endpoint": "/debug/ask"
        }
    )
    
    if verbose:
        logger.info(
            "🔍 DEBUG: Raw request details",
            extra={
                "raw_request": request.model_dump(),
                "localai_base_url": localai_client.client.base_url,
                "default_model": localai_client.default_model,
            }
        )
    
    try:
        # Validate request
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Call LocalAI
        logger.info("🔍 DEBUG: Calling LocalAI ask method")
        response = await localai_client.ask(
            question=request.question,
            model=request.model,
            temperature=request.temperature
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        if verbose:
            logger.info(
                "🔍 DEBUG: Raw LocalAI response",
                extra={
                    "raw_response": response.model_dump() if hasattr(response, 'model_dump') else str(response),
                    "response_type": type(response).__name__,
                    "processing_time_ms": int(processing_time * 1000),
                }
            )
        
        logger.info(
            "🔍 DEBUG: Ask request completed successfully",
            extra={
                "model": response.model if hasattr(response, 'model') else "unknown",
                "answer_length": len(response.answer) if hasattr(response, 'answer') else 0,
                "processing_time_ms": int(processing_time * 1000),
                "done": response.done if hasattr(response, 'done') else True,
            }
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "🔍 DEBUG: Ask request failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": int(processing_time * 1000),
                "question_length": len(request.question),
                "verbose": verbose,
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Debug ask failed: {str(e)}"
        ) from e


@router.post(
    "/embed",
    responses={
        200: {"description": "Embedding generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "LocalAI service error"},
        503: {"model": ErrorResponse, "description": "LocalAI service unavailable"},
    },
    summary="Debug: Generate embeddings directly",
    description="""
    **Debug endpoint for testing text embedding generation.**
    
    This endpoint allows direct testing of LocalAI's embedding capabilities
    with comprehensive logging and response inspection for debugging purposes.
    
    **Debug Features:**
    - Verbose embedding generation logging
    - Raw embedding vector inspection
    - Dimension and value range analysis
    - Performance timing metrics
    
    **Use Cases:**
    - Manual testing of embedding generation
    - Debugging vector similarity issues
    - Performance benchmarking
    - Embedding quality assessment
    """,
)
async def debug_embed(
    text: str = Query(..., description="Text to generate embeddings for"),
    model: str = Query(default=None, description="Embedding model name (uses default if not specified)"),
    verbose: bool = Query(default=False, description="Enable verbose logging for debugging")
) -> Dict[str, Any]:
    """Generate embeddings directly with debug logging."""
    start_time = time.time()
    
    logger.info(
        "🔍 DEBUG: Embed request received",
        extra={
            "text": text[:100] + "..." if len(text) > 100 else text,
            "text_length": len(text),
            "model": model or "default",
            "verbose": verbose,
            "endpoint": "/debug/embed"
        }
    )
    
    if verbose:
        logger.info(
            "🔍 DEBUG: Raw embed request details",
            extra={
                "full_text": text,
                "localai_base_url": localai_client.client.base_url,
                "default_model": localai_client.default_model,
            }
        )
    
    try:
        # Validate request
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text cannot be empty"
            )
        
        # Call LocalAI
        logger.info("🔍 DEBUG: Calling LocalAI embed method")
        embeddings = await localai_client.embed(
            text=text,
            model=model
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Analyze embeddings
        embedding_stats = {
            "dimensions": len(embeddings),
            "min_value": min(embeddings) if embeddings else None,
            "max_value": max(embeddings) if embeddings else None,
            "mean_value": sum(embeddings) / len(embeddings) if embeddings else None,
        }
        
        if verbose:
            logger.info(
                "🔍 DEBUG: Raw embedding response",
                extra={
                    "embedding_sample": embeddings[:10] if len(embeddings) > 10 else embeddings,
                    "embedding_stats": embedding_stats,
                    "processing_time_ms": int(processing_time * 1000),
                }
            )
        
        logger.info(
            "🔍 DEBUG: Embed request completed successfully",
            extra={
                "model": model or localai_client.default_model,
                "text_length": len(text),
                "embedding_dimensions": len(embeddings),
                "processing_time_ms": int(processing_time * 1000),
                **embedding_stats,
            }
        )
        
        return {
            "embeddings": embeddings,
            "metadata": {
                "model": model or localai_client.default_model,
                "text_length": len(text),
                "processing_time_ms": int(processing_time * 1000),
                "stats": embedding_stats,
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "🔍 DEBUG: Embed request failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": int(processing_time * 1000),
                "text_length": len(text),
                "verbose": verbose,
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Debug embed failed: {str(e)}"
        ) from e


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "LocalAI service error"},
        503: {"model": ErrorResponse, "description": "LocalAI service unavailable"},
    },
    summary="Debug: Generate text directly",
    description="""
    **Debug endpoint for testing text generation capabilities.**
    
    This endpoint allows direct testing of LocalAI's text generation with
    comprehensive logging and response inspection for debugging purposes.
    
    **Debug Features:**
    - Verbose generation logging
    - Raw response inspection
    - Token usage analysis
    - Performance timing metrics
    
    **Use Cases:**
    - Manual testing of text generation
    - Debugging prompt engineering
    - Performance benchmarking
    - Response quality assessment
    """,
)
async def debug_generate(
    request: GenerateRequest,
    verbose: bool = Query(default=False, description="Enable verbose logging for debugging")
) -> GenerateResponse:
    """Generate text directly with debug logging."""
    start_time = time.time()
    
    logger.info(
        "🔍 DEBUG: Generate request received",
        extra={
            "prompt": request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt,
            "prompt_length": len(request.prompt),
            "model": request.model or "default",
            "temperature": request.temperature,
            "stream": request.stream,
            "verbose": verbose,
            "endpoint": "/debug/generate"
        }
    )
    
    if verbose:
        logger.info(
            "🔍 DEBUG: Raw generate request details",
            extra={
                "full_prompt": request.prompt,
                "raw_request": request.model_dump(),
                "localai_base_url": localai_client.client.base_url,
                "default_model": localai_client.default_model,
            }
        )
    
    try:
        # Validate request
        if not request.prompt.strip():
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Check if streaming is requested (not supported in debug endpoint)
        if request.stream:
            logger.warning("🔍 DEBUG: Streaming requested but not supported in debug endpoint")
            raise HTTPException(
                status_code=400,
                detail="Streaming not supported in debug endpoint. Use /debug/generate/stream for streaming."
            )
        
        # Call LocalAI
        logger.info("🔍 DEBUG: Calling LocalAI generate method")
        response = await localai_client.generate(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            stream=False
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        if verbose:
            logger.info(
                "🔍 DEBUG: Raw LocalAI response",
                extra={
                    "raw_response": response.model_dump() if hasattr(response, 'model_dump') else str(response),
                    "response_type": type(response).__name__,
                    "processing_time_ms": int(processing_time * 1000),
                }
            )
        
        logger.info(
            "🔍 DEBUG: Generate request completed successfully",
            extra={
                "model": response.model if hasattr(response, 'model') else "unknown",
                "response_length": len(response.response) if hasattr(response, 'response') else 0,
                "processing_time_ms": int(processing_time * 1000),
                "done": response.done if hasattr(response, 'done') else True,
            }
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "🔍 DEBUG: Generate request failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": int(processing_time * 1000),
                "prompt_length": len(request.prompt),
                "verbose": verbose,
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Debug generate failed: {str(e)}"
        ) from e


@router.get(
    "/status",
    summary="Debug: LocalAI status and configuration",
    description="""
    **Debug endpoint for inspecting LocalAI configuration and status.**
    
    This endpoint provides detailed information about the LocalAI client
    configuration, connection status, and available capabilities.
    
    **Information Provided:**
    - LocalAI connection details
    - Available models
    - Service health status
    - Configuration parameters
    """,
)
async def debug_status(
    verbose: bool = Query(default=False, description="Include detailed configuration information")
) -> Dict[str, Any]:
    """Get LocalAI status and configuration details."""
    start_time = time.time()
    
    logger.info(
        "🔍 DEBUG: Status request received",
        extra={
            "verbose": verbose,
            "endpoint": "/debug/status"
        }
    )
    
    try:
        # Check health
        is_healthy = await localai_client.health_check()
        
        # Get models if healthy
        models = []
        if is_healthy:
            try:
                model_list = await localai_client.list_models()
                models = [model.name for model in model_list]
            except Exception as e:
                logger.warning(f"🔍 DEBUG: Could not fetch models: {e}")
        
        processing_time = time.time() - start_time
        
        status_info = {
            "service": "LocalAI",
            "healthy": is_healthy,
            "base_url": str(localai_client.client.base_url),
            "default_model": localai_client.default_model,
            "available_models": models,
            "model_count": len(models),
            "processing_time_ms": int(processing_time * 1000),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        
        if verbose:
            status_info.update({
                "timeout": localai_client.client.timeout,
                "client_type": type(localai_client.client).__name__,
                "debug_mode": True,
            })
        
        logger.info(
            "🔍 DEBUG: Status request completed",
            extra={
                "healthy": is_healthy,
                "model_count": len(models),
                "processing_time_ms": int(processing_time * 1000),
            }
        )
        
        return status_info
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            "🔍 DEBUG: Status request failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "processing_time_ms": int(processing_time * 1000),
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Debug status failed: {str(e)}"
        ) from e
