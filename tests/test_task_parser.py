"""
Tests for task_parser module
"""

import pytest
import tempfile
import os
from pathlib import Path
from task_runner.task_parser import TaskParser, Task


class TestTaskParser:
    """Test cases for TaskParser"""

    @pytest.fixture
    def temp_tasks_dir(self):
        """Create a temporary directory for tasks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_task_file(self, temp_tasks_dir):
        """Create a sample task file"""
        content = """---
id: T-001
title: "Test Task"
status: pending
priority: high
dependencies: []
---

## Descripción
This is a test task.

## Criterios de Aceptación
- [ ] Criterion 1
- [ ] Criterion 2

## Tests Unitarios
```bash
pytest tests/
```
"""
        task_file = temp_tasks_dir / "T-001.md"
        task_file.write_text(content, encoding="utf-8")
        return task_file

    def test_parse_task_file(self, sample_task_file):
        """Test parsing a single task file"""
        parser = TaskParser(sample_task_file.parent)
        tasks = parser.parse_all_tasks()
        
        assert len(tasks) == 1
        task = tasks[0]
        assert task.id == "T-001"
        assert task.title == "Test Task"
        assert task.status == "pending"
        assert task.priority == "high"
        assert task.description == "This is a test task."
        assert len(task.acceptance_criteria) == 2
        assert "Criterion 1" in task.acceptance_criteria[0]
        assert len(task.unit_tests) == 1

    def test_parse_task_with_dependencies(self, temp_tasks_dir):
        """Test parsing task with dependencies"""
        content = """---
id: T-002
title: "Dependent Task"
status: pending
priority: medium
dependencies: [T-001]
---

## Descripción
A task that depends on T-001.
"""
        task_file = temp_tasks_dir / "T-002.md"
        task_file.write_text(content, encoding="utf-8")
        
        parser = TaskParser(temp_tasks_dir)
        tasks = parser.parse_all_tasks()
        
        assert len(tasks) == 1
        assert tasks[0].dependencies == ["T-001"]

    def test_parse_multiple_tasks(self, temp_tasks_dir):
        """Test parsing multiple task files"""
        for i in range(1, 4):
            content = f"""---
id: T-{i:03d}
title: "Task {i}"
status: pending
priority: medium
dependencies: []
---

## Descripción
Task number {i}.
"""
            (temp_tasks_dir / f"T-{i:03d}.md").write_text(content, encoding="utf-8")
        
        parser = TaskParser(temp_tasks_dir)
        tasks = parser.parse_all_tasks()
        
        assert len(tasks) == 3
        assert [t.id for t in tasks] == ["T-001", "T-002", "T-003"]

    def test_update_task_status(self, temp_tasks_dir):
        """Test updating task status"""
        content = """---
id: T-001
title: "Test Task"
status: pending
priority: high
dependencies: []
---

## Descripción
Test task.
"""
        task_file = temp_tasks_dir / "T-001.md"
        task_file.write_text(content, encoding="utf-8")
        
        parser = TaskParser(temp_tasks_dir)
        tasks = parser.parse_all_tasks()
        task = tasks[0]
        
        parser.update_task_status(task, "completed")
        
        updated_content = task_file.read_text(encoding="utf-8")
        assert "status: completed" in updated_content

    def test_empty_tasks_directory(self, temp_tasks_dir):
        """Test parsing empty directory"""
        parser = TaskParser(temp_tasks_dir)
        tasks = parser.parse_all_tasks()
        
        assert len(tasks) == 0


class TestTaskModel:
    """Test cases for Task dataclass"""

    def test_task_defaults(self):
        """Test task default values"""
        task = Task(id="T-001", title="Test")
        
        assert task.status == "pending"
        assert task.priority == "medium"
        assert task.dependencies == []
        assert task.description == ""
        assert task.acceptance_criteria == []
        assert task.unit_tests == []

    def test_task_with_all_fields(self):
        """Test task with all fields"""
        task = Task(
            id="T-001",
            title="Full Task",
            status="completed",
            priority="high",
            dependencies=["T-002"],
            description="A description",
            acceptance_criteria=[" criterion"],
            unit_tests=["npm test"]
        )
        
        assert task.id == "T-001"
        assert task.status == "completed"
        assert task.priority == "high"
        assert task.dependencies == ["T-002"]
