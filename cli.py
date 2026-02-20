#!/usr/bin/env python3
"""
AI Task Orchestrator CLI

Sistema autónomo de orquestación de tareas para desarrollo de software con agentes de IA.
"""

import click
import yaml
from pathlib import Path
from typing import Optional

from task_runner.task_engine import TaskEngine
from task_runner.task_parser import TaskParser
from task_runner.utils import load_config, setup_logging, ensure_directories


@click.group()
@click.option('--config', '-c', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """AI Task Orchestrator - Automatiza desarrollo con agentes de IA"""
    ctx.ensure_object(dict)
    
    # Cargar configuración
    cfg = load_config(config)
    ctx.obj['config'] = cfg
    ctx.obj['verbose'] = verbose
    
    # Setup logging
    log_dir = Path(cfg.get('directories', {}).get('logs', './logs'))
    log_level = "DEBUG" if verbose else cfg.get('orchestrator', {}).get('log_level', 'INFO')
    setup_logging(log_dir, log_level)
    
    # ensure_directories(cfg)  # Eliminado de aquí para evitar creación de carpetas por defecto


@cli.command()
@click.option('--path', '-p', default='.', help='Directorio donde inicializar (por defecto el actual)')
@click.pass_context
def init(ctx, path):
    """Inicializa un nuevo proyecto en el directorio (estilo git init)"""
    base_path = Path(path).absolute()
    project_dir = base_path / ".ai-tasks"
    
    if project_dir.exists():
        click.echo(f"⚠️  Ya existe un proyecto en {base_path}")
        return
    
    click.echo(f"🚀 Inicializando AI Task Orchestrator en: {base_path}")
    
    # Crear estructura oculta
    dirs = [
        project_dir / "tasks",
        project_dir / "screenshots",
        project_dir / "reports",
        project_dir / "logs",
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True)
        click.echo(f"  📁 {dir_path.relative_to(base_path)}")
    
    # Copiar/Crear config.yaml
    config_content = """# AI Task Orchestrator Configuration
orchestrator:
  max_retries: 3
  parallel_workers: 1
  log_level: INFO
  max_iterations: 15

opencode:
  model: kimi-k2.5-free
  provider: zen # openrouter | zen | opencode
  
directories:
  tasks: ./tasks
  screenshots: ./screenshots
  reports: ./reports
  logs: ./logs

files:
  status: ./task-status.json
  context: ../project-context.md
"""
    (project_dir / "config.yaml").write_text(config_content, encoding="utf-8")
    click.echo(f"  ⚙️  .ai-tasks/config.yaml")
    
    # Crear project-context.md en la raíz del proyecto (visible)
    context_content = """# Project Context

## Descripción
[Describe aquí tu proyecto]

## Stack Tecnológico
- Frontend: [React/Vue/Angular/etc.]
- Backend: [Node/Python/etc.]

## Convenciones
- Estilo de código: [Standard/Airbnb/etc.]
- Commits: [Conventional Commits/etc.]
"""
    
    context_file = base_path / "project-context.md"
    if not context_file.exists():
        context_file.write_text(context_content, encoding="utf-8")
        click.echo(f"  📝 project-context.md")
    
    # Crear tarea de ejemplo
    example_task = '''---
id: T-001
title: "Configuración inicial"
status: pending
priority: high
dependencies: []
---

## Descripción
Verificar que el orquestador está correctamente configurado.

## Criterios de Aceptación
- [ ] El sistema puede leer este archivo
- [ ] El agente puede ejecutar comandos básicos
'''
    
    (project_dir / "tasks" / "T-001.md").write_text(example_task, encoding="utf-8")
    click.echo(f"  ✅ .ai-tasks/tasks/T-001.md (ejemplo)")
    
    click.echo(f"\n✨ Proyecto inicializado exitosamente!")
    click.echo(f"\nPróximos pasos:")
    click.echo(f"  # Edita project-context.md")
    click.echo(f"  # Ejecuta: python run.py run")


@cli.command()
@click.option('--task', '-t', help='Ejecutar tarea específica por ID')
@click.option('--parallel', '-p', is_flag=True, help='Ejecutar tareas en paralelo')
@click.option('--dry-run', is_flag=True, help='Mostrar qué se ejecutaría sin ejecutar')
@click.pass_context
def run(ctx, task, parallel, dry_run):
    """Ejecuta tareas pendientes"""
    config = ctx.obj['config']
    
    if dry_run:
        click.echo("🔍 MODO DRY-RUN - No se ejecutarán cambios\n")
    
    # Asegurar directorios antes de correr
    from task_runner.utils import ensure_directories
    ensure_directories(config)
    
    engine = TaskEngine(config)
    
    if task:
        click.echo(f"🎯 Ejecutando tarea: {task}")
        engine.run(task_id=task)
    else:
        if parallel:
            click.echo("⚡ Ejecutando en modo paralelo\n")
        else:
            click.echo("▶️  Ejecutando en modo secuencial\n")
        
        engine.run(parallel=parallel)


@cli.command()
@click.pass_context
def status(ctx):
    """Muestra el estado actual de todas las tareas"""
    config = ctx.obj['config']
    engine = TaskEngine(config)
    
    status_data = engine.get_status()
    summary = status_data['summary']
    
    click.echo("\n📊 Estado del Proyecto\n")
    click.echo(f"  Total:      {summary['total']}")
    click.echo(f"  ✅ Completadas: {summary['completed']}")
    click.echo(f"  ❌ Fallidas:    {summary['failed']}")
    click.echo(f"  ⏳ Pendientes:  {summary['pending']}")
    click.echo(f"  🔄 En progreso: {summary['in_progress']}")
    
    if summary['blocked'] > 0:
        click.echo(f"  🔒 Bloqueadas:  {summary['blocked']}")
    
    if summary['total'] > 0:
        success_rate = (summary['completed'] / summary['total']) * 100
        click.echo(f"\n  📈 Progreso: {success_rate:.1f}%")
    
    click.echo("\n📋 Detalle de tareas:\n")
    
    for task in status_data['tasks']:
        icon = {
            'completed': '✅',
            'failed': '❌',
            'pending': '⏳',
            'in_progress': '🔄'
        }.get(task.status, '❓')
        
        click.echo(f"  {icon} {task.id}: {task.title}")
        click.echo(f"     Status: {task.status} | Priority: {task.priority}")
        
        if task.dependencies:
            click.echo(f"     Dependencies: {', '.join(task.dependencies)}")
        
        if task.error_message:
            click.echo(f"     Error: {task.error_message[:100]}...")
        
        click.echo()


@cli.command()
@click.option('--format', '-f', default='all', type=click.Choice(['json', 'html', 'md', 'all']))
@click.option('--open', 'open_report', is_flag=True, help='Abrir reporte en navegador (solo HTML)')
@click.pass_context
def report(ctx, format, open_report):
    """Genera y muestra reportes de ejecución"""
    from task_runner.report_generator import ReportGenerator
    
    config = ctx.obj['config']
    engine = TaskEngine(config)
    engine.load_tasks()
    
    reports_dir = config.get('directories', {}).get('reports', './reports')
    generator = ReportGenerator(reports_dir)
    
    generated = generator.generate(
        engine.tasks,
        engine.execution_log,
        format=format
    )
    
    click.echo("\n📊 Reportes generados:\n")
    
    for fmt, path in generated.items():
        click.echo(f"  📄 {fmt.upper()}: {path}")
    
    if open_report and 'html' in generated:
        import webbrowser
        import os
        html_path = generated['html']
        abs_path = os.path.abspath(html_path)
        webbrowser.open(f'file://{abs_path}')
        click.echo(f"\n🌐 Abriendo reporte HTML...")


@cli.command()
@click.argument('title')
@click.option('--priority', default='medium', type=click.Choice(['low', 'medium', 'high']))
@click.option('--id', 'task_id', help='ID de la tarea (auto-generado si no se especifica)')
@click.pass_context
def create_task(ctx, title, priority, task_id):
    """Crea una nueva tarea a partir de plantilla"""
    config = ctx.obj['config']
    tasks_dir = Path(config.get('directories', {}).get('tasks', './tasks'))
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar ID si no se proporciona
    if not task_id:
        existing = list(tasks_dir.glob("T-*.md"))
        max_num = 0
        for f in existing:
            try:
                num = int(f.stem.split('-')[1])
                max_num = max(max_num, num)
            except:
                pass
        task_id = f"T-{max_num + 1:03d}"
    
    task_file = tasks_dir / f"{task_id}.md"
    
    if task_file.exists():
        click.echo(f"❌ Error: La tarea {task_id} ya existe")
        return
    
    # Crear contenido de la tarea
    task_content = f'''---
id: {task_id}
title: "{title}"
status: pending
priority: {priority}
dependencies: []
estimated_time: ""
---

## Descripción
[Describe la funcionalidad a implementar]

## Criterios de Aceptación
- [ ] [Criterio 1]
- [ ] [Criterio 2]
- [ ] [Criterio 3]

## Tests Unitarios
```bash
# [Comando para ejecutar tests]
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:3000/
  
  - action: screenshot
    filename: result.png

console_checks:
  - no_errors: true

performance_thresholds:
  lcp: 2500
  cls: 0.1
```

## Definition of Done
- [ ] Tests unitarios pasan
- [ ] Screenshots validados visualmente
- [ ] Console sin errores
- [ ] Métricas performance dentro de umbrales
'''
    
    task_file.write_text(task_content, encoding="utf-8")
    
    click.echo(f"✅ Tarea creada: {task_file}")
    click.echo(f"\n📝 Editando {task_file}...")
    
    # Intentar abrir con editor por defecto
    import subprocess
    import os
    
    editor = os.environ.get('EDITOR', 'notepad' if os.name == 'nt' else 'nano')
    try:
        subprocess.Popen([editor, str(task_file)])
    except:
        pass


@cli.command()
@click.pass_context
def retry(ctx):
    """Re-ejecuta tareas fallidas"""
    config = ctx.obj['config']
    engine = TaskEngine(config)
    engine.load_tasks()
    
    failed_tasks = [t for t in engine.tasks if t.status == "failed"]
    
    if not failed_tasks:
        click.echo("✅ No hay tareas fallidas para reintentar")
        return
    
    click.echo(f"🔄 Reintentando {len(failed_tasks)} tarea(s) fallida(s):\n")
    
    for task in failed_tasks:
        click.echo(f"  • {task.id}: {task.title}")
        # Resetear estado
        task.status = "pending"
        task.error_message = None
        task.retry_count = 0
        engine.parser.update_task_status(task, "pending")
    
    click.echo("\n▶️  Ejecutando...")
    engine.run()


@cli.command()
@click.confirmation_option(prompt='¿Estás seguro? Esto eliminará todo el estado de ejecución')
@click.pass_context
def reset(ctx):
    """Resetea el estado de todas las tareas (vuelven a pending)"""
    config = ctx.obj['config']
    engine = TaskEngine(config)
    engine.load_tasks()
    
    click.echo("🔄 Reseteando estado de tareas...\n")
    
    for task in engine.tasks:
        if task.status != "pending":
            old_status = task.status
            task.status = "pending"
            task.error_message = None
            task.retry_count = 0
            task.started_at = None
            task.completed_at = None
            engine.parser.update_task_status(task, "pending")
            click.echo(f"  ♻️  {task.id}: {old_status} → pending")
    
    # Limpiar archivo de estado
    status_file = Path(config.get('files', {}).get('status', './task-status.json'))
    if status_file.exists():
        status_file.unlink()
        click.echo(f"\n🗑️  {status_file} eliminado")
    
    click.echo("\n✅ Reset completado. Todas las tareas están en estado 'pending'")


if __name__ == '__main__':
    cli()
