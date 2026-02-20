# AI Task Orchestrator - Instructional Context

## Project Overview
**AI Task Orchestrator** is an autonomous development system that allows AI agents to implement, test, and validate software tasks defined in Markdown files. It uses a **Tool Calling Agent** architecture (v2.0) to interact with the project codebase, execute terminal commands, and perform visual validation via Chrome DevTools Protocol (CDP).

### Main Technologies
- **Language:** Python 3.10+
- **LLM APIs:** OpenRouter or Zen API (OpenCode) using `openai` SDK.
- **Task Management:** Markdown files with YAML frontmatter.
- **Automation/Testing:** Chrome DevTools Protocol (CDP) for browser automation and screenshots.
- **CLI Framework:** Click.

### Architecture
1.  **Task Parser:** Reads `.md` files in the `tasks/` directory, extracting YAML metadata, acceptance criteria, and test configurations.
2.  **Task Engine:** Orchestrates execution, manages dependencies, and handles retries.
3.  **ToolCallingAgent:** The core AI agent that runs in a loop, calling tools to read/write files and execute terminal commands until the task is complete.
4.  **CDP Wrapper & Visual Validator:** Automates browser checks and uses vision-capable LLMs to verify the UI against screenshots.
5.  **Report Generator:** Produces execution summaries in JSON, HTML, and Markdown.

---

## Building and Running

### Prerequisites
- Python 3.10+
- Chrome/Chromium running with remote debugging:
  `chrome.exe --remote-debugging-port=9222`
- An API Key for OpenRouter or Zen API in a `.env` file.

### Key Commands
- **Initialize a project:** `python run.py init <project_name>`
- **Create a task:** `python run.py create-task "Task Title" [--priority high|medium|low]`
- **Run the orchestrator:** `python run.py run [--task T-XXX] [--parallel]`
- **Check status:** `python run.py status`
- **Generate reports:** `python run.py report`
- **Retry failed tasks:** `python run.py retry`
- **Reset state:** `python run.py reset`

---

## Development Conventions

### Task Definition (`tasks/*.md`)
Tasks must follow the markdown template with YAML frontmatter:
```yaml
---
id: T-001
title: "Implement Login"
status: pending
priority: high
dependencies: []
---
## Description
...
## Criterios de Aceptación
- [ ] Feature X
## Tests Unitarios
```bash
npm test
\```
## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:3000
```
```

### Agent Loop (V2)
The system operates using an iterative "Agent Loop" in `ToolCallingAgent`. It maintains a message history and can call several native tools:
- `execute_terminal_command`: Runs bash/powershell commands.
- `read_file`: Reads project files.
- `write_file`: Modifies/creates files.
- `finish_task`: Signals task completion.

### Environment & Safety
- **Credentials:** API keys must be stored in `.env`. Never commit `.env` files.
- **Terminal:** On Windows, use **PowerShell** or **CMD**. Avoid MINGW64/Git Bash due to session compatibility issues with some LLM CLI tools.
- **Encodings:** Use `$env:PYTHONIOENCODING = "utf-8"` in PowerShell if encountering Unicode issues.

---

## Directory Structure
- `task_runner/`: Core logic (Engine, Parser, Agent, CDP, Validator).
- `tasks/`: Task definitions for the current project.
- `templates/`: Templates for tasks and project context.
- `reports/`: Generated execution reports.
- `screenshots/`: Visual validation artifacts.
- `logs/`: Orchestrator and agent execution logs.
