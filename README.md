# AI Task Orchestrator 🤖

> **El Management autónomo para Agentes de IA.**
>
> Define tareas en archivos markdown y deja que un equipo de agentes (ToolCalling) las implemente, testee en terminal, valide e incluso verifique la interfaz visualmente. Soporta OpenRouter y la API Zen (OpenCode).
>
> **Tags:** `ai-agents` `autonomous-coding` `tool-calling` `llm` `orchestrator` `testing` `browser-automation`

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Demo

```bash
# 1. Instalar
git clone https://github.com/mcarbonell/ai-task-orchestrator.git
cd ai-task-orchestrator
pip install -r requirements.txt
cp .env.example .env # (Añade tu OPENROUTER_API_KEY o ZEN_API_KEY aquí)

# 2. Crear proyecto
python run.py init mi-proyecto
cd mi-proyecto

# 3. Crear tarea
python run.py create-task "Implementar landing page"

# 4. Ejecutar (la IA entra en Agent Loop!)
python run.py run
```

## ✨ ¿Qué es esto?

**AI Task Orchestrator** es un sistema que permite a las IAs trabajar de manera **completamente autónoma** en proyectos de desarrollo.

### Flujo de Trabajo

```
Tareas (Markdown) 
      ↓
Orquestador → OpenCode (IA) 
      ↓                    ↓
CDP Tests ←─ Validación ←─┘
(Screenshots)
```

1. 📋 **Descompones** tu proyecto en tareas (archivos markdown)
2. 🤖 **El sistema ejecuta** cada tarea con agentes de IA
3. ✅ **Valida automáticamente** resultados (tests + screenshots)
4. 🔄 **Si falla**, reintenta con feedback del error
5. 📊 **Genera reportes** de progreso

### Características Principales

- ✅ **Orquestación completa** - Gestiona dependencias entre tareas
- ✅ **Validación automática** - Tests unitarios + E2E + screenshots
- ✅ **Validación visual con IA** - Analiza screenshots para detectar errores
- ✅ **Chrome DevTools Protocol** - Control total del navegador para testing
- ✅ **Reintentos inteligentes** - Feedback loop automático
- ✅ **Paralelización** - Ejecuta tareas independientes simultáneamente
- ✅ **Reportes detallados** - JSON, HTML y Markdown

## 📦 Instalación

