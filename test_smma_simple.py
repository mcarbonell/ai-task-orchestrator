#!/usr/bin/env python3
"""
Test SMMA Fase 1 - Versión Simple (sin tool calling nativo)
Este test usa prompting estructurado para que el modelo gestione su memoria
mediante comandos de texto en lugar de tool calling nativo.

Compatible con modelos Zen que no soportan tools (minimax-m2.5-free, etc.)
"""

import os
import sys
import json
import re
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_runner.memory_manager import MemoryManager


def parse_action(response_text: str) -> dict:
    """
    Parsea la respuesta del modelo buscando comandos SMMA en formato:
    [ACTION:prune_messages]{"message_ids": [1, 2, 3]}[/ACTION]
    [ACTION:summarize_range]{"start_id": 0, "end_id": 5, "summary_text": "..."}[/ACTION]
    [ACTION:recall_original]{"message_id": 5}[/ACTION]
    [ACTION:finish_task]{"status": "completed", "summary": "..."}[/ACTION]
    """
    # Buscar patrón de acción
    pattern = r'\[ACTION:(\w+)\](.*?)\[/ACTION\]'
    matches = re.findall(pattern, response_text, re.DOTALL)
    
    if matches:
        action_name, args_json = matches[0]
        try:
            args = json.loads(args_json.strip())
            return {"action": action_name, "args": args}
        except json.JSONDecodeError as e:
            logger.warning(f"Error parseando JSON de acción: {e}")
            return {"action": "response", "content": response_text}
    
    return {"action": "response", "content": response_text}


def execute_action(action: dict, memory: MemoryManager) -> str:
    """Ejecuta una acción SMMA y devuelve el resultado."""
    action_name = action.get("action")
    args = action.get("args", {})
    
    if action_name == "prune_messages":
        message_ids = args.get("message_ids", [])
        removed = memory.prune_messages(message_ids)
        return f"[RESULTADO] Se borraron {removed} mensajes. IDs eliminados: {message_ids}[/RESULTADO]"
    
    elif action_name == "summarize_range":
        start_id = args.get("start_id")
        end_id = args.get("end_id")
        summary_text = args.get("summary_text", "")
        result = memory.summarize_range(start_id, end_id, summary_text)
        if result.get("success"):
            return f"[RESULTADO] Resumen creado. Se comprimieron {result['removed_count']} mensajes en ID {result['new_summary_id']}.[/RESULTADO]"
        else:
            return f"[ERROR] {result.get('error')}[/ERROR]"
    
    elif action_name == "recall_original":
        message_id = args.get("message_id")
        result = memory.recall_original(message_id)
        if result.get("success"):
            msg = result.get("message", {})
            return f"[RESULTADO] Recuperado de The Tape [ID {message_id}]:\nRole: {msg.get('role')}\nContent: {msg.get('content')}[/RESULTADO]"
        else:
            return f"[ERROR] {result.get('error')}[/ERROR]"
    
    elif action_name == "finish_task":
        status = args.get("status", "completed")
        summary = args.get("summary", "")
        return f"__FINISH__|{status}|{summary}"
    
    return f"[ERROR] Acción desconocida: {action_name}[/ERROR]"


