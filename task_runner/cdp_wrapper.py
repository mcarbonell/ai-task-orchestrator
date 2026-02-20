"""
CDP Wrapper - Integración con CDP Controller
"""

import subprocess
import json
import logging
import time
from typing import Dict, Optional, List
from pathlib import Path
import urllib.request


class CDPWrapper:
    """Wrapper para CDP Controller"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 9222)
        self.controller_path = config.get("controller_path")
        self.logger = logging.getLogger("CDPWrapper")
        self.page_id: Optional[str] = None
        
        # Auto-detectar controller_path si no está configurado
        if not self.controller_path:
            self._autodetect_controller()
    
    def _autodetect_controller(self):
        """Intenta encontrar cdp_controller.py automáticamente"""
        # Buscar en directorios comunes
        search_paths = [
            Path("cdp_controller.py"),
            Path("../cdp_controller.py"),
            Path("../cdp_controller/src/cdp_controller.py"),
            Path("../../cdp_controller.py"),
            Path.home() / "cdp_controller.py",
        ]
        
        # Buscar en variable de entorno
        import os
        if os.getenv("CDP_CONTROLLER_PATH"):
            search_paths.insert(0, Path(os.getenv("CDP_CONTROLLER_PATH")))
        
        for path in search_paths:
            if path.exists():
                self.controller_path = str(path.absolute())
                self.logger.info(f"✅ CDP Controller encontrado: {self.controller_path}")
                return
        
        self.logger.warning("⚠️  CDP Controller no encontrado. Especifica la ruta en config.yaml")
    
    def is_available(self) -> bool:
        """Verifica si Chrome está ejecutándose con remote debugging"""
        try:
            response = urllib.request.urlopen(
                f"http://{self.host}:{self.port}/json/version",
                timeout=2
            )
            return response.getcode() == 200
        except Exception as e:
            self.logger.error(f"❌ Chrome CDP no disponible: {e}")
            return False
    
    def _run_cdp_command(self, *args) -> Dict:
        """Ejecuta un comando del CDP Controller"""
        if not self.controller_path:
            raise RuntimeError("CDP Controller path no configurado")
        
        cmd = ["python", self.controller_path] + list(args)
        
        self.logger.debug(f"CDP Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8"
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout ejecutando comando CDP"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_page_id(self) -> str:
        """Obtiene el ID de la primera pestaña disponible"""
        if self.page_id:
            return self.page_id
        
        result = self._run_cdp_command("list")
        
        if not result["success"]:
            raise RuntimeError(f"No se pudo obtener lista de pestañas: {result.get('error')}")
        
        # Parsear output para obtener primer ID
        lines = result["output"].strip().split('\n')
        if not lines:
            raise RuntimeError("No hay pestañas disponibles")
        
        # Formato: "1. [ID] Título - URL"
        first_line = lines[0]
        match = first_line.split('[')
        if len(match) < 2:
            raise RuntimeError(f"Formato inesperado: {first_line}")
        
        self.page_id = match[1].split(']')[0]
        self.logger.info(f"📄 Usando página ID: {self.page_id}")
        
        return self.page_id
    
    def navigate(self, url: str):
        """Navega a una URL"""
        self.logger.info(f"🌐 Navegando a: {url}")
        page_id = self._get_page_id()
        
        result = self._run_cdp_command("navigate", page_id, url)
        
        if not result["success"]:
            raise RuntimeError(f"Error navegando: {result.get('error')}")
        
        # Esperar a que cargue
        time.sleep(2)
        self.logger.info("✅ Navegación completada")
    
    def screenshot(self, output_path: str, width: Optional[int] = None, height: Optional[int] = None):
        """Captura un screenshot"""
        self.logger.info(f"📸 Capturando screenshot: {output_path}")
        page_id = self._get_page_id()
        
        # Crear directorio si no existe
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        args = ["screenshot", page_id, output_path]
        
        if width and height:
            args.extend([str(width), str(height)])
            self.logger.info(f"   Viewport: {width}x{height}")
        
        result = self._run_cdp_command(*args)
        
        if not result["success"]:
            raise RuntimeError(f"Error capturando screenshot: {result.get('error')}")
        
        self.logger.info(f"✅ Screenshot guardado: {output_path}")
    
    def evaluate(self, code: str) -> any:
        """Ejecuta JavaScript en la página"""
        self.logger.info(f"⚡ Ejecutando JavaScript: {code[:50]}...")
        page_id = self._get_page_id()
        
        result = self._run_cdp_command("eval", page_id, code)
        
        if not result["success"]:
            raise RuntimeError(f"Error evaluando JS: {result.get('error')}")
        
        # Intentar extraer el resultado
        # El output puede ser complejo, intentamos parsearlo
        output = result["output"]
        
        # Buscar en el output el valor de retorno
        try:
            # Buscar línea con "result":
            for line in output.split('\n'):
                if '"value"' in line:
                    # Extraer valor
                    json_str = output[output.find('{'):output.rfind('}')+1]
                    data = json.loads(json_str)
                    return data.get("result", {}).get("value")
        except:
            pass
        
        return output
    
    def click(self, selector: str):
        """Hace click en un elemento"""
        code = f'document.querySelector("{selector}").click()'
        self.evaluate(code)
    
    def get_console_logs(self) -> List[Dict]:
        """Obtiene logs de la consola"""
        # Nota: Esto requiere implementación en cdp_controller.py
        # Por ahora devolvemos lista vacía
        self.logger.warning("⚠️  get_console_logs no implementado completamente")
        return []
    
    def get_performance_metrics(self) -> Dict:
        """Obtiene métricas de performance"""
        self.logger.info("📊 Obteniendo métricas de performance")
        page_id = self._get_page_id()
        
        # Usar comando performance del CDP Controller
        result = self._run_cdp_command("performance", page_id)
        
        if not result["success"]:
            self.logger.warning("⚠️  No se pudieron obtener métricas de performance")
            return {}
        
        # Parsear output (esto es simplificado, necesitaría parsear mejor)
        metrics = {}
        output = result["output"]
        
        # Buscar líneas con métricas
        for line in output.split('\n'):
            if 'LCP' in line and ':' in line:
                try:
                    value = float(line.split(':')[1].strip().replace('ms', ''))
                    metrics['lcp'] = value
                except:
                    pass
            elif 'CLS' in line and ':' in line:
                try:
                    value = float(line.split(':')[1].strip())
                    metrics['cls'] = value
                except:
                    pass
            elif 'FCP' in line and ':' in line:
                try:
                    value = float(line.split(':')[1].strip().replace('ms', ''))
                    metrics['fcp'] = value
                except:
                    pass
        
        return metrics
