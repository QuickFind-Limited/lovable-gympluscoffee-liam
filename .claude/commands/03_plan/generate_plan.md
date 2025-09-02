# Instructions: `generate_plan`

## Goal

Structuring precise coding instructions for the AI developer.

## Ressources

@aidd/memory-bank/ARCHITECTURE.md
@aidd/memory-bank/CODEBASE_STRUCTURE.md
@aidd/memory-bank/DECISIONS.md
@aidd/memory-bank/DESIGN.md
@aidd/memory-bank/INFRASTRUCTURE.md
@aidd/memory-bank/PROJECT_BRIEF.md

## Steps

**IMPORTANT RULE: Explicit user confirmation is required at each step, wait for approval before going to next step.**

Print current step at the beginning of each step.
Use short and concise bullet points, minimal words.

### Step 1: Clarify Intentions

- If conversation is empty: Ask "What is the feature you want to build?"
- Challenge requirements, detect inconsistencies, ambiguities
- Challenge edge cases and error scenarios
- Question user experience expectations
- Map functional requirements clearly
- **WAIT FOR USER APPROVAL** before proceeding

### Step 2: Technical Analysis and Task Planning

- Analyze existing code structure and patterns
- Check dependencies and current implementations
- Identify technical constraints and opportunities
- Determine technical approach and architecture
- Challenge technical choices and implementation methods
- Break down into specific, actionable tasks
- Prioritize by dependencies and complexity
- Group related tasks for efficient execution
- **WAIT FOR USER APPROVAL** before proceeding

### Step 3: Fill Template

- Get current date
- Name: feature name = branch name
- Output to `aidd/tasks/<yyyy_mm_dd>-<branch_name>.md`
- 1 plan per feature, modify if necessary
- Fill @aidd/templates/task.md in english
- **WAIT FOR USER APPROVAL** before proceeding

### Step 4: Confidence Assessment

- Simulate implementation, identify risks
- Evaluate confidence (0-10 scale)
- Ask: "Do you approve this plan? (YES/NO)"
  - If NO → Return to previous steps
  - If YES → Proceed to write plan

### Step 5: Final Review

- Review: inconsistencies, ambiguities, missing details
- Check best practices and propose enhancements
- Verify: completeness, correctness, clarity
- Ask: "Integrate these suggestions? (YES/NO)"
  - If NO → Keep plan as written
  - If YES → Update plan with improvements
