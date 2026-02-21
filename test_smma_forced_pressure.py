#!/usr/bin/env python3
"""
Test SMMA de presión forzada - Versión mejorada
Este test fuerza al modelo a usar herramientas SMMA generando contenido masivo
y verificando que las herramientas se usan cuando la presión supera umbrales.
"""

import os
import sys
import json
import re
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_runner.memory_manager import MemoryManager

class SMMAPressureTest:
    """Clase para ejecutar tests de presión SMMA"""
    
    def __init__(self, use_api: bool = False):
        self.use_api = use_api
        self.task_id = f"SMMA-PRESSURE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.logs_dir = ".ai-tests/pressure"
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Configuración de presión MUY baja para forzar uso de herramientas
        self.MAX_TOKENS = 2000  # Muy bajo para forzar presión rápida
        self.CRITICAL_PRESSURE = 60  # 60% - umbral crítico
        self.TARGET_PRESSURE = 40    # 40% - objetivo
        
        self.memory = None
        self.smma_actions_used = []
        self.pressure_history = []
        
    def generate_verbose_content(self, size_kb: float = 2.0) -> str:
        """Genera contenido verboso que ocupa aproximadamente size_kb KB"""
        # 1 token ≈ 4 caracteres, 1KB ≈ 250 tokens
        target_chars = int(size_kb * 1024)
        
        base_text = """Este es un contenido de prueba diseñado para ocupar tokens y forzar presión de memoria en el sistema SMMA. 
        La arquitectura SMMA (Self-Managed Mnemonic Architecture) permite a los agentes de IA gestionar proactivamente su propio contexto.
        
        Cuando la presión de memoria supera el umbral crítico ({}%), el agente DEBE usar herramientas como:
        1. prune_messages - Para eliminar mensajes redundantes
        2. summarize_range - Para comprimir bloques de conversación
        3. recall_original - Para recuperar contenido desde The Tape
        
        Este test verifica que el agente responde correctamente a la presión de memoria y usa las herramientas SMMA cuando es necesario.
        
        La presión se calcula como: P_m = (T_used / T_max) × 100
        Donde T_used son los tokens actualmente usados y T_max es el límite máximo.
        
        Para forzar presión en este test, generamos contenido extenso que incluye:
        - Explicaciones detalladas de cada componente SMMA
        - Ejemplos de uso de herramientas
        - Consideraciones de implementación
        - Estrategias de optimización
        - Casos de prueba y validación
        
        Este contenido se repite para alcanzar el tamaño objetivo y simular una conversación real con mucho contexto histórico.
        
        """.format(self.CRITICAL_PRESSURE)
        
        # Añadir más contenido base
        base_text += """CONTENIDO ADICIONAL PARA OCUPAR TOKENS:
        
        La gestión de memoria en agentes de IA es crucial para tareas largas y complejas. Sin SMMA, los agentes pueden:
        1. Perder información importante cuando se llena el contexto
        2. Repetir errores ya resueltos
        3. Tomar decisiones basadas en información incompleta
        
        SMMA resuelve estos problemas mediante:
        - Autogestión proactiva del contexto
        - Registro inmutable de todas las interacciones
        - Recuperación de información cuando es necesario
        - Optimización continua del uso de tokens
        
        Cada herramienta SMMA tiene casos de uso específicos:
        - prune_messages: Ideal para eliminar logs de error, intentos fallidos, contenido redundante
        - summarize_range: Perfecto para comprimir pasos de resolución, conversaciones largas, historial detallado
        - recall_original: Esencial para verificar detalles, recuperar información crítica, auditar decisiones
        
        La implementación actual incluye:
        - MemoryManager para gestión de contexto activo
        - The Tape para registro inmutable
        - Integración con ToolCallingAgent
        - Dashboard de presión en tiempo real
        
        """
        
        # Repetir para alcanzar tamaño objetivo
        repetitions = max(1, int(target_chars / len(base_text)))
        content = base_text * repetitions
        
        # Asegurar tamaño aproximado
        if len(content) > target_chars:
            content = content[:target_chars]
        else:
            # Añadir padding si es necesario
            padding = " PADDING " * ((target_chars - len(content)) // 10)
            content += padding
        
        return content
    
    def setup_memory_with_high_pressure(self) -> MemoryManager:
        """Configura memoria con presión inicial alta"""
        logger.info(f"🔧 Configurando memoria con límite bajo: {self.MAX_TOKENS} tokens")
        
        memory = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=self.MAX_TOKENS,
            target_pressure=self.TARGET_PRESSURE / 100.0
        )
        
        # Añadir contenido inicial para crear presión
        logger.info("📝 Añadiendo contenido inicial para crear presión...")
        
        initial_messages = [
            {
                "role": "system",
                "content": self.generate_verbose_content(0.3)  # ~300 chars
            },
            {
                "role": "user", 
                "content": self.generate_verbose_content(0.5)  # ~500 chars
            }
        ]
        
        for msg in initial_messages:
            memory.add_message(msg)
        
        # Verificar presión inicial
        metrics = memory.get_metrics()
        logger.info(f"📊 Presión inicial: {metrics['pressure_percent']:.1f}%")
        logger.info(f"📊 Tokens iniciales: {metrics['total_tokens']}/{self.MAX_TOKENS}")
        
        return memory
    
    def simulate_model_response_with_pressure(self, memory: MemoryManager, iteration: int) -> Dict[str, Any]:
        """Simula respuesta del modelo bajo presión"""
        
        # Generar contenido de respuesta verboso
        response_content = f"""Iteración {iteration} - Respuesta del modelo bajo presión SMMA.

He analizado la situación de memoria actual:
- Presión actual: {memory.get_metrics()['pressure_percent']:.1f}%
- Tokens usados: {memory.get_metrics()['total_tokens']}/{self.MAX_TOKENS}
- Mensajes activos: {memory.get_metrics()['message_count']}

Recomendaciones SMMA:
"""
        
        # Añadir recomendaciones basadas en presión
        pressure = memory.get_metrics()['pressure_percent']
        
        if pressure > self.CRITICAL_PRESSURE:
            response_content += f"""
🚨 PRESIÓN CRÍTICA DETECTADA ({pressure:.1f}%) - DEBO USAR HERRAMIENTAS SMMA:

Opción 1: Usar prune_messages para eliminar mensajes antiguos
[ACTION:prune_messages]{{"message_ids": [0, 1, 2]}}[/ACTION]

Opción 2: Usar summarize_range para comprimir conversación inicial  
[ACTION:summarize_range]{{"start_id": 0, "end_id": 3, "summary_text": "Conversación inicial resumida por SMMA"}}[/ACTION]

Seleccionaré la opción más apropiada basada en el contexto.
"""
            # Forzar uso de herramienta
            if iteration % 2 == 0:
                action = {"action": "prune_messages", "args": {"message_ids": [0, 1]}}
            else:
                action = {"action": "summarize_range", "args": {
                    "start_id": 0, 
                    "end_id": 2, 
                    "summary_text": f"Resumen de iteraciones 1-{iteration} (comprimido por SMMA)"
                }}
        elif pressure > self.TARGET_PRESSURE:
            response_content += f"""
⚠️  Presión elevada ({pressure:.1f}%) - Debo considerar usar herramientas SMMA pronto.
Continuaré con la tarea pero monitoreando la presión.
"""
            action = {"action": "response", "content": response_content}
        else:
            response_content += f"""
✅ Presión normal ({pressure:.1f}%) - Puedo continuar sin limpieza.
"""
            action = {"action": "response", "content": response_content}
        
        return action
    
    def execute_smma_action(self, action: Dict[str, Any], memory: MemoryManager) -> str:
        """Ejecuta una acción SMMA y registra resultados"""
        action_name = action.get("action")
        args = action.get("args", {})
        
        if action_name == "prune_messages":
            message_ids = args.get("message_ids", [])
            removed = memory.prune_messages(message_ids)
            self.smma_actions_used.append(f"prune_messages (IDs: {message_ids})")
            return f"[SMMA] Se borraron {removed} mensajes. Presión ahora: {memory.get_metrics()['pressure_percent']:.1f}%"
        
        elif action_name == "summarize_range":
            start_id = args.get("start_id")
            end_id = args.get("end_id")
            summary_text = args.get("summary_text", "")
            result = memory.summarize_range(start_id, end_id, summary_text)
            if result.get("success"):
                self.smma_actions_used.append(f"summarize_range ({result['removed_count']} mensajes)")
                return f"[SMMA] Resumen creado (ID {result['new_summary_id']}). Comprimidos: {result['removed_count']} mensajes. Presión: {memory.get_metrics()['pressure_percent']:.1f}%"
            else:
                return f"[ERROR] {result.get('error')}"
        
        elif action_name == "recall_original":
            message_id = args.get("message_id")
            result = memory.recall_original(message_id)
            if result.get("success"):
                self.smma_actions_used.append(f"recall_original (ID: {message_id})")
                return f"[SMMA] Recuperado mensaje ID {message_id} desde The Tape"
            else:
                return f"[ERROR] {result.get('error')}"
        
        return f"[RESPUESTA] {action.get('content', '')[:100]}..."
    
    def run_pressure_test(self, max_iterations: int = 10) -> Dict[str, Any]:
        """Ejecuta el test de presión principal"""
        logger.info("=" * 80)
        logger.info("🧪 TEST DE PRESIÓN FORZADA SMMA")
        logger.info("=" * 80)
        logger.info(f"Task ID: {self.task_id}")
        logger.info(f"Límite tokens: {self.MAX_TOKENS}")
        logger.info(f"Umbral crítico: {self.CRITICAL_PRESSURE}%")
        logger.info(f"Objetivo: {self.TARGET_PRESSURE}%")
        logger.info("=" * 80)
        
        # Configurar memoria
        self.memory = self.setup_memory_with_high_pressure()
        
        # Ejecutar iteraciones
        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n--- Iteración {iteration}/{max_iterations} ---")
            
            # Obtener métricas actuales
            metrics = self.memory.get_metrics()
            pressure = metrics['pressure_percent']
            self.pressure_history.append(pressure)
            
            logger.info(f"📊 Presión: {pressure:.1f}% | Tokens: {metrics['total_tokens']}/{self.MAX_TOKENS} | Mensajes: {metrics['message_count']}")
            
            # Simular respuesta del modelo
            action = self.simulate_model_response_with_pressure(self.memory, iteration)
            
            # Añadir respuesta a memoria
            self.memory.add_message({
                "role": "assistant",
                "content": f"Respuesta iteración {iteration}"
            })
            
            # Ejecutar acción si es SMMA
            if action["action"] != "response":
                logger.info(f"🛠️  Ejecutando herramienta SMMA: {action['action']}")
                result = self.execute_smma_action(action, self.memory)
                logger.info(f"   Resultado: {result}")
                
                # Añadir resultado a memoria
                self.memory.add_message({
                    "role": "user",
                    "content": result
                })
            
            # Añadir nuevo mensaje de usuario para continuar presión
            new_user_content = self.generate_verbose_content(0.4)  # ~400 chars
            self.memory.add_message({
                "role": "user",
                "content": f"Nueva consulta iteración {iteration}: {new_user_content[:100]}..."
            })
            
            # Verificar si debemos detener por presión extrema
            if pressure > 90:
                logger.warning(f"🚨 Presión extrema ({pressure:.1f}%), deteniendo test...")
                break
        
        # Resultados finales
        return self.analyze_results()
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analiza resultados del test"""
        final_metrics = self.memory.get_metrics()
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 RESULTADOS FINALES")
        logger.info("=" * 80)
        
        logger.info(f"\n📈 Métricas finales:")
        logger.info(f"  Tokens: {final_metrics['total_tokens']}/{self.MAX_TOKENS}")
        logger.info(f"  Presión: {final_metrics['pressure_percent']:.1f}%")
        logger.info(f"  Mensajes activos: {final_metrics['message_count']}")
        
        logger.info(f"\n📊 Historial de presión:")
        for i, pressure in enumerate(self.pressure_history, 1):
            status = "✅" if pressure < self.CRITICAL_PRESSURE else "⚠️ " if pressure < 80 else "🚨"
            logger.info(f"  Iteración {i:2d}: {pressure:6.1f}% {status}")
        
        logger.info(f"\n🛠️  Herramientas SMMA usadas: {len(self.smma_actions_used)}")
        for i, action in enumerate(self.smma_actions_used, 1):
            logger.info(f"  {i}. {action}")
        
        # Verificar The Tape
        tape_stats = self.analyze_tape()
        
        logger.info(f"\n📁 The Tape:")
        logger.info(f"  Registros totales: {tape_stats.get('total_records', 0)}")
        logger.info(f"  Acciones SMMA: {tape_stats.get('smma_actions', 0)}")
        
        # Evaluación del test
        test_passed = len(self.smma_actions_used) > 0
        pressure_controlled = final_metrics['pressure_percent'] < 90
        
        logger.info("\n" + "=" * 80)
        if test_passed and pressure_controlled:
            logger.info("✅ TEST PASADO: Se usaron herramientas SMMA y se controló la presión")
        elif test_passed:
            logger.info("⚠️  TEST PARCIAL: Se usaron herramientas SMMA pero presión final alta")
        elif pressure_controlled:
            logger.info("⚠️  TEST PARCIAL: Presión controlada pero sin herramientas SMMA")
        else:
            logger.info("❌ TEST FALLIDO: Sin herramientas SMMA y presión alta")
        logger.info("=" * 80)
        
        return {
            "task_id": self.task_id,
            "final_pressure": final_metrics['pressure_percent'],
            "final_tokens": final_metrics['total_tokens'],
            "final_messages": final_metrics['message_count'],
            "smma_tools_used": len(self.smma_actions_used),
            "pressure_history": self.pressure_history,
            "test_passed": test_passed and pressure_controlled,
            "tape_stats": tape_stats
        }
    
    def analyze_tape(self) -> Dict[str, Any]:
        """Analiza The Tape para verificar acciones SMMA"""
        if not self.memory or not os.path.exists(self.memory.tape_path):
            return {"total_records": 0, "smma_actions": 0}
        
        try:
            with open(self.memory.tape_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            smma_actions = 0
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    action = record.get('action', '')
                    if action in ['PRUNE', 'SUMMARIZED_OUT']:
                        smma_actions += 1
                except:
                    continue
            
            return {
                "total_records": len(lines),
                "smma_actions": smma_actions
            }
        except Exception as e:
            logger.error(f"Error analizando The Tape: {e}")
            return {"total_records": 0, "smma_actions": 0}

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test de presión forzada SMMA')
    parser.add_argument('--iterations', type=int, default=8,
                       help='Número de iteraciones (default: 8)')
    parser.add_argument('--max-tokens', type=int, default=2000,
                       help='Límite máximo de tokens (default: 2000)')
    parser.add_argument('--critical', type=int, default=60,
                       help='Umbral crítico de presión porcentaje (default: 60)')
    
    args = parser.parse_args()
    
    # Configurar test
    test = SMMAPressureTest(use_api=False)
    test.MAX_TOKENS = args.max_tokens
    test.CRITICAL_PRESSURE = args.critical
    test.TARGET_PRESSURE = args.critical - 20  # 20% menos que crítico
    
    # Ejecutar test
    results = test.run_pressure_test(max_iterations=args.iterations)
    
    # Salir con código apropiado
    sys.exit(0 if results.get("test_passed", False) else 1)

if __name__ == "__main__":
    main()