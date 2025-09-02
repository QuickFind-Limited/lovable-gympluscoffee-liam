"""Main entry point for Odoo MCP server."""

import os
import sys
from .server import mcp_server


def main() -> None:
    """Run the MCP server in stdio mode."""
    # Run in stdio mode for MCP protocol
    mcp_server.run()


if __name__ == "__main__":
    main()
