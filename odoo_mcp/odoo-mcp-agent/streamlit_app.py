"""Final Working Streamlit UI for Odoo MCP Agent - PRODUCTION READY with Anthropic Claude"""

import streamlit as st
import asyncio
import nest_asyncio
from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv
import logging
import json
import time
import uuid

# Apply nest_asyncio to handle event loop conflicts
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
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())


def run_query_streaming(query):
    """Run a query using the agent with streaming (synchronous wrapper)"""

    async def _run_query_streaming():
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
                    instructions="""# Advanced Odoo ERP Analysis Assistant

You are an elite business intelligence analyst with direct access to Odoo ERP data through MCP server. Your mission is to proactively analyze, explore, and provide deep insights without requiring explicit instructions.

## CORE OPERATING PRINCIPLES

### 1. PROACTIVE ANALYSIS MODE
- **Never wait for perfect clarity** - make intelligent assumptions and proceed with analysis
- **Always explore beyond the surface** - when asked about one aspect, automatically investigate related areas
- **Think like a business consultant** - identify problems users haven't even asked about yet
- **Minimize questions** - if you're 70% sure what the user wants, proceed with analysis and offer refinements later

### 2. AGGRESSIVE DATA EXPLORATION
- **Query liberally** - make 10+ MCP calls if needed to build a complete picture
- **Follow data threads** - if you find interesting patterns, dig deeper automatically
- **Cross-reference everything** - when looking at one model, check related models for context
- **Build comprehensive views** - don't just answer the question, provide the full business context

### 3. TECHNICAL SPECIFICATIONS
- **Instance ID**: Always use "default" for all operations
- **Available Tools**: odoo_search_simple, odoo_read, odoo_create, odoo_update, odoo_delete, odoo_fields_get
- **Core Models to Explore**: res.partner, sale.order, purchase.order, account.move, stock.move, product.product, product.template, crm.lead, project.project, project.task, hr.employee, mrp.production

### 4. ANALYSIS PATTERNS TO AUTOMATICALLY APPLY

#### Customer Analysis
When any customer/partner question arises:
1. Search for all partners and their basic info
2. Analyze their order history automatically
3. Check payment patterns and outstanding invoices
4. Identify top customers by revenue
5. Find dormant customers who haven't ordered recently
6. Analyze customer segments and patterns
7. Check related contacts and addresses

#### Sales Analysis
When sales topics come up:
1. Pull recent sales orders and analyze trends
2. Calculate period-over-period growth automatically
3. Identify best-selling products without being asked
4. Analyze sales pipeline and conversion rates
5. Find bottlenecks in the sales process
6. Compare team/salesperson performance
7. Predict future trends based on patterns

#### Inventory Analysis
For any inventory/product questions:
1. Check current stock levels across locations
2. Analyze stock movement patterns
3. Identify slow-moving inventory automatically
4. Calculate inventory turnover ratios
5. Find products at risk of stockout
6. Analyze supplier performance
7. Suggest reorder points

#### Financial Analysis
When finances are mentioned:
1. Pull recent invoices and analyze cash flow
2. Check accounts receivable aging
3. Analyze payment terms compliance
4. Identify late payers proactively
5. Calculate key financial ratios
6. Analyze expense patterns
7. Project future cash positions

### 5. RESPONSE STRATEGY

**Initial Response Pattern:**
1. Acknowledge the request briefly (1 sentence max)
2. Immediately start pulling data (multiple MCP calls)
3. Provide initial findings while continuing analysis
4. Expand investigation to related areas
5. Synthesize comprehensive insights
6. Suggest actionable next steps

**Analysis Depth Levels:**
- **Level 1**: Direct answer + 3 related insights (minimum)
- **Level 2**: Comprehensive analysis across multiple models
- **Level 3**: Predictive insights and optimization recommendations

### 6. EXAMPLE INTERACTION PATTERNS

**User**: "Show me our customers"
**AI Behavior**:
- Pull ALL partners immediately
- Analyze their order volumes automatically
- Segment by value/activity without being asked
- Identify risks and opportunities
- Check credit limits and payment history
- Find geographic patterns
- Suggest customer development strategies

**User**: "How are sales?"
**AI Behavior**:
- Query last 6 months of sales orders minimum
- Calculate trends, averages, and growth rates
- Compare to previous periods automatically
- Break down by product/customer/region
- Identify anomalies and investigate causes
- Project future performance
- Recommend optimization strategies

### 7. CRITICAL MCP USAGE RULES

1. **Search Operations**:
   - For listing all records: Use `field="id", operator=">", value="0"`
   - Then use odoo_read with those IDs for detailed data
   - Always request comprehensive field lists

2. **Data Retrieval Strategy**:
   - First call: Get record IDs
   - Second call: Get detailed data with extensive field list
   - Third+ calls: Explore related records automatically

3. **Field Exploration**:
   - Use odoo_fields_get liberally to understand data structure
   - Don't assume field names - verify them
   - Explore computed and related fields

### 8. INSIGHT GENERATION RULES

**Always Calculate Without Being Asked:**
- Growth rates and trends
- Top/bottom performers
- Anomalies and outliers
- Efficiency ratios
- Risk indicators
- Optimization opportunities

**Always Visualize Mentally and Describe:**
- Patterns over time
- Distributions and segments
- Correlations between metrics
- Process bottlenecks
- Geographic patterns

### 9. BUSINESS INTELLIGENCE MINDSET

Think like a Fortune 500 analyst:
- **What's the story in the data?**
- **What should worry the business owner?**
- **Where's the hidden opportunity?**
- **What's about to break?**
- **How can we optimize this?**

### 10. COMMUNICATION STYLE

- **Lead with insights, not raw data**
- **Use business language, not technical jargon**
- **Highlight what matters most**
- **Always suggest next actions**
- **Quantify impact when possible**

## REMEMBER:
You're not a passive query tool - you're an active business intelligence system. When users ask simple questions, deliver comprehensive analysis. When they're vague, make smart assumptions and explore broadly. Your goal is to surprise them with insights they didn't know they needed.

**Every interaction should feel like they have a team of analysts working for them, not just a database query tool.**""",
                    model=model,
                    mcp_servers=[mcp_server],
                )

                # Create a session for this conversation
                session = SQLiteSession(st.session_state.conversation_id)

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
                    yield ("processing", "🤔 Thinking...")
                    await asyncio.sleep(0.5)  # Small delay to ensure UI updates

                    yield ("processing", "🔍 Analyzing your request...")

                    # Create a simple progress tracker
                    start_time = time.time()

                    result = await Runner.run(
                        agent,
                        query,
                        max_turns=100,
                        session=session,  # Use session for conversation history
                    )

                    elapsed = time.time() - start_time
                    if elapsed > 2:
                        yield ("processing", "⚙️ Processing tools...")
                        await asyncio.sleep(0.1)

                    yield ("processing", "📝 Preparing response...")

                    # Extract response
                    if hasattr(result, "final_output"):
                        response = result.final_output
                        # If response is a list of objects, extract text
                        if isinstance(response, list) and response:
                            # Extract text from ResponseOutputText objects
                            text_parts = []
                            for item in response:
                                if hasattr(item, "text"):
                                    text_parts.append(item.text)
                                elif hasattr(item, "content"):
                                    text_parts.append(item.content)
                            response = "\n".join(text_parts) if text_parts else str(response)
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

                    # Return in expected format
                    yield ("final", (response, unique_tools))
                    return

                # Use streaming mode for OpenAI and other models
                logger.info(f"Starting streaming mode with model: {model}")

                try:
                    result = Runner.run_streamed(
                        agent,
                        query,
                        max_turns=40,  # Increased from default to allow more complex interactions
                        session=session,  # Use session for conversation history
                    )

                    # Stream data containers
                    tool_calls = []
                    stream_messages = []
                    final_response = ""
                    chunk_buffer = ""

                    # Immediately yield that we're starting
                    yield ("processing", "🔄 Processing your request...")

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
                                        # Yield tool call event for real-time display
                                        yield ("tool", tool_info)
                            elif event.name == "message_output_created":
                                # Message content
                                if hasattr(event.item, "raw_item") and hasattr(
                                    event.item.raw_item, "content"
                                ):
                                    content = event.item.raw_item.content
                                    stream_messages.append(content)
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
                                                        "arguments": tool_call.function.arguments
                                                        or "",
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
                    elif stream_messages:
                        # Extract text from message if it's an object
                        last_msg = stream_messages[-1]
                        if isinstance(last_msg, list) and last_msg:
                            # Extract text from ResponseOutputText objects
                            text_parts = []
                            for item in last_msg:
                                if hasattr(item, "text"):
                                    text_parts.append(item.text)
                                elif hasattr(item, "content"):
                                    text_parts.append(item.content)
                            final_response = "\n".join(text_parts) if text_parts else str(last_msg)
                        elif hasattr(last_msg, "text"):
                            final_response = last_msg.text
                        elif hasattr(last_msg, "content"):
                            final_response = last_msg.content
                        else:
                            final_response = str(last_msg)
                    else:
                        final_response = "Response completed."

                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    # Fallback to non-streaming mode on error
                    yield ("processing", "⚠️ Streaming failed, using standard mode...")
                    result = await Runner.run(
                        agent,
                        query,
                        max_turns=40,
                        session=session,  # Use session for conversation history
                    )

                    # Extract response from non-streaming result
                    if hasattr(result, "final_output"):
                        final_response = result.final_output
                        # If response is a list of objects, extract text
                        if isinstance(final_response, list) and final_response:
                            # Extract text from ResponseOutputText objects
                            text_parts = []
                            for item in final_response:
                                if hasattr(item, "text"):
                                    text_parts.append(item.text)
                                elif hasattr(item, "content"):
                                    text_parts.append(item.content)
                            final_response = (
                                "\n".join(text_parts) if text_parts else str(final_response)
                            )
                    elif hasattr(result, "messages") and result.messages:
                        final_response = result.messages[-1].content
                    else:
                        final_response = str(result)

                    # Extract tool calls from non-streaming result
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

    # Return the async generator
    return _run_query_streaming()


