# AI Task Orchestrator - Instructional Context

## Project Overview
**AI Task Orchestrator** is an autonomous development system. It follows a **decentralized, git-like philosophy**, where each project contains its own configuration and task definitions in a hidden `.ai-tasks` directory.

### Key Concepts
- **Project Root Discovery:** The system identifies a project by the presence of a `.ai-tasks` directory.
- **Self-Contained:** Configuration (`config.yaml`), tasks (`tasks/*.md`), logs, and reports reside within `.ai-tasks`.
- **Global Context:** `project-context.md` in the project root provides high-level instructions to the AI agents.

---

## Building and Running

### Project Initialization
To start using the orchestrator in a new or existing repository:
```bash
python cli.py init
```
This creates the `.ai-tasks` structure and `project-context.md`.

### Core Workflow
1. **Define Tasks:** Create `.md` files in `.ai-tasks/tasks/`.
2. **Execute:** Run `python cli.py run`. The system automatically finds the project root.
3. **Retry:** Use `python cli.py retry` for failed tasks.

---

## Development Conventions

### Task Location
All project-specific tasks **MUST** be located in `.ai-tasks/tasks/`.

### Task Definition Template
```yaml
---
id: T-XXX
title: "Task Title"
status: pending
priority: medium
dependencies: []
---
## Descripción
...
## Criterios de Aceptación
- [ ] ...
```

### Agent Environment
- **Provider:** Prefers Zen API (OpenCode) or OpenRouter.
- **Model:** Recommended `minimax-m2.5-free` for stability.
- **OS:** Windows (PowerShell/CMD). Ensure `$env:PYTHONIOENCODING = "utf-8"` is set if encounter Unicode issues during execution.

---

## Directory Structure (Standard Project)
- `.ai-tasks/`
    - `config.yaml`: Local orchestrator settings.
    - `tasks/`: Task definitions.
    - `logs/`: Execution logs.
    - `reports/`: Execution summaries.
    - `task-status.json`: Runtime state.
- `project-context.md`: Project-wide context for the AI agents.
- `[Your Source Code]`: The project being developed.
