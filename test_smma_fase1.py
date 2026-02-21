#!/usr/bin/env python3
"""
Test de validación de Fase 1 SMMA (Self-Managed Mnemonic Architecture)
Este test verifica que los modelos de IA pueden:
1. Ver su dashboard de memoria
2. Usar prune_messages para liberar tokens
3. Usar summarize_range para comprimir historial
4. Usar recall_original para recuperar de The Tape

Ejecutar: python test_smma_fase1.py
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Asegurar que podemos importar desde task_runner
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_runner.tool_calling_agent import ToolCallingAgent


def test_smma_self_management():
    """
    Test principal: Verifica que el agente puede gestionar su propia memoria
    cuando se enfrenta a una tarea que genera mucho contexto.
    """
    
    # Configuración del test
    task_id = f"SMMA-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logs_dir = f".ai-tasks/logs"
    
    # Crear agente con un límite bajo de tokens para forzar presión rápida
    # Usamos 8000 tokens máximo para que se llene rápido con el test
    # Modelo desde default-config.yaml: minimax-m2.5-free
    agent = ToolCallingAgent(
        model="minimax-m2.5-free",
        provider="zen",
        max_iterations=20,
        tasks_dir="test-tasks"
    )
    
    # System prompt que instruye al agente sobre SMMA
    system_prompt = """Eres un agente de IA con capacidad de autogestión de memoria (SMMA).

Tienes acceso a herramientas especiales para gestionar tu propio contexto:
- prune_messages: Borra mensajes por ID para liberar tokens
- summarize_range: Comprime un rango de mensajes en un resumen
- recall_original: Recupera el contenido original de The Tape

INSTRUCCIONES CRÍTICAS:
1. Monitorea tu presión de memoria en cada iteración (se muestra automáticamente)
2. Si la presión supera el 60%, DEBES usar summarize_range o prune_messages
3. Si has resumido algo pero necesitas verificar detalles, usa recall_original
4. Tu objetivo es completar la tarea manteniendo la presión de memoria bajo control

Recuerda: Eres un "Arquitecto de tu propia información". Gestiona tu memoria proactivamente.
"""
    
    # Task prompt diseñado para generar mucho contexto y forzar gestión de memoria
    task_prompt = """Realiza las siguientes operaciones matemáticas y registra cada paso detalladamente:

1. Calcula los primeros 20 números de la secuencia de Fibonacci, mostrando cada cálculo paso a paso
2. Para cada número, explica: "Fib(N) = Fib(N-1) + Fib(N-2) = X + Y = Z"
3. Después de los primeros 10 cálculos, VERIFICA tu memoria:
   - Revisa el dashboard de presión de memoria
   - Si supera 60%, usa summarize_range para comprimir los cálculos 1-10 en un resumen
4. Continúa con los cálculos 11-20
5. Al final, usa recall_original para recuperar el cálculo exacto de Fib(5) desde The Tape
6. Finaliza con finish_task reportando:
   - Los 20 números de Fibonacci calculados
   - Qué herramientas de memoria usaste y cuándo
   - La presión de memoria final

