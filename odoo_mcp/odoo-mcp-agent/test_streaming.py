#!/usr/bin/env python3
"""Test streaming functionality"""

import asyncio
import logging
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_streaming():
    """Test the streaming functionality"""
    try:
        # Use proven async context manager pattern
        async with MCPServerStdio(
            params={
                "command": "uv",
                "args": ["run", "odoo-mcp-server"],
            }
        ) as mcp_server:
            # Create agent with OpenAI model (streaming should work)
            model = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")

            agent = Agent(
                name="Test Agent",
                instructions="You are a test agent. Just respond with a simple greeting.",
                model=model,
                mcp_servers=[mcp_server],
            )

            # Test streaming
            logger.info("Testing streaming mode...")
            result = Runner.run_streamed(
                agent,
                "Hello, just say hi back!",
                max_turns=1,
            )

            # Process streaming events
            chunk_count = 0
            async for event in result.stream_events():
                chunk_count += 1
                logger.info(f"Received event type: {event.type}")

                if event.type == "raw_response_event":
                    # Log raw content
                    if hasattr(event, "data"):
                        logger.info(f"Raw data received: {type(event.data)}")

            logger.info(f"Total chunks received: {chunk_count}")

            # Test accessing result after streaming
            logger.info("Checking if we can access result after streaming...")
            # The result object itself is the streaming container, not awaitable
            logger.info(f"Result type: {type(result)}")

            return True

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_streaming())
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
