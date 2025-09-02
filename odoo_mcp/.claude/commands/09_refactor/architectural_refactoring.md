# Agent `architectural_refactoring` $ARGUMENTS

Goal: Analyze and refactor feature-based architecture through collaborative planning and systematic implementation
Outcome: Optimized and standardized feature architecture with improved consistency and maintainability

## Ressources

@aidd/rules/frontend/feature-architecture.md
@aidd/rules/frontend/refactoring-patterns.md
@aidd/rules/shared/collaboration-guidelines.md

## Steps

```mermaid
flowchart TD
    A["/architectural_refactoring"] --> B["User provides target scope"]
    B --> C["analyze_current_architecture"]

    C --> D["AI proposes improvement analysis"]
    D --> E{User validates analysis?}
    E -->|No| F["User provides feedback"]
    F --> D
    E -->|Yes| G["AI suggests refactoring options"]

    G --> H["present_refactoring_options"]
    H --> I{User selects approach?}
    I -->|Change| J["User requests modifications"]
    J --> G
    I -->|Accept| K["collaborative_planning"]

    K --> L["AI challenges user decisions"]
    L --> M["User provides rationale"]
    M --> N{Agreement reached?}
    N -->|No| L
    N -->|Yes| O["generate_refactoring_plan"]

    O --> P["validate_plan_feasibility"]
    P --> Q{Plan validated?}
    Q -->|No| R["revise_plan"]
    R --> O
    Q -->|Yes| S["execute_refactoring"]

    S --> T["verify_implementation"]
    T --> U["User approval"]
```
