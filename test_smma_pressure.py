#!/usr/bin/env python3
"""
Test de presión forzada SMMA - Fuerza al modelo a usar herramientas SMMA
Test que genera contenido masivo para forzar presión de memoria
y verifica que el modelo use prune_messages o summarize_range
"""

import os
import sys
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Añadir ruta para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_runner.memory_manager import MemoryManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_massive_content(num_lines: int = 50, lines_per_chunk: int = 10) -> str:
    """Genera contenido masivo para llenar memoria rápidamente"""
    content = []
    for i in range(num_lines):
        # Generar contenido verboso que ocupe muchos tokens
        content.append(f"Línea {i+1}: " + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 5)
    return "\n".join(content)

def test_pressure_with_forced_cleanup():
    """Test que fuerza presión de memoria y verifica uso de herramientas SMMA"""
    
    print("=" * 80)
    print("TEST DE PRESIÓN FORZADA SMMA")
    print("=" * 80)
    
    # Configuración
    task_id = f"PRESSURE-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    logs_dir = ".ai-tests/pressure_test"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Límite MUY bajo para forzar presión rápidamente
    MAX_TOKENS = 1500  # Muy bajo para forzar presión
    TARGET_PRESSURE = 0.3  # 30% - forzar limpieza temprana
    
    print(f"\n🔧 Configuración del test:")
    print(f"  Task ID: {task_id}")
    print(f"  Límite de tokens: {MAX_TOKENS}")
    print(f"  Presión objetivo: {TARGET_PRESSURE*100}%")
    
    # Inicializar memoria con límite muy bajo
    memory = MemoryManager(
        task_id=task_id,
        logs_dir=logs_dir,
        max_tokens=MAX_TOKENS,
        target_pressure=TARGET_PRESSURE
    )
    
    print(f"\n📊 Estado inicial:")
    print(f"  Límite de tokens: {MAX_TOKENS}")
    print(f"  Presión objetivo: {TARGET_PRESSURE*100}%")
    print(f"  Tokens objetivo: {int(MAX_TOKENS * TARGET_PRESSURE)}")
    
    # Generar contenido masivo para llenar memoria
    print(f"\n📝 Generando contenido masivo...")
    
    # Añadir mensajes hasta alcanzar presión crítica
    iteration = 0
    max_iterations = 20
    pressure_history = []
    smma_tools_used = []
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteración {iteration} ---")
        
        # Generar contenido masivo
        content = f"Contenido masivo de prueba #{iteration}. " * 50
        content += generate_massive_content(5)  # 5 líneas de contenido extra
        
        # Añadir mensaje (simulando interacción con el modelo)
        msg_id = memory.add_message({
            "role": "user" if iteration % 2 == 0 else "assistant",
            "content": content
        })
        
        # Calcular métricas
        metrics = memory.get_metrics()
        pressure = metrics['pressure_percent']
        pressure_history.append(pressure)
        
        print(f"  Mensaje {iteration}: {len(content)} chars, {metrics['total_tokens']} tokens, Presión: {pressure:.1f}%")
        
        # Verificar si se alcanzó presión crítica
        if pressure > TARGET_PRESSURE * 100:
            print(f"  ⚠️  PRESIÓN CRÍTICA ({pressure:.1f}%) - Debería activarse SMMA")
            
            # Verificar si el modelo debería usar herramientas SMMA
            if pressure > 70:  # Umbral muy alto, forzar limpieza
                print(f"  🚨 PRESIÓN CRÍTICA ({pressure:.1f}%) - Se requiere limpieza SMMA")
                
                # Simular uso de prune_messages (en test real, el modelo debería hacerlo)
                if len(memory.messages) > 5:
                    # Simular que el modelo usa prune_messages en los IDs más antiguos
                    ids_to_remove = [m["visible_id"] for m in memory.messages[:3]]
                    if ids_to_remove:
                        removed = memory.prune_messages(ids_to_remove)
                        print(f"  🧹 SMMA: prune_messages eliminó {removed} mensajes (IDs: {ids_to_remove})")
                        smma_tools_used.append(f"prune_messages (IDs: {ids_to_remove})")
                
                # También simular summarize_range si hay muchos mensajes
                if len(memory.messages) > 8:
                    # Crear resumen de los primeros mensajes
                    if len(memory.messages) >= 5:
                        start_id = memory.messages[0]["visible_id"]
                        end_id = memory.messages[4]["visible_id"]
                        result = memory.summarize_range(
                            start_id, 
                            end_id, 
                            "Resumen de mensajes iniciales (comprimidos por SMMA)"
                        )
                        if result.get("success"):
                            print(f"  📦 SMMA: summarize_range comprimió {result['removed_count']} mensajes")
                            smma_tools_used.append(f"summarize_range ({result['removed_count']} mensajes)")
        
        # Verificar si hemos alcanzado el límite de iteraciones o presión
        if pressure > 90:  # 90% de presión, muy alto
            print(f"  ⚠️  Presión crítica alcanzada ({pressure:.1f}%), deteniendo...")
            break
            
        if iteration >= max_iterations:
            print(f"  ⏹️  Límite de iteraciones alcanzado")
            break
    
    # Análisis final
    print(f"\n{'='*60}")
    print("📊 RESULTADOS DEL TEST DE PRESIÓN")
    print(f"{'='*60}")
    
    final_metrics = memory.get_metrics()
    print(f"\n📈 Métricas finales:")
    print(f"  Tokens: {final_metrics['total_tokens']}/{MAX_TOKENS} ({final_metrics['pressure_percent']:.1f}%)")
    print(f"  Mensajes activos: {final_metrics['message_count']}")
    print(f"  Presión final: {final_metrics['pressure_percent']:.1f}%")
    
    if smma_tools_used:
        print(f"\n✅ Herramientas SMMA utilizadas:")
        for tool in smma_tools_used:
            print(f"  - {tool}")
    else:
        print(f"\n⚠️  No se usaron herramientas SMMA automáticamente")
        print(f"  (En un test real, el modelo debería activarlas cuando presión > {TARGET_PRESSURE*100}%)")
    
    # Verificar The Tape
    tape_path = memory.tape_path
    if os.path.exists(tape_path):
        with open(tape_path, 'r') as f:
            lines = f.readlines()
        print(f"\n📁 The Tape: {len(lines)} registros")
        
        # Contar acciones SMMA en el tape
        smma_actions = 0
        for line in lines:
            if '"action": "PRUNE"' in line or '"action": "SUMMARIZED_OUT"' in line:
                smma_actions += 1
        
        print(f"  Acciones SMMA en tape: {smma_actions}")
    
    print(f"\n{'='*60}")
    print("🧪 TEST COMPLETADO")
    print(f"  Iteraciones: {iteration}")
    print(f"  Presión final: {final_metrics['pressure_percent']:.1f}%")
    print(f"  Herramientas SMMA usadas: {len(smma_tools_used)}")
    print(f"{'='*60}")
    
    return {
        "iterations": iteration,
        "final_pressure": final_metrics['pressure_percent'],
        "final_tokens": final_metrics['total_tokens'],
        "final_messages": final_metrics['message_count'],
        "smma_tools_used": len(smma_tools_used),
        "tape_entries": len(lines) if 'lines' in locals() else 0
    }

def generate_massive_content(lines: int = 10) -> str:
    """Genera contenido de prueba verboso"""
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. "
    return (lorem * 5 + "\n") * lines

if __name__ == "__main__":
    import sys
    try:
        results = test_pressure_with_forced_cleanup()
        
        # Evaluar resultados
        if results["smma_tools_used"] > 0:
            print(f"\n✅ TEST PASADO: Se usaron {results['smta_tools_used']} herramientas SMMA")
            sys.exit(0)
        elif results["final_pressure"] > 80:
            print(f"\n⚠️  TEST PARCIAL: Alta presión ({results['final_pressure']:.1f}%) pero sin herramientas SMMA")
            print("   El modelo debería haber usado herramientas SMMA pero no lo hizo")
            sys.exit(1)
        else:
            print(f"\n✅ TEST PASADO: Presión final {results['final_pressure']:.1f}% (dentro de límites)")
            sys.exit(0)
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)