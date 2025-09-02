#!/usr/bin/env python3
"""Simple test to check OpenAI configuration"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
import asyncio

# Load environment variables
load_dotenv()


async def test_openai():
    """Test basic OpenAI connection"""
    try:
        # Create client
        client = AsyncOpenAI()

        # Test with a simple completion
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4-0125-preview"),
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=10,
        )

        print(f"Response: {response.choices[0].message.content}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_openai())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
