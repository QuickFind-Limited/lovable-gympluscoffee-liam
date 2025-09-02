"""Final Working Streamlit UI for Odoo MCP Agent - PRODUCTION READY with Anthropic Claude"""

import streamlit as st
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv
import logging
import json
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()


# Create OpenAI-compatible client for Anthropic Claude
def create_claude_client():
    """Create AsyncOpenAI client configured for Anthropic"""
    # Check if we should use OpenAI instead of Anthropic
    use_openai = os.getenv("USE_OPENAI", "").lower() in ["true", "1", "yes"]

    if os.getenv("ANTHROPIC_API_KEY") and not use_openai:
        return AsyncOpenAI(
            base_url="https://api.anthropic.com/v1/", api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    return None


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(page_title="Odoo AI Assistant", page_icon="🤖", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []


async def run_query_async(query):
    """Run a query using the agent with async support"""
    try:
        # Use proven async context manager pattern
        async with MCPServerStdio(
            params={
                "command": "uv",
                "args": ["run", "odoo-mcp-server"],
            }
        ) as mcp_server:
            # Create agent with appropriate model configuration
            claude_client = create_claude_client()

            if claude_client:
                # Use Anthropic Claude with OpenAI-compatible client
                model = OpenAIChatCompletionsModel(
                    model="claude-sonnet-4-20250514", openai_client=claude_client
                )
            else:
                # Use standard OpenAI model
                model = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")

            agent = Agent(
                name="Odoo Assistant",
                instructions="""You are a highly capable AI assistant with access to Odoo ERP system through MCP server.

                CRITICAL INSTRUCTIONS FOR TOOL USAGE:
                - Always use instance_id "default" for all Odoo operations
                - To list partners: Use odoo_search_simple with field="id", operator=">", value="0" first,
                  then use odoo_read with those IDs and fields=["id", "name", "email", "phone"]
                - Available tools: odoo_search_simple, odoo_read, odoo_create, odoo_update, odoo_delete, odoo_fields_get
                - Use basic fields only: id, name, email, phone, street, city, country_id
                - For search operations, always specify field, operator, and value

                You can help users with:
                - Creating, reading, updating, and deleting Odoo records
                - Searching for records based on various criteria
                - Managing business workflows in Odoo
                - Generating reports and insights from Odoo data
                - Analyzing business patterns and providing insights

                Always be precise, helpful, and provide detailed explanations. When working with Odoo data,
                ensure you understand the user's requirements clearly before making any changes.""",
                model=model,
                mcp_servers=[mcp_server],
            )

            # Determine if we should use streaming based on the model type
            use_streaming = True

            # Check if we're using an OpenAI model (not Claude through OpenAI client)
            if isinstance(model, str):
                # Direct OpenAI model string - definitely use streaming
                use_streaming = True
            elif isinstance(model, OpenAIChatCompletionsModel):
                # Check if it's a Claude model wrapped in OpenAI client
                model_name = getattr(model, "model", "")
                if "claude" in str(model_name).lower():
                    use_streaming = False
                else:
                    # OpenAI model through OpenAIChatCompletionsModel - use streaming
                    use_streaming = True

            if not use_streaming:
                # Use non-streaming mode for Anthropic Claude
                result = await Runner.run(
                    agent,
                    query,
                    max_turns=100,
                )

                # Extract response
                if hasattr(result, "final_output"):
                    response = result.final_output
                elif hasattr(result, "messages") and result.messages:
                    response = result.messages[-1].content
                else:
                    response = str(result)

                # Extract tool calls
                tool_calls = []
                if hasattr(result, "new_items"):
                    for item in result.new_items:
                        if type(item).__name__ == "ToolCallItem" and hasattr(item, "raw_item"):
                            raw = item.raw_item
                            if hasattr(raw, "name") and hasattr(raw, "arguments"):
                                tool_calls.append(
                                    {
                                        "name": raw.name,
                                        "arguments": raw.arguments,
                                    }
                                )

                # Remove duplicates
                seen = set()
                unique_tools = []
                for tool in tool_calls:
                    key = f"{tool['name']}:{tool['arguments']}"
                    if key not in seen:
                        seen.add(key)
                        unique_tools.append(tool)

                yield ("final", (response, unique_tools))
                return

            # Use streaming mode for OpenAI and other models
            logger.info(f"Starting streaming mode with model: {model}")

            result = Runner.run_streamed(
                agent,
                query,
                max_turns=40,
            )

            # Stream data containers
            tool_calls = []
            messages = []
            final_response = ""
            chunk_buffer = ""

            # Process streaming events
            async for event in result.stream_events():
                if event.type == "run_item_stream_event":
                    if event.name == "tool_called":
                        # Extract tool information from the event
                        if hasattr(event.item, "raw_item"):
                            raw = event.item.raw_item
                            if hasattr(raw, "name") and hasattr(raw, "arguments"):
                                tool_info = {
                                    "name": raw.name,
                                    "arguments": raw.arguments,
                                }
                                tool_calls.append(tool_info)
                                yield ("tool", tool_info)
                    elif event.name == "message_output_created":
                        # Message content
                        if hasattr(event.item, "raw_item") and hasattr(
                            event.item.raw_item, "content"
                        ):
                            content = event.item.raw_item.content
                            messages.append(content)
                elif event.type == "raw_response_event":
                    # Raw streaming content - handle different event structures
                    content = None

                    # Try different ways to extract content based on OpenAI streaming format
                    if hasattr(event, "data"):
                        if hasattr(event.data, "choices") and event.data.choices:
                            # Standard OpenAI streaming format
                            choice = event.data.choices[0]
                            if hasattr(choice, "delta"):
                                delta = choice.delta
                                if hasattr(delta, "content") and delta.content:
                                    content = delta.content
                                elif hasattr(delta, "tool_calls"):
                                    # Handle streaming tool calls
                                    for tool_call in delta.tool_calls:
                                        if hasattr(tool_call, "function"):
                                            tc_info = {
                                                "name": tool_call.function.name,
                                                "arguments": tool_call.function.arguments or "",
                                            }
                                            yield ("tool", tc_info)
                        elif hasattr(event.data, "content") and event.data.content:
                            # Fallback for other streaming formats
                            content = event.data.content

                    if content:
                        chunk_buffer += content
                        yield ("content", content)

            # For streaming, the response is built from the chunks
            if chunk_buffer:
                final_response = chunk_buffer
            elif messages:
                final_response = messages[-1]
            else:
                final_response = "Response completed."

            # Remove duplicate tools
            seen = set()
            unique_tools = []
            for tool in tool_calls:
                key = f"{tool['name']}:{tool['arguments']}"
                if key not in seen:
                    seen.add(key)
                    unique_tools.append(tool)

            yield ("final", (final_response, unique_tools))

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise e


# Main UI
st.title("🤖 Odoo AI Assistant")
st.markdown("Production-ready interface to interact with your Odoo system")

# Sidebar
with st.sidebar:
    # Example queries
    st.subheader("Example Queries")
    examples = [
        "List all partners in Odoo",
        "Show me available Odoo models",
        "Search for customers with email containing 'gmail'",
        "Create a new product called 'Office Chair' with price 250",
    ]

    for example in examples:
        if st.button(example, key=f"ex_{hash(example)}"):
            st.session_state.next_prompt = example

# Chat interface

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Display tool calls if available (for assistant messages)
        if message["role"] == "assistant" and "tool_calls" in message and message["tool_calls"]:
            with st.expander(f"🛠️ Tools Used ({len(message['tool_calls'])})"):
                for tool in message["tool_calls"]:
                    st.markdown(f"**{tool['name']}**")
                    try:
                        # Pretty print JSON arguments
                        import json

                        args = json.loads(tool["arguments"])
                        st.code(json.dumps(args, indent=2), language="json")
                    except Exception:
                        # Fallback to raw display if not valid JSON
                        st.code(tool["arguments"], language="text")

# Add a streaming status indicator
if "streaming_active" not in st.session_state:
    st.session_state.streaming_active = False

# Chat input
if prompt := st.chat_input("Ask me anything about your Odoo system...") or st.session_state.get(
    "next_prompt"
):
    if "next_prompt" in st.session_state:
        prompt = st.session_state.next_prompt
        del st.session_state.next_prompt

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        tool_placeholder = st.container()

        # Containers for streaming data
        stream_data = {"response_text": "", "tool_calls": [], "displayed_tools": set()}

        try:
            st.session_state.streaming_active = True

            # Run the async generator synchronously
            async def process_query():
                # Show initial processing message
                message_placeholder.markdown("🔄 Processing your request...")

                async for event_type, data in run_query_async(prompt):
                    if event_type == "tool":
                        # Real-time tool display
                        tool_key = f"{data['name']}:{data['arguments']}"
                        if tool_key not in stream_data["displayed_tools"]:
                            stream_data["displayed_tools"].add(tool_key)
                            with tool_placeholder:
                                # Create a unique key for each tool call
                                with st.expander(f"🛠️ Using: {data['name']}", expanded=True):
                                    try:
                                        args = json.loads(data["arguments"])
                                        st.code(json.dumps(args, indent=2), language="json")
                                    except Exception:
                                        st.code(data["arguments"], language="text")

                    elif event_type == "content":
                        # Streaming content
                        stream_data["response_text"] += data
                        # Show streaming indicator with current content
                        message_placeholder.markdown(stream_data["response_text"] + "▌")

                    elif event_type == "final":
                        # Final response and all tools
                        final_response, all_tools = data
                        stream_data["response_text"] = final_response
                        stream_data["tool_calls"] = all_tools
                        message_placeholder.markdown(stream_data["response_text"])

                        # Display tools after completion for non-streaming mode
                        if stream_data["tool_calls"] and not stream_data["displayed_tools"]:
                            with tool_placeholder:
                                # Show all tools at once for Claude
                                for tool in stream_data["tool_calls"]:
                                    with st.expander(f"🛠️ Used: {tool['name']}", expanded=False):
                                        try:
                                            args = json.loads(tool["arguments"])
                                            st.code(json.dumps(args, indent=2), language="json")
                                        except Exception:
                                            st.code(tool["arguments"], language="text")

                return stream_data["response_text"], stream_data["tool_calls"]

            # Run the async function
            response, tool_calls = asyncio.run(process_query())

            # Store message with tool information
            message_data = {"role": "assistant", "content": response}
            if tool_calls:
                message_data["tool_calls"] = tool_calls
            st.session_state.messages.append(message_data)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            message_placeholder.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            logger.error(f"Query processing failed: {e}")
        finally:
            st.session_state.streaming_active = False
