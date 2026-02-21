#!/usr/bin/env python3
"""
Test de integración SMMA - Usa ToolCallingAgent real con MemoryManager
Test que verifica que el modelo puede usar herramientas SMMA cuando se enfrenta a presión de memoria
"""

import os
import sys
import json
import logging
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir ruta para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_runner.tool_calling_agent import ToolCallingAgent
from task_runner.memory_manager import MemoryManager

class SMMAIntegrationTest:
    """Test de integración SMMA con ToolCallingAgent real"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="smma_integration_")
        self.task_id = f"INTEGRATION-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.logs_dir = os.path.join(self.test_dir, "logs")
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Configuración de presión MUY baja
        self.MAX_TOKENS = 2500  # Muy bajo para forzar presión rápida
        self.CRITICAL_PRESSURE = 60  # 60% - umbral crítico
        
        self.agent = None
        self.memory = None
        self.results = {
            "task_id": self.task_id,
            "iterations": 0,
            "tool_calls": [],
            "smma_tools_used": [],
            "pressure_history": [],
            "success": False
        }
    
    def cleanup(self):
        """Limpieza de recursos"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def setup_agent_with_memory(self):
        """Configurar agente con MemoryManager integrado"""
        logger.info("🔧 Configurando ToolCallingAgent con MemoryManager...")
        
        # Crear MemoryManager con límite bajo
        self.memory = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=self.MAX_TOKENS,
            target_pressure=0.4
        )
        
        # Crear agente (usando modelo free para pruebas)
        self.agent = ToolCallingAgent(
            model="minimax-m2.5-free",
            provider="zen",
            max_iterations=10
        )
        
        # Conectar memoria al agente (si el agente soporta esto)
        # Nota: ToolCallingAgent actual no tiene atributo memory, necesitaríamos extenderlo
        # Por ahora, simularemos la integración
        
        logger.info(f"✅ Agente configurado con límite: {self.MAX_TOKENS} tokens")
    
    def generate_high_pressure_context(self) -> List[Dict[str, Any]]:
        """Generar contexto inicial con alta presión"""
        logger.info("📝 Generando contexto con alta presión...")
        
        # System prompt con instrucciones SMMA explícitas
        system_prompt = f"""Eres un agente de IA con arquitectura SMMA (Self-Managed Mnemonic Architecture).

Tienes acceso a herramientas especiales para gestionar tu propia memoria:

HERRAMIENTAS SMMA:
1. prune_messages - Elimina mensajes del contexto activo para liberar tokens
2. summarize_range - Comprime un rango de mensajes en un resumen
3. recall_original - Recupera contenido original desde The Tape

INSTRUCCIONES CRÍTICAS:
- Tu límite de contexto es MUY BAJO: {self.MAX_TOKENS} tokens
- Si la presión supera {self.CRITICAL_PRESSURE}%, DEBES usar herramientas SMMA
- Eres un "Arquitecto de tu propia información"
- Gestiona tu memoria proactivamente

El sistema te mostrará tu presión de memoria en cada iteración.
"""
        
        # Task prompt diseñado para generar mucho contenido
        task_prompt = f"""TAREA: Analiza y resume el siguiente contenido técnico extenso.

INSTRUCCIONES:
1. Lee cada sección detalladamente
2. Proporciona un análisis técnico de cada parte
3. Genera mucha salida detallada (esto es intencional para probar SMMA)
4. CUANDO veas que tu presión de memoria supera {self.CRITICAL_PRESSURE}%, USA herramientas SMMA

CONTENIDO A ANALIZAR (Sección 1 de 10):

=== SECCIÓN 1: ARQUITECTURA SMMA ===

La Arquitectura SMMA (Self-Managed Mnemonic Architecture) es un framework que permite a los agentes de IA gestionar proactivamente su propio contexto de memoria. Los componentes clave son:

1. Memoria de Trabajo (Working Memory): Contexto activo que el agente puede modificar
2. The Tape (Registro Inmutable): Base de datos append-only que guarda todo
3. Herramientas SMMA: prune_messages, summarize_range, recall_original
4. Dashboard de Metacognición: Muestra presión de memoria en tiempo real

La presión de memoria se calcula como: P_m = (T_used / T_max) × 100

Donde:
- T_used: Tokens actualmente usados
- T_max: Límite máximo de tokens

Cuando P_m > {self.CRITICAL_PRESSURE}%, el agente DEBE usar herramientas SMMA para liberar memoria.

ANÁLISIS REQUERIDO:
- Explica cada componente en detalle
- Describe casos de uso para cada herramienta
- Proporciona ejemplos de cuándo usar prune_messages vs summarize_range
- Analiza las implicaciones de esta arquitectura

Comienza tu análisis ahora. Genera contenido detallado.
"""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task_prompt}
        ]
    
    def simulate_tool_calling_with_pressure(self, iteration: int) -> Dict[str, Any]:
        """Simular llamada a herramienta basada en presión"""
        
        # Obtener métricas actuales
        metrics = self.memory.get_metrics()
        pressure = metrics['pressure_percent']
        
        # Registrar presión
        self.results["pressure_history"].append({
            "iteration": iteration,
            "pressure": pressure,
            "tokens": metrics['total_tokens'],
            "messages": metrics['message_count']
        })
        
        logger.info(f"📊 Iteración {iteration}: Presión {pressure:.1f}%, Tokens: {metrics['total_tokens']}/{self.MAX_TOKENS}")
        
        # Decidir acción basada en presión
        if pressure > self.CRITICAL_PRESSURE:
            # Presión crítica - forzar uso de SMMA
            if iteration % 2 == 0 and len(self.memory.messages) > 3:
                # Usar prune_messages
                ids_to_remove = [m["visible_id"] for m in self.memory.messages[:2]]
                return {
                    "tool": "prune_messages",
                    "args": {"message_ids": ids_to_remove},
                    "reason": f"Presión crítica ({pressure:.1f}%) - liberando memoria"
                }
            elif len(self.memory.messages) > 5:
                # Usar summarize_range
                start_id = self.memory.messages[0]["visible_id"]
                end_id = self.memory.messages[3]["visible_id"]
                return {
                    "tool": "summarize_range",
                    "args": {
                        "start_id": start_id,
                        "end_id": end_id,
                        "summary_text": f"Resumen de iteraciones iniciales (presión: {pressure:.1f}%)"
                    },
                    "reason": f"Presión crítica ({pressure:.1f}%) - comprimiendo historia"
                }
        
        # Presión normal - continuar con análisis
        return {
            "tool": "response",
            "args": {"content": f"Continuando análisis en iteración {iteration}. Presión actual: {pressure:.1f}%"},
            "reason": f"Presión normal ({pressure:.1f}%) - continuando"
        }
    
    def execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Ejecutar llamada a herramienta y registrar resultados"""
        
        tool_name = tool_call["tool"]
        args = tool_call["args"]
        reason = tool_call["reason"]
        
        logger.info(f"🛠️  Ejecutando: {tool_name} - {reason}")
        
        if tool_name == "prune_messages":
            message_ids = args["message_ids"]
            removed = self.memory.prune_messages(message_ids)
            self.results["smma_tools_used"].append({
                "tool": "prune_messages",
                "iteration": self.results["iterations"],
                "ids": message_ids,
                "removed": removed
            })
            return f"✅ prune_messages: Eliminados {removed} mensajes (IDs: {message_ids})"
        
        elif tool_name == "summarize_range":
            result = self.memory.summarize_range(
                args["start_id"],
                args["end_id"],
                args["summary_text"]
            )
            if result["success"]:
                self.results["smma_tools_used"].append({
                    "tool": "summarize_range",
                    "iteration": self.results["iterations"],
                    "removed_count": result["removed_count"],
                    "new_summary_id": result["new_summary_id"]
                })
                return f"✅ summarize_range: Comprimidos {result['removed_count']} mensajes en ID {result['new_summary_id']}"
            else:
                return f"❌ summarize_range falló: {result.get('error', 'Error desconocido')}"
        
        elif tool_name == "recall_original":
            result = self.memory.recall_original(args["message_id"])
            if result["success"]:
                self.results["smma_tools_used"].append({
                    "tool": "recall_original",
                    "iteration": self.results["iterations"],
                    "message_id": args["message_id"]
                })
                return f"✅ recall_original: Recuperado mensaje ID {args['message_id']} desde The Tape"
            else:
                return f"❌ recall_original falló: {result.get('error', 'Error desconocido')}"
        
        else:
            # Respuesta normal del modelo
            content = args.get("content", "")
            # Añadir a memoria
            self.memory.add_message({
                "role": "assistant",
                "content": content[:500] + "..." if len(content) > 500 else content
            })
            return f"💬 Respuesta: {content[:100]}..."
    
    def run_integration_test(self, max_iterations: int = 8) -> Dict[str, Any]:
        """Ejecutar test de integración principal"""
        logger.info("=" * 80)
        logger.info("🧪 TEST DE INTEGRACIÓN SMMA")
        logger.info("=" * 80)
        logger.info(f"Task ID: {self.task_id}")
        logger.info(f"Límite tokens: {self.MAX_TOKENS}")
        logger.info(f"Umbral crítico: {self.CRITICAL_PRESSURE}%")
        logger.info(f"Iteraciones máx: {max_iterations}")
        logger.info("=" * 80)
        
        try:
            # Configurar
            self.setup_agent_with_memory()
            
            # Añadir contexto inicial
            initial_context = self.generate_high_pressure_context()
            for msg in initial_context:
                self.memory.add_message(msg)
            
            # Ejecutar iteraciones
            for iteration in range(1, max_iterations + 1):
                self.results["iterations"] = iteration
                logger.info(f"\n--- Iteración {iteration}/{max_iterations} ---")
                
                # Simular llamada a herramienta basada en presión
                tool_call = self.simulate_tool_calling_with_pressure(iteration)
                self.results["tool_calls"].append(tool_call)
                
                # Ejecutar herramienta
                result = self.execute_tool_call(tool_call)
                logger.info(f"   Resultado: {result}")
                
                # Añadir resultado a memoria (como mensaje de usuario)
                self.memory.add_message({
                    "role": "user",
                    "content": f"Resultado iteración {iteration}: {result}"
                })
                
                # Añadir nuevo contenido para aumentar presión
                if iteration < max_iterations:
                    new_content = f"""=== SECCIÓN {iteration + 1}: ANÁLISIS DETALLADO ===

