# SMMA v2: Self-Managed Memory Architecture
**Version:** 2.0  
**Objetivo:** Dotar al agente de IA de plena autonomía sobre su cognición, tratando la memoria de contexto como un espacio de trabajo gestionable — no como un log cronológico de mensajes.

---

## 1. Principio Fundamental

La memoria de contexto es la **mesa de trabajo** del agente, no un archivo de logs. El agente decide qué permanece, qué se resume, qué se descarta y cómo se organiza. El contexto deja de ser un scroll cronológico pasivo para convertirse en un espacio activo y estructurado.

**Analogía con un sistema operativo:**
- **CPU** → El modelo LLM (razonamiento)
- **RAM** → Memoria de contexto (espacio de trabajo activo)
- **Disco duro** → Archivos persistentes en `.smma/` (memoria a largo plazo)
- **System calls** → Herramientas de gestión de memoria
- **Monitor de recursos** → Dashboard de metacognición

---

## 2. Estructura de la Memoria de Contexto (RAM)

El contexto se organiza en **secciones** con propósitos distintos, no en una secuencia plana de mensajes.

| # | Sección | Persistencia | Tokens aprox. | Editable por agente | Propósito |
|---|---------|-------------|---------------|---------------------|-----------|
| 1 | System Prompt / Identidad | Disco (fijo) | 1,000–2,000 | No | Instrucciones SMMA, personalidad, reglas de comportamiento |
| 2 | Dashboard de Metacognición | Auto-generado | 200–300 | No (automático) | Presión de memoria, alertas, acciones recomendadas |
| 3 | Perfil del Usuario | Disco (.md) | 500–1,500 | Sí | Preferencias, estilo, decisiones recurrentes del usuario |
| 4 | Contexto del Proyecto | Disco (.md) | 2,000–5,000 | Sí | Arquitectura, stack, objetivos, estructura del proyecto |
| 5 | Estado de la Tarea Actual | Disco (.md) | 1,000–3,000 | Sí | Objetivo, criterios de éxito, subtareas, progreso, bloqueos |
| 6 | Notas del Agente | Disco (.md) | 500–2,000 | Sí | Scratchpad libre: hipótesis, ideas, recordatorios, decisiones pendientes |
| 7 | Log de Acciones | En memoria | 5,000–20,000 | Sí (prune/summarize) | Historial de lo ejecutado, resumible y podable |
| 8 | Espacio de Trabajo | En memoria | Variable (resto) | Sí | Archivos abiertos, outputs de herramientas, razonamiento activo |

**Presupuesto fijo (secciones 1–6):** ~5,000–14,000 tokens — fracción mínima del contexto total.  
**Espacio dinámico (secciones 7–8):** El resto disponible, gestionado activamente por el agente.

---

## 3. Detalle de Secciones

### 3.1 System Prompt / Identidad (Sección 1)
Instrucciones fijas que definen el comportamiento SMMA. El agente no puede modificarlas. Incluye:
- Quién es el agente y cómo debe gestionar su memoria
- Reglas de auto-optimización
- Referencia a las herramientas disponibles

### 3.2 Dashboard de Metacognición (Sección 2)
Inyectado automáticamente por el sistema en cada iteración. Ejemplo:

```
ESTADO DE MEMORIA:
- Contexto: 45,242 / 160,000 tokens (28.3%)
- Presión de memoria: BAJA
- Secciones en disco cargadas: 4/5
- Acción recomendada: Ninguna. Procede con normalidad.
```

La **presión de memoria** ($P_m$) se calcula como:

$$P_m = \left( \frac{T_{used}}{T_{safe}} \right) \times 100$$

Donde $T_{safe}$ es el 80% del límite real del modelo (margen de seguridad contra cortes abruptos).

El umbral de activación de auto-optimización es un **hiperparámetro** configurable. Valor inicial sugerido: 50%. Se ajusta experimentalmente.

### 3.3 Perfil del Usuario (Sección 3)
Persistente entre sesiones. El agente lo actualiza conforme aprende sobre el usuario.

```markdown
## Usuario
- Nombre: [nombre]
- Prefiere soluciones pragmáticas sobre académicamente perfectas
- Stack principal: Python, async
- Estilo de código: limpio, pocos comentarios, nombres descriptivos
- Decisiones recurrentes: SQLite sobre Postgres, simplicidad sobre escalabilidad prematura
- Idioma de comunicación: Español
```

### 3.4 Contexto del Proyecto (Sección 4)
Visión global del proyecto. Se carga al inicio de cada sesión.

```markdown
## Proyecto: ai-task-orchestrator
- Propósito: Orquestador de tareas para agentes de IA
- Stack: Python 3.12, asyncio, SQLite
- Arquitectura: [descripción breve]
- Módulos principales: task_runner/, core/, tools/
- Convenciones: [estilo de código, patrones usados]
```

### 3.5 Estado de la Tarea Actual (Sección 5)
El "post-it grande" en el centro de la mesa. Responde a: ¿qué estoy haciendo ahora mismo?

```markdown
## Tarea Actual
- Objetivo: Refactorizar el módulo de autenticación para soportar OAuth2
- Criterio de éxito: Tests pasando, backward compatible
- Subtareas: [x] Analizar código actual [ ] Diseñar interfaz [ ] Implementar
- Bloqueado por: Nada
- Decisiones tomadas: Usar authlib (más mantenida que oauthlib)
```

### 3.6 Notas del Agente (Sección 6)
Scratchpad libre. El equivalente a post-its en la mesa. No existe en ninguna arquitectura actual.

```markdown
## Notas
- El módulo auth.py tiene dependencias circulares con user.py — investigar
- Hipótesis: el bug de timeout es por connection pooling, no por la query
- TODO: preguntar al usuario sobre la política de retry
```

