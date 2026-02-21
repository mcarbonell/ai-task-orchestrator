import os
import json
import logging
import uuid
import time
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Gestor de contexto (Working Memory) y Registro Inmutable (The Tape).
    Implementa la Arquitectura SMMA (Self-Managed Mnemonic Architecture) fase 1.
    """
    def __init__(self, task_id: str, logs_dir: str = ".ai-tasks/logs", max_tokens: int = 100000, target_pressure: float = 0.5):
        self.task_id = task_id
        self.logs_dir = logs_dir
        self.max_tokens = max_tokens
        # Recomendamos 25% - 50% según la indicación del usuario
        self.target_pressure = target_pressure 
        
        # La memoria activa con metadatos: [{ "internal_id": str, "tokens": int, "role": str, "raw_msg": Any, "visible_id": int }]
        self.messages: List[Dict[str, Any]] = []
        
        # Archivo append-only "The Tape"
        self.tape_path = os.path.join(self.logs_dir, f"tape_{self.task_id}.jsonl")
        self._ensure_logs_dir()

        # Contador autoincremental para IDs de mensajes expuestos al LLM
        # Así el LLM puede borrarlos pidiendo "borra el mensaje 4"
        self._next_id = 0
        
    def _ensure_logs_dir(self):
        os.makedirs(self.logs_dir, exist_ok=True)
        # Si no existe the tape, escribimos cabecera
        if not os.path.exists(self.tape_path):
            with open(self.tape_path, "w", encoding="utf-8") as f:
                f.write(json.dumps({
                    "action": "INIT", 
                    "timestamp": time.time(), 
                    "task_id": self.task_id
                }) + "\n")
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimación aproximada de tokens (1 token ≈ 4 caracteres ingles/código, 3 en español).
        Usaremos 3.5 como promedio conservador."""
        if not text:
            return 0
        return max(1, int(len(text) / 3.5))
        
    def _calculate_message_tokens(self, msg_dict: Dict[str, Any]) -> int:
        """Calcula tokens aprox de un mensaje serializado a dict."""
        content_str = str(msg_dict.get("content", ""))
        
        if "tool_calls" in msg_dict and msg_dict["tool_calls"]:
            content_str += str(msg_dict["tool_calls"])
            
        return self._estimate_tokens(content_str)
        
    def _append_to_tape(self, msg_dict: Dict[str, Any], msg_internal_id: str, visible_id: int):
        """Escribe de forma inmutable a La Cinta (registro persistente)."""
        try:
            tape_record = {
                "internal_id": msg_internal_id,
                "visible_id": visible_id,
                "timestamp": time.time(),
                "action": "ADD_MESSAGE",
                "message": msg_dict
            }
            with open(self.tape_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(tape_record) + "\n")
        except Exception as e:
            logger.error(f"Error escribiendo en The Tape: {e}")

    def add_message(self, msg: Any) -> int:
        """Añade un mensaje a la memoria de trabajo y a La Cinta. Devuelve el ID visible para el LLM."""
        is_obj = hasattr(msg, "role")
        
        # Tratar de convertir a dicc solo para conteo y logs
        msg_dict = {}
        if is_obj:
            try:
                # Intento de parsear Pydantic models (OpenAI>=1.0)
                msg_dict = msg.model_dump()
            except AttributeError:
                msg_dict = {"role": getattr(msg, "role", "unknown"), "content": getattr(msg, "content", "")}
                if hasattr(msg, "tool_calls"): msg_dict["tool_calls"] = msg.tool_calls
                if hasattr(msg, "name"): msg_dict["name"] = msg.name
                if hasattr(msg, "tool_call_id"): msg_dict["tool_call_id"] = msg.tool_call_id
        else:
            msg_dict = dict(msg) # asumimos un diccionario normal
            
        msg_internal_id = str(uuid.uuid4())[:12]
        visible_id = self._next_id
        self._next_id += 1
        
        tokens = self._calculate_message_tokens(msg_dict)
        
        # En memory guardamos un wrapper, pero dejaremos un campo `raw_msg` 
        # para pasárselo intacto a la API después (necesario por las clases openai)
        wrapper = {
            "internal_id": msg_internal_id,
            "visible_id": visible_id,
            "role": msg_dict.get("role", "unknown"),
            "tokens": tokens,
            "raw_msg": msg
        }
        
        self.messages.append(wrapper)
        self._append_to_tape(msg_dict, msg_internal_id, visible_id)
        
        return visible_id
        
    def get_active_messages_for_llm(self) -> List[Any]:
        """Devuelve los mensajes crudos listos para ser enviados al SDK del modelo."""
        return [m["raw_msg"] for m in self.messages]

    def get_messages_with_ids(self) -> List[Dict[str, Any]]:
        """Devuelve un formato digerible para generar el dashboard del agente."""
        return [
            {
                "id": m["visible_id"],
                "role": m["role"],
                "tokens": m["tokens"],
                "content_preview": str(getattr(m["raw_msg"], "content", m["raw_msg"].get("content", "")))[:50].replace("\n", " ") + "..."
            }
            for m in self.messages
        ]
        
    def get_metrics(self) -> Dict[str, Any]:
        """Calcula The Memory Pressure ($P_m$) y otros datos de la memoria."""
        total_tokens = sum(m["tokens"] for m in self.messages)
        pressure = (total_tokens / self.max_tokens) * 100 if self.max_tokens > 0 else 0
        
        return {
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "pressure_percent": round(pressure, 2),
            "target_pressure": round(self.target_pressure * 100, 2),
            "message_count": len(self.messages),
            "is_critical": pressure > (self.target_pressure * 100 * 1.5) # Si excede 50% extra de su target ideal
        }
        
    def prune_messages(self, visible_ids_to_remove: List[int]) -> int:
        """Herramienta SMMA: Elimina mensajes del contexto activo."""
        initial_len = len(self.messages)
        
        # Filtramos
        removed_msgs = [m for m in self.messages if m["visible_id"] in visible_ids_to_remove]
        self.messages = [m for m in self.messages if m["visible_id"] not in visible_ids_to_remove]
        
        # Registrar mutación en The Tape
        for rm in removed_msgs:
            tape_record = {"internal_id": rm["internal_id"], "visible_id": rm["visible_id"], "timestamp": time.time(), "action": "PRUNE"}
            try:
                with open(self.tape_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(tape_record) + "\n")
            except Exception:
                pass
                
        return initial_len - len(self.messages)

    def summarize_range(self, start_id: int, end_id: int, summary_text: str) -> Dict[str, Any]:
        """Herramienta SMMA: Comprime una seccion de historia en un solo mensaje."""
        # Encontramos los index en el array
        start_idx = -1
        end_idx = -1
        
        for i, m in enumerate(self.messages):
            if m["visible_id"] == start_id: start_idx = i
            if m["visible_id"] == end_id: end_idx = i
            
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            return {"success": False, "error": f"Invalid IDs. start_idx={start_idx}, end_idx={end_idx}"}
            
        # Extraer los borrados
        removed = self.messages[start_idx:end_idx+1]
        
        # Crear mensaje reemplazo como diccionario (raw_msg será diccionario, 
        # lo cual es soportado por los clientes de OpenAI al menos para roles estándares)
        visible_id = self._next_id
        self._next_id += 1
        
        summary_raw_dict = {"role": "system", "content": f"[MEMORIA RESUMIDA (IDs {start_id}-{end_id})]: {summary_text}"}
        tokens = self._calculate_message_tokens(summary_raw_dict)
        internal_id = str(uuid.uuid4())[:12]
        
        replacement = {
            "internal_id": internal_id,
            "visible_id": visible_id,
            "role": "system",
            "tokens": tokens,
            "raw_msg": summary_raw_dict
        }
        
        # Splicing array
        self.messages[start_idx:end_idx+1] = [replacement]
        
        # Log Tape
        self._append_to_tape(summary_raw_dict, internal_id, visible_id)
        for rm in removed:
            tape_record = {"internal_id": rm["internal_id"], "visible_id": rm["visible_id"], "timestamp": time.time(), "action": "SUMMARIZED_OUT"}
            try:
                with open(self.tape_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(tape_record) + "\n")
            except: pass
            
        return {"success": True, "removed_count": len(removed), "new_summary_id": visible_id}

    def recall_original(self, visible_id: int) -> Dict[str, Any]:
        """Herramienta SMMA: Recupera el contenido original de un mensaje desde La Cinta (The Tape).
        
        Útil cuando la IA ha resumido o borrado algo pero necesita verificar detalles exactos.
        """
        try:
            if not os.path.exists(self.tape_path):
                return {"success": False, "error": "The Tape no existe"}
            
            # Buscar en el archivo JSONL
            with open(self.tape_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        # Buscar por visible_id en mensajes añadidos
                        if record.get("visible_id") == visible_id and record.get("action") == "ADD_MESSAGE":
                            return {
                                "success": True,
                                "visible_id": visible_id,
                                "internal_id": record.get("internal_id"),
                                "timestamp": record.get("timestamp"),
                                "message": record.get("message")
                            }
                    except json.JSONDecodeError:
                        continue
            
            return {"success": False, "error": f"No se encontró mensaje con visible_id={visible_id} en The Tape"}
            
        except Exception as e:
            return {"success": False, "error": f"Error leyendo The Tape: {str(e)}"}