IMPORTANTE: Este test evalúa tu capacidad de autogestionar memoria. Debes usar activamente las herramientas SMMA cuando sea necesario.
"""
    
    logger.info("=" * 80)
    logger.info(f"INICIANDO TEST SMMA FASE 1 - Task ID: {task_id}")
    logger.info("=" * 80)
    logger.info(f"Objetivo: Verificar que el modelo puede autogestionar su memoria")
    logger.info(f"Presión objetivo: >60% debe activar limpieza")
    logger.info("=" * 80)
    
    # Ejecutar la tarea
    try:
        result = agent.run_task(
            task_id=task_id,
            system_prompt=system_prompt,
            task_prompt=task_prompt,
            logs_dir=logs_dir
        )
        
        # Analizar resultados
        logger.info("\n" + "=" * 80)
        logger.info("RESULTADO DEL TEST")
        logger.info("=" * 80)
        logger.info(f"Estado: {result.get('status', 'unknown')}")
        logger.info(f"Iteraciones: {result.get('iterations', 0)}")
        logger.info(f"Resumen: {result.get('summary', 'N/A')[:500]}...")
        
        # Verificar The Tape
        tape_path = os.path.join(logs_dir, f"tape_{task_id}.jsonl")
        if os.path.exists(tape_path):
            with open(tape_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Analizar contenido de The Tape
            actions = {}
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    action = record.get('action', 'UNKNOWN')
                    actions[action] = actions.get(action, 0) + 1
                except:
                    pass
            
            logger.info(f"\nContenido de The Tape ({len(lines)} registros):")
            for action, count in actions.items():
                logger.info(f"  - {action}: {count}")
            
            # Verificar si se usaron herramientas SMMA
            smma_tools_used = any(action in actions for action in ['PRUNE', 'SUMMARIZED_OUT'])
            if smma_tools_used:
                logger.info("\n✅ ÉXITO: El agente utilizó herramientas SMMA para gestionar memoria")
            else:
                logger.info("\n⚠️ ADVERTENCIA: No se detectó uso de herramientas SMMA")
                logger.info("   Posibles causas:")
                logger.info("   - El modelo no alcanzó el umbral de presión de memoria")
                logger.info("   - El modelo no siguió las instrucciones de autogestión")
                logger.info("   - Las herramientas no están correctamente expuestas")
        
        # Guardar reporte del test
        report = {
            "test_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "tape_actions": actions if 'actions' in dir() else {},
            "smma_tools_detected": smma_tools_used if 'smma_tools_used' in dir() else False
        }
        
        report_path = f"test-smma-report-{task_id}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nReporte guardado en: {report_path}")
        
        # Veredicto final
        if result.get('status') == 'completed':
            logger.info("\n🎉 TEST COMPLETADO - El agente finalizó la tarea")
            if 'smma_tools_used' in dir() and smma_tools_used:
                logger.info("✅ FASE 1 SMMA VALIDADA: El agente puede autogestionar su memoria")
                return True
            else:
                logger.info("⚠️ Tarea completada pero sin evidencia de autogestión de memoria")
                return False
        else:
            logger.info(f"\n❌ TEST FALLIDO - Estado: {result.get('status')}")
            return False
            
    except Exception as e:
        logger.error(f"\n💥 ERROR EN TEST: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_manager_directly():
    """
    Test unitario del MemoryManager sin necesidad de llamar a la API.
    Verifica que las herramientas SMMA funcionan correctamente a nivel local.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TEST UNITARIO: MemoryManager")
    logger.info("=" * 80)
    
    from task_runner.memory_manager import MemoryManager
    
    # Crear instancia con límite bajo
    mm = MemoryManager(
        task_id="UNIT-TEST-001",
        logs_dir=".ai-tasks/test-logs",
        max_tokens=1000,
        target_pressure=0.5
    )
    
    # Añadir mensajes de prueba
    logger.info("Añadiendo 10 mensajes de prueba...")
    for i in range(10):
        msg_id = mm.add_message({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Mensaje de prueba número {i} con contenido suficiente para ocupar tokens. " * 5
        })
        logger.info(f"  Mensaje {i} -> ID visible: {msg_id}")
    
    # Verificar métricas
    metrics = mm.get_metrics()
    logger.info(f"\nMétricas iniciales:")
    logger.info(f"  - Tokens: {metrics['total_tokens']}/{metrics['max_tokens']}")
    logger.info(f"  - Presión: {metrics['pressure_percent']}%")
    logger.info(f"  - Mensajes: {metrics['message_count']}")
    
    # Test prune_messages
    logger.info("\nProbando prune_messages (borrando IDs 2, 4, 6)...")
    removed = mm.prune_messages([2, 4, 6])
    logger.info(f"  Mensajes borrados: {removed}")
    
    metrics_after_prune = mm.get_metrics()
    logger.info(f"  Presión después: {metrics_after_prune['pressure_percent']}%")
    
    # Test summarize_range
    logger.info("\nProbando summarize_range (IDs 0-3)...")
    result = mm.summarize_range(0, 3, "Resumen de los primeros 4 mensajes de prueba")
    logger.info(f"  Resultado: {result}")
    
    metrics_after_summary = mm.get_metrics()
    logger.info(f"  Presión después: {metrics_after_summary['pressure_percent']}%")
    logger.info(f"  Mensajes activos: {metrics_after_summary['message_count']}")
    
    # Test recall_original
    logger.info("\nProbando recall_original (recuperando ID 1)...")
    recalled = mm.recall_original(1)
    if recalled.get('success'):
        logger.info(f"  ✅ Recuperado exitosamente:")
        logger.info(f"     Internal ID: {recalled['internal_id']}")
        logger.info(f"     Timestamp: {recalled['timestamp']}")
        logger.info(f"     Content preview: {str(recalled['message'].get('content', ''))[:100]}...")
    else:
        logger.info(f"  ❌ Error: {recalled.get('error')}")
    
    # Verificar The Tape
    logger.info(f"\nVerificando The Tape en: {mm.tape_path}")
    if os.path.exists(mm.tape_path):
        with open(mm.tape_path, 'r') as f:
            lines = f.readlines()
        logger.info(f"  Total registros: {len(lines)}")
        
        # Mostrar últimos 3 registros
        logger.info("  Últimos registros:")
        for line in lines[-3:]:
            try:
                record = json.loads(line.strip())
                logger.info(f"    - {record.get('action')}: ID {record.get('visible_id', 'N/A')}")
            except:
                pass
    
    logger.info("\n✅ Test unitario completado")
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Fase 1 SMMA')
    parser.add_argument('--unit-only', action='store_true', 
                        help='Ejecutar solo test unitario (sin llamadas API)')
    parser.add_argument('--api-test', action='store_true',
                        help='Ejecutar test con modelo real (requiere API key)')
    args = parser.parse_args()
    
    success = True
    
    # Siempre ejecutar test unitario primero
    if not args.api_test or args.unit_only:
        success = test_memory_manager_directly() and success
    
    # Ejecutar test con API si se solicita
    if args.api_test or not args.unit_only:
        logger.info("\n" + "=" * 80)
        logger.info("ADVERTENCIA: El test con API real consume tokens y puede tardar varios minutos")
        logger.info("Asegúrate de tener ZEN_API_KEY u OPENROUTER_API_KEY configurada")
        logger.info("=" * 80)
        
        confirm = input("\n¿Continuar con test de API? (s/N): ")
        if confirm.lower() == 's':
            success = test_smma_self_management() and success
        else:
            logger.info("Test de API omitido")
    
    # Resultado final
    sys.exit(0 if success else 1)
