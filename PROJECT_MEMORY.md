# AI Task Orchestrator - Memoria del Proyecto

**Fecha:** 2026-02-20
**Estado:** Funcional v2.1 (Estructura Estilo Git)
**Ubicación:** `C:\Users\mrcm_\Local\proj\ai-task-orchestrator`

---

## 🎯 Cambio de Filosofía (v2.1)

El proyecto ha evolucionado de una gestión centralizada de proyectos a una **gestión descentralizada y autocontenida**, inspirada en el funcionamiento de Git.

### Puntos Clave:
1. **Directorio `.ai-tasks`:** Todo lo relacionado con la orquestación (configuración, tareas, logs, reportes) vive dentro de este directorio oculto en la raíz de cada proyecto.
2. **Auto-descubrimiento:** El CLI busca recursivamente hacia arriba el directorio `.ai-tasks`. Esto permite ejecutar comandos desde cualquier subcarpeta del proyecto.
3. **Portabilidad:** Al estar las tareas y el contexto dentro del repo, el orquestador se convierte en una herramienta de equipo.
4. **Contexto Visible:** `project-context.md` se ubica en la raíz del proyecto para facilitar su edición manual, sirviendo como la "biblia" de contexto para los agentes.

---

## 📁 Estructura del Sistema

```
ai-task-orchestrator/          # El Software (Instalable/Global)
├── cli.py                     # Punto de entrada
├── task_runner/               # Lógica de negocio
└── ...

Tu-Proyecto/                   # Tu Código
├── .ai-tasks/                 # El Cerebro del Proyecto
│   ├── config.yaml            # Config local
│   ├── tasks/                 # T-XXX.md
│   ├── logs/
│   ├── reports/
│   └── task-status.json       # Estado de ejecución
└── project-context.md         # Contexto para la IA
```

---

## ✅ Mejoras Recientes

- **Resolución de Rutas:** Las rutas en `config.yaml` se resuelven relativas a la ubicación del archivo de configuración, permitiendo ejecutar el orquestador desde cualquier lugar.
- **Lazy Directory Creation:** El CLI ya no crea carpetas por defecto (`tasks/`, `logs/`, etc.) en la raíz del orquestador. Solo se crean dentro de `.ai-tasks` cuando se inicializa o ejecuta un proyecto.
- **Comando `init` Simplificado:** Ahora funciona como `git init`, inicializando el proyecto en la carpeta actual por defecto.

---

## 🚀 Comandos Actualizados

```bash
# Inicializar (crea .ai-tasks/ y project-context.md)
python cli.py init

# Ejecutar (detecta automáticamente el proyecto más cercano)
python cli.py run

# Reintentar tareas fallidas (resetea estado a pending y lanza run)
python cli.py retry
```

---

## 🔧 Configuración Recomendada (Zen API)

Para evitar errores de cuota (429) detectados con modelos `free`, se recomienda:
- **Modelo:** `minimax-m2.5-free`
- **Proveedor:** `zen`

---

## 💡 Notas para Futuras Sesiones

1. **Priorizar `.ai-tasks`:** Siempre que se trabaje en un proyecto, verificar que las tareas estén en `.ai-tasks/tasks/`.
2. **Project Context:** Es vital mantener `project-context.md` actualizado para que la IA no alucine o intente instalar dependencias innecesarias (como ocurrió en la prueba de T-001).
3. **Windows Unicode:** Se sigue recomendando `$env:PYTHONIOENCODING = "utf-8"` debido a que las salidas de procesos (como `npm test`) pueden contener caracteres que rompan el pipe de Python en Windows.