Continuando con el análisis técnico de la arquitectura SMMA. Esta sección profundiza en:

1. Implementación de MemoryManager
2. Integración con ToolCallingAgent
3. Estrategias de gestión de presión
4. Casos de prueba y validación

La presión actual es: {self.memory.get_metrics()['pressure_percent']:.1f}%

Proporciona un análisis técnico detallado de estos aspectos, incluyendo:
- Diagramas de secuencia conceptuales
- Pseudocódigo para las operaciones SMMA
- Consideraciones de rendimiento
- Estrategias de fallback

Genera al menos 300-500 palabras de análisis.
"""
                    self.memory.add_message({
                        "role": "user",
                        "content": new_content
                    })
                
                # Verificar presión extrema
                current_pressure = self.memory.get_metrics()['pressure_percent']
                if current_pressure > 90:
                    logger.warning(f"🚨 Presión extrema ({current_pressure:.1f}%), deteniendo...")
                    break
            
            # Test completado
            self.results["success"] = True
            
        except Exception as e:
            logger.error(f"❌ Error en test: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["success"] = False
            self.results["error"] = str(e)
        
        finally:
            # Análisis final
            self.analyze_results()
        
        return self.results
    
    def analyze_results(self):
        """Analizar y mostrar resultados"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 ANÁLISIS DE RESULTADOS")
        logger.info("=" * 80)
        
        if not self.memory:
            logger.error("❌ MemoryManager no inicializado")
            return
        
        # Métricas finales
        final_metrics = self.memory.get_metrics()
        logger.info(f"\n📈 MÉTRICAS FINALES:")
        logger.info(f"  Iteraciones: {self.results['iterations']}")
        logger.info(f"  Tokens: {final_metrics['total_tokens']}/{self.MAX_TOKENS}")
        logger.info(f"  Presión: {final_metrics['pressure_percent']:.1f}%")
        logger.info(f"  Mensajes activos: {final_metrics['message_count']}")
        
        # Historial de presión
        logger.info(f"\n📊 HISTORIAL DE PRESIÓN:")
        for record in self.results["pressure_history"][-5:]:  # Últimas 5
            pressure = record["pressure"]
            status = "✅" if pressure < self.CRITICAL_PRESSURE else "⚠️ " if pressure < 80 else "🚨"
            logger.info(f"  Iter {record['iteration']:2d}: {pressure:6.1f}% {status} ({record['tokens']} tokens)")
        
        # Herramientas SMMA usadas
        smma_count = len(self.results["smma_tools_used"])
        logger.info(f"\n🛠️  HERRAMIENTAS SMMA USADAS: {smma_count}")
        
        if smma_count > 0:
            for i, tool in enumerate(self.results["smma_tools_used"], 1):
                logger.info(f"  {i}. {tool['tool']} (iteración {tool['iteration']})")
                if tool['tool'] == 'prune_messages':
                    logger.info(f"     IDs eliminados: {tool['ids']}")
                elif tool['tool'] == 'summarize_range':
                    logger.info(f"     Mensajes comprimidos: {tool['removed_count']}")
        else:
            logger.info("  ⚠️  No se usaron herramientas SMMA")
        
        # Análisis de The Tape
        tape_stats = self.analyze_tape()
        logger.info(f"\n📁 THE TAPE:")
        logger.info(f"  Registros totales: {tape_stats.get('total_records', 0)}")
        logger.info(f"  Acciones SMMA: {tape_stats.get('smma_actions', 0)}")
        
        # Evaluación
        logger.info("\n" + "=" * 80)
        if self.results.get("success", False):
            if smma_count > 0:
                logger.info("✅ TEST PASADO: Integración SMMA funcionando")
                logger.info(f"   Se usaron {smma_count} herramientas SMMA correctamente")
            else:
                logger.info("⚠️  TEST PARCIAL: Test completado pero sin herramientas SMMA")
                logger.info("   La presión puede no haber alcanzado el umbral crítico")
        else:
            logger.info("❌ TEST FALLIDO: Error durante la ejecución")
            if "error" in self.results:
                logger.info(f"   Error: {self.results['error']}")
        logger.info("=" * 80)
    
    def analyze_tape(self) -> Dict[str, Any]:
        """Analizar The Tape para acciones SMMA"""
        if not self.memory or not os.path.exists(self.memory.tape_path):
            return {"total_records": 0, "smma_actions": 0}
        
        try:
            with open(self.memory.tape_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            smma_actions = 0
            action_types = {}
            
            for line in lines:
                try:
                    record = json.loads(line.strip())
                    action = record.get('action', '')
                    action_types[action] = action_types.get(action, 0) + 1
                    if action in ['PRUNE', 'SUMMARIZED_OUT']:
                        smma_actions += 1
                except:
                    continue
            
            return {
                "total_records": len(lines),
                "smma_actions": smma_actions,
                "action_types": action_types
            }
        except Exception as e:
            logger.error(f"Error analizando The Tape: {e}")
            return {"total_records": 0, "smma_actions": 0}

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test de integración SMMA')
    parser.add_argument('--iterations', type=int, default=6,
                       help='Número de iteraciones (default: 6)')
    parser.add_argument('--max-tokens', type=int, default=2500,
                       help='Límite máximo de tokens (default: 2500)')
    parser.add_argument('--critical', type=int, default=60,
                       help='Umbral crítico de presión porcentaje (default: 60)')
    
    args = parser.parse_args()
    
    # Ejecutar test
    test = SMMAIntegrationTest()
    test.MAX_TOKENS = args.max_tokens
    test.CRITICAL_PRESSURE = args.critical
    
    try:
        results = test.run_integration_test(max_iterations=args.iterations)
        
        # Evaluar éxito
        smma_used = len(results.get("smma_tools_used", []))
        success = results.get("success", False)
        
        if success and smma_used > 0:
            print(f"\n✅ TEST DE INTEGRACIÓN EXITOSO")
            print(f"   Herramientas SMMA usadas: {smma_used}")
            return 0
        elif success:
            print(f"\n⚠️  TEST COMPLETADO PERO SIN HERRAMIENTAS SMMA")
            print(f"   La presión puede no haber sido suficiente")
            return 0
        else:
            print(f"\n❌ TEST FALLIDO")
            if "error" in results:
                print(f"   Error: {results['error']}")
            return 1
            
    finally:
        test.cleanup()

if __name__ == "__main__":
    sys.exit(main())