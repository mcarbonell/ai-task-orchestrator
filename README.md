# AI Task Orchestrator 🤖

> **Autonomous Management for AI Agents.**
>
> Define tasks in markdown files and let a team of ToolCalling agents implement, test in terminal, validate, and even verify the UI visually. Supports OpenRouter and Zen API (OpenCode).
>
> **Philosophy:** Works like Git. Initialize a hidden `.ai-tasks` directory in your project and manage everything from there.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Quick Demo

```bash
# 1. Install (only once)
git clone https://github.com/mcarbonell/ai-task-orchestrator.git
cd ai-task-orchestrator
pip install -r requirements.txt
cp .env.example .env # Configure your API keys

# 2. Initialize in YOUR project (like git init)
cd /path/to/your/code
python /path/to/orchestrator/cli.py init

# 3. Run (the AI will read project-context.md and tasks in .ai-tasks/tasks)
python /path/to/orchestrator/cli.py run
```

## ✨ What is this?

**AI Task Orchestrator** is a system that allows AIs to work **completely autonomously** on development projects, keeping all task context within the project's own repository.

### Git-Style Workflow

The orchestrator automatically searches for a `.ai-tasks` directory by traversing up the folder tree. This allows running it from any subdirectory of the project.

```
My-Project/
├── .ai-tasks/             <-- Managed by the Orchestrator
│   ├── config.yaml
│   ├── tasks/             <-- Your tasks (.md)
│   ├── logs/
│   ├── reports/
│   └── task-status.json
├── project-context.md     <-- Global context for the AI (Editable)
├── src/
└── package.json
```

## 📦 Installation

### Prerequisites
- **Python 3.10+**
- **Chrome/Chromium** - With remote debugging enabled (`--remote-debugging-port=9222`)

### Configuration
1. Clone the repo and install dependencies.
2. Configure the `.env` file in the orchestrator root with your `ZEN_API_KEY` or `OPENROUTER_API_KEY`.

## 🚀 Usage

### Initialize Project
Inside your code folder:
```bash
python path/to/cli.py init
```
This will create the `.ai-tasks` directory and a `project-context.md` file in your project root.

### Task Management
Tasks are stored in `.ai-tasks/tasks/`. You can create them manually or using:
```bash
python path/to/cli.py create-task "Implement Header"
```

### Running and Status
```bash
# See what needs to be done
python path/to/cli.py status

# Launch the AI agent
python path/to/cli.py run

# If a task fails, fix and retry
python path/to/cli.py retry
```

## 🔧 Per-Project Configuration

Each project has its own `config.yaml` inside `.ai-tasks/`. You can adjust the AI model, retries, or performance thresholds specifically for that repo.

```yaml
opencode:
  model: minimax-m2.5-free # Recommended model for Zen API
  provider: zen
```

## 🏗️ V2 Architecture

- **Auto-Discovery:** Searches for the `.ai-tasks` project root by going up.
- **ToolCallingAgent:** 100% native API-based agency loop.
- **CDP Integration:** Real browser validation.
- **Portable:** All orchestrator state lives in the repo, enabling task sharing across the team.

## 📝 Task Format (.md)
```markdown
---
id: T-001
title: "Title"
status: pending
priority: high
dependencies: []
---
## Description
...
## Acceptance Criteria
- [ ] ...
## Unit Tests
```bash
npm test
\```
```

---
**Ready to delegate real development to AI?** 🚀
