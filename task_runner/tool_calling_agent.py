import os
import json
import logging
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    logging.warning("El paquete 'openai' no está instalado. Instálalo con 'pip install openai'")
    OpenAI = None

load_dotenv()
logger = logging.getLogger(__name__)

class ToolCallingAgent:
    """
    Agente 100% basado en API (Tool Calling) usando la abstracción de OpenAI.
    Soporta OpenRouter y la nueva API Zen (OpenCode).
    """

    def __init__(
        self, 
        model: str = "kimi-k2.5-free", 
        provider: str = "zen",  # "zen" o "openrouter"
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        max_iterations: int = 15,
        tasks_dir: str = "tasks"
    ):
        self.model = model
        self.max_iterations = max_iterations
        self.tasks_dir = tasks_dir
        
        # Configurar URLs por defecto según el proveedor
        if provider == "zen":
            self.base_url = base_url or "https://opencode.ai/zen/v1"
            self.api_key = api_key or os.getenv("ZEN_API_KEY")
        elif provider == "openrouter":
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        else:
            self.base_url = base_url
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            logger.error(f"No se encontró API Key para el proveedor '{provider}'")
        
        # Instanciar cliente
        if OpenAI:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
            )
        else:
            self.client = None


        self.messages: List[Dict[str, Any]] = []
        
        # Definición de herramientas (JSON Schema)
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_terminal_command",
                    "description": "Ejecuta un comando en la terminal (PowerShell o CMD) y devuelve stdout y stderr. Úsalo para compilar, testear, o usar utilidades del CLI.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "El comando exacto a ejecutar."
                            },
                            "cwd": {
                                "type": "string",
                                "description": "Directorio de trabajo (opcional). Por defecto usa la raíz del proyecto."
                            }
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Lee el contenido íntegro de un archivo local.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta relativa o absoluta del archivo a leer."
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Escribe contenido en un archivo (sobrescribe o crea uno nuevo).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Ruta del archivo."
                            },
                            "content": {
                                "type": "string",
                                "description": "Contenido completo a escribir en el archivo."
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_subtask",
                    "description": "Crea una nueva tarea en formato markdown para el Orchestrator. Útil cuando descubres que un problema es muy complejo y debe manejarse por separado.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Título breve de la nueva tarea."
                            },
                            "description": {
                                "type": "string",
                                "description": "Descripción detallada del problema o feature a implementar."
                            }
                        },
                        "required": ["title", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "finish_task",
                    "description": "Finaliza tu ejecución declarando que has acabado tu objetivo o que es imposible continuar.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": ["completed", "failed"],
                                "description": "Estado final de la tarea."
                            },
                            "summary": {
                                "type": "string",
                                "description": "Resumen técnico de lo que se hizo o la razón del fallo."
                            }
                        },
                        "required": ["status", "summary"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "prune_messages",
                    "description": "SMMA: Elimina mensajes redundantes o logs de errores del contexto activo para liberar tokens. Se recomienda usar si te acercas al límite de contexto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_ids": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Lista de IDs numéricos de los mensajes a borrar."
                            }
                        },
                        "required": ["message_ids"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "summarize_range",
                    "description": "SMMA: Reemplaza un bloque de mensajes (entre start_id y end_id) por un mensaje resumen que conserva lo importante.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "start_id": {
                                "type": "integer",
                                "description": "ID del primer mensaje a resumir."
                            },
                            "end_id": {
                                "type": "integer",
                                "description": "ID del último mensaje a resumir inclusive."
                            },
                            "summary_text": {
                                "type": "string",
                                "description": "Texto del resumen que encapsula la información útil resuelta en esos pasos."
                            }
                        },
                        "required": ["start_id", "end_id", "summary_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recall_original",
                    "description": "SMMA: Recupera el contenido original completo de un mensaje desde el Registro Inmutable (The Tape). Útil cuando has resumido o borrado algo pero necesitas verificar detalles exactos que ya no están en el contexto activo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message_id": {
                                "type": "integer",
                                "description": "ID numérico del mensaje a recuperar desde The Tape."
                            }
                        },
                        "required": ["message_id"]
                    }
                }
            }
        ]


    def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Ejecuta una herramienta y devuelve la salida como string."""
        logger.info(f"🛠️ Tool Call: {name}({args})")
        
        # Interceptor SMMA (Fase 4)
        if hasattr(self, 'memory') and name not in ["prune_messages", "summarize_range", "finish_task"]:
            metrics = self.memory.get_metrics()
            # Interceptamos si la presión de memoria supera un límite peligroso (ej. 85%)
            if metrics["pressure_percent"] > 85.0:
                logger.warning(f"🚨 INTERCEPTOR SMMA ACTIVO: Bloqueando {name} por falta de memoria ({metrics['pressure_percent']}%)")
                return f"ERROR CRÍTICO: Contexto al límite ({metrics['pressure_percent']}%). Tienes estrictamente prohibido ejecutar la herramienta '{name}'. Tu siguiente acción OBLIGATORIA debe ser invocar 'summarize_range' o 'prune_messages' para limpiar el historial y liberar tokens."

        try:
            if name == "execute_terminal_command":
                cmd = args.get("command")
                cwd = args.get("cwd", os.getcwd())
                # Ejecutamos con timeout por seguridad
                # En Windows forzamos pwsh o dejamos el shell default
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    cwd=cwd, 
                    capture_output=True, 
                    text=True,
                    timeout=120
                )
                
                output = f"EXIT CODE: {result.returncode}\n"
                if result.stdout:
                    output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"
                    
                return output.strip() or "Comando ejecutado sin salida (éxito)."

            elif name == "read_file":
                path = args.get("path")
                if not os.path.exists(path):
                    return f"ERROR: Archivo no encontrado - {path}"
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()

            elif name == "write_file":
                path = args.get("path")
                content = args.get("content")
                
                # Asegurar directorio
                os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
                
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"ÉXITO: Archivo guardado correctamente en {path}"

            elif name == "create_subtask":
                title = args.get("title")
                desc = args.get("description")
                task_id = f"T-AUTO-{int(datetime.now().timestamp())}"
                filename = f"{self.tasks_dir}/{task_id}.md"
                
                os.makedirs(self.tasks_dir, exist_ok=True)
                content = f"---\nid: {task_id}\ntitle: \"{title}\"\nstatus: pending\npriority: high\ndependencies: []\n---\n\n## Descripción\n{desc}\n"
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                    
                return f"ÉXITO: Subtarea creada {filename}"
                
            elif name == "finish_task":
                status = args.get("status")
                summary = args.get("summary")
                return f"TASK_FINISHED_{status.upper()}: {summary}"
                
            elif name == "prune_messages":
                message_ids = args.get("message_ids", [])
                if not isinstance(message_ids, list):
                    return "ERROR: message_ids debe ser una lista de enteros."
                removed = self.memory.prune_messages(message_ids)
                return f"ÉXITO: Se borraron {removed} mensajes del contexto activo."
                
            elif name == "summarize_range":
                start_id = args.get("start_id")
                end_id = args.get("end_id")
                summary_text = args.get("summary_text")
                res = self.memory.summarize_range(start_id, end_id, summary_text)
                if res.get("success"):
                    return f"ÉXITO: Se resumieron {res['removed_count']} mensajes. Resumen insertado como ID visible {res['new_summary_id']}."
                else:
                    return f"ERROR resumiendo: {res.get('error')}"
                
            elif name == "recall_original":
                message_id = args.get("message_id")
                res = self.memory.recall_original(message_id)
                if res.get("success"):
                    msg = res.get("message", {})
                    return f"ÉXITO: Mensaje original recuperado de The Tape [ID {res['visible_id']}, timestamp {res['timestamp']}]:\\nRole: {msg.get('role')}\\nContent: {msg.get('content')}"
                else:
                    return f"ERROR recuperando: {res.get('error')}"

            else:
                return f"ERROR: Herramienta desconocida '{name}'"

                
        except Exception as e:
            return f"ERROR al ejecutar '{name}': {str(e)}"

    def run_task(self, task_id: str, system_prompt: str, task_prompt: str, logs_dir: str = ".ai-tasks/logs") -> Dict[str, Any]:
        """Inicia el loop de agencia basándonos en la directiva inicial."""
        if not self.client:
            return {"status": "failed", "summary": "No se pudo inicializar OpenAI client (Revisa pip o OPENROUTER_API_KEY)."}
            
        from .memory_manager import MemoryManager
        self.memory = MemoryManager(task_id=task_id, logs_dir=logs_dir, max_tokens=200000, target_pressure=0.25)

        # Limpiamos/reiniciamos el historial
        self.memory.add_message({"role": "system", "content": system_prompt})
        self.memory.add_message({"role": "user", "content": task_prompt})

        iteration = 0
        final_status = "failed"
        final_summary = "Límite de iteraciones alcanzado sin un 'finish_task'."

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"🔄 Iteración {iteration}/{self.max_iterations}")
            
            # Llamamos al modelo
            try:
                # Fase 2 Dashboard
                metrics = self.memory.get_metrics()
                dashboard_msg = None
                if metrics["message_count"] > 4:
                    dash_content = f"[SISTEMA SMMA] Presión de memoria: {metrics['pressure_percent']}%. Mensajes activos: {metrics['message_count']}."
                    if metrics["is_critical"]:
                        dash_content += " ALERTA: Acercándose al límite de contexto. Considera usar herramientas de limpieza explícitamente si existen, o resume."
                    dashboard_msg = {"role": "system", "content": dash_content}
                
                messages_to_send = self.memory.get_active_messages_for_llm()
                if dashboard_msg:
                    messages_to_send.append(dashboard_msg)

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_to_send,
                    tools=self.tools,
                    tool_choice="auto"
                )
            except Exception as e:
                logger.error(f"Error llamando a la API: {e}")
                return {"status": "failed", "summary": f"API Error: {e}"}

            message = response.choices[0].message
            # Guardamos respuesta en el historial
            self.memory.add_message(message) 

            # ¿El modelo pidió ejecutar herramientas?
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                        
                    # Ejecutar herramienta local
                    result_string = self._execute_tool(func_name, args)
                    
                    # Añadimos resultado al hilo para que la IA lo sepa en la próxima iteración
                    # self.messages.append({
                    #    "role": "tool",
                    #    "tool_call_id": tool_call.id,
                    #    "name": func_name,
                    #    "content": result_string
                    # })

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": result_string
                    }
                    self.memory.add_message(tool_msg)  # ¡Añádelo a MemoryManager!
                    
                    # Interceptar finalización
                    if func_name == "finish_task":
                        status_str = args.get("status", "completed")
                        return {
                            "status": status_str,
                            "summary": args.get("summary", "Done."),
                            "iterations": iteration
                        }
            else:
                # El agente decidió no llamar herramientas y solo respondió texto
                # A veces lo hacen para dar conversación. Le forzamos a seguir
                logger.debug(f"IA: {message.content}")
                self.messages.append({
                    "role": "user", 
                    "content": "No has llamado a 'finish_task' ni otra herramienta. Por favor, decide qué debes hacer a continuación o finaliza."
                })

        return {
            "status": final_status, 
            "summary": final_summary,
            "iterations": iteration
        }
