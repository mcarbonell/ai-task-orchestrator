import os
import sys

from task_runner.tool_calling_agent import ToolCallingAgent
from task_runner.memory_manager import MemoryManager

def test_interceptor():
    print("\n--- TEST SMMA: INTERCEPTOR FASE 4 ---")
    
    agent = ToolCallingAgent(model="test")
    # Inicializamos una memoria forzada muy pequeña
    agent.memory = MemoryManager(task_id="TEST-001", logs_dir=".ai-tasks/logs", max_tokens=100, target_pressure=0.25)
    
    # Rellenamos de basura para aumentar tokens (aprox 3.5 char = 1 token)
    basura = "a" * int(100 * 3.5) # aprox ~100 tokens > 85% de 100
    agent.memory.add_message({"role": "user", "content": basura})
    
    metrics = agent.memory.get_metrics()
    print(f"Presión actual: {metrics['pressure_percent']}%")
    
    # Tratamos de ejecutar un comando de shell (debe ser bloqueado)
    print("\nIntento LLM de llamar a 'execute_terminal_command'...")
    res = agent._execute_tool("execute_terminal_command", {"command": "echo hola"})
    print(f"Salida de la tool:\n>> {res}")
    
    # Tratamos de limpiar la memoria (NO debe ser bloqueado)
    print("\nIntento LLM de llamar a 'prune_messages'...")
    # Le pasaremos un ID inválido solo para ver que NO da error crítico de contexto
    res_prune = agent._execute_tool("prune_messages", {"message_ids": [777]})
    print(f"Salida de la tool prune:\n>> {res_prune}")
    
if __name__ == "__main__":
    test_interceptor()
