# AI Task Orchestrator 🤖

> **El Management autónomo para Agentes de IA.**
>
> Define tareas en archivos markdown y deja que un equipo de agentes (ToolCalling) las implemente, testee en terminal, valide e incluso verifique la interfaz visualmente. Soporta OpenRouter y la API Zen (OpenCode).
>
> **Filosofía:** Funciona como Git. Inicializa un directorio oculto `.ai-tasks` en tu proyecto y gestiona todo desde allí.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Demo Rápida

```bash
# 1. Instalar (solo una vez)
git clone https://github.com/mcarbonell/ai-task-orchestrator.git
cd ai-task-orchestrator
pip install -r requirements.txt
cp .env.example .env # Configura tus API keys

# 2. Inicializar en TU proyecto (como git init)
cd /ruta/a/tu/codigo
python /ruta/a/orchestrator/cli.py init

# 3. Ejecutar (la IA leerá project-context.md y las tareas en .ai-tasks/tasks)
python /ruta/a/orchestrator/cli.py run
```

## ✨ ¿Qué es esto?

**AI Task Orchestrator** es un sistema que permite a las IAs trabajar de manera **completamente autónoma** en proyectos de desarrollo, manteniendo todo el contexto de las tareas dentro del propio repositorio del proyecto.

### Flujo de Trabajo Estilo Git

El orquestador busca automáticamente un directorio `.ai-tasks` subiendo por el árbol de carpetas. Esto permite ejecutarlo desde cualquier subdirectorio del proyecto.

```
Mi-Proyecto/
├── .ai-tasks/             <-- Gestionado por el Orquestador
│   ├── config.yaml
│   ├── tasks/             <-- Tus tareas (.md)
│   ├── logs/
│   ├── reports/
│   └── task-status.json
├── project-context.md     <-- Contexto global para la IA (Editable)
├── src/
└── package.json
```

## 📦 Instalación

### Prerrequisitos
- **Python 3.10+**
- **Chrome/Chromium** - Con debugging remoto habilitado (`--remote-debugging-port=9222`)

### Configuración
1. Clona el repo e instala dependencias.
2. Configura el archivo `.env` en la raíz del orquestador con tu `ZEN_API_KEY` o `OPENROUTER_API_KEY`.

## 🚀 Uso

### Inicializar Proyecto
Dentro de la carpeta de tu código:
```bash
python path/to/cli.py init
```
Esto creará el directorio `.ai-tasks` y un archivo `project-context.md` en la raíz de tu proyecto.

### Gestión de Tareas
Las tareas se guardan en `.ai-tasks/tasks/`. Puedes crearlas manualmente o usando:
```bash
python path/to/cli.py create-task "Implementar Header"
```

### Ejecución y Estado
```bash
# Ver qué hay que hacer
python path/to/cli.py status

# Lanzar el agente de IA
python path/to/cli.py run

# Si una tarea falla, corregir y reintentar
python path/to/cli.py retry
```

## 🔧 Configuración por Proyecto

Cada proyecto tiene su propio `config.yaml` dentro de `.ai-tasks/`. Puedes ajustar el modelo de IA, los reintentos o los umbrales de performance específicamente para ese repo.

```yaml
opencode:
  model: minimax-m2.5-free # Modelo recomendado para Zen API
  provider: zen
```

## 🏗️ Arquitectura V2

- **Auto-Discovery:** Busca la raíz del proyecto `.ai-tasks` hacia arriba.
- **ToolCallingAgent:** Loop de agencia 100% nativo vía API.
- **CDP Integration:** Validación real en navegador.
- **Portable:** Todo el estado del orquestador vive en el repo, permitiendo compartir tareas entre el equipo.

## 📝 Formato de Tareas (.md)
```markdown
---
id: T-001
title: "Título"
status: pending
priority: high
dependencies: []
---
## Descripción
...
## Criterios de Aceptación
- [ ] ...
## Tests Unitarios
```bash
npm test
\```
```

---
**¿Listo para delegar desarrollo real en IA?** 🚀