### Prerrequisitos
- **Python 3.10+** (Recomendado)
- **Chrome/Chromium** - Para tests E2E con CDP
- **CDP Controller** - [cdp-controller](https://github.com/mcarbonell/cdp-controller) corriendo en tu máquina (`--remote-debugging-port=9222`)

### 1. Clonar y Configurar Dependencias
```bash
git clone https://github.com/mcarbonell/ai-task-orchestrator.git
cd ai-task-orchestrator
pip install -r requirements.txt
```

### 2. Variables de Entorno (¡Importante!)
El orquestador V2 utiliza una arquitectura nativa de Agent **sin depender de CLI frágiles**. Todo funciona por API (OpenRouter o la API OpenCode Zen).

Copia el `env.example`:
```bash
cp .env.example .env
```
Edita `.env` y añade tus claves:
```env
# Ejemplo para OpenRouter
OPENROUTER_API_KEY=tu_clave_aqui

# Ejemplo para Zen API
ZEN_API_KEY=tu_clave_aqui
```

### 3. Verificar Chrome con CDP (Windows)
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
# Verificar conexión
curl http://127.0.0.1:9222/json/version
```

## 🚀 Uso Rápido

### 1. Inicializar Proyecto

```bash
python run.py init mi-proyecto
cd mi-proyecto
```

### 2. Definir Tarea

Crea `tasks/T-001-login.md`:

```markdown
---
id: T-001
title: "Implementar login"
status: pending
priority: high
dependencies: []
---

## Descripción
Crear formulario de login con React.

## Criterios de Aceptación
- [ ] Input email con validación
- [ ] Input password
- [ ] Botón submit

## Tests Unitarios
```bash
npm test LoginForm.test.tsx
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:5173/login
  
  - action: screenshot
    filename: login.png
    width: 1280
    height: 720
```

## Definition of Done
- [ ] Tests pasan
- [ ] Screenshots válidos
- [ ] Console sin errores
```

### 3. Ejecutar

```bash
# Ver estado
python run.py status

# Ejecutar todas las tareas (¡Aquí entra la IA en acción!)
python run.py run

# Ejecutar tarea específica  
python run.py run --task T-001

# Ver reporte
python run.py report
```

## 🔧 Configuración

Crea/Edita `orchestrator-config.yaml`:

```yaml
orchestrator:
  max_retries: 3
  parallel_workers: 2
  log_level: INFO

opencode:
  # Opciones proveedor V2: "zen" o "openrouter"
  provider: zen
  model: kimi-k2.5-free
  timeout: 300

cdp:
  host: 127.0.0.1
  port: 9222
  controller_path: "/path/to/cdp_controller.py"

validation:
  performance:
    lcp: 2500
    cls: 0.1
    fcp: 1800
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    AI TASK ORCHESTRATOR                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Task Files → Task Parser → Task Engine → ToolCallingAgent  │
│       (md)        (YAML)      (logic)        (API V2)       │
│                              /      \                       │
│                        CDP Tests    Visual Validator        │
│                       (Chrome)      (Vision API)            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Componentes:**
- **Task Engine:** Orquesta ejecución, gestiona estado, inyecta historial
- **Task Parser:** Lee archivos markdown, extrae metadatos YAML
- **ToolCallingAgent:** Agente iterativo LLM 100% autónomo (OpenRouter/Zen)
- **CDP Wrapper:** Controla Chrome para tests E2E y toma de Screenshots
- **Visual Validator:** Convierte las vistas a Base64 y pasa QA Visual
- **Report Generator:** Crea reportes JSON/HTML/Markdown

## 📝 Formato de Tareas

Las tareas son archivos markdown con frontmatter YAML:

```markdown
---
id: T-001
title: "Nombre de la tarea"
status: pending
priority: high
dependencies: [T-002]  # Opcional (inyecta historial)
estimated_time: "2h"
---

## Descripción
Descripción detallada de la funcionalidad.

## Criterios de Aceptación
- [ ] Item 1
- [ ] Item 2

## Tests Unitarios
```bash
comando para tests
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:3000/
  
  - action: screenshot
    filename: result.png
    width: 1280
    height: 720

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
```

## 📊 Comandos CLI

```bash
# Inicializar proyecto
python run.py init <nombre>

# Crear nueva tarea
python run.py create-task "Título" [--priority high|medium|low]

# Ver estado
python run.py status

# Ejecutar tareas
python run.py run [--task T-001] [--parallel]

# Generar reportes
python run.py report [--format json|html|md|all]

# Re-ejecutar fallidas
python run.py retry

# Resetear estado
python run.py reset
```

## 🐛 Solución de Problemas

### `ModuleNotFoundError: No module named 'dotenv'`
**Causa:** No instalaste las dependencias del `requirements.txt`.
**Solución:** Ejecuta `pip install -r requirements.txt`.

### Chrome no conecta (Para Screenshots/Tests E2E)
```bash
# Verificar Chrome está en modo debug
curl http://127.0.0.1:9222/json/version

# Windows CMD de atajo para abrir Chrome
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

## 🗺️ Roadmap

### v2.0 (Actual) ✅
- [x] Migración total a arquitectura `ToolCallingAgent` por API nativa
- [x] Independencia del frágil OpenCode CLI global
- [x] Validación Visual QA inyectando Base64 multimodal directamente
- [x] Inyección de historial por Agente basado en `dependencies`
- [x] Compatibilidad OpenRouter y Zen API (.env variable)

### v3.0 (Futuro)
- [ ] Agente Planner: LLM inicial que genera los `tasks/T-xxx.md` automáticamente dado un prompt humano.
- [ ] Multi-agent (diferentes perfiles de agentes para diferentes tareas)
- [ ] Integración CI/CD (GitHub Actions, GitLab CI)
- [ ] Dashboard web de progreso

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add feature'`
4. Push: `git push origin feature/amazing-feature`
5. Abre un Pull Request

Lee [CONTRIBUTING.md](CONTRIBUTING.md) para más detalles.

## 📝 Licencia

MIT License - ver [LICENSE](LICENSE)

## 💬 Comunidad

- [Discusiones](https://github.com/mcarbonell/ai-task-orchestrator/discussions)
- [Issues](https://github.com/mcarbonell/ai-task-orchestrator/issues)

---

**¿Listo para delegar desarrollo real en IA?** 🚀

### Windows PowerShell (Recomendado)
```powershell
# Usando el script incluido
.\run-orchestrator.ps1 init mi-proyecto
cd mi-proyecto
.\run-orchestrator.ps1 run

# O directamente con Python
python run.py init mi-proyecto
cd mi-proyecto
python run.py run
```

### Windows CMD
```cmd
run.bat init mi-proyecto
cd mi-proyecto
run.bat run
```

⚠️ **IMPORTANTE:** No uses Git Bash/MINGW64 - OpenCode no funciona en ese terminal.

¡Deja que la IA haga el trabajo!