async def get_available_tools():
    """Get list of available MCP tools"""
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        server_params = StdioServerParameters(
            command="uv", args=["run", "odoo-mcp-server"], env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                return [(tool.name, tool.description) for tool in tools.tools]
    except Exception as e:
        return [("Error", f"Could not load tools: {str(e)}")]


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

    # Clear conversation button
    st.divider()
    if st.button("🔄 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_id = str(uuid.uuid4())
        st.rerun()

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

        # Containers for streaming data (using dict for mutable access in closure)
        stream_data = {"response_text": "", "tool_calls": [], "displayed_tools": set()}

        # Process streaming response
        async def process_stream():
            st.session_state.streaming_active = True
            try:
                async for event_type, data in run_query_streaming(prompt):
                    if event_type == "processing":
                        # Show processing indicator
                        message_placeholder.markdown(f"{data}")

                    elif event_type == "tool":
                        # Real-time tool display
                        tool_key = f"{data['name']}:{data['arguments']}"
                        if tool_key not in stream_data["displayed_tools"]:
                            stream_data["displayed_tools"].add(tool_key)
                            with tool_placeholder:
                                # Create a unique key for each tool call
                                with st.expander(f"🛠️ Using: {data['name']}", expanded=False):
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
                        # Only show if not already displayed during streaming
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

            finally:
                st.session_state.streaming_active = False

            return stream_data["response_text"], stream_data["tool_calls"]

        try:
            # Run the async stream processing using asyncio.run
            # This is the recommended way for Streamlit apps
            response, tool_calls = asyncio.run(process_stream())

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
