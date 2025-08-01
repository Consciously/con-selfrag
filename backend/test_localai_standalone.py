#!/usr/bin/env python3
"""
Standalone test script for LocalAI client functionality.

This script tests the LocalAI client directly without importing the full FastAPI app.
It only requires: loguru, openai, and pydantic.

Usage:
    python test_localai_standalone.py
"""

import asyncio
import os
import sys
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import List

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field


# Minimal models for testing (copied from app.models)
class GenerateResponse(BaseModel):
    """Response model for text generation."""
    response: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used for generation")
    done: bool = Field(default=True, description="Whether generation is complete")


class AskResponse(BaseModel):
    """Response model for conversational questions."""
    answer: str = Field(..., description="Answer to the question")
    model: str = Field(..., description="Model used for answering")


class ModelInfo(BaseModel):
    """Model information."""
    name: str = Field(..., description="Model name")
    size: str | None = Field(None, description="Model size")


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Human-readable error message")
    detail: str | None = Field(None, description="Detailed error information")
    timestamp: str = Field(..., description="Error timestamp")


# Minimal config class
class Config:
    """Minimal configuration for testing."""
    def __init__(self):
        self.localai_host = os.getenv("LOCALAI_HOST", "localhost")
        self.localai_port = int(os.getenv("LOCALAI_PORT", "8080"))
        self.localai_timeout = float(os.getenv("LOCALAI_TIMEOUT", "30.0"))
        self.default_model = os.getenv("DEFAULT_MODEL", "llama-3.2-1b-instruct")
    
    @property
    def localai_base_url(self) -> str:
        """Get LocalAI base URL."""
        return f"http://{self.localai_host}:{self.localai_port}/v1"


