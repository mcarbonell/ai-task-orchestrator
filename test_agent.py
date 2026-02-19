import os
import logging
from dotenv import load_dotenv
from task_runner.tool_calling_agent import ToolCallingAgent

logging.basicConfig(level=logging.INFO)
load_dotenv()

def main():
    print("Iniciando ToolCallingAgent...")
    
    agent = ToolCallingAgent(
        model="kimi-k2.5-free", # Modelos gratis potentes de Zen
        provider="zen",         # "zen" u "openrouter"
        max_iterations=10
    )
    
    system_prompt = """
    Eres un agente de software autónomo dentro de AI Task Orchestrator. 
    Tienes herramientas para ejecutar comandos en la terminal (Powershell), leer, y escribir archivos.
    Usa siempre las herramientas disponibles para inspeccionar el sistema antes de actuar.
    Cuando termines la tarea o agotes tus opciones, llama OBLIGATORIAMENTE a la herramienta 'finish_task'.
    """
    
    task_prompt = """
    Tarea de prueba:
    1. Lista los archivos en el directorio actual (donde se ejecuta el script) usando un comando de terminal.
    2. Crea un archivo 'hello_agent.txt' usando la herramienta 'write_file' con algún mensaje de que estás vivo.
    3. Finaliza la tarea con resumen de lo que hiciste.
    """
    
    print("\n[+] Asignando tarea al agente...\n")
    result = agent.run_task(system_prompt=system_prompt, task_prompt=task_prompt)
    
    print("\n" + "="*40)
    print("✅ RESULTADO FINAL:")
    print(f"Estado: {result.get('status')}")
    print(f"Iteraciones: {result.get('iterations')}")
    print(f"Resumen:\n{result.get('summary')}")
    print("="*40)

if __name__ == "__main__":
    main()
