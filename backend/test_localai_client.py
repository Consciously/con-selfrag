#!/usr/bin/env python3
"""
Test script for LocalAI client functionality.

This script tests all LocalAI client methods:
- generate() - Non-streaming text generation
- generate_stream() - Streaming text generation  
- ask() - Conversational Q&A
- embed() - Text embedding generation
- list_models() - Available model listing
- health_check() - Service health verification

Usage:
    python test_localai_client.py
"""

import asyncio
import json
import sys
from typing import List

from loguru import logger

# Add the app directory to the path
sys.path.append("app")

from app.localai_client import localai_client


class LocalAIClientTester:
    """Comprehensive LocalAI client testing suite."""

    def __init__(self):
        self.client = localai_client
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
                for model in models[:3]:  # Show first 3 models
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
                
                # Show first few chunks
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
            # Embedding might not be available in all LocalAI setups
            logger.warning("   ⚠️ Note: Embedding functionality may not be available in your LocalAI setup")
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling with invalid inputs."""
        logger.info("🚨 Testing error handling...")
        
        try:
            # Test invalid streaming flag
            try:
                await self.client.generate(prompt="test", stream=True)
                logger.error("❌ Error handling: FAILED - Should have raised ValueError for stream=True")
                return False
            except ValueError as e:
                logger.success("✅ Error handling: PASSED - Correctly raised ValueError for stream=True")
            
            # Test empty prompt
            try:
                await self.client.generate(prompt="")
                logger.warning("⚠️ Error handling: Empty prompt was accepted (may be valid)")
            except Exception as e:
                logger.info(f"   📝 Empty prompt handling: {type(e).__name__}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test: ERROR - {str(e)}")
            return False

    async def run_all_tests(self) -> dict:
        """Run all LocalAI client tests."""
        logger.info("🚀 Starting LocalAI Client Test Suite")
        logger.info("=" * 50)
        
        # Test in logical order
        tests = [
            ("Health Check", self.test_health_check),
            ("List Models", self.test_list_models),
            ("Text Generation", self.test_generate),
            ("Streaming Generation", self.test_generate_stream),
            ("Conversational Q&A", self.test_ask),
            ("Text Embeddings", self.test_embed),
            ("Error Handling", self.test_error_handling),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 Running: {test_name}")
            try:
                await test_func()
            except Exception as e:
                logger.error(f"❌ {test_name}: UNEXPECTED ERROR - {str(e)}")
            
            # Small delay between tests
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
        
        # Exit with appropriate code
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        if passed_tests >= total_tests * 0.8:  # 80% pass rate is acceptable
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