# Standalone LocalAI client (simplified version)
class StandaloneLocalAIClient:
    """Standalone LocalAI client for testing."""

    def __init__(self, config: Config):
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
    ) -> GenerateResponse:
        """Generate text using LocalAI."""
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
                },
            )

            return GenerateResponse(
                response=generated_text,
                model=model_name,
                done=True,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Text generation failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise Exception(f"Text generation failed: {str(e)}") from e

    async def generate_stream(
        self, 
        prompt: str, 
        model: str | None = None, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[str, None]:
        """Generate streaming text using LocalAI."""
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
            logger.error(
                "Streaming text generation failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                },
                exc_info=True,
            )
            yield f"Error: {str(e)}"

    async def ask(
        self, 
        question: str, 
        model: str | None = None, 
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AskResponse:
        """Ask a conversational question using chat completions."""
        model_name = model or self.default_model
        start_time = time.time()

        try:
            logger.info(
                "Processing conversational question",
                extra={
                    "model": model_name,
                    "temperature": temperature,
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
                },
            )

            return AskResponse(
                answer=answer,
                model=model_name,
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Conversational question processing failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise Exception(f"Question processing failed: {str(e)}") from e

    async def embed(self, text: str, model: str | None = None) -> List[float]:
        """Generate embeddings for the given text."""
        model_name = model or "text-embedding-ada-002"
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
                },
            )

            return embeddings

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "Text embedding generation failed",
                extra={
                    "model": model_name,
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise Exception(f"Text embedding generation failed: {str(e)}") from e

    async def list_models(self) -> List[ModelInfo]:
        """List available models."""
        start_time = time.time()

        try:
            logger.info("Fetching available models")

            models = await self.client.models.list()

            duration = time.time() - start_time
            model_list = [
                ModelInfo(name=model.id, size=None)
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
            logger.error(
                "Model listing failed",
                extra={
                    "duration_seconds": round(duration, 3),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise Exception(f"Failed to list models: {str(e)}") from e

    async def health_check(self) -> bool:
        """Check if LocalAI is healthy and responsive."""
        start_time = time.time()

        try:
            logger.debug("Performing LocalAI health check")
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
                    "status": "unhealthy",
                },
            )
            return False


# Test suite (same as before but using standalone client)
class LocalAIClientTester:
    """Comprehensive LocalAI client testing suite."""

    def __init__(self):
        config = Config()
        self.client = StandaloneLocalAIClient(config)
        self.test_results = {
            "health_check": False,
            "list_models": False,
            "generate": False,
            "generate_stream": False,
            "ask": False,
            "embed": False,
        }

    async def test_health_check(self) -> bool:
        """Test LocalAI health check."""
        logger.info("🏥 Testing health check...")
        
        try:
            is_healthy = await self.client.health_check()
            
            if is_healthy:
                logger.success("✅ Health check: PASSED - LocalAI is healthy")
                self.test_results["health_check"] = True
                return True
            else:
                logger.error("❌ Health check: FAILED - LocalAI is not healthy")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check: ERROR - {str(e)}")
            return False

    async def test_list_models(self) -> bool:
        """Test model listing functionality."""
        logger.info("📋 Testing model listing...")
        
        try:
            models = await self.client.list_models()
            
            if models and len(models) > 0:
                logger.success(f"✅ List models: PASSED - Found {len(models)} models")
                for model in models[:3]:
                    logger.info(f"   📦 Model: {model.name}")
                if len(models) > 3:
                    logger.info(f"   ... and {len(models) - 3} more models")
                
                self.test_results["list_models"] = True
                return True
            else:
                logger.warning("⚠️ List models: No models found")
                return False
                
        except Exception as e:
            logger.error(f"❌ List models: ERROR - {str(e)}")
            return False

    async def test_generate(self) -> bool:
        """Test non-streaming text generation."""
        logger.info("🤖 Testing text generation (non-streaming)...")
        
        test_prompt = "Write a short poem about artificial intelligence."
        
        try:
            response = await self.client.generate(
                prompt=test_prompt,
                temperature=0.7,
                max_tokens=100
            )
            
            if response and response.response:
                logger.success("✅ Generate: PASSED")
                logger.info(f"   📝 Prompt: {test_prompt}")
                logger.info(f"   🤖 Model: {response.model}")
                logger.info(f"   📄 Response: {response.response[:100]}...")
                logger.info(f"   ✅ Done: {response.done}")
                
                self.test_results["generate"] = True
                return True
            else:
                logger.error("❌ Generate: FAILED - Empty response")
                return False
                
        except Exception as e:
            logger.error(f"❌ Generate: ERROR - {str(e)}")
            return False

    async def test_generate_stream(self) -> bool:
        """Test streaming text generation."""
        logger.info("🌊 Testing streaming text generation...")
        
        test_prompt = "Explain machine learning in simple terms."
        chunks_received = 0
        total_text = ""
        
        try:
            logger.info(f"   📝 Prompt: {test_prompt}")
            logger.info("   🌊 Streaming response:")
            
            async for chunk in self.client.generate_stream(
                prompt=test_prompt,
                temperature=0.7,
                max_tokens=150
            ):
                if chunk.startswith("Error:"):
                    logger.error(f"❌ Generate stream: ERROR - {chunk}")
                    return False
                
                chunks_received += 1
                total_text += chunk
                
                if chunks_received <= 5:
                    logger.info(f"   📦 Chunk {chunks_received}: {repr(chunk)}")
                elif chunks_received == 6:
                    logger.info("   ... (continuing stream)")
            
            if chunks_received > 0:
                logger.success(f"✅ Generate stream: PASSED - Received {chunks_received} chunks")
                logger.info(f"   📄 Total text length: {len(total_text)} characters")
                
                self.test_results["generate_stream"] = True
                return True
            else:
                logger.error("❌ Generate stream: FAILED - No chunks received")
                return False
                
        except Exception as e:
            logger.error(f"❌ Generate stream: ERROR - {str(e)}")
            return False

    async def test_ask(self) -> bool:
        """Test conversational Q&A."""
        logger.info("💬 Testing conversational Q&A...")
        
        test_question = "What is the capital of France?"
        
        try:
            response = await self.client.ask(
                question=test_question,
                temperature=0.3,
                max_tokens=50
            )
            
            if response and response.answer:
                logger.success("✅ Ask: PASSED")
                logger.info(f"   ❓ Question: {test_question}")
                logger.info(f"   🤖 Model: {response.model}")
                logger.info(f"   💬 Answer: {response.answer}")
                
                self.test_results["ask"] = True
                return True
            else:
                logger.error("❌ Ask: FAILED - Empty answer")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ask: ERROR - {str(e)}")
            return False

    async def test_embed(self) -> bool:
        """Test text embedding generation."""
        logger.info("🔢 Testing text embedding generation...")
        
        test_text = "This is a test sentence for embedding generation."
        
        try:
            embeddings = await self.client.embed(text=test_text)
            
            if embeddings and len(embeddings) > 0:
                logger.success("✅ Embed: PASSED")
                logger.info(f"   📝 Text: {test_text}")
                logger.info(f"   🔢 Embedding dimensions: {len(embeddings)}")
                logger.info(f"   📊 First 5 values: {embeddings[:5]}")
                logger.info(f"   📈 Value range: [{min(embeddings):.4f}, {max(embeddings):.4f}]")
                
                self.test_results["embed"] = True
                return True
            else:
                logger.error("❌ Embed: FAILED - Empty embeddings")
                return False
                
        except Exception as e:
            logger.error(f"❌ Embed: ERROR - {str(e)}")
            logger.warning("   ⚠️ Note: Embedding functionality may not be available in your LocalAI setup")
            return False

    async def run_all_tests(self) -> dict:
        """Run all LocalAI client tests."""
        logger.info("🚀 Starting LocalAI Client Test Suite (Standalone)")
        logger.info("=" * 50)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("List Models", self.test_list_models),
            ("Text Generation", self.test_generate),
            ("Streaming Generation", self.test_generate_stream),
            ("Conversational Q&A", self.test_ask),
            ("Text Embeddings", self.test_embed),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ {test_name}: UNEXPECTED ERROR - {str(e)}")
            
            await asyncio.sleep(0.5)
        
        # Print summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 50)
        
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        
        for test_name, passed in self.test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        logger.info(f"\n🎯 Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.success("🎉 ALL TESTS PASSED! LocalAI client is fully functional.")
        elif passed_tests >= total_tests * 0.8:
            logger.warning(f"⚠️ Most tests passed ({passed_tests}/{total_tests}). Some features may not be available.")
        else:
            logger.error(f"❌ Many tests failed ({passed_tests}/{total_tests}). Check LocalAI setup.")
        
        return self.test_results


async def main():
    """Main test execution function."""
    try:
        tester = LocalAIClientTester()
        results = await tester.run_all_tests()
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        if passed_tests >= total_tests * 0.8:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 Test suite failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Configure logger for testing
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
    )
    
    # Run the test suite
    asyncio.run(main())
