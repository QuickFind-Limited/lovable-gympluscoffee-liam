# Odoo MCP Server - Troubleshooting Guide

## Table of Contents
1. [Common Issues](#common-issues)
2. [Connection Problems](#connection-problems)
3. [Authentication Errors](#authentication-errors)
4. [MCP Server Issues](#mcp-server-issues)
5. [Odoo API Errors](#odoo-api-errors)
6. [Performance Issues](#performance-issues)
7. [Claude Desktop Integration](#claude-desktop-integration)
8. [Debugging Tools](#debugging-tools)
9. [FAQ](#faq)

## Common Issues

### Server Not Starting

**Symptom:** The MCP server fails to start or immediately exits.

**Solutions:**

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **Verify installation:**
   ```bash
   # Reinstall dependencies
   uv pip install -e .
   # or
   pip install -e .
   ```

3. **Check for port conflicts (if using HTTP mode):**
   ```bash
   lsof -i :3000  # Check if port is in use
   ```

4. **Enable debug logging:**
   ```bash
   MCP_LOG_LEVEL=DEBUG uv run odoo-mcp-server
   ```

### Import Errors

**Symptom:** `ModuleNotFoundError` or `ImportError`

**Solutions:**

1. **Ensure you're in the project directory:**
   ```bash
   cd /path/to/odoo-mcp-server
   ```

2. **Install in development mode:**
   ```bash
   uv pip install -e .
   ```

3. **Check PYTHONPATH:**
   ```bash
   export PYTHONPATH=/path/to/odoo-mcp-server/src:$PYTHONPATH
   ```

## Connection Problems

### Cannot Connect to Odoo

**Symptom:** `ConnectionError` or timeout errors

**Diagnostic Steps:**

1. **Test the URL directly:**
   ```bash
   curl -I https://your-instance.odoo.com
   ```

2. **Check network connectivity:**
   ```bash
   ping your-instance.odoo.com
   ```

3. **Verify the URL format:**
   - ✅ Correct: `https://mycompany.odoo.com`
   - ❌ Wrong: `https://mycompany.odoo.com/` (trailing slash)
   - ❌ Wrong: `mycompany.odoo.com` (missing protocol)

**Solutions:**

1. **For self-hosted Odoo:**
   - Ensure XML-RPC is enabled
   - Check firewall rules
   - Verify port 8069 (or custom port) is accessible

2. **For Odoo Online:**
   - Ensure your subscription is active
   - Check if API access is enabled for your plan

3. **For proxy environments:**
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   export HTTPS_PROXY=http://proxy.company.com:8080
   ```

### SSL Certificate Errors

**Symptom:** SSL verification failed

**Solutions:**

1. **For self-signed certificates (development only):**
   ```python
   # In connection.py, add to session creation:
   ssl_context = ssl.create_default_context()
   ssl_context.check_hostname = False
   ssl_context.verify_mode = ssl.CERT_NONE
   ```

2. **Update certificates:**
   ```bash
   # macOS
   brew install ca-certificates

   # Ubuntu/Debian
   sudo apt-get update && sudo apt-get install ca-certificates
   ```

## Authentication Errors

### Invalid Credentials

**Symptom:** Authentication failed error

**Diagnostic Steps:**

1. **Test credentials manually:**
   ```bash
   uv run python test_connection_simple.py
   ```

2. **Verify environment variables:**
   ```bash
   echo $ODOO_URL
   echo $ODOO_DATABASE
   echo $ODOO_USERNAME
   ```

**Solutions:**

1. **For Odoo Online users using SSO:**
   - Set a password in Odoo (My Profile → Account Security)
   - Use the password, not SSO credentials

2. **Check user permissions:**
   - Log into Odoo web interface
   - Go to Settings → Users
   - Verify "API Access" is enabled

3. **Database name issues:**
   - For Odoo Online: Usually your subdomain (e.g., "mycompany")
   - For self-hosted: Check with your admin

### Session Timeout

**Symptom:** Authentication works initially but fails after some time

**Solutions:**

1. **Implement session refresh:**
   ```python
   # The connection pool handles this automatically
   # Ensure you're using the latest version
   ```

2. **Increase session timeout in Odoo:**
   - Settings → General Settings → Security
   - Increase "Inactivity Period"

## MCP Server Issues

### Server Not Appearing in Claude Desktop

**Symptom:** MCP tools not available in Claude Desktop

**Diagnostic Steps:**

1. **Check Claude Desktop logs:**
   - macOS: `~/Library/Logs/Claude/`
   - Windows: `%LOCALAPPDATA%\Claude\logs\`
   - Linux: `~/.local/share/Claude/logs/`

2. **Verify configuration syntax:**
   ```bash
   # Validate JSON
   python -m json.tool < claude_desktop_config.json
   ```

**Solutions:**

1. **Path issues:**
   ```json
   {
     "mcpServers": {
       "odoo": {
         "command": "/usr/bin/python3",  // Use absolute path
         "args": ["-m", "odoo_mcp"],
         "cwd": "/absolute/path/to/odoo-mcp-server"  // Must be absolute
       }
     }
   }
   ```

2. **Permission issues:**
   ```bash
   # Make scripts executable
   chmod +x /path/to/odoo-mcp-server/src/odoo_mcp/__main__.py
   ```

3. **Environment variables not passing:**
   ```json
   {
     "env": {
       "PYTHONPATH": "/path/to/odoo-mcp-server/src",
       "ODOO_URL": "value",  // Don't use $VAR syntax
       "PATH": "/usr/local/bin:/usr/bin:/bin"  // Include system PATH
     }
   }
   ```

### Tools Not Working

**Symptom:** Tools appear but return errors when used

**Solutions:**

1. **Check server is actually running:**
   - Look for Python process in Claude Desktop logs
   - Try running server standalone first

2. **Verify all dependencies:**
   ```bash
   uv pip list | grep -E "fastmcp|aiohttp|pydantic"
   ```

## Odoo API Errors

### Field Does Not Exist

**Symptom:** `Field 'field_name' does not exist on model`

**Solutions:**

1. **Check available fields:**
   ```python
   # Use odoo_fields_get tool
   fields = await odoo_fields_get(model="res.partner")
   print(fields.keys())
   ```

2. **Version differences:**
   - Odoo 15: Uses `customer` boolean
   - Odoo 16+: Uses `customer_rank` integer

### Access Denied to Model

**Symptom:** `AccessError: User has no access to model`

**Solutions:**

1. **Check user groups:**
   - In Odoo: Settings → Users → Select user
   - Verify groups like "Sales", "Inventory"

2. **Grant necessary permissions:**
   - Add user to required groups
   - Or create custom access rights

### Method Does Not Exist

**Symptom:** `Method 'method_name' does not exist`

**Solutions:**

1. **Verify method availability:**
   ```python
   # Check model methods
   model_info = await odoo_execute(
       model="ir.model",
       method="search_read",
       args=[[["model", "=", "sale.order"]]],
       kwargs={"fields": ["name", "model"]}
   )
   ```

2. **Use correct method names:**
   - `create` not `create_record`
   - `write` not `update`
   - `unlink` not `delete`

## Performance Issues

### Slow Response Times

**Diagnostic Steps:**

1. **Enable timing logs:**
   ```bash
   MCP_LOG_LEVEL=DEBUG uv run odoo-mcp-server 2>&1 | grep -E "time|duration"
   ```

2. **Check Odoo server load:**
   - Monitor Odoo logs
   - Check database performance

**Solutions:**

1. **Optimize queries:**
   ```python
   # Bad: Multiple calls
   for id in ids:
       record = await odoo_read(model="res.partner", ids=[id])

   # Good: Single call
   records = await odoo_read(model="res.partner", ids=ids)
   ```

2. **Use field filtering:**
   ```python
   # Only request needed fields
   await odoo_search_read(
       model="product.product",
       domain=[],
       fields=["name", "list_price"],  # Not all fields
       limit=100
   )
   ```

3. **Implement pagination:**
   ```python
   # For large datasets
   offset = 0
   limit = 100
   while True:
       records = await odoo_search_read(
           model="res.partner",
           domain=[],
           limit=limit,
           offset=offset
       )
       if not records:
           break
       offset += limit
   ```

### Memory Issues

**Symptom:** High memory usage or out of memory errors

**Solutions:**

1. **Limit batch sizes:**
   ```python
   # Process in chunks
   chunk_size = 500
   for i in range(0, len(large_list), chunk_size):
       chunk = large_list[i:i + chunk_size]
       # Process chunk
   ```

2. **Clear connection pool:**
   ```python
   # Periodically clear unused connections
   await connection_pool.cleanup()
   ```

## Claude Desktop Integration

### Configuration Not Loading

**Symptom:** Changes to config file not taking effect

**Solutions:**

1. **Completely restart Claude Desktop:**
   - Quit from system tray/menu bar
   - Not just close window

2. **Check file permissions:**
   ```bash
   ls -la ~/Library/Application\ Support/Claude/
   # Should be readable by your user
   ```

3. **Validate JSON syntax:**
   ```bash
   # Common issues: trailing commas, quotes
   jq . claude_desktop_config.json
   ```

### Server Crashes in Claude Desktop

**Symptom:** Server starts but crashes when used

**Solutions:**

1. **Check memory limits:**
   ```json
   {
     "env": {
       "PYTHONUNBUFFERED": "1",  // See output immediately
       "MCP_LOG_LEVEL": "DEBUG"   // More logging
     }
   }
   ```

2. **Use wrapper script:**
   ```bash
   #!/bin/bash
   # wrapper.sh
   cd /path/to/odoo-mcp-server
   exec python -m odoo_mcp 2>&1 | tee -a /tmp/odoo-mcp.log
   ```

## Debugging Tools

### Test Scripts

1. **Basic connection test:**
   ```bash
   uv run python test_connection_simple.py
   ```

2. **Full MCP client test:**
   ```bash
   uv run python test_mcp_client.py
   ```

3. **Interactive debugging:**
   ```python
   # debug_odoo.py
   import asyncio
   from odoo_mcp.connection import OdooAsyncClient

   async def debug():
       client = OdooAsyncClient(
           url="https://your-instance.odoo.com",
           database="your-db",
           username="your-user",
           password="your-pass"  # pragma: allowlist secret
       )
       await client.authenticate()
       # Add debugging code here

   asyncio.run(debug())
   ```

### Logging

1. **Enable verbose logging:**
   ```bash
   export MCP_LOG_LEVEL=DEBUG
   export PYTHONUNBUFFERED=1
   ```

2. **Log to file:**
   ```bash
   uv run odoo-mcp-server 2>&1 | tee odoo-mcp.log
   ```

3. **Filter logs:**
   ```bash
   # Only errors
   grep ERROR odoo-mcp.log

   # Connection issues
   grep -E "connect|auth|session" odoo-mcp.log
   ```

### Network Debugging

1. **Capture traffic (development only):**
   ```bash
   # Using mitmproxy
   mitmproxy -p 8080
   export HTTPS_PROXY=http://localhost:8080
   ```

2. **Test raw XML-RPC:**
   ```python
   import xmlrpc.client

   url = "https://your-instance.odoo.com"
   db = "your-database"
   username = "your-username"
   password = "your-password"  # pragma: allowlist secret

   common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
   uid = common.authenticate(db, username, password, {})
   print(f"Authenticated with UID: {uid}")
   ```

## FAQ

### Q: Can I use API keys instead of passwords?

**A:** Currently, Odoo's XML-RPC interface only supports username/password authentication. API keys are not supported by the standard Odoo API.

### Q: Why am I getting "database does not exist" errors?

**A:** For Odoo Online, the database name is usually your subdomain (e.g., for `mycompany.odoo.com`, use `mycompany`). For self-hosted, ask your administrator.

### Q: How do I handle custom fields?

**A:** Custom fields (starting with `x_`) work the same as standard fields. Use `odoo_fields_get` to discover them:
```python
fields = await odoo_fields_get(model="res.partner")
custom_fields = {k: v for k, v in fields.items() if k.startswith("x_")}
```

### Q: Can I use this with Odoo.sh?

**A:** Yes, Odoo.sh instances work the same as self-hosted. Use the provided URL and database name from your Odoo.sh dashboard.

### Q: How do I handle multi-company setups?

**A:** The MCP server uses the user's default company. To work with multiple companies, you need different users or use the `company_id` context:
```python
await odoo_execute(
    model="res.partner",
    method="create",
    args=[{"name": "Test"}],
    kwargs={"context": {"company_id": 2}}
)
```

### Q: What's the rate limit for API calls?

**A:** Odoo doesn't have strict rate limits, but:
- Be respectful of server resources
- Use batch operations when possible
- Implement exponential backoff for retries
- Consider caching frequently accessed data

---

For additional help:
1. Check the [API Reference](./API_REFERENCE.md)
2. Review the [Usage Guide](./USAGE_GUIDE.md)
3. Enable debug logging and check the logs
4. Test with the provided test scripts
5. Open an issue on GitHub with detailed error information
