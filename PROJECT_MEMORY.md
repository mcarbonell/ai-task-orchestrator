# AI Task Orchestrator - Memoria del Proyecto

**Fecha:** 2026-02-17  
**Estado:** MVP Funcional v1.0  
**Ubicación:** `C:\Users\mrcm_\Local\proj\ai-task-orchestrator`

---

## 🎯 Propósito del Proyecto

Sistema de orquestación de tareas para desarrollo de software con agentes de IA. Permite definir tareas en archivos markdown y que la IA las implemente, testee y valide automáticamente sin intervención humana.

**Flujo:**
1. Definir tareas en archivos markdown (con YAML frontmatter)
2. El sistema ejecuta cada tarea con OpenCode/agentes de IA
3. Valida automáticamente (tests unitarios + E2E + screenshots)
4. Si falla, reintenta con feedback
5. Genera reportes de progreso

---

## 📁 Estructura del Proyecto

```
ai-task-orchestrator/
├── run.py                      # Launcher principal
├── cli.py                      # CLI con Click (7 comandos)
├── config.yaml                 # Configuración global
├── requirements.txt            # Dependencias Python
├── task_runner/                # Core del sistema (7 módulos)
│   ├── __init__.py
│   ├── task_engine.py         # Orquestador principal (574 líneas)
│   ├── task_parser.py         # Parser de markdown YAML (244 líneas)
│   ├── opencode_runner.py     # Wrapper OpenCode CLI (125 líneas)
│   ├── cdp_wrapper.py         # Wrapper CDP Controller (256 líneas)
│   ├── visual_validator.py    # Validación visual IA (114 líneas)
│   ├── report_generator.py    # Generador reportes (191 líneas)
│   └── utils.py               # Utilidades (63 líneas)
├── templates/                  # Plantillas para nuevos proyectos
│   ├── task-template.md
│   └── project-context-template.md
├── example-project/           # Ejemplo: e-commerce
│   ├── tasks/
│   │   ├── T-001-setup.md
│   │   └── T-002-header.md
│   └── project-context.md
└── test-real-project/         # Proyecto de prueba real
```

---

## 🔧 Arquitectura del Sistema

### Componentes Principales

**1. Task Engine (`task_engine.py`)**
- Orquesta ejecución de tareas
- Gestiona dependencias entre tareas
- Maneja reintentos con backoff
- Soporta ejecución paralela
- Estados: pending → in_progress → validating → completed/failed

**2. Task Parser (`task_parser.py`)**
- Lee archivos markdown
- Extrae frontmatter YAML
- Parsea criterios de aceptación (checkboxes)
- Extrae tests unitarios (bloques de código)
- Parsea tests E2E (configuración YAML)

**3. OpenCode Runner (`opencode_runner.py`)**
- Wrapper para ejecutar `opencode run`
- Construye prompts enriquecidos
- Gestiona reintentos
- NOTA: Requiere sesión inicializada manualmente primero

**4. CDP Wrapper (`cdp_wrapper.py`)**
- Integra cdp_controller.py del usuario
- Navega a URLs
- Captura screenshots
- Ejecuta JavaScript
- Obtiene métricas de performance

**5. Visual Validator (`visual_validator.py`)**
- Usa IA con visión para validar screenshots
- Envía imágenes a OpenCode con --file
- Detecta errores de UI/UX

**6. Report Generator (`report_generator.py`)**
- Genera reportes JSON, HTML, Markdown
- Incluye métricas de ejecución
- Muestra progreso visual

---

## ⚠️ Limitación Conocida: OpenCode Session

**Problema:** OpenCode CLI requiere una sesión inicializada manualmente antes de poder ejecutar `opencode run`.

**Error:** `Session not found`

**Solución actual (documentada):**
```bash
# 1. Iniciar OpenCode manualmente una vez
opencode

# 2. Esperar que cargue
# 3. Salir con Ctrl+C

# 4. Ahora el orchestrator funcionará
python run.py run
```

**Posibles soluciones a investigar:**
1. Usar SDK de OpenCode en lugar de CLI
2. Configurar servidor persistente con `opencode serve`
3. Usar flag `--continue` (ya implementado pero no funciona sin sesión previa)
4. Integrar directamente con API de OpenRouter

---

## 🚀 Cómo usar el Sistema

### Comandos CLI

```bash
# Inicializar proyecto
python run.py init mi-proyecto

# Crear tarea
python run.py create-task "Implementar login"

# Ver estado
python run.py status

# Ejecutar tareas
python run.py run
python run.py run --task T-001
python run.py run --parallel

# Generar reportes
python run.py report

# Re-ejecutar fallidas
python run.py retry

# Resetear estado
python run.py reset
```

### Formato de Tareas

```markdown
---
id: T-001
title: "Nombre de la tarea"
status: pending
priority: high
dependencies: [T-002]
estimated_time: "2h"
---

## Descripción
Descripción detallada.

## Criterios de Aceptación
- [ ] Item 1
- [ ] Item 2

## Tests Unitarios
```bash
npm test Component.test.tsx
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
- [ ] Screenshots válidos
- [ ] Console sin errores
```

---

## 🔧 Configuración

**Archivo:** `orchestrator-config.yaml`

```yaml
orchestrator:
  max_retries: 3
  parallel_workers: 2
  log_level: INFO

