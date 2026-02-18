"""
Utils - Utilidades comunes
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Optional


def load_config(config_path: Optional[str] = None) -> Dict:
    """
    Carga configuración desde archivo YAML
    
    Args:
        config_path: Ruta al archivo de config. Si es None, busca config.yaml
    
    Returns:
        Dict con configuración
    """
    if config_path is None:
        # Buscar en ubicaciones comunes
        search_paths = [
            Path("config.yaml"),
            Path("orchestrator-config.yaml"),
            Path.home() / ".config" / "ai-task-orchestrator" / "config.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                config_path = path
                break
    
    if not config_path or not Path(config_path).exists():
        logging.warning("No se encontró archivo de configuración. Usando defaults.")
        return get_default_config()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


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
