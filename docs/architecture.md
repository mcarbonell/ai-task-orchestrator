# AI Task Orchestrator - Architecture

## Overview

The AI Task Orchestrator is a system designed to fully automate software development using AI agents. It uses a task orchestration approach where each task is an atomic unit of work that can be executed, validated, and completed autonomously.

## Design Principles

1. **Autonomy**: The system must operate without human intervention during task execution
2. **Atomicity**: Tasks are independent and complete in themselves
3. **Automatic Validation**: Each task includes its own validation criteria
4. **Intelligent Retries**: If a task fails, it's retried with error feedback
5. **Observability**: The entire process is traced and reported

## Component Architecture

### 1. Task Engine (Orchestrator)

The core of the system. Responsible for:
- Managing task state (state machine)
- Coordinating sequential or parallel execution
- Handling dependencies between tasks
- Managing retries with backoff
- Generating consolidated reports

**Execution Flow:**
```
Load Tasks → Check Dependencies → Execute Task → Validate → 
    ↓
Completed / Retry / Failed
```

### 2. Task Parser

Converts markdown files into domain objects:
- Extracts YAML metadata (frontmatter)
- Parses acceptance criteria
- Extracts test commands
- Parses CDP configuration (navigation, screenshots, eval)

**Task Format:**
```yaml
---
id: T-001
title: "Name"
status: pending
priority: high
dependencies: [T-002]
---
```

### 3. Tool Calling Agent

100% native API-based agent:
- Builds enriched prompts with context
- Makes tool_calls to the API
- Captures output and errors
- Support for visual validation (sending screenshots)

**Integration:**
```python
client.chat.completions.create(
    model="minimax-m2.5-free",
    tools=[...],
    messages=[...]
)
```

### 4. CDP Wrapper

Chrome DevTools Protocol integration:
- Abstracts commands from cdp_controller.py
- Manages WebSocket connection
- Methods: navigate, screenshot, evaluate, click
- Collects performance metrics

### 5. Visual Validator

Uses AI with vision capability to validate UI:
- Sends screenshots to OpenCode
- Analyzes visual elements
- Detects layout errors
- Verifies responsive design

### 6. Report Generator

Generates execution artifacts:
- JSON: Structured data
- HTML: Visual dashboard
- Markdown: Documentation

## Data Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Task Files  │────→│ Task Parser  │────→│ Task Engine  │
│  (.md)      │     │              │     │              │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                     ┌───────────────────────────┼───────────┐
                     ▼                           ▼           ▼
             ┌──────────────┐          ┌──────────────┐  ┌──────────────┐
             │Tool Calling  │          │ CDP Wrapper  │  │   Validator  │
             │   Agent     │          └──────┬───────┘  └──────┬───────┘
             └──────┬───────┘                 │                 │
                    │                         ▼                 ▼
                    ▼                 ┌──────────────┐  ┌──────────────┐
             ┌──────────────┐        │    Chrome    │  │  Visual AI   │
             │   AI Agent   │        │    (CDP)     │  │   Analysis   │
             │  (OpenCode)  │        └──────────────┘  └──────────────┘
             └──────────────┘
```

## Task States

```
    ┌────────────┐
    │  Pending   │
    └─────┬──────┘
          │
          ▼
   ┌────────────┐
   │In Progress │
   └─────┬──────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────┐
│Validating│  │  Failed  │
└───┬───┘  └────┬───┘
    │            │
    ▼            │ (retry < max)
┌───────┐       │
│Completed│◄────┘
└───────┘
```

## Design Patterns

### 1. Command Pattern
Each operation (navigate, screenshot, eval) is a command with parameters.

### 2. Strategy Pattern
Different validation strategies: unit tests, E2E, visual.

### 3. Template Method
Task execution follows a defined but extensible flow.

### 4. Observer Pattern
Logging and reports observe engine events.

## Scalability Considerations

- **Parallelization**: Independent tasks can run in parallel
- **External State**: State saved to files (not in memory)
- **Idempotency**: Re-running a task produces the same result
- **Recovery**: If the process fails, it can resume from saved state

## Security

- No secrets stored in task files
- Environment variables for sensitive configuration
- CDP sandbox (isolated Chrome)
- Time limits on executions

## Future Extensions

1. **Plugin System**: Allow custom plugins for validations
2. **Multi-Agent**: Different agents for different task types
3. **Auto-Planning**: AI generates tasks from requirements
4. **Git Integration**: Auto-commit when completing tasks
5. **CI/CD Integration**: GitHub Actions, GitLab CI, etc.