opencode:
  model: opencode/kimi-k2.5
  agent: build
  timeout: 300

cdp:
  host: 127.0.0.1
  port: 9222
  controller_path: "C:\\Users\\mrcm_\\Local\\proj\\webrenove\\cdp_controller.py"

validation:
  performance:
    lcp: 2500
    cls: 0.1
    fcp: 1800

directories:
  tasks: ./tasks
  screenshots: ./screenshots
  reports: ./reports
  logs: ./logs
```

---

## 📊 Estado de Desarrollo

### ✅ Completado (MVP v1.0)

- [x] Task Engine con orquestación completa
- [x] Task Parser para archivos markdown
- [x] Integración CDP Controller
- [x] CLI completo con 7 comandos
- [x] Generación de reportes (JSON/HTML/Markdown)
- [x] Ejemplos de proyectos
- [x] Documentación completa
- [x] Tests manuales funcionando

### ⚠️ Con Limitaciones

- [x] OpenCode Runner (requiere sesión manual primero)

### 🔄 Pendiente (Roadmap)

- [ ] Resolver sesión de OpenCode automáticamente
- [ ] SDK de OpenCode para ejecución 100% automática
- [ ] Visual regression testing
- [ ] Watch mode
- [ ] Multi-agent support
- [ ] Planning automático
- [ ] Dashboard web
- [ ] Tests unitarios del propio orchestrator

---

## 🐛 Issues Conocidos (¡ACTUALIZADO 2026-02-18!)

### 1. **Terminal Incompatible - CRÍTICO** ✅ RESUELTO

**Problema:** OpenCode falla con "Session not found" o "Unauthorized" en MINGW64/Git Bash

**Descubrimiento:** OpenCode funciona perfectamente en PowerShell/CMD, solo falla en MINGW64

**Solución:** 
```powershell
# ✓ Usar Windows PowerShell (recomendado)
PS> opencode -m opencode/kimi-k2.5 run "Hola"

# ✓ O Windows CMD
C:\> opencode -m opencode/kimi-k2.5 run "Hola"

# ✗ NO usar MINGW64/Git Bash
$ opencode run "Hola"  # Error: Session not found
```

**Impacto:** Todo el sistema debe ejecutarse en PowerShell/CMD, no en Git Bash.

### 2. **Unicode en Windows**
Errores de encoding con emojis (no crítico, solo visual)
- Workaround: Usar PowerShell
- Los errores no afectan el funcionamiento

### 3. **Resuelto: OpenCode Session**
Ya NO requiere inicialización manual en PowerShell/CMD. El error "Session not found" era por usar el terminal equivocado.

---

## 📈 Potencial del Proyecto

**¿Por qué puede volverse viral?**

1. **Timing:** Peak del hype de agentes de IA (2025-2026)
2. **Problema real:** Automatización de desarrollo es demandada
3. **Solución completa:** No es un script, es un sistema integral
4. **Integración elegante:** Conecta herramientas existentes (OpenCode + CDP)
5. **Open Source:** Código limpio, bien documentado, extensible
6. **Workflow completo:** Desde planificación hasta validación

**Próximos pasos para viralización:**
- Resolver issue de OpenCode session
- Crear demo video mostrando ejecución completa
- Publicar en Reddit (r/programming, r/webdev)
- Post en Hacker News (Show HN)
- Hilo en Twitter/X explicando el flujo
- Más ejemplos (React, Vue, Python APIs)

---

## 🔗 Recursos

- **OpenCode:** https://opencode.ai
- **CDP Controller:** Herramienta del usuario en `C:\Users\mrcm_\Local\proj\webrenove\`
- **Chrome DevTools Protocol:** https://chromedevtools.github.io/devtools-protocol/

---

## 👤 Contexto del Usuario

- **Nombre:** Mario Raúl Carbonell Martínez, trabaja en proyectos web
- **Stack:** React, TypeScript, Vite, Tailwind
- **Herramientas:** OpenCode CLI, CDP Controller propio
- **Objetivo:** Automatizar desarrollo con agentes de IA
- **Sistema:** Windows con Python 3.14
- **Modelo preferido:** moonshotai/kimi-k2.5 (o opencode/kimi-k2.5)

---

## 💡 Notas para Futuras Sesiones

1. **Siempre verificar** que Chrome esté ejecutándose con remote debugging
2. **Recordar** la limitación de OpenCode session
3. **Usar** `$env:PYTHONIOENCODING = "utf-8"` en Windows para evitar errores Unicode
4. **Estructura de tareas** es flexible, puede adaptarse a cualquier proyecto
5. **El sistema es extensible** - fácil añadir nuevos comandos CDP o validaciones

---

**Última actualización:** 2026-02-17  
**Versión:** 1.0.0 MVP  
**Estado:** Funcional con workaround documentado
