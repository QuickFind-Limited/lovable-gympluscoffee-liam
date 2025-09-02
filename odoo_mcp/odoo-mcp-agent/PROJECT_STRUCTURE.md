# Odoo MCP Agent - Project Structure

## 📁 Files Overview

### Core Application
- **`streamlit_app.py`** - Main Streamlit application with real-time tool display
- **`.env`** - Environment variables (API keys, Odoo credentials)
- **`.env.example`** - Template for environment variables

### Documentation
- **`README.md`** - Main documentation with setup instructions
- **`TOOL_USAGE_DEMO.md`** - Demo of tool usage display feature
- **`PROJECT_STRUCTURE.md`** - This file

### Configuration
- **`mcp_agent.config.yaml`** - MCP server configuration for odoo-mcp-server
- **`pyproject.toml`** - Python project configuration

### Scripts
- **`launch_app.sh`** - Quick launcher for Streamlit app
- **`run.sh`** - Multi-purpose runner script (app, install)

### Dependencies
- **`uv.lock`** - UV package manager lock file

### Hidden Directories
- **`.venv/`** - Python virtual environment
- **`.swarm/`** - Claude Flow swarm data (if using MCP tools)

## 🚀 Quick Start

1. Copy `.env.example` to `.env` and add your credentials
2. Install dependencies: `./run.sh install`
3. Run the app: `streamlit run streamlit_app.py`

## 🧹 Cleanup Performed

Removed:
- Test files (test_*.py)
- Old src/ directory with outdated implementation
- Empty directories (docs/, config/, tests/)
- Cache directories (__pycache__, .ruff_cache)
- Duplicate README files
- Outdated implementation files
