"""
Task Engine - Orquestador principal del sistema
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .task_parser import TaskParser, Task
from .opencode_runner import OpenCodeRunner
from .cdp_wrapper import CDPWrapper
from .visual_validator import VisualValidator
from .report_generator import ReportGenerator


class TaskEngine:
    """Orquestador principal de tareas"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.tasks_dir = Path(config.get("directories", {}).get("tasks", "./tasks"))
        self.status_file = Path(config.get("files", {}).get("status", "./task-status.json"))
        self.log_dir = Path(config.get("directories", {}).get("logs", "./logs"))
        
        # Asegurar directorios existen
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, config.get("orchestrator", {}).get("log_level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / "orchestrator.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("TaskEngine")
        
        # Inicializar componentes
        self.parser = TaskParser(self.tasks_dir)
        self.opencode = OpenCodeRunner(config.get("opencode", {}))
        self.cdp = CDPWrapper(config.get("cdp", {}))
        self.visual_validator = VisualValidator(config.get("validation", {}).get("visual", {}), config.get("opencode", {}))
        self.report_generator = ReportGenerator(config.get("directories", {}).get("reports", "./reports"))
        
        # Estado de ejecución
        self.tasks: List[Task] = []
        self.execution_log: List[Dict] = []
    
    def load_tasks(self) -> List[Task]:
        """Carga todas las tareas desde archivos"""
        self.logger.info(f"Cargando tareas desde {self.tasks_dir}")
        self.tasks = self.parser.parse_all_tasks()
        self.logger.info(f"{len(self.tasks)} tareas cargadas")
        return self.tasks
    
    def get_next_tasks(self) -> List[Task]:
        """Obtiene las siguientes tareas listas para ejecutar"""
        ready_tasks = []
        
        for task in self.tasks:
            if task.status != "pending":
                continue
            
            # Verificar dependencias
            deps_satisfied = all(
                any(t.id == dep and t.status == "completed" for t in self.tasks)
                for dep in task.dependencies
            )
            
            if deps_satisfied:
                ready_tasks.append(task)
        
        return ready_tasks
    
    def run(self, task_id: Optional[str] = None, parallel: bool = False):
        """Ejecuta el orchestrator"""
        self.logger.info("🚀 Iniciando AI Task Orchestrator")
        
        # Cargar tareas
        self.load_tasks()
        
        if task_id:
            # Ejecutar tarea específica
            task = next((t for t in self.tasks if t.id == task_id), None)
            if not task:
                self.logger.error(f"❌ Tarea {task_id} no encontrada")
                return
            self._execute_task(task)
        else:
            # Ejecutar todas las tareas pendientes
            self._run_all_tasks(parallel)
        
        # Generar reporte
        self.report_generator.generate(self.tasks, self.execution_log)
        
        # Guardar estado
        self._save_status()
    
    def _run_all_tasks(self, parallel: bool = False):
        """Ejecuta todas las tareas pendientes"""
        max_workers = self.config.get("orchestrator", {}).get("parallel_workers", 1)
        
        if parallel and max_workers > 1:
            self._run_parallel(max_workers)
        else:
            self._run_sequential()
    
    def _run_sequential(self):
        """Ejecuta tareas secuencialmente"""
        while True:
            ready_tasks = self.get_next_tasks()
            
            if not ready_tasks:
                # Verificar si quedan tareas pendientes bloqueadas
                pending_tasks = [t for t in self.tasks if t.status == "pending"]
                if pending_tasks:
                    self.logger.warning(f"⚠️  {len(pending_tasks)} tareas bloqueadas por dependencias")
                    for t in pending_tasks:
                        self.logger.warning(f"   - {t.id}: depende de {t.dependencies}")
                break
            
            # Ejecutar primera tarea disponible
            task = ready_tasks[0]
            success = self._execute_task(task)
            
            if not success:
                self.logger.warning(f"⚠️  Tarea {task.id} falló, continuando con siguientes...")
    
    def _run_parallel(self, max_workers: int):
        """Ejecuta tareas en paralelo donde sea posible"""
        self.logger.info(f"⚡ Ejecutando en paralelo con {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            completed_tasks = set()
            
            while True:
                # Obtener tareas listas
                ready_tasks = [
                    t for t in self.get_next_tasks()
                    if t.id not in completed_tasks and t.id not in futures.values()
                ]
                
                if not ready_tasks and not futures:
                    break
                
                # Enviar tareas a ejecutar
                for task in ready_tasks[:max_workers - len(futures)]:
                    future = executor.submit(self._execute_task, task)
                    futures[future] = task.id
                
                # Esperar a que alguna termine
                done_futures = [f for f in futures.keys() if f.done()]
                
                for future in done_futures:
                    task_id = futures.pop(future)
                    completed_tasks.add(task_id)
                    
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"❌ Error en tarea {task_id}: {e}")
    
    def _execute_task(self, task: Task) -> bool:
        """Ejecuta una tarea individual completa"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"📋 Ejecutando tarea: {task.id} - {task.title}")
        self.logger.info(f"{'='*60}")
        
        task.status = "in_progress"
        task.started_at = datetime.now()
        self.parser.update_task_status(task, "in_progress")
        
        execution_record = {
            "task_id": task.id,
            "started_at": task.started_at.isoformat(),
            "steps": []
        }
        
        max_retries = self.config.get("orchestrator", {}).get("max_retries", 3)
        
        for attempt in range(max_retries):
            self.logger.info(f"\n🔄 Intento {attempt + 1}/{max_retries}")
            
            try:
                # 1. Ejecutar implementación con OpenCode
                self.logger.info("🤖 Invocando agente de IA...")
                implementation_result = self._run_implementation(task, attempt)
                
                if not implementation_result["success"]:
                    if attempt < max_retries - 1:
                        self.logger.warning("⚠️  Implementación falló, reintentando...")
                        continue
                    else:
                        raise Exception(f"Implementación falló después de {max_retries} intentos")
                
                # 2. Ejecutar tests unitarios
                self.logger.info("🧪 Ejecutando tests unitarios...")
                unit_test_result = self._run_unit_tests(task)
                execution_record["steps"].append({
                    "step": "unit_tests",
                    "success": unit_test_result["success"],
                    "details": unit_test_result
                })
                
                if not unit_test_result["success"]:
                    if attempt < max_retries - 1:
                        self.logger.warning("⚠️  Tests unitarios fallaron, reintentando...")
                        continue
                    else:
                        raise Exception("Tests unitarios fallaron")
                
                # 3. Ejecutar tests E2E con CDP
                self.logger.info("🌐 Ejecutando tests E2E con CDP...")
                e2e_result = self._run_e2e_tests(task)
                execution_record["steps"].append({
                    "step": "e2e_tests",
                    "success": e2e_result["success"],
                    "details": e2e_result
                })
                
                if not e2e_result["success"]:
                    if attempt < max_retries - 1:
                        self.logger.warning("⚠️  Tests E2E fallaron, reintentando...")
                        continue
                    else:
                        raise Exception("Tests E2E fallaron")
                
                # 4. Validar visualmente con IA
                if self.config.get("validation", {}).get("visual", {}).get("enabled", True):
                    self.logger.info("👁️  Validando visualmente con IA...")
                    visual_result = self._validate_visual(task, e2e_result.get("screenshots", []))
                    execution_record["steps"].append({
                        "step": "visual_validation",
                        "success": visual_result["success"],
                        "details": visual_result
                    })
                    
                    if not visual_result["success"]:
                        if attempt < max_retries - 1:
                            self.logger.warning("⚠️  Validación visual falló, reintentando...")
                            continue
                        else:
                            raise Exception("Validación visual falló")
                
                # ¡Éxito!
                task.status = "completed"
                task.completed_at = datetime.now()
                task.artifacts = e2e_result.get("screenshots", [])
                self.parser.update_task_status(task, "completed")
                
                execution_record["completed_at"] = task.completed_at.isoformat()
                execution_record["success"] = True
                self.execution_log.append(execution_record)
                
                self.logger.info(f"✅ Tarea {task.id} completada exitosamente!")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Error en intento {attempt + 1}: {e}")
                task.retry_count += 1
                
                if attempt == max_retries - 1:
                    # Último intento falló
                    task.status = "failed"
                    task.error_message = str(e)
                    self.parser.update_task_status(task, "failed", str(e))
                    
                    execution_record["completed_at"] = datetime.now().isoformat()
                    execution_record["success"] = False
                    execution_record["error"] = str(e)
                    self.execution_log.append(execution_record)
                    
                    self.logger.error(f"❌ Tarea {task.id} falló después de {max_retries} intentos")
                    return False
        
        return False
    
    def _run_implementation(self, task: Task, attempt: int) -> Dict:
        """Ejecuta la implementación con OpenCode"""
        # Preparar prompt con contexto
        prompt = self._build_implementation_prompt(task, attempt)
        
        # Ejecutar OpenCode
        result = self.opencode.run(prompt, task_id=task.id)
        
        return {
            "success": result.get("success", False),
            "output": result.get("output", ""),
            "error": result.get("error", None)
        }
    
    def _build_implementation_prompt(self, task: Task, attempt: int) -> str:
        """Construye el prompt para OpenCode"""
        prompt_parts = [
            f"TASK ID: {task.id}",
            f"TITLE: {task.title}",
            "",
            "## Descripción",
            task.description,
            "",
            "## Criterios de Aceptación",
        ]
        
        for criterion in task.acceptance_criteria:
            prompt_parts.append(f"- {criterion}")
        
        if task.unit_tests:
            prompt_parts.extend([
                "",
                "## Tests Unitarios a Implementar",
            ])
            for test in task.unit_tests:
                prompt_parts.append(f"```bash\n{test}\n```")
        
        if attempt > 0 and task.error_message:
            prompt_parts.extend([
                "",
                "## ⚠️ ERROR PREVIO (por favor corrige)",
                task.error_message,
            ])
        
        prompt_parts.extend([
            "",
            "## Instrucciones",
            "1. Implementa la funcionalidad solicitada",
            "2. Asegúrate de que pase todos los criterios de aceptación",
            "3. Implementa los tests unitarios",
            "4. Ejecuta los tests para verificar que pasan",
            "5. NO implementes funcionalidad adicional fuera del scope",
            "",
            "Después de implementar, ejecuta automáticamente los tests unitarios.",
        ])
        
        return "\n".join(prompt_parts)
    
    def _run_unit_tests(self, task: Task) -> Dict:
        """Ejecuta tests unitarios"""
        if not task.unit_tests:
            return {"success": True, "message": "No hay tests unitarios definidos"}
        
        results = []
        for test_cmd in task.unit_tests:
            result = self.opencode.run_bash(test_cmd, task_id=task.id)
            results.append({
                "command": test_cmd,
                "success": result.get("exit_code", 1) == 0,
                "output": result.get("output", "")
            })
        
        all_passed = all(r["success"] for r in results)
        
        return {
            "success": all_passed,
            "tests": results
        }
    
    def _run_e2e_tests(self, task: Task) -> Dict:
        """Ejecuta tests E2E con CDP"""
        if not task.e2e_tests.steps:
            return {"success": True, "message": "No hay tests E2E definidos", "screenshots": []}
        
        # Asegurar CDP está disponible
        if not self.cdp.is_available():
            return {
                "success": False,
                "error": "CDP Controller no disponible. Asegúrate de que Chrome esté ejecutándose con --remote-debugging-port=9222"
            }
        
        # Ejecutar steps
        screenshots = []
        console_errors = []
        performance_metrics = {}
        
        try:
            for step in task.e2e_tests.steps:
                self.logger.info(f"  - Ejecutando: {step.action}")
                
                if step.action == "navigate":
                    url = step.params.get("url") or step.params.get("value")
                    self.cdp.navigate(url)
                
                elif step.action == "screenshot":
                    filename = step.params.get("filename") or step.params.get("value")
                    width = step.params.get("width")
                    height = step.params.get("height")
                    
                    screenshot_path = self._get_screenshot_path(task.id, filename)
                    self.cdp.screenshot(screenshot_path, width=width, height=height)
                    screenshots.append(str(screenshot_path))
                
                elif step.action == "eval":
                    code = step.params.get("code") or step.params.get("value")
                    result = self.cdp.evaluate(code)
                    
                    # Verificar expectativa si existe
                    if "expect" in step.params:
                        expected = step.params["expect"]
                        if result != expected:
                            return {
                                "success": False,
                                "error": f"Eval result mismatch. Expected: {expected}, Got: {result}",
                                "screenshots": screenshots
                            }
                
                elif step.action == "wait":
                    ms = step.params.get("milliseconds", 1000)
                    import time
                    time.sleep(ms / 1000)
                
                elif step.action == "click":
                    selector = step.params.get("selector") or step.params.get("value")
                    self.cdp.click(selector)
            
            # Verificar console errors
            if task.e2e_tests.console_checks.fail_on_error:
                console_logs = self.cdp.get_console_logs()
                errors = [log for log in console_logs if log.get("level") == "error"]
                
                if errors:
                    return {
                        "success": False,
                        "error": f"Console errors detected: {errors}",
                        "screenshots": screenshots
                    }
            
            # Verificar métricas de performance
            if any([task.e2e_tests.performance_thresholds.lcp,
                   task.e2e_tests.performance_thresholds.cls,
                   task.e2e_tests.performance_thresholds.fcp]):
                metrics = self.cdp.get_performance_metrics()
                
                if task.e2e_tests.performance_thresholds.lcp:
                    if metrics.get("lcp", 0) > task.e2e_tests.performance_thresholds.lcp:
                        return {
                            "success": False,
                            "error": f"LCP {metrics.get('lcp')}ms excede umbral {task.e2e_tests.performance_thresholds.lcp}ms",
                            "screenshots": screenshots
                        }
            
            return {
                "success": True,
                "screenshots": screenshots,
                "metrics": performance_metrics
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "screenshots": screenshots
            }
    
    def _validate_visual(self, task: Task, screenshots: List[str]) -> Dict:
        """Valida visualmente usando IA"""
        if not screenshots:
            return {"success": True, "message": "No hay screenshots para validar"}
        
        results = []
        for screenshot_path in screenshots:
            result = self.visual_validator.validate(
                screenshot_path,
                task.description,
                task.acceptance_criteria
            )
            results.append({
                "screenshot": screenshot_path,
                "valid": result.get("valid", False),
                "feedback": result.get("feedback", "")
            })
        
        all_valid = all(r["valid"] for r in results)
        
        return {
            "success": all_valid,
            "validations": results
        }
    
    def _get_screenshot_path(self, task_id: str, filename: str) -> Path:
        """Obtiene la ruta para guardar un screenshot"""
        screenshots_dir = Path(self.config.get("directories", {}).get("screenshots", "./screenshots"))
        task_dir = screenshots_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir / filename
    
    def _save_status(self):
        """Guarda el estado actual a archivo JSON"""
        status = {
            "last_updated": datetime.now().isoformat(),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "dependencies": t.dependencies,
                    "retry_count": t.retry_count,
                    "started_at": t.started_at.isoformat() if t.started_at else None,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "error_message": t.error_message
                }
                for t in self.tasks
            ],
            "summary": {
                "total": len(self.tasks),
                "completed": len([t for t in self.tasks if t.status == "completed"]),
                "failed": len([t for t in self.tasks if t.status == "failed"]),
                "pending": len([t for t in self.tasks if t.status == "pending"]),
                "in_progress": len([t for t in self.tasks if t.status == "in_progress"])
            }
        }
        
        self.status_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        self.logger.info(f"💾 Estado guardado en {self.status_file}")
    
    def get_status(self) -> Dict:
        """Obtiene el estado actual de todas las tareas"""
        if not self.tasks:
            self.load_tasks()
        
        return {
            "tasks": self.tasks,
            "summary": {
                "total": len(self.tasks),
                "completed": len([t for t in self.tasks if t.status == "completed"]),
                "failed": len([t for t in self.tasks if t.status == "failed"]),
                "pending": len([t for t in self.tasks if t.status == "pending"]),
                "in_progress": len([t for t in self.tasks if t.status == "in_progress"]),
                "blocked": len([t for t in self.tasks if t.status == "pending" and t.dependencies])
            }
        }
