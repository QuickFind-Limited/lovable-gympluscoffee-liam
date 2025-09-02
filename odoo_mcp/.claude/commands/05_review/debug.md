# Agent: `debug`

Goal: Debug an issue in the codebase.

## Steps

### Find bug

1. Summarize the issue with you own words.
2. List action paths (e.g. user clicks button -> calls function in file1 -> updates state in file2...).
3. Find relevant files to find bug in codebase based on issue description.
4. List 3 best potential causes with small description + confidence level.
5. Wait for user validation.

### Propose solution

1. For selected causes, use MCP if necessary.
2. Draw a quick fix plan.
3. Wait for user validation, then apply it.
