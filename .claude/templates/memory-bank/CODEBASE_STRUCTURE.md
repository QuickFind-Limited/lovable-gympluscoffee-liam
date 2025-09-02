# CODEBASE_STRUCTURE.md

<!--
IMPORTANT: THOSE ARE RULES FOR AI, DO NOT USE THOSE INTO FILLED TEMPLATE.

- FOCUS: Code organization, naming conventions, module structure
- EXCLUDE: Infrastructure details, deployment info, tool configurations
- EXAMPLES: PascalCase for components, Feature-based folders, Import/export patterns
- NEVER INCLUDE: Infrastructure setup, framework selection, business rationales
-->

## Naming Conventions

- **Files**: [pattern - camelCase/kebab-case/PascalCase]
- **Components**: [pattern - PascalCase]
- **Functions**: [pattern - camelCase]
- **Variables**: [pattern - camelCase]
- **Constants**: [pattern - UPPER_CASE]
- **Types/Interfaces**: [pattern - PascalCase]

## Module Dependencies

- **Module Graph**: [Description of how modules relate]
- **Circular Dependencies**: [Any known circular dependencies and resolution]
- **Import/Export Strategy**: [How modules are imported/exported]

## Code Organization Principles

- **Separation of Concerns**: [How different concerns are separated]
- **Domain-Driven Design**: [How business domains are organized]
- **Feature-Based Structure**: [How features are organized]

### Frontend

{Structure organization for frontend codebase}

```
/src
  /components     # UI components
  /services       # Business logic
  /models         # Data models
  /utils          # Helper functions
  /hooks          # Custom hooks
  /types          # Type definitions
  /constants      # Application constants
  /config         # Configuration files
  /assets         # Static assets
  /tests          # Test files
```

## Configuration

- **Config Files Location**: [Where configuration files are stored]
  - Application config paths
  - Build config paths
  - Test config paths

## Code Quality

- **Linting**: [Linter configuration and rules]
- **Formatting**: [Code formatter configuration]
- **Type Checking**: [TypeScript configuration if applicable]
- **Pre-commit Hooks**: [Git hooks configuration]
