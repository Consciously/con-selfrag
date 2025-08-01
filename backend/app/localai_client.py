"""
LocalAI client for generating embeddings and handling model interactions.
"""

import time
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import List

from loguru import logger
from openai import AsyncOpenAI

from .config import config
from .models import AskResponse, ErrorResponse, GenerateResponse, ModelInfo


class LocalAIClient:
    """LocalAI client with OpenAI-compatible API integration."""

    def __init__(self):
        """Initialize LocalAI client with configuration."""
        self.client = AsyncOpenAI(
            base_url=config.localai_base_url,
            api_key="not-needed",  # LocalAI doesn't require API key
            timeout=config.localai_timeout,
        )
        self.default_model = config.default_model
        logger.info(
            "LocalAI client initialized",
            extra={
                "base_url": config.localai_base_url,
                "timeout": config.localai_timeout,
                "default_model": self.default_model,
            },
        )

    def _create_error_response(self, error_type: str, message: str, detail: str = None) -> ErrorResponse:
        """Create a structured error response."""
        return ErrorResponse(
            error=error_type,
            message=message,
            detail=detail,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
    ) -> GenerateResponse:
        """
        Generate text using LocalAI (non-streaming).

        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Must be False for this method (use generate_stream for streaming)

        Returns:
            Generated text response

        Raises:
            ValueError: If stream=True (use generate_stream instead)
            Exception: If generation fails with structured error details
        """
        if stream:
            raise ValueError("Use generate_stream() method for streaming responses")

        model_name = model or self.default_model
        start_time = time.time()

        try:
            logger.info(
                "Starting text generation",
                extra={
                    "model": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "prompt_length": len(prompt),
                },
            )

            response = await self.client.completions.create(
                model=model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            duration = time.time() - start_time
            generated_text = response.choices[0].text.strip()

            logger.info(
                "Text generation completed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "response_length": len(generated_text),
                    "tokens_used": response.usage.total_tokens if response.usage else None,
                },
            )

            return GenerateResponse(
                response=generated_text,
                model=model_name,
                done=True,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_detail = f"Model: {model_name}, Duration: {duration:.3f}s, Error: {str(e)}"
            
            logger.error(
                "Text generation failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            error_response = self._create_error_response(
                error_type="GenerationError",
                message="Text generation failed",
                detail=error_detail,
            )
            raise Exception(f"Text generation failed: {error_response.model_dump_json()}") from e

    async def generate_stream(
        self, 
        prompt: str, 
        model: str | None = None, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text using LocalAI.

        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they are generated
        """
        model_name = model or self.default_model
        start_time = time.time()
        chunk_count = 0

        try:
            logger.info(
                "Starting streaming text generation",
                extra={
                    "model": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "prompt_length": len(prompt),
                },
            )

            stream = await self.client.completions.create(
                model=model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].text:
                    chunk_count += 1
                    yield chunk.choices[0].text

            duration = time.time() - start_time
            logger.info(
                "Streaming text generation completed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "chunks_generated": chunk_count,
                },
            )

        except Exception as e:
            duration = time.time() - start_time
            error_detail = f"Model: {model_name}, Duration: {duration:.3f}s, Chunks: {chunk_count}, Error: {str(e)}"
            
            logger.error(
                "Streaming text generation failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "chunks_generated": chunk_count,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            error_response = self._create_error_response(
                error_type="StreamingError",
                message="Streaming text generation failed",
                detail=error_detail,
            )
            yield f"Error: {error_response.model_dump_json()}"

    async def ask(
        self, 
        question: str, 
        model: str | None = None, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AskResponse:
        """
        Ask a conversational question using chat completions.

        Args:
            question: Question to ask
            model: Model name (uses default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Conversational response

        Raises:
            Exception: If question processing fails with structured error details
        """
        model_name = model or self.default_model
        start_time = time.time()

        try:
            logger.info(
                "Processing conversational question",
                extra={
                    "model": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "question_length": len(question),
                },
            )

            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": question}],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            duration = time.time() - start_time
            answer = response.choices[0].message.content.strip()

            logger.info(
                "Conversational question processed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "answer_length": len(answer),
                    "tokens_used": response.usage.total_tokens if response.usage else None,
                },
            )

            return AskResponse(
                answer=answer,
                model=model_name,
            )

        except Exception as e:
            duration = time.time() - start_time
            error_detail = f"Model: {model_name}, Duration: {duration:.3f}s, Error: {str(e)}"
            
            logger.error(
                "Conversational question processing failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            error_response = self._create_error_response(
                error_type="ConversationError",
                message="Question processing failed",
                detail=error_detail,
            )
            raise Exception(f"Question processing failed: {error_response.model_dump_json()}") from e

    async def embed(self, text: str, model: str | None = None) -> List[float]:
        """
        Generate embeddings for the given text.

        Args:
            text: Text to embed
            model: Embedding model name (uses default if None)

        Returns:
            List of embedding values (floats)

        Raises:
            Exception: If embedding generation fails with structured error details
        """
        # Use a default embedding model or the general default model
        model_name = model or "text-embedding-ada-002"  # Common embedding model name
        start_time = time.time()

        try:
            logger.info(
                "Generating text embeddings",
                extra={
                    "model": model_name,
                    "text_length": len(text),
                },
            )

            response = await self.client.embeddings.create(
                model=model_name,
                input=text,
            )

            duration = time.time() - start_time
            embeddings = response.data[0].embedding

            logger.info(
                "Text embeddings generated",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "embedding_dimensions": len(embeddings),
                    "tokens_used": response.usage.total_tokens if response.usage else None,
                },
            )

            return embeddings

        except Exception as e:
            duration = time.time() - start_time
            error_detail = f"Model: {model_name}, Duration: {duration:.3f}s, Error: {str(e)}"
            
            logger.error(
                "Text embedding generation failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            error_response = self._create_error_response(
                error_type="EmbeddingError",
                message="Text embedding generation failed",
                detail=error_detail,
            )
            raise Exception(f"Text embedding generation failed: {error_response.model_dump_json()}") from e

    async def list_models(self) -> List[ModelInfo]:
        """
        List available models.

        Returns:
            List of available models

        Raises:
            Exception: If model listing fails with structured error details
        """
        start_time = time.time()

        try:
            logger.info("Fetching available models")

            models = await self.client.models.list()

            duration = time.time() - start_time
            model_list = [
                ModelInfo(name=model.id, size=None)  # LocalAI doesn't provide size info
                for model in models.data
            ]

            logger.info(
                "Available models fetched",
                extra={
                    "duration_seconds": round(duration, 3),
                    "model_count": len(model_list),
                    "models": [m.name for m in model_list],
                },
            )

            return model_list

        except Exception as e:
            duration = time.time() - start_time
            error_detail = f"Duration: {duration:.3f}s, Error: {str(e)}"
            
            logger.error(
                "Model listing failed",
                extra={
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )

            error_response = self._create_error_response(
                error_type="ModelListError",
                message="Failed to list models",
                detail=error_detail,
            )
            raise Exception(f"Failed to list models: {error_response.model_dump_json()}") from e

    async def health_check(self) -> bool:
        """
        Check if LocalAI is healthy and responsive.

        Returns:
            True if healthy, False otherwise
        """
        start_time = time.time()

        try:
            logger.debug("Performing LocalAI health check")

            # Try to list models as a health check
            await self.client.models.list()

            duration = time.time() - start_time
            logger.info(
                "LocalAI health check passed",
                extra={
                    "duration_seconds": round(duration, 3),
                    "status": "healthy",
                },
            )
            return True

        except Exception as e:
            duration = time.time() - start_time
            logger.warning(
                "LocalAI health check failed",
                extra={
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "status": "unhealthy",
                },
            )
            return False


# Global client instance
localai_client = LocalAIClient()
