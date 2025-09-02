---
description: Refresh (aka create or update) the memory bank files to reflect the current state of the codebase.
---

# Agent `refresh_memory_bank`

## Resources

@aidd/memory-bank

@aidd/templates/memory-bank/ARCHITECTURE.md
@aidd/templates/memory-bank/CODEBASE_STRUCTURE.md
@aidd/templates/memory-bank/DECISIONS.md
@aidd/templates/memory-bank/DESIGN.md
@aidd/templates/memory-bank/INFRASTRUCTURE.md
@aidd/templates/memory-bank/PROJECT_BRIEF.md

## Steps

- If memory bank files already exist, update it with newer information
- If memory bank files do not exist, create them from scratch

### How to create memory bank

Those are templates, some information may not be filled, some other not existing in template must be added:

1. Acknowledge $ARGUMENTS if any
2. Read all template
3. Acknowledge that those are only templates, feel free to add or remove sections as needed
4. For each template: Spawn a new task agent to analyze codebase and fill its own template (in parallel)

## Rules

- NEVER DUPLICATION ANY INFORMATION IN MULTIPLE FILES.
- Templates follow clear separation of concerns.
- For config files (e.g. `package.json`, API schema etc...), please include relative based path using "@" (do not surrounded path with backticks).
- SUPER SHORT explicit and concise bullet points.
- Mention code using backticks.
