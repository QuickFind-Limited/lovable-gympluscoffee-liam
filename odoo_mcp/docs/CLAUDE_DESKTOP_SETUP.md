# Setting Up Odoo MCP Server with Claude Desktop

This guide walks you through setting up the Odoo MCP server to work with Claude Desktop.

## Prerequisites

- Claude Desktop installed on your system
- Odoo MCP server installed and configured
- Odoo instance with API access

## Step 1: Locate Claude Desktop Configuration

Find your Claude Desktop configuration file based on your operating system:

### macOS
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

### Windows
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Linux
```bash
~/.config/Claude/claude_desktop_config.json
```

## Step 2: Configure the MCP Server

### Basic Configuration

Edit the configuration file and add the Odoo MCP server:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uv",
      "args": ["run", "odoo-mcp-server"],
      "cwd": "/absolute/path/to/odoo-mcp-server",
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DATABASE": "your-database",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"  # pragma: allowlist secret
      }
    }
  }
}
```

### Multiple Odoo Instances

To connect to multiple Odoo instances:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uv",
      "args": ["run", "odoo-mcp-server"],
      "cwd": "/absolute/path/to/odoo-mcp-server",
      "env": {
        "ODOO_URL": "https://dev.odoo.com",
        "ODOO_DATABASE": "dev",
        "ODOO_USERNAME": "dev-user",
        "ODOO_PASSWORD": "dev-pass",  # pragma: allowlist secret

        "ODOO_INSTANCE_PRODUCTION_URL": "https://prod.odoo.com",
        "ODOO_INSTANCE_PRODUCTION_DATABASE": "prod",
        "ODOO_INSTANCE_PRODUCTION_USERNAME": "prod-user",
        "ODOO_INSTANCE_PRODUCTION_PASSWORD": "prod-pass",  # pragma: allowlist secret

        "ODOO_INSTANCE_STAGING_URL": "https://staging.odoo.com",
        "ODOO_INSTANCE_STAGING_DATABASE": "staging",
        "ODOO_INSTANCE_STAGING_USERNAME": "staging-user",
        "ODOO_INSTANCE_STAGING_PASSWORD": "staging-pass"  # pragma: allowlist secret
      }
    }
  }
}
```

### Using Python Instead of uv

If you don't have uv installed, use Python directly:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "odoo_mcp"],
      "cwd": "/absolute/path/to/odoo-mcp-server",
      "env": {
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DATABASE": "your-database",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"  # pragma: allowlist secret
      }
    }
  }
}
```

## Step 3: Path Configuration

### Finding the Correct Path

#### macOS/Linux
```bash
# Find the absolute path
cd /path/to/odoo-mcp-server
pwd
# Copy this path to use in cwd
```

#### Windows
```cmd
# Find the absolute path
cd C:\path\to\odoo-mcp-server
echo %cd%
# Copy this path to use in cwd
```

### Example Paths

**macOS**: `/Users/username/projects/odoo-mcp-server`
**Windows**: `C:\\Users\\username\\projects\\odoo-mcp-server` (note the double backslashes)
**Linux**: `/home/username/projects/odoo-mcp-server`

## Step 4: Restart Claude Desktop

After saving the configuration:

1. Completely quit Claude Desktop (not just close the window)
2. Start Claude Desktop again
3. The MCP server should now be available

## Step 5: Verify the Connection

### Test Basic Connection

Ask Claude:
> "What MCP tools do you have available?"

Expected response should include Odoo tools like:
- odoo_create
- odoo_read
- odoo_search
- etc.

### Test Odoo Connection

Ask Claude:
> "Can you connect to Odoo and count how many contacts we have?"

This will test if the server can authenticate and query Odoo.

## Troubleshooting

### Server Not Appearing

1. **Check the path**: Ensure `cwd` points to the correct directory
2. **Check the command**: Verify `uv` or `python` is in your PATH
3. **Check logs**: Look in Claude Desktop logs for errors

### Authentication Errors

1. **Verify credentials**: Test with `test_connection_simple.py`
2. **Check API access**: Ensure your Odoo user has API access enabled
3. **Check URL format**: Should include https:// and no trailing slash

### Permission Errors

**macOS/Linux**: Ensure the script is executable:
```bash
chmod +x /path/to/odoo-mcp-server/src/odoo_mcp/__main__.py
```

### View Claude Desktop Logs

**macOS**: `~/Library/Logs/Claude/`
**Windows**: `%LOCALAPPDATA%\Claude\logs\`
**Linux**: `~/.local/share/Claude/logs/`

## Advanced Configuration

### Custom Python Environment

If using a virtual environment:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "odoo_mcp"],
      "cwd": "/path/to/odoo-mcp-server",
      "env": {
        "PYTHONPATH": "/path/to/odoo-mcp-server/src",
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DATABASE": "your-database",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"  # pragma: allowlist secret
      }
    }
  }
}
```

### Debug Mode

Enable debug logging:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uv",
      "args": ["run", "odoo-mcp-server"],
      "cwd": "/path/to/odoo-mcp-server",
      "env": {
        "MCP_LOG_LEVEL": "DEBUG",
        "ODOO_URL": "https://your-instance.odoo.com",
        "ODOO_DATABASE": "your-database",
        "ODOO_USERNAME": "your-username",
        "ODOO_PASSWORD": "your-password"  # pragma: allowlist secret
      }
    }
  }
}
```

## Security Best Practices

1. **Don't share config files**: They contain sensitive credentials
2. **Use environment variables**: Consider using system environment variables instead of hardcoding
3. **Restrict file permissions**:
   ```bash
   chmod 600 ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```
4. **Use API keys**: When available, use API keys instead of passwords

## Example Interactions

Once configured, you can ask Claude things like:

### Basic Operations
- "Show me all draft sales orders"
- "Create a new contact named John Doe"
- "Update product ABC123's price to $99.99"

### Reports and Analysis
- "Analyze our current inventory levels"
- "Generate a sales report for this month"
- "Show me products that need reordering"

### Multi-Instance Operations
- "On the production instance, count total customers"
- "Compare sales between dev and production"

## Next Steps

1. Review the [Usage Guide](./USAGE_GUIDE.md) for all available commands
2. Check the [API Reference](./API_REFERENCE.md) for detailed parameter information
3. See [Troubleshooting](./TROUBLESHOOTING.md) for common issues

---

For more help, see the main [README](../README.md) or open an issue on GitHub.
