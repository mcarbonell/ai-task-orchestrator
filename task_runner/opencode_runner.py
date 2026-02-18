"""
OpenCode Runner - Wrapper para invocar OpenCode CLI
Versión simplificada que funciona con sesiones existentes
"""

import subprocess
import json
import logging
from typing import Dict, Optional


class OpenCodeRunner:
    """Wrapper para ejecutar OpenCode CLI"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model = config.get("model", "opencode/kimi-k2.5")
        self.agent = config.get("agent", "build")
        self.timeout = config.get("timeout", 300)
        self.logger = logging.getLogger("OpenCodeRunner")
    
    def run(self, prompt: str, task_id: Optional[str] = None) -> Dict:
        """
        Ejecuta un prompt en OpenCode
        
        NOTA: Requiere que el usuario haya iniciado OpenCode al menos una vez:
        1. Ejecuta: opencode
        2. Cierra con Ctrl+C
        3. Luego este runner funcionará
        """
        self.logger.info(f"Ejecutando OpenCode para tarea {task_id or 'N/A'}")
        
        # Crear un script temporal para ejecutar el comando
        # Usamos --continue que reutiliza la última sesión
        cmd = ["opencode", "run", "--continue"]
        
        if self.model:
            cmd.extend(["--model", self.model])
        
        if self.agent:
            cmd.extend(["--agent", self.agent])
        
        if task_id:
            cmd.extend(["--title", f"Task-{task_id}"])
        
        cmd.append(prompt)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8"
            )
            
            self.logger.info(f"OpenCode completado (exit code: {result.returncode})")
            
            # Verificar si falló por falta de sesión
            if "Session not found" in result.stderr:
                return {
                    "success": False,
                    "error": "No hay sesión de OpenCode iniciada. Por favor ejecuta 'opencode' manualmente una vez primero."
                }
            
            output = result.stdout
            try:
                parsed_output = json.loads(output)
            except json.JSONDecodeError:
                parsed_output = output
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "output": parsed_output,
                "stderr": result.stderr,
                "error": result.stderr if result.returncode != 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Timeout después de {self.timeout} segundos"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "OpenCode CLI no encontrado"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_bash(self, command: str, task_id: Optional[str] = None) -> Dict:
        """Ejecuta un comando bash"""
        self.logger.info(f"Ejecutando comando: {command}")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8"
            )
            
            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "output": result.stdout,
                "stderr": result.stderr,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e)
            }
