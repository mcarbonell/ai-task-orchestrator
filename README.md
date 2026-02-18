# AI Task Orchestrator 🤖

> **Automatiza el desarrollo de software con agentes de IA.**
> 
> Define tareas en archivos markdown, y deja que la IA las implemente, testee y valide automáticamente.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![OpenCode](https://img.shields.io/badge/OpenCode-1.1+-green.svg)](https://opencode.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Demo

```bash
# 1. Instalar
git clone https://github.com/tuusuario/ai-task-orchestrator.git
cd ai-task-orchestrator
pip install -r requirements.txt

# 2. Crear proyecto
python run.py init mi-proyecto
cd mi-proyecto

# 3. Crear tarea
python run.py create-task "Implementar login"

# 4. Ejecutar (la IA hace el trabajo!)
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

### ⚠️ IMPORTANTE: Terminal Compatible

**OpenCode solo funciona correctamente en:**
- ✅ **Windows PowerShell** (recomendado)
- ✅ **Windows CMD** 
- ❌ **MINGW64/Git Bash** - NO funciona (error: "Session not found")

**Para usar:**
```powershell
# PowerShell (como administrador o normal)
PS> cd ai-task-orchestrator
PS> python run.py status
```

### Prerrequisitos

- **Python 3.8+**
- **OpenCode CLI** - [Instalación](https://opencode.ai/docs/installation)
- **Chrome/Chromium** - Para tests E2E con CDP
- **CDP Controller** - [Tu herramienta](https://github.com/tuusuario/cdp-controller)

### Setup

```bash
# Clonar repositorio
git clone https://github.com/tuusuario/ai-task-orchestrator.git
cd ai-task-orchestrator

# Instalar dependencias
pip install -r requirements.txt

# Verificar OpenCode
opencode --version

# Verificar Chrome con CDP
# Windows:
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

# Ejecutar todas las tareas
python run.py run

# Ejecutar tarea específica  
python run.py run --task T-001

# Ver reporte
python run.py report
```

## 🔧 Configuración

Crea `orchestrator-config.yaml`:

```yaml
orchestrator:
  max_retries: 3
  parallel_workers: 2
  log_level: INFO

opencode:
  model: opencode/kimi-k2.5  # Tu modelo favorito
  agent: build
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

## ⚠️ Nota Importante sobre OpenCode

**Limitación conocida:** OpenCode CLI requiere una sesión inicializada manualmente antes de poder ejecutarse en modo no-interactivo.

### Solución (una sola vez):

```bash
# 1. Iniciar OpenCode manualmente
opencode

# 2. Esperar que cargue completamente
# 3. Salir con Ctrl+C

# 4. Ahora el orchestrator funcionará automáticamente
python run.py run
```

**Alternativa:** Configurar `base_url` para usar un servidor OpenCode persistente.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    AI TASK ORCHESTRATOR                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Task Files → Task Parser → Task Engine → OpenCode Agent   │
│       (md)        (YAML)      (logic)        (AI)          │
│                              /      \                       │
│                        CDP Tests    Visual Validator       │
│                       (Chrome)      (Vision AI)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Componentes:**
- **Task Engine:** Orquesta ejecución, gestiona estado, reintentos
- **Task Parser:** Lee archivos markdown, extrae metadatos YAML
- **OpenCode Runner:** Wrapper para invocar agentes de IA
- **CDP Wrapper:** Controla Chrome para tests E2E
- **Visual Validator:** Usa IA para validar screenshots
- **Report Generator:** Crea reportes JSON/HTML/Markdown

## 📝 Formato de Tareas

Las tareas son archivos markdown con frontmatter YAML:

```markdown
---
id: T-001
title: "Nombre de la tarea"
status: pending
priority: high
dependencies: [T-002]  # Opcional
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

### "Session not found" o "Unauthorized" con OpenCode

**Causa:** Estás usando MINGW64/Git Bash. OpenCode NO funciona en este terminal.

**Solución:** Usa Windows PowerShell o CMD:
```powershell
# PowerShell (recomendado)
PS C:\> cd ai-task-orchestrator
PS C:\ai-task-orchestrator> python run.py status
```

### Chrome no conecta

```bash
# Verificar Chrome está en modo debug
curl http://127.0.0.1:9222/json/version

# Reiniciar Chrome completamente
```

### Errores de Unicode en Windows

```bash
# PowerShell
$env:PYTHONIOENCODING = "utf-8"
python run.py run
```

## 🗺️ Roadmap

### v1.0 (Actual) ✅
- Orquestación de tareas con dependencias
- Integración OpenCode CLI
- Tests E2E con CDP
- Validación visual con IA
- Reportes JSON/HTML/Markdown

### v1.1 (Próximo)
- [ ] SDK de OpenCode para ejecución 100% automática
- [ ] Auto-corrección de errores
- [ ] Visual regression testing
- [ ] Watch mode

### v2.0 (Futuro)
- [ ] Multi-agent (diferentes agentes para diferentes tareas)
- [ ] Planning automático (IA genera tareas desde requerimientos)
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

- [Discusiones](https://github.com/tuusuario/ai-task-orchestrator/discussions)
- [Issues](https://github.com/tuusuario/ai-task-orchestrator/issues)

---

**¿Listo para automatizar tu desarrollo?** 🚀

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
