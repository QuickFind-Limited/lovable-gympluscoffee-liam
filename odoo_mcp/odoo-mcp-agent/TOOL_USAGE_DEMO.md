# Tool Usage Display Demo

The Streamlit app displays MCP tools as they are being used!

## How It Works

1. **For OpenAI Models**: Real-time streaming mode
   - Uses `run_streamed` method to receive events as they happen
   - Tools appear instantly as they're called
   - Live updates with expanded view

2. **For Claude (Anthropic)**: Post-completion display
   - Due to compatibility limitations, uses non-streaming mode
   - Tools are shown after the response completes
   - All tools displayed at once with collapsible views

3. **Tool Types**: Common MCP tools you'll see:
   - `odoo_search_simple` - To search for records
   - `odoo_read` - To read record details
   - `odoo_fields_get` - To get field information
   - `odoo_create`, `odoo_update`, `odoo_delete` - For data modifications

## Example

When you ask "List all partners in Odoo", you'll see tools appear in real-time:

**First** (appears immediately):
```
🛠️ Using: odoo_search_simple ▼
{
  "instance_id": "default",
  "model": "res.partner",
  "field": "id",
  "operator": ">",
  "value": 0,
  "limit": 10
}
```

**Then** (appears after search completes):
```
🛠️ Using: odoo_read ▼
{
  "instance_id": "default", 
  "model": "res.partner",
  "ids": [1, 3, 46, 47, 48],
  "fields": ["id", "name", "email", "phone"]
}
```

**Finally**: The complete response appears with the partner list

## Features

- **Real-Time Feedback**: See tools as they execute, not after completion
- **Transparency**: Watch the AI's decision-making process unfold
- **Debugging**: Identify issues as they happen
- **Learning**: Understand the sequence and timing of operations
- **History**: All tool usage preserved in chat history

## Testing

1. Run the Streamlit app:
   ```bash
   streamlit run streamlit_app.py
   ```

2. Ask any Odoo-related question

3. Look for the "🛠️ Tools Used" expander below the response

4. Click to expand and see the tool details!

This feature works with both OpenAI and Anthropic Claude models.