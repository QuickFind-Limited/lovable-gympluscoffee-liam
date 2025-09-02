<!---
Notes for developer ONLY:
- Use Claude to validate your mermaid schema in an artefact
-->

# Instructions `generate_commands`

Aims to generate or modify commands.

- Can be an existing command
- Orchestration commands are the onces with orchestration logic
- Instructions are the agent one, focus on single behavior, goal and outcome
- Write files in English
- Claude command files are stored in `aidd/commands/`

## Command generation flow

- `agent` are snake_case commands
- Actions are regular mermaid (e.g. `["Review existing command"]`)

```mermaid
flowchart TD
    A["/generate_commands"] --> B["1. Ask user what command is about"]

    B --> C["2. Check for existing command"]
    C --> D{Command exists?}

    D -->|Yes| E["Ask if existing command is correct"]
    D -->|No| F["Launch creation flow"]

    E --> G{Use existing?}
    G -->|Yes| H["Review existing command"]
    G -->|No| F

    F --> I["3. Ask about sub-agents"]
    I --> J{Sub-agents needed?}

    J -->|Yes| K["Plan orchestrator + instructions"]
    J -->|No| L["Plan single file approach"]

    K --> M["4. Generate full plan with big steps"]
    L --> M

    M --> N["Present plan to user"]
    N --> O{User validation?}

    O -->|Approved| P["5. Write command file(s)"]
    O -->|Changes needed| Q["Modify plan based on feedback"]

    Q --> N
    P --> R["Command generation complete"]
    H --> R
```

## Command files (Orchestrators)

Orchestrate a flow, bind to others commands, launch parallel tasks...

Template:
@aidd/templates/orchestration.md

## Instruction files

Define behavior, provide guidance, and ensure clarity in command execution.

Template:
@aidd/templates/instruction.md
