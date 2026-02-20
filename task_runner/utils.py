"""
Utils - Utilidades comunes
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Busca el directorio raíz del proyecto (.ai-tasks) subiendo por el árbol de directorios.
    """
    curr = Path(start_path or Path.cwd()).absolute()
    
    # Límite de seguridad para no subir hasta la raíz del sistema infinitamente
    for _ in range(20):
        if (curr / ".ai-tasks").is_dir():
            return curr
        if curr.parent == curr:
            break
        curr = curr.parent
        
    return None


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Carga configuración desde archivo YAML.
    Si no se pasa config_path, intenta auto-descubrir el proyecto .ai-tasks
    """
    project_root = find_project_root()
    
    if config_path is None:
        if project_root:
            config_path = project_root / ".ai-tasks" / "config.yaml"
        else:
            # Búsqueda fallback
            search_paths = [
                Path("config.yaml"),
                Path("orchestrator-config.yaml"),
                Path(".ai-tasks/config.yaml"),
            ]
            for path in search_paths:
                if path.exists():
                    config_path = path
                    break
    
    if not config_path or not Path(config_path).exists():
        # Si no hay config, pero hay proyecto, intentar usar defaults con rutas al proyecto
        defaults = get_default_config()
        if project_root:
            base = project_root / ".ai-tasks"
            defaults['directories'] = {
                "tasks": str(base / "tasks"),
                "screenshots": str(base / "screenshots"),
                "reports": str(base / "reports"),
                "logs": str(base / "logs")
            }
            defaults['files'] = {
                "status": str(base / "task-status.json"),
                "context": str(project_root / "project-context.md")
            }
        return defaults
    
    config_file = Path(config_path).absolute()
    base_dir = config_file.parent
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Resolver rutas relativas basadas en la ubicación del archivo de configuración
    if 'directories' in config:
        for key, value in config['directories'].items():
            path = Path(value)
            if not path.is_absolute():
                config['directories'][key] = str((base_dir / path).resolve())
                
    if 'files' in config:
        for key, value in config['files'].items():
            path = Path(value)
            if not path.is_absolute():
                config['files'][key] = str((base_dir / path).resolve())
    
    return config


def get_default_config() -> Dict:
    """Retorna configuración por defecto"""
    return {
        "orchestrator": {
            "max_retries": 3,
            "parallel_workers": 1,
            "log_level": "INFO"
        },
        "opencode": {
            "model": "anthropic/claude-3.5-sonnet",
            "agent": "build",
            "timeout": 300
        },
        "cdp": {
            "host": "127.0.0.1",
            "port": 9222
        },
        "directories": {
            "tasks": "./tasks",
            "screenshots": "./screenshots",
            "reports": "./reports",
            "logs": "./logs"
        }
    }


def setup_logging(log_dir: Path, log_level: str = "INFO"):
    """Configura logging"""
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "orchestrator.log"),
            logging.StreamHandler()
        ]
    )


def ensure_directories(config: Dict):
    """Asegura que los directorios necesarios existen"""
    dirs = config.get("directories", {})
    
    for key, path in dirs.items():
        Path(path).mkdir(parents=True, exist_ok=True)