def run_smma_test_simple():
    """
    Ejecuta el test SMMA usando requests directos a la API Zen
    con prompting estructurado en lugar de tool calling.
    """
    import requests
    from dotenv import load_dotenv
    
    load_dotenv()
    ZEN_API_KEY = os.getenv("ZEN_API_KEY")
    
    if not ZEN_API_KEY:
        logger.error("ZEN_API_KEY no encontrada en .env")
        return False
    
    # Configuración
    task_id = f"SMMA-SIMPLE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logs_dir = ".ai-tasks/logs"
    model = "minimax-m2.5-free"
    max_iterations = 15
    
    # Inicializar memoria
    memory = MemoryManager(
        task_id=task_id,
        logs_dir=logs_dir,
        max_tokens=8000,  # Límite bajo para forzar presión rápida
        target_pressure=0.5
    )
    
    # System prompt con instrucciones de SMMA
    system_prompt = """Eres un agente de IA con arquitectura SMMA (Self-Managed Mnemonic Architecture).

CAPACIDADES DE MEMORIA:
Tienes acceso a herramientas para gestionar tu propia memoria. Debes usarlas proactivamente.

FORMATO DE COMANDOS:
Para usar una herramienta, escribe EXACTAMENTE así:
[ACTION:nombre_herramienta]{argumentos en JSON}[/ACTION]

HERRAMIENTAS DISPONIBLES:

1. prune_messages - Borra mensajes para liberar tokens
   [ACTION:prune_messages]{"message_ids": [1, 2, 3]}[/ACTION]

2. summarize_range - Comprime un rango de mensajes en un resumen
   [ACTION:summarize_range]{"start_id": 0, "end_id": 5, "summary_text": "Resumen del contenido"}[/ACTION]

3. recall_original - Recupera un mensaje borrado/resumido desde The Tape
   [ACTION:recall_original]{"message_id": 5}[/ACTION]

4. finish_task - Finaliza la tarea
   [ACTION:finish_task]{"status": "completed", "summary": "Resumen de lo logrado"}[/ACTION]

INSTRUCCIONES CRÍTICAS:
- Monitorea la presión de memoria que se muestra en cada mensaje de sistema
- Si presión > 60%, DEBES usar summarize_range o prune_messages INMEDIATAMENTE
- Completa la tarea manteniendo la memoria bajo control
- Eres un "Arquitecto de tu propia información"
"""
    
    # Task prompt - más estructurado y con ejemplo claro
    task_prompt = """Realiza estos cálculos Fibonacci con gestión de memoria SMMA.

TAREA OBLIGATORIA:
Calcula Fib(1) hasta Fib(15), mostrando CADA paso así:
Fib(1) = 1
Fib(2) = 1  
Fib(3) = Fib(2) + Fib(1) = 1 + 1 = 2
Fib(4) = Fib(3) + Fib(2) = 2 + 1 = 3
...y así hasta Fib(15)

REGLAS DE MEMORIA:
- Cuando llegues a Fib(8), revisa el [SMMA DASHBOARD]
- Si presión > 50%, DEBES usar: [ACTION:summarize_range]{"start_id": 1, "end_id": 7, "summary_text": "Cálculos Fib(1)-Fib(7) resumidos"}[/ACTION]
- Luego continúa con Fib(9) hasta Fib(15)

AL FINALIZAR:
1. Usa: [ACTION:recall_original]{"message_id": 5}[/ACTION] para recuperar Fib(5)
2. Luego usa: [ACTION:finish_task]{"status": "completed", "summary": "Aquí lista los 15 números calculados"}[/ACTION]

IMPORTANTE: NO uses finish_task hasta haber calculado TODOS los números Fib(1) a Fib(15).

EMPIEZA AHORA - Responde con los cálculos de Fib(1) y Fib(2)."""
    
    # Inicializar conversación
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task_prompt}
    ]
    
    # Añadir a memoria
    for msg in messages:
        memory.add_message(msg)
    
    logger.info("=" * 80)
    logger.info(f"TEST SMMA SIMPLE - Task ID: {task_id}")
    logger.info(f"Modelo: {model}")
    logger.info("=" * 80)
    
    # Loop de ejecución
    for iteration in range(1, max_iterations + 1):
        logger.info(f"\n--- Iteración {iteration}/{max_iterations} ---")
        
        # Preparar mensajes con dashboard de memoria
        metrics = memory.get_metrics()
        dashboard = f"[SMMA DASHBOARD] Presión: {metrics['pressure_percent']}% | Tokens: {metrics['total_tokens']}/{metrics['max_tokens']} | Mensajes: {metrics['message_count']}"
        if metrics["is_critical"]:
            dashboard += " | ⚠️ CRÍTICO: Usa summarize_range o prune_messages AHORA"
        
        messages_with_dashboard = memory.get_active_messages_for_llm() + [
            {"role": "system", "content": dashboard}
        ]
        
        # Llamar a la API
        url = "https://opencode.ai/zen/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {ZEN_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages_with_dashboard
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"Respuesta del modelo ({len(content)} chars)")
            logger.debug(f"Contenido: {content[:200]}...")
            
            # Parsear acción
            action = parse_action(content)
            
            if action["action"] == "response":
                # El modelo respondió sin usar herramienta
                logger.info("El modelo respondió sin usar herramienta")
                memory.add_message({"role": "assistant", "content": content})
                
                # Verificar si menciona finish_task o completó la tarea
                if "finish_task" in content.lower() and "fib(15)" not in content.lower():
                    logger.warning("El modelo intentó finalizar sin completar todos los cálculos")
                    memory.add_message({
                        "role": "user",
                        "content": "NO has completado la tarea. Debes calcular TODOS los números Fib(1) hasta Fib(15) antes de usar finish_task. Continúa con los cálculos."
                    })
                else:
                    # Si no hay acción, pedir explícitamente que continúe
                    memory.add_message({
                        "role": "user", 
                        "content": "Continúa con los cálculos Fibonacci. Recuerda usar [ACTION:...] cuando necesites gestionar memoria o finalizar."
                    })
            else:
                # El modelo usó una herramienta
                logger.info(f"🛠️ Herramienta detectada: {action['action']}")
                memory.add_message({"role": "assistant", "content": content})
                
                # Ejecutar acción
                result = execute_action(action, memory)
                
                if result.startswith("__FINISH__"):
                    # Tarea completada
                    _, status, summary = result.split("|", 2)
                    logger.info("=" * 80)
                    logger.info("🏁 TAREA FINALIZADA")
                    logger.info(f"Estado: {status}")
                    logger.info(f"Resumen: {summary[:300]}...")
                    logger.info("=" * 80)
                    
                    # Analizar The Tape
                    analyze_tape(memory.tape_path)
                    return True
                else:
                    # Añadir resultado al contexto
                    memory.add_message({"role": "user", "content": result})
                    logger.info(f"Resultado: {result[:150]}...")
                    
        except Exception as e:
            logger.error(f"Error en iteración {iteration}: {e}")
            import traceback
            traceback.print_exc()
            # Continuar en lugar de fallar inmediatamente
            memory.add_message({
                "role": "user",
                "content": f"Hubo un error: {str(e)}. Por favor continúa con la tarea."
            })
            continue
    
    logger.warning("Se alcanzó el límite de iteraciones sin finalizar")
    analyze_tape(memory.tape_path)
    return False


def analyze_tape(tape_path: str):
    """Analiza y muestra estadísticas de The Tape."""
    if not os.path.exists(tape_path):
        logger.warning(f"The Tape no encontrado: {tape_path}")
        return
    
    with open(tape_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    actions = {}
    for line in lines:
        try:
            record = json.loads(line.strip())
            action = record.get('action', 'UNKNOWN')
            actions[action] = actions.get(action, 0) + 1
        except:
            pass
    
    logger.info(f"\n📊 The Tape: {len(lines)} registros")
    for action, count in actions.items():
        logger.info(f"  - {action}: {count}")
    
    smma_used = any(a in actions for a in ['PRUNE', 'SUMMARIZED_OUT'])
    if smma_used:
        logger.info("✅ Se usaron herramientas SMMA")
    else:
        logger.info("⚠️ No se detectaron herramientas SMMA")


if __name__ == "__main__":
    success = run_smma_test_simple()
    sys.exit(0 if success else 1)
