# Arquitectura SMMA: Self-Managed Mnemonic Architecture
**Versión:** 1.0  
**Objetivo:** Permitir que un Agente de IA gestione proactivamente su ventana de contexto, memoria a largo plazo y precisión histórica mediante herramientas de auto-edición.

---

## 1. Componentes del Sistema

### A. El Núcleo Agéntico (LLM)
El motor de razonamiento. Debe ser un modelo con alta capacidad de seguimiento de instrucciones (Gemini 1.5 Pro, GPT-4o, Claude 3.5 Sonnet) que reciba metadatos constantes sobre su estado interno.

### B. Memoria de Trabajo (Contexto Activo)
Es el "presente" de la IA. No es estático; es una lista de objetos de mensaje que la IA puede modificar.
* **Atributos de mensaje:** `id`, `role`, `content`, `timestamp`, `token_count`, `is_summary` (booleano).

### C. El Registro Inmutable (La "Cinta")
Una base de datos (SQLite o JSONL) que guarda **absolutamente todo** en su forma original. 
* Incluso si la IA borra un mensaje de su "Memoria de Trabajo", el registro persiste.
* Permite la recuperación de datos si la IA detecta que ha "olvidado" algo importante.

### D. Memoria Semántica (LTM - Long Term Memory)
Base de datos vectorial (ChromaDB, Pinecone) para almacenar conceptos, soluciones a problemas pasados y preferencias del usuario que deben persistir entre diferentes sesiones o tareas.

---

## 2. El "Dashboard" de Metacognición
En cada iteración, el sistema inyecta en el `System Prompt` o como un mensaje de sistema recurrente el estado de sus recursos:

> **ESTADO DE MEMORIA ACTUAL:**
> - Contexto Usado: 45,242 / 200,000 tokens (22.6%)
> - Mensajes Activos: 24
> - Alerta: El contexto está despejado. Procede con normalidad.

---

## 3. Toolset de Gestión de Memoria (`MemoryTools`)

La IA tiene acceso a las siguientes funciones críticas:

| Herramienta | Parámetros | Descripción |
| :--- | :--- | :--- |
| `prune_messages` | `message_ids: list[int]` | Elimina mensajes redundantes o logs de errores del contexto activo. |
| `summarize_range` | `start_id, end_id, summary_text` | Reemplaza un bloque de mensajes por un único mensaje de tipo `summary`. |
| `recall_original` | `message_id` | Consulta el **Registro Inmutable** y trae de vuelta el contenido exacto de un mensaje borrado o resumido. |
| `commit_to_ltm` | `key, content, tags` | Guarda información crítica en la memoria a largo plazo (fuera de la sesión). |
| `search_ltm` | `query` | Realiza una búsqueda semántica en experiencias pasadas. |

---

## 4. Flujo de Operación (Control Loop)

1.  **Entrada:** El usuario asigna una tarea compleja.
2.  **Análisis de Recursos:** La IA revisa su Dashboard de tokens.
3.  **Ejecución:** La IA usa herramientas para resolver la tarea.
4.  **Auto-Optimización (Trigger):** * Si tokens > 70%, la IA *debe* ejecutar `summarize_range` sobre los pasos iniciales.
    * Si una herramienta falla 3 veces, la IA usa `prune_messages` para borrar los intentos fallidos y no "contaminar" su lógica futura.
5.  **Verificación:** Si la IA duda de un dato tras un resumen, usa `recall_original`.
6.  **Finalización:** Antes de cerrar, la IA decide qué lecciones aprendidas enviar a `commit_to_ltm`.

---

## 5. Lógica de Cálculo de Contexto
Para la gestión precisa, se utiliza la siguiente relación para determinar la "presión de memoria" ($P_m$):

$$P_m = \left( \frac{T_{used}}{T_{max}} \right) \times 100$$

Donde:
- $T_{used}$: Tokens actuales calculados mediante el tokenizador del modelo.
- $T_{max}$: Límite de seguridad definido (ej. 80% del límite real del modelo para evitar cortes abruptos).

---

## 6. Consideraciones de Implementación
* **IDs Persistentes:** Los IDs de los mensajes deben ser incrementales y únicos por sesión.
* **Respaldo de Seguridad:** El sistema debe permitir al usuario humano forzar un `reset` del contexto si la IA se "auto-edita" hacia un bucle infinito.
* **Prompting de Identidad:** La IA debe ser instruida para verse a sí misma como un "Arquitecto de su propia información".