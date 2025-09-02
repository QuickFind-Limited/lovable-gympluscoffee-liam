# Odoo MCP Server

A Model Context Protocol (MCP) server that provides secure access to Odoo ERP systems, enabling AI agents to interact with Odoo data and operations.

> **🚀 Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for step-by-step instructions to get running in 5 minutes!

## Features

- 🚀 Full async implementation with aiohttp
- 🔐 Secure authentication with Odoo instances
- 📊 Complete CRUD operations for all Odoo models
- 🔍 Advanced search and filtering capabilities
- 🏗️ Type-safe Python 3.13+ implementation
- 🧪 Comprehensive test coverage with real Odoo testing
- 📦 FastMCP framework for optimal performance
- 🎨 Streamlit UI for interactive Odoo operations
- 🤖 AI-powered assistant with conversation history

## Installation

```bash
# Using uv (recommended)
uv pip install odoo-mcp-server

# Using pip
pip install odoo-mcp-server
```

## Quick Start

### 1. Set up environment variables

Create a `.env` file with your Odoo credentials:

```env
ODOO_URL=https://your-instance.odoo.com
ODOO_DATABASE=your-database
ODOO_USERNAME=your-username
ODOO_PASSWORD=your-password
```

### 2. Run the server

```bash
# Run the MCP server
uv run odoo-mcp-server

# Or with Python
python -m odoo_mcp
```

### 3. Connect with an MCP client

The server runs in stdio mode and can be used with any MCP client like Claude Desktop.

## Streamlit UI Application

The project includes a production-ready Streamlit interface for interacting with your Odoo system through an AI assistant.

### Running the Streamlit App

1. Navigate to the `odoo-mcp-agent` directory:
   ```bash
   cd odoo-mcp-agent
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

### Features

- **AI Assistant**: Powered by OpenAI or Claude for intelligent Odoo operations
- **Conversation History**: Maintains context across interactions using SQLiteSession
- **Real-time Streaming**: See responses as they're generated
- **Tool Visibility**: Track which Odoo operations are being performed
- **Example Queries**: Quick-start templates for common operations
- **Clear Conversation**: Reset chat history when needed

### Configuration

The Streamlit app uses the same `.env` file as the MCP server. Additionally, you can configure:

```env
# AI Provider Configuration
USE_OPENAI=true  # Set to false to use Claude
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-claude-key  # If using Claude
```

## Available Tools

### CRUD Operations

- **odoo_create** - Create new records
- **odoo_read** - Read existing records
- **odoo_update** - Update records
- **odoo_delete** - Delete records

### Search Operations

- **odoo_search** - Search for record IDs
- **odoo_search_read** - Search and read in one operation
- **odoo_search_count** - Count matching records

### Metadata Operations

- **odoo_fields_get** - Get model field definitions
- **odoo_execute** - Execute any model method

## Usage Examples

### Create a Partner

```python
result = await session.call_tool(
    "odoo_create",
    {
        "instance_id": "default",
        "model": "res.partner",
        "values": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
    }
)
```

### Search for Sales Orders

```python
result = await session.call_tool(
    "odoo_search_read",
    {
        "instance_id": "default",
        "model": "sale.order",
        "domain": [["state", "=", "sale"]],
        "fields": ["name", "partner_id", "amount_total"],
        "limit": 10
    }
)
```

### Update Product Price

```python
result = await session.call_tool(
    "odoo_update",
    {
        "instance_id": "default",
        "model": "product.product",
        "ids": [42],
        "values": {
            "list_price": 99.99
        }
    }
)
```

## Resources

The server also provides MCP resources for browsing Odoo data:

- `odoo://instance` - List available models
- `odoo://instance/model` - List records of a model
- `odoo://instance/model/id` - Get a specific record

## Development

### Prerequisites

- Python 3.13+
- uv package manager
- Access to an Odoo instance with API enabled

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/odoo-mcp-server
cd odoo-mcp-server

# Install dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
uv run pytest
```

### Testing

The project uses real Odoo instance testing (no mocks!):

```bash
# Run all tests
uv run pytest

# Run integration tests only
uv run pytest tests/integration/

# Run with coverage
uv run pytest --cov=src
```

### Code Quality

```bash
# Run linting
uv run ruff check .

# Run type checking
uv run mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Architecture

The server follows a clean architecture pattern:

```
src/odoo_mcp/
├── __init__.py
├── __main__.py        # Entry point
├── server.py          # FastMCP server setup
├── connection.py      # Odoo connection management
├── tools.py           # MCP tool implementations
├── resources.py       # MCP resource handlers
├── types.py           # Type definitions
├── config.py          # Configuration management
└── errors.py          # Custom exceptions
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

1. **MCP server not found**: Ensure you've installed the package with `pip install -e .` in the root directory
2. **Streamlit app connection issues**: Verify that `uv run odoo-mcp-server` works from the command line
3. **Authentication errors**: Double-check your Odoo credentials in the `.env` file
4. **Virtual environment issues**: Make sure to activate the correct virtual environment before running

### Getting Help

- Check the logs in the terminal for detailed error messages
- Ensure all environment variables are properly set
- Verify your Odoo instance has XML-RPC API enabled

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Inspired by the [Model Context Protocol](https://modelcontextprotocol.io/)
- Tested against [Odoo](https://www.odoo.com/) v17+
- UI powered by [Streamlit](https://streamlit.io/)
- AI agents powered by [OpenAI Agents SDK](https://github.com/openai/openai-agents-python)
