"""
LocalAI client following YAGNI principles.
Uses OpenAI-compatible API for LocalAI integration.
"""

import asyncio
from typing import AsyncGenerator, List, Dict, Any
from loguru import logger
from openai import AsyncOpenAI

from .config import config
from .models import GenerateResponse, AskResponse, ModelInfo, ErrorResponse


class LocalAIClient:
    """LocalAI client with OpenAI-compatible API integration."""

    def __init__(self):
        """Initialize LocalAI client with configuration."""
        self.client = AsyncOpenAI(
            base_url=config.localai_base_url,
            api_key="not-needed",  # LocalAI doesn't require API key
            timeout=config.localai_timeout
        )
        self.default_model = config.default_model

    async def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> GenerateResponse:
        """
        Generate text using LocalAI.

        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature
            stream: Enable streaming (not implemented for simplicity)

        Returns:
            Generated text response
        """
        model_name = model or self.default_model

        try:
            logger.info(f"Generating text with model: {model_name}")

            response = await self.client.completions.create(
                model=model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=1000,
                stream=False
            )

            return GenerateResponse(
                response=response.choices[0].text.strip(),
                model=model_name,
                done=True
            )

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise Exception(f"Text generation failed: {str(e)}") from e

    async def generate_stream(
        self, prompt: str, model: str | None = None, temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming text using LocalAI.

        Args:
            prompt: Input prompt
            model: Model name (uses default if None)
            temperature: Sampling temperature

        Yields:
            Text chunks as they are generated
        """
        model_name = model or self.default_model

        try:
            logger.info(f"Generating streaming text with model: {model_name}")

            stream = await self.client.completions.create(
                model=model_name,
                prompt=prompt,
                temperature=temperature,
                max_tokens=1000,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].text:
                    yield chunk.choices[0].text

        except Exception as e:
            logger.error(f"Error in streaming generation: {str(e)}")
            yield f"Error: {str(e)}"

    async def ask(
        self, question: str, model: str | None = None, temperature: float = 0.7
    ) -> AskResponse:
        """
        Ask a conversational question using chat completions.

        Args:
            question: Question to ask
            model: Model name (uses default if None)
            temperature: Sampling temperature

        Returns:
            Conversational response
        """
        model_name = model or self.default_model

        try:
            logger.info(f"Asking question with model: {model_name}")

            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": question}
                ],
                temperature=temperature,
                max_tokens=1000
            )

            return AskResponse(
                answer=response.choices[0].message.content.strip(),
                model=model_name
            )

        except Exception as e:
            logger.error(f"Error asking question: {str(e)}")
            raise Exception(f"Question processing failed: {str(e)}") from e

    async def list_models(self) -> List[ModelInfo]:
        """
        List available models.

        Returns:
            List of available models
        """
        try:
            logger.info("Fetching available models")

            models = await self.client.models.list()

            return [
                ModelInfo(name=model.id, size=None)  # LocalAI doesn't provide size info
                for model in models.data
            ]

        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            raise Exception(f"Failed to list models: {str(e)}") from e

    async def health_check(self) -> bool:
        """
        Check if LocalAI is healthy and responsive.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to list models as a health check
            await self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"LocalAI health check failed: {str(e)}")
            return False


# Global client instance
localai_client = LocalAIClient()
