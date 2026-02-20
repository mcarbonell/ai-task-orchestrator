"""
Tests for utils module
"""

import pytest
import tempfile
import os
from pathlib import Path
from task_runner.utils import find_project_root, load_config, get_default_config, ensure_directories


class TestFindProjectRoot:
    """Test cases for find_project_root"""

    def test_finds_ai_tasks_dir(self):
        """Test finding .ai-tasks directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            ai_tasks_dir = project_root / ".ai-tasks"
            ai_tasks_dir.mkdir()
            
            result = find_project_root(project_root)
            
            assert result == project_root

    def test_finds_nested_ai_tasks_dir(self):
        """Test finding .ai-tasks in parent directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            ai_tasks_dir = project_root / ".ai-tasks"
            ai_tasks_dir.mkdir()
            
            subdir = project_root / "src" / "utils"
            subdir.mkdir(parents=True)
            
            result = find_project_root(subdir)
            
            assert result == project_root

    def test_returns_none_when_not_found(self):
        """Test returns None when no .ai-tasks found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_project_root(Path(tmpdir))
            
            assert result is None


class TestLoadConfig:
    """Test cases for load_config"""

    def test_loads_existing_config(self):
        """Test loading existing config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_content = """
orchestrator:
  max_retries: 5
opencode:
  model: test-model
"""
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            
            config = load_config(str(config_path))
            
            assert config["orchestrator"]["max_retries"] == 5
            assert config["opencode"]["model"] == "test-model"

    def test_returns_defaults_when_no_config(self):
        """Test returns defaults when no config exists"""
        config = load_config(None)
        
        assert "orchestrator" in config
        assert "opencode" in config

    def test_resolves_relative_paths(self):
        """Test relative paths are resolved correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_content = """
directories:
  tasks: ./tasks
  logs: ./logs
"""
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(config_content)
            
            config = load_config(str(config_path))
            
            assert config["directories"]["tasks"].startswith(str(tmpdir))
            assert config["directories"]["logs"].startswith(str(tmpdir))


class TestGetDefaultConfig:
    """Test cases for get_default_config"""

    def test_returns_default_config(self):
        """Test returns valid default config"""
        config = get_default_config()
        
        assert "orchestrator" in config
        assert "opencode" in config
        assert "cdp" in config
        assert "directories" in config

    def test_default_model_is_minimax(self):
        """Test default model is minimax-m2.5-free"""
        config = get_default_config()
        
        assert config["opencode"]["model"] == "minimax-m2.5-free"

    def test_default_provider_is_zen(self):
        """Test default provider is zen"""
        config = get_default_config()
        
        assert config["opencode"]["provider"] == "zen"


class TestEnsureDirectories:
    """Test cases for ensure_directories"""

    def test_creates_directories(self):
        """Test directories are created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "directories": {
                    "tasks": str(Path(tmpdir) / "tasks"),
                    "logs": str(Path(tmpdir) / "logs"),
                }
            }
            
            ensure_directories(config)
            
            assert (Path(tmpdir) / "tasks").is_dir()
            assert (Path(tmpdir) / "logs").is_dir()

    def test_handles_empty_directories(self):
        """Test handles empty directories config"""
        config = {}
        
        ensure_directories(config)
