"""
Task Parser - Parsea archivos markdown de tareas en objetos Python
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class PerformanceThresholds:
    lcp: Optional[int] = None  # Largest Contentful Paint (ms)
    cls: Optional[float] = None  # Cumulative Layout Shift
    fcp: Optional[int] = None  # First Contentful Paint (ms)
    ttfb: Optional[int] = None  # Time to First Byte (ms)


@dataclass
class ConsoleChecks:
    fail_on_error: bool = True
    allowed_warnings: List[str] = field(default_factory=list)


@dataclass
class CDPStep:
    action: str  # navigate, screenshot, eval, wait, click
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CDPTest:
    steps: List[CDPStep] = field(default_factory=list)
    console_checks: ConsoleChecks = field(default_factory=lambda: ConsoleChecks())
    performance_thresholds: PerformanceThresholds = field(default_factory=lambda: PerformanceThresholds())


@dataclass
class Task:
    id: str
    title: str
    status: str = "pending"
    priority: str = "medium"
    dependencies: List[str] = field(default_factory=list)
    estimated_time: str = ""
    description: str = ""
    acceptance_criteria: List[str] = field(default_factory=list)
    unit_tests: List[str] = field(default_factory=list)
    e2e_tests: CDPTest = field(default_factory=lambda: CDPTest())
    definition_of_done: List[str] = field(default_factory=list)
    file_path: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)


class TaskParser:
    """Parsea archivos markdown de tareas"""
    
    def __init__(self, tasks_dir: Path):
        self.tasks_dir = Path(tasks_dir)
    
    def parse_all_tasks(self) -> List[Task]:
        """Parsea todas las tareas del directorio"""
        tasks = []
        
        if not self.tasks_dir.exists():
            return tasks
        
        for task_file in sorted(self.tasks_dir.glob("*.md")):
            try:
                task = self.parse_task_file(task_file)
                tasks.append(task)
            except Exception as e:
                print(f"❌ Error parseando {task_file}: {e}")
        
        return tasks
    
    def parse_task_file(self, file_path: Path) -> Task:
        """Parsea un archivo de tarea individual"""
        content = file_path.read_text(encoding="utf-8")
        
        # Extraer frontmatter YAML
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        
        if frontmatter_match:
            frontmatter = yaml.safe_load(frontmatter_match.group(1))
            body = content[frontmatter_match.end():]
        else:
            frontmatter = {}
            body = content
        
        # Parsear secciones del body
        sections = self._parse_sections(body)
        
        # Extraer criterios de aceptación
        acceptance_criteria = self._extract_checkboxes(sections.get("Criterios de Aceptación", ""))
        
        # Extraer tests unitarios
        unit_tests = self._extract_code_blocks(sections.get("Tests Unitarios", ""), "bash")
        
        # Parsear tests E2E
        e2e_tests = self._parse_e2e_tests(sections.get("Tests E2E (CDP)", ""))
        
        # Extraer definition of done
        definition_of_done = self._extract_checkboxes(sections.get("Definition of Done", ""))
        
        # Crear objeto Task
        task = Task(
            id=frontmatter.get("id", file_path.stem),
            title=frontmatter.get("title", file_path.stem),
            status=frontmatter.get("status", "pending"),
            priority=frontmatter.get("priority", "medium"),
            dependencies=frontmatter.get("dependencies", []),
            estimated_time=frontmatter.get("estimated_time", ""),
            description=sections.get("Descripción", "").strip(),
            acceptance_criteria=acceptance_criteria,
            unit_tests=unit_tests,
            e2e_tests=e2e_tests,
            definition_of_done=definition_of_done,
            file_path=file_path
        )
        
        return task
    
    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parsea secciones markdown (## Título)"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                # Guardar sección anterior
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                
                # Iniciar nueva sección
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Guardar última sección
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _extract_checkboxes(self, content: str) -> List[str]:
        """Extrae items de checklist markdown"""
        checkboxes = []
        for line in content.split('\n'):
            match = re.match(r'\s*-\s*\[.\]\s*(.+)', line)
            if match:
                checkboxes.append(match.group(1).strip())
        return checkboxes
    
    def _extract_code_blocks(self, content: str, language: str = None) -> List[str]:
        """Extrae bloques de código markdown"""
        blocks = []
        pattern = r'```(?:' + (language or r'\w*') + r')?\n(.*?)\n```'
        for match in re.finditer(pattern, content, re.DOTALL):
            blocks.append(match.group(1).strip())
        return blocks
    
    def _parse_e2e_tests(self, content: str) -> CDPTest:
        """Parsea configuración de tests E2E en YAML"""
        # Extraer bloque YAML
        yaml_match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        
        if not yaml_match:
            return CDPTest()
        
        try:
            config = yaml.safe_load(yaml_match.group(1))
        except yaml.YAMLError:
            return CDPTest()
        
        # Parsear steps
        steps = []
        for step_config in config.get("steps", []):
            if isinstance(step_config, dict):
                # Formato: {action: navigate, url: ...} o {navigate: {url: ...}}
                if "action" in step_config:
                    # Formato explícito: action, url, etc.
                    action = step_config.pop("action")
                    params = step_config  # El resto son parámetros
                else:
                    # Formato implícito: {navigate: {url: ...}}
                    action = list(step_config.keys())[0]
                    params = step_config[action]
                    if not isinstance(params, dict):
                        params = {"value": params}
            else:
                # Formato simplificado: "action: params"
                parts = step_config.split(":", 1)
                action = parts[0].strip()
                params = {"value": parts[1].strip()} if len(parts) > 1 else {}
            
            steps.append(CDPStep(action=action, params=params))
        
        # Parsear console checks
        console_config = config.get("console_checks", {})
        # Si es una lista, convertir a diccionario
        if isinstance(console_config, list) and len(console_config) > 0:
            # Tomar el primer elemento si es una lista de diccionarios
            if isinstance(console_config[0], dict):
                merged_config = {}
                for item in console_config:
                    if isinstance(item, dict):
                        merged_config.update(item)
                console_config = merged_config
            else:
                console_config = {}
        elif not isinstance(console_config, dict):
            console_config = {}
        
        console_checks = ConsoleChecks(
            fail_on_error=console_config.get("no_errors", True),
            allowed_warnings=console_config.get("allowed_warnings", [])
        )
        
        # Parsear performance thresholds
        perf_config = config.get("performance_thresholds", {})
        performance_thresholds = PerformanceThresholds(
            lcp=perf_config.get("lcp"),
            cls=perf_config.get("cls"),
            fcp=perf_config.get("fcp"),
            ttfb=perf_config.get("ttfb")
        )
        
        return CDPTest(
            steps=steps,
            console_checks=console_checks,
            performance_thresholds=performance_thresholds
        )
    
    def update_task_status(self, task: Task, new_status: str, error_message: str = None):
        """Actualiza el estado de una tarea en su archivo"""
        if not task.file_path or not task.file_path.exists():
            return
        
        content = task.file_path.read_text(encoding="utf-8")
        
        # Actualizar frontmatter
        frontmatter_match = re.match(r'^(---\s*\n)(.*?)(\n---\s*\n)', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = yaml.safe_load(frontmatter_match.group(2))
            frontmatter["status"] = new_status
            
            # Reconstruir archivo
            new_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
            new_content = f"---\n{new_frontmatter}---\n{content[frontmatter_match.end():]}"
            
            task.file_path.write_text(new_content, encoding="utf-8")
        
        # Actualizar objeto
        task.status = new_status
        if error_message:
            task.error_message = error_message
