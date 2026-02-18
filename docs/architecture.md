# AI Task Orchestrator - Architecture

## Visión General

El AI Task Orchestrator es un sistema diseñado para automatizar completamente el desarrollo de software mediante agentes de IA. Utiliza un enfoque de orquestación de tareas donde cada tarea es una unidad atómica de trabajo que puede ser ejecutada, validada y completada de forma autónoma.

## Principios de Diseño

1. **Autonomía**: El sistema debe operar sin intervención humana durante la ejecución de tareas
2. **Atomicidad**: Las tareas son independientes y completas por sí mismas
3. **Validación Automática**: Cada tarea incluye sus propios criterios de validación
4. **Reintentos Inteligentes**: Si una tarea falla, se reintenta con feedback del error
5. **Observabilidad**: Todo el proceso está trazado y reportado

## Arquitectura de Componentes

### 1. Task Engine (Orquestador)

El núcleo del sistema. Responsable de:
- Gestionar el estado de las tareas (máquina de estados)
- Coordinar la ejecución secuencial o paralela
- Manejar dependencias entre tareas
- Gestionar reintentos con backoff
- Generar reportes consolidados

**Flujo de Ejecución:**
```
Load Tasks → Check Dependencies → Execute Task → Validate → 
   ↓
Completed / Retry / Failed
```

### 2. Task Parser

Convierte archivos markdown en objetos de dominio:
- Extrae metadatos YAML (frontmatter)
- Parsea criterios de aceptación
- Extrae comandos de tests
- Parsea configuración de CDP (navegación, screenshots, eval)

**Formato de Tarea:**
```yaml
---
id: T-001
title: "Nombre"
status: pending
priority: high
dependencies: [T-002]
---
```

### 3. OpenCode Runner

Wrapper sobre el CLI de OpenCode:
- Construye prompts enriquecidos con contexto
- Ejecuta `opencode run` con flags apropiados
- Captura output y errores
- Soporte para validación visual (envío de screenshots)

**Integración:**
```bash
opencode run \
  --model anthropic/claude-3.5-sonnet \
  --agent build \
  --file screenshot.png \
  "Implementa esta funcionalidad..."
```

### 4. CDP Wrapper

Integración con Chrome DevTools Protocol:
- Abstrae comandos del cdp_controller.py
- Gestiona conexión WebSocket
- Métodos: navigate, screenshot, evaluate, click
- Recolecta métricas de performance

### 5. Visual Validator

Usa IA con capacidad de visión para validar UI:
- Envía screenshots a OpenCode
- Analiza elementos visuales
- Detecta errores de layout
- Verifica responsive design

### 6. Report Generator

Genera artefactos de ejecución:
- JSON: Datos estructurados
- HTML: Dashboard visual
- Markdown: Documentación

## Flujo de Datos

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Task Files  │────→│ Task Parser  │────→│ Task Engine  │
│  (.md)      │     │              │     │              │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                    ┌───────────────────────────┼───────────┐
                    ▼                           ▼           ▼
            ┌──────────────┐          ┌──────────────┐  ┌──────────────┐
            │OpenCode Runner│          │ CDP Wrapper  │  │   Validator  │
            └──────┬───────┘          └──────┬───────┘  └──────┬───────┘
                   │                         │                 │
                   ▼                         ▼                 ▼
            ┌──────────────┐          ┌──────────────┐  ┌──────────────┐
            │   AI Agent   │          │    Chrome    │  │  Visual AI   │
            │  (OpenCode)  │          │   (CDP)      │  │   Analysis   │
            └──────────────┘          └──────────────┘  └──────────────┘
```

## Estados de Tareas

```
    ┌────────────┐
    │  Pending   │
    └─────┬──────┘
          │
          ▼
   ┌────────────┐
   │In Progress │
   └─────┬──────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐  ┌────────┐
│Validating│  │  Failed  │
└───┬───┘  └────┬───┘
    │            │
    ▼            │ (retry < max)
┌───────┐       │
│Completed│◄────┘
└───────┘
```

## Patrones de Diseño

### 1. Command Pattern
Cada operación (navigate, screenshot, eval) es un comando con parámetros.

### 2. Strategy Pattern
Diferentes estrategias de validación: unit tests, E2E, visual.

### 3. Template Method
Ejecución de tarea sigue un flujo definido pero extensible.

### 4. Observer Pattern
Logging y reportes observan eventos del engine.

## Consideraciones de Escalabilidad

- **Paralelización**: Tareas independientes pueden ejecutarse en paralelo
- **Estado Externo**: Estado guardado en archivos (no en memoria)
- **Idempotencia**: Re-ejecutar una tarea produce el mismo resultado
- **Recuperación**: Si falla el proceso, se puede reanudar desde el estado guardado

## Seguridad

- No se almacenan secrets en archivos de tareas
- Variables de entorno para configuración sensible
- Sandbox de CDP (Chrome aislado)
- Límites de tiempo en ejecuciones

## Extensiones Futuras

1. **Plugin System**: Permitir plugins personalizados para validaciones
2. **Multi-Agent**: Diferentes agentes para diferentes tipos de tareas
3. **Auto-Planning**: IA genera tareas a partir de requerimientos
4. **Git Integration**: Auto-commit al completar tareas
5. **CI/CD Integration**: GitHub Actions, GitLab CI, etc.
