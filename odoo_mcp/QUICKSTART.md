# Quick Start Guide - Odoo MCP with Streamlit UI

## Prerequisites

- Python 3.12+
- Git
- An Odoo instance with API access
- OpenAI API key (or Anthropic API key for Claude)

## Step-by-Step Instructions

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/QuickFind-Limited/odoo_mcp.git
cd odoo_mcp

# Install the MCP server package
pip install -e .
```

### 2. Configure Environment

Create a `.env` file in the `odoo-mcp-agent` directory:

```bash
cd odoo-mcp-agent
```

Create `.env` file with:

```env
# Odoo Connection (REQUIRED)
ODOO_URL=https://your-instance.odoo.com/
ODOO_DATABASE=your-database-name
ODOO_USERNAME=your-username@example.com
ODOO_PASSWORD=your-password

# AI Configuration (REQUIRED - choose one)
USE_OPENAI=true
OPENAI_API_KEY=sk-your-openai-key-here

# OR use Claude (set USE_OPENAI=false)
# USE_OPENAI=false
# ANTHROPIC_API_KEY=sk-ant-your-claude-key-here
```

### 3. Install Dependencies

```bash
# Still in odoo-mcp-agent directory
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Verify MCP Server

```bash
# Test that the MCP server is working
uv run odoo-mcp-server --help
```

You should see the FastMCP banner. Press Ctrl+C to exit.

### 5. Run the Streamlit App

```bash
# Make sure you're in odoo-mcp-agent directory with venv activated
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Using the App

1. **Chat Interface**: Type your questions or commands in the chat input
2. **Example Queries**: Click any example in the sidebar to get started
3. **Clear Conversation**: Use the button in the sidebar to reset chat history

### Example Commands

- "List all partners in Odoo"
- "Show me the last 5 sales orders"
- "Create a new contact named John Smith"
- "Search for products with price > 100"
- "Update the phone number for partner ID 7"

## Troubleshooting

### App Won't Start

1. Check virtual environment is activated:
   ```bash
   which python  # Should show .venv/bin/python
   ```

2. Verify all packages are installed:
   ```bash
   pip list | grep -E "(streamlit|openai|agents)"
   ```

3. Check environment variables:
   ```bash
   cat .env  # Make sure all required values are set
   ```

### Connection Errors

1. Test Odoo connection:
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ODOO_URL'))"
   ```

2. Verify MCP server works:
   ```bash
   uv run odoo-mcp-server --help
   ```

### AI Provider Issues

- For OpenAI: Verify your API key at https://platform.openai.com/api-keys
- For Claude: Verify your API key at https://console.anthropic.com/

## Next Steps

- Explore the example queries in the sidebar
- Check `odoo_mcp_examples.md` for more complex operations
- Review the main README.md for detailed documentation

## Need Help?

- Check logs in the terminal for detailed error messages
- Ensure your Odoo instance has XML-RPC API enabled
- Verify all credentials in the `.env` file are correct
