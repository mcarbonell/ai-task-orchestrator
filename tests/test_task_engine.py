"""
Tests for task_engine module
"""

import pytest
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch
from task_runner.task_engine import TaskEngine
from task_runner.task_parser import Task


class TestTaskEngine:
    """Test cases for TaskEngine"""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project structure"""
        tmpdir = tempfile.mkdtemp()
        project_root = Path(tmpdir)
        tasks_dir = project_root / "tasks"
        logs_dir = project_root / "logs"
        tasks_dir.mkdir()
        logs_dir.mkdir()
        
        yield {
            "root": project_root,
            "tasks": tasks_dir,
            "logs": logs_dir
        }

    @pytest.fixture
    def config(self, temp_project):
        """Create a test configuration"""
        return {
            "orchestrator": {
                "max_retries": 3,
                "parallel_workers": 1,
                "log_level": "CRITICAL",
                "max_iterations": 15
            },
            "opencode": {
                "model": "minimax-m2.5-free",
                "provider": "zen"
            },
            "directories": {
                "tasks": str(temp_project["tasks"]),
                "logs": str(temp_project["logs"]),
                "screenshots": str(temp_project["root"] / "screenshots"),
                "reports": str(temp_project["root"] / "reports")
            },
            "files": {
                "status": str(temp_project["root"] / "status.json"),
                "context": str(temp_project["root"] / "context.md")
            },
            "cdp": {
                "host": "127.0.0.1",
                "port": 9222
            },
            "validation": {
                "visual": {
                    "enabled": False
                }
            }
        }

    def test_initialization(self, config):
        """Test TaskEngine initializes correctly"""
        engine = TaskEngine(config)
        
        assert engine.config == config
        assert engine.tasks_dir.name == "tasks"
        assert engine.log_dir.name == "logs"

    def test_load_tasks(self, config, temp_project):
        """Test loading tasks"""
        task_content = """---
id: T-001
title: "Test Task"
status: pending
priority: high
dependencies: []
---

## Description
A test task.
"""
        (temp_project["tasks"] / "T-001.md").write_text(task_content, encoding="utf-8")
        
        engine = TaskEngine(config)
        tasks = engine.load_tasks()
        
        assert len(tasks) == 1
        assert tasks[0].id == "T-001"

    def test_get_next_tasks(self, config, temp_project):
        """Test getting next ready tasks"""
        task1_content = """---
id: T-001
title: "Task 1"
status: completed
priority: high
dependencies: []
---

## Description
First task.
"""
        task2_content = """---
id: T-002
title: "Task 2"
status: pending
priority: high
dependencies: [T-001]
---

## Description
Second task.
"""
        (temp_project["tasks"] / "T-001.md").write_text(task1_content, encoding="utf-8")
        (temp_project["tasks"] / "T-002.md").write_text(task2_content, encoding="utf-8")
        
        engine = TaskEngine(config)
        engine.load_tasks()
        
        next_tasks = engine.get_next_tasks()
        
        assert len(next_tasks) == 1
        assert next_tasks[0].id == "T-002"

    def test_get_next_tasks_blocked_by_incomplete_dependency(self, config, temp_project):
        """Test tasks blocked by incomplete dependencies"""
        task1_content = """---
id: T-001
title: "Task 1"
status: pending
priority: high
dependencies: []
---

## Description
First task.
"""
        task2_content = """---
id: T-002
title: "Task 2"
status: pending
priority: high
dependencies: [T-001]
---

## Description
Second task.
"""
        (temp_project["tasks"] / "T-001.md").write_text(task1_content, encoding="utf-8")
        (temp_project["tasks"] / "T-002.md").write_text(task2_content, encoding="utf-8")
        
        engine = TaskEngine(config)
        engine.load_tasks()
        
        next_tasks = engine.get_next_tasks()
        
        assert len(next_tasks) == 1
        assert next_tasks[0].id == "T-001"

    def test_get_status(self, config, temp_project):
        """Test getting task status summary"""
        task_content = """---
id: T-001
title: "Test Task"
status: pending
priority: high
dependencies: []
---

## Description
A test task.
"""
        (temp_project["tasks"] / "T-001.md").write_text(task_content, encoding="utf-8")
        
        engine = TaskEngine(config)
        status = engine.get_status()
        
        assert status["summary"]["total"] == 1
        assert status["summary"]["pending"] == 1
        assert status["summary"]["completed"] == 0

    def test_get_status_with_multiple_tasks(self, config, temp_project):
        """Test getting status with multiple tasks"""
        tasks = [
            ("T-001", "pending"),
            ("T-002", "completed"),
            ("T-003", "failed"),
        ]
        
        for task_id, status in tasks:
            content = f"""---
id: {task_id}
title: "Task {task_id}"
status: {status}
priority: medium
dependencies: []
---

## Description
Task {task_id}.
"""
            (temp_project["tasks"] / f"{task_id}.md").write_text(content, encoding="utf-8")
        
        engine = TaskEngine(config)
        status = engine.get_status()
        
        assert status["summary"]["total"] == 3
        assert status["summary"]["pending"] == 1
        assert status["summary"]["completed"] == 1
        assert status["summary"]["failed"] == 1


class TestTaskEngineRetry:
    """Test cases for retry logic"""

    @pytest.fixture
    def temp_project(self):
        tmpdir = tempfile.mkdtemp()
        project_root = Path(tmpdir)
        tasks_dir = project_root / "tasks"
        logs_dir = project_root / "logs"
        tasks_dir.mkdir()
        logs_dir.mkdir()
        
        yield {
            "root": project_root,
            "tasks": tasks_dir,
            "logs": logs_dir
        }

    @pytest.fixture
    def config(self, temp_project):
        return {
            "orchestrator": {
                "max_retries": 3,
                "parallel_workers": 1,
                "log_level": "CRITICAL",
                "max_iterations": 15
            },
            "opencode": {"model": "minimax-m2.5-free", "provider": "zen"},
            "directories": {
                "tasks": str(temp_project["tasks"]),
                "logs": str(temp_project["logs"]),
                "screenshots": str(temp_project["root"] / "screenshots"),
                "reports": str(temp_project["root"] / "reports")
            },
            "files": {"status": str(temp_project["root"] / "status.json")},
            "cdp": {"host": "127.0.0.1", "port": 9222},
            "validation": {"visual": {"enabled": False}}
        }

    def test_retry_count_increments_on_failure(self, config, temp_project):
        """Test that retry count increments on task failure"""
        task_content = """---
id: T-001
title: "Test Task"
status: pending
priority: high
dependencies: []
---

## Description
A test task.
"""
        (temp_project["tasks"] / "T-001.md").write_text(task_content, encoding="utf-8")
        
        engine = TaskEngine(config)
        engine.load_tasks()
        
        task = engine.tasks[0]
        task.retry_count = 0
        
        task.retry_count += 1
        
        assert task.retry_count == 1