### 3.7 Log de Acciones (Sección 7)
Historial de lo ejecutado en la sesión actual. Es lo más susceptible a resumen y poda.

### 3.8 Espacio de Trabajo (Sección 8)
Contenido volátil: archivos abiertos, outputs de herramientas, resultados de búsquedas. Es lo primero que se poda cuando sube la presión de memoria.

---

## 4. Memoria Persistente (Disco)

Estructura en disco, legible tanto por el agente como por el humano:

```
.smma/
├── identity.md          # System prompt (sección 1, solo lectura)
├── user_profile.md      # Sección 3, editable por el agente
├── project_context.md   # Sección 4, editable por el agente
├── current_task.md      # Sección 5, editable por el agente
├── agent_notes.md       # Sección 6, editable por el agente
└── session_log.jsonl    # Registro inmutable ("La Cinta")
```

**Principios de diseño:**
- **Sin bases de datos vectoriales.** Archivos markdown planos, simples, auditables.
- **Legibles por humanos.** El usuario puede abrir cualquier archivo y ver qué "piensa" el agente.
- **Editables por ambos.** El humano puede corregir el perfil de usuario o el contexto del proyecto manualmente si lo desea.
- **Cargados al inicio.** Las secciones 3–6 se leen de disco al comenzar cada sesión.

### El Registro Inmutable (session_log.jsonl)
Guarda absolutamente todo en su forma original. Incluso si el agente elimina un mensaje de su contexto activo, el registro persiste.

```json
{"id": 1, "timestamp": "2026-02-21T10:00:00Z", "role": "user", "content": "...", "token_count": 150}
{"id": 2, "timestamp": "2026-02-21T10:00:05Z", "role": "assistant", "content": "...", "token_count": 320}
{"id": 3, "timestamp": "2026-02-21T10:00:10Z", "role": "tool", "content": "...", "token_count": 890}
```

Permite recuperación si el agente detecta que ha "olvidado" algo importante tras un resumen o poda.

---

## 5. Herramientas de Gestión de Memoria (System Calls)

6 herramientas que cubren el ciclo completo de gestión:

### Gestión del contexto activo (RAM)

| Herramienta | Parámetros | Descripción |
|:---|:---|:---|
| `prune_messages` | `message_ids: list[int]` | Elimina mensajes redundantes del contexto activo (logs de error repetidos, intentos fallidos, outputs obsoletos) |
| `summarize_range` | `start_id, end_id, summary_text` | Reemplaza un bloque de mensajes por un único resumen compacto |
| `recall_original` | `message_id` | Recupera el contenido original de un mensaje borrado o resumido desde el Registro Inmutable |

### Gestión de memoria persistente (Disco)

| Herramienta | Parámetros | Descripción |
|:---|:---|:---|
| `save_to_disk` | `file_name, content` | Persiste o actualiza un archivo `.md` en `.smma/` |
| `load_from_disk` | `file_name` | Carga un archivo `.md` de `.smma/` al contexto activo |
| `edit_section` | `section_name, new_content` | Actualiza directamente una sección del contexto (perfil, notas, tarea, proyecto) |

---

## 6. Flujo de Operación (Control Loop)

1. **Inicio de sesión:** El sistema carga las secciones 1–6 desde disco. El agente tiene visión global inmediata.
2. **Recepción de tarea:** El usuario asigna trabajo. El agente actualiza la sección 5 (Estado de la Tarea).
3. **Ejecución:** El agente trabaja, usa herramientas, razona. El log de acciones y espacio de trabajo crecen.
4. **Auto-optimización:** Basándose en el Dashboard:
   - Si $P_m$ > umbral → `summarize_range` sobre pasos iniciales, `prune_messages` sobre outputs obsoletos
   - Si un intento falla 3+ veces → podar intentos fallidos, anotar la conclusión en Notas del Agente
   - Si descubre información relevante sobre el usuario/proyecto → `edit_section` o `save_to_disk`
5. **Verificación:** Si el agente duda de un dato tras un resumen → `recall_original`
6. **Fin de sesión:** El agente actualiza los archivos persistentes con lecciones aprendidas, estado de la tarea, y notas relevantes.

---

## 7. Jerarquía de Confianza

Cuando existen datos contradictorios entre fuentes:

1. **Registro Inmutable** (máxima confianza — es lo que realmente pasó)
2. **Archivos en disco** (alta confianza — persistentes y editables deliberadamente)
3. **Resúmenes en contexto** (confianza media — pueden perder matices)
4. **Inferencia del agente** (confianza baja — verificar antes de actuar)

---

## 8. Mecanismos de Seguridad

- **IDs persistentes:** Incrementales y únicos por sesión.
- **Reset humano:** El usuario puede forzar un reset del contexto si el agente entra en un bucle de auto-edición.
- **Auditoría:** Todos los archivos `.smma/` son legibles por el humano en cualquier momento.
- **Protección de mensajes:** El usuario puede marcar mensajes como `pinned` para que el agente no los pode.
- **Registro inmutable:** Garantiza que nunca se pierde información de forma irrecuperable.

---

## 9. Consideraciones de Implementación

- **Modelos compatibles:** Cualquier LLM con buena capacidad de seguimiento de instrucciones y soporte de tool calling.
- **Tokenizador:** Se usa el tokenizador nativo del modelo para cálculos precisos de $P_m$.
- **Umbral de auto-optimización:** Hiperparámetro configurable. Comenzar en 50% y ajustar experimentalmente.
- **Tamaño máximo de secciones en disco:** Configurable por sección para evitar que una sola sección consuma demasiado contexto al cargar.
