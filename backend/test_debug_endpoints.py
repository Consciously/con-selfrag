#!/usr/bin/env python3
"""
Test script for debug endpoints - Manual verification of LocalAI integration.

This script provides comprehensive testing of the debug endpoints to verify
end-to-end LocalAI functionality before integrating into production endpoints.
"""

import asyncio
import json
import time
from typing import Any, Dict

import httpx


class DebugEndpointTester:
    """Comprehensive tester for debug endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def print_section(self, title: str):
        """Print a formatted section header."""
        print(f"\n{'='*60}")
        print(f"🔍 {title}")
        print('='*60)
    
    def print_test(self, test_name: str):
        """Print a formatted test header."""
        print(f"\n📋 Testing: {test_name}")
        print('-' * 40)
    
    def print_result(self, success: bool, message: str, data: Dict[str, Any] = None):
        """Print formatted test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {message}")
        
        if data:
            print(f"📊 Response Data:")
            print(json.dumps(data, indent=2, default=str))
    
    async def test_debug_status(self, verbose: bool = False):
        """Test the debug status endpoint."""
        self.print_test("Debug Status Endpoint")
        
        try:
            params = {"verbose": verbose} if verbose else {}
            response = await self.client.get(f"{self.base_url}/debug/status", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"Status check successful (verbose={verbose})", data)
                return data
            else:
                self.print_result(False, f"Status check failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.print_result(False, f"Status check error: {str(e)}")
            return None
    
    async def test_debug_ask(self, question: str, model: str = None, temperature: float = 0.7, verbose: bool = False):
        """Test the debug ask endpoint."""
        self.print_test(f"Debug Ask: '{question[:50]}{'...' if len(question) > 50 else ''}'")
        
        try:
            payload = {
                "question": question,
                "temperature": temperature
            }
            if model:
                payload["model"] = model
            
            params = {"verbose": verbose} if verbose else {}
            
            start_time = time.time()
            response = await self.client.post(
                f"{self.base_url}/debug/ask",
                json=payload,
                params=params
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"Ask successful in {duration:.2f}s", {
                    "question": question,
                    "answer": data.get("answer", "No answer field"),
                    "model": data.get("model", "Unknown model"),
                    "done": data.get("done", "Unknown status"),
                    "duration_seconds": round(duration, 2)
                })
                return data
            else:
                self.print_result(False, f"Ask failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.print_result(False, f"Ask error: {str(e)}")
            return None
    
    async def test_debug_embed(self, text: str, model: str = None, verbose: bool = False):
        """Test the debug embed endpoint."""
        self.print_test(f"Debug Embed: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        try:
            params = {
                "text": text,
                "verbose": verbose
            }
            if model:
                params["model"] = model
            
            start_time = time.time()
            response = await self.client.post(
                f"{self.base_url}/debug/embed",
                params=params
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                embeddings = data.get("embeddings", [])
                metadata = data.get("metadata", {})
                
                self.print_result(True, f"Embed successful in {duration:.2f}s", {
                    "text_length": len(text),
                    "embedding_dimensions": len(embeddings),
                    "embedding_sample": embeddings[:5] if embeddings else [],
                    "metadata": metadata,
                    "duration_seconds": round(duration, 2)
                })
                return data
            else:
                self.print_result(False, f"Embed failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.print_result(False, f"Embed error: {str(e)}")
            return None
    
    async def test_debug_generate(self, prompt: str, model: str = None, temperature: float = 0.7, verbose: bool = False):
        """Test the debug generate endpoint."""
        self.print_test(f"Debug Generate: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")
        
        try:
            payload = {
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            }
            if model:
                payload["model"] = model
            
            params = {"verbose": verbose} if verbose else {}
            
            start_time = time.time()
            response = await self.client.post(
                f"{self.base_url}/debug/generate",
                json=payload,
                params=params
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(True, f"Generate successful in {duration:.2f}s", {
                    "prompt": prompt,
                    "response": data.get("response", "No response field"),
                    "model": data.get("model", "Unknown model"),
                    "done": data.get("done", "Unknown status"),
                    "duration_seconds": round(duration, 2)
                })
                return data
            else:
                self.print_result(False, f"Generate failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.print_result(False, f"Generate error: {str(e)}")
            return None
    
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite for all debug endpoints."""
        print("🚀 Starting Comprehensive Debug Endpoint Tests")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Basic Status Check
        self.print_section("1. Basic Service Status")
        status_basic = await self.test_debug_status(verbose=False)
        
        # Test 2: Verbose Status Check
        self.print_section("2. Verbose Service Status")
        status_verbose = await self.test_debug_status(verbose=True)
        
        # Test 3: Simple Question
        self.print_section("3. Simple Question Test")
        await self.test_debug_ask(
            question="What is the capital of France?",
            temperature=0.3,
            verbose=False
        )
        
        # Test 4: Technical Question
        self.print_section("4. Technical Question Test")
        await self.test_debug_ask(
            question="Explain the difference between async and sync programming in Python.",
            temperature=0.5,
            verbose=True
        )
        
        # Test 5: Simple Text Embedding
        self.print_section("5. Simple Text Embedding")
        await self.test_debug_embed(
            text="Hello, world! This is a test sentence.",
            verbose=False
        )
        
        # Test 6: Technical Text Embedding
        self.print_section("6. Technical Text Embedding")
        await self.test_debug_embed(
            text="FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.",
            verbose=True
        )
        
        # Test 7: Simple Text Generation
        self.print_section("7. Simple Text Generation")
        await self.test_debug_generate(
            prompt="Write a haiku about programming:",
            temperature=0.8,
            verbose=False
        )
        
        # Test 8: Code Generation
        self.print_section("8. Code Generation Test")
        await self.test_debug_generate(
            prompt="Write a Python function to calculate the factorial of a number:",
            temperature=0.2,
            verbose=True
        )
        
        # Test 9: Long Text Processing
        self.print_section("9. Long Text Processing")
        long_text = """
        Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines 
        that can perform tasks that typically require human intelligence. These tasks include learning, reasoning, 
        problem-solving, perception, and language understanding. AI has evolved significantly over the past few decades, 
        with machine learning and deep learning being major driving forces behind recent advances.
        """
        await self.test_debug_embed(text=long_text.strip(), verbose=False)
        
        # Test 10: Error Handling - Empty Input
        self.print_section("10. Error Handling Tests")
        await self.test_debug_ask(question="", verbose=False)
        await self.test_debug_embed(text="", verbose=False)
        await self.test_debug_generate(prompt="", verbose=False)
        
        print(f"\n🏁 Test Suite Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
    
    async def interactive_mode(self):
        """Interactive mode for manual testing."""
        print("🎮 Interactive Debug Mode")
        print("Available commands:")
        print("  ask <question> - Ask a question")
        print("  embed <text> - Generate embeddings")
        print("  generate <prompt> - Generate text")
        print("  status - Check service status")
        print("  quit - Exit interactive mode")
        print()
        
        while True:
            try:
                command = input("debug> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                elif command.lower() == 'status':
                    await self.test_debug_status(verbose=True)
                elif command.startswith('ask '):
                    question = command[4:].strip()
                    if question:
                        await self.test_debug_ask(question, verbose=True)
                    else:
                        print("❌ Please provide a question after 'ask'")
                elif command.startswith('embed '):
                    text = command[6:].strip()
                    if text:
                        await self.test_debug_embed(text, verbose=True)
                    else:
                        print("❌ Please provide text after 'embed'")
                elif command.startswith('generate '):
                    prompt = command[9:].strip()
                    if prompt:
                        await self.test_debug_generate(prompt, verbose=True)
                    else:
                        print("❌ Please provide a prompt after 'generate'")
                elif command == '':
                    continue
                else:
                    print("❌ Unknown command. Use 'ask', 'embed', 'generate', 'status', or 'quit'")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """Main function to run debug endpoint tests."""
    import sys
    
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    async with DebugEndpointTester(base_url) as tester:
        if len(sys.argv) > 2 and sys.argv[2] == "interactive":
            await tester.interactive_mode()
        else:
            await tester.run_comprehensive_tests()


if __name__ == "__main__":
    print("🔍 Debug Endpoint Tester")
    print("Usage:")
    print("  python test_debug_endpoints.py [base_url] [interactive]")
    print("  python test_debug_endpoints.py http://localhost:8000")
    print("  python test_debug_endpoints.py http://localhost:8000 interactive")
    print()
    
    asyncio.run(main())
