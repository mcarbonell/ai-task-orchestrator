#!/usr/bin/env python3
"""
Test unitario SMMA - Pruebas específicas de MemoryManager
Test que verifica funcionalidad básica, edge cases y consistencia
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime
import unittest

# Añadir ruta para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from task_runner.memory_manager import MemoryManager

class TestMemoryManager(unittest.TestCase):
    """Test unitario para MemoryManager"""
    
    def setUp(self):
        """Configuración antes de cada test"""
        self.test_dir = tempfile.mkdtemp(prefix="smma_test_")
        self.task_id = f"UNIT-TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.logs_dir = os.path.join(self.test_dir, "logs")
        
    def tearDown(self):
        """Limpieza después de cada test"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test: Inicialización básica"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        self.assertEqual(mm.task_id, self.task_id)
        self.assertEqual(mm.max_tokens, 10000)
        self.assertEqual(mm.target_pressure, 0.5)
        self.assertEqual(len(mm.messages), 0)
        self.assertTrue(os.path.exists(mm.tape_path))
    
    def test_add_message(self):
        """Test: Añadir mensajes y verificar IDs"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Añadir varios mensajes
        ids = []
        for i in range(5):
            msg_id = mm.add_message({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Mensaje de prueba {i}"
            })
            ids.append(msg_id)
        
        # Verificar IDs únicos y secuenciales
        self.assertEqual(len(set(ids)), 5)  # Todos únicos
        self.assertEqual(ids, list(range(5)))  # Secuenciales 0,1,2,3,4
        self.assertEqual(len(mm.messages), 5)
        
        # Verificar que The Tape tiene registros
        self.assertTrue(os.path.exists(mm.tape_path))
        with open(mm.tape_path, 'r') as f:
            lines = f.readlines()
        self.assertGreaterEqual(len(lines), 6)  # INIT + 5 mensajes
    
    def test_prune_messages(self):
        """Test: Eliminar mensajes con prune_messages"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Añadir mensajes
        for i in range(10):
            mm.add_message({
                "role": "user",
                "content": f"Mensaje {i}"
            })
        
        initial_count = len(mm.messages)
        
        # Eliminar algunos mensajes
        removed = mm.prune_messages([2, 4, 6, 8])
        
        # Verificar resultados
        self.assertEqual(removed, 4)
        self.assertEqual(len(mm.messages), initial_count - 4)
        
        # Verificar que los IDs eliminados ya no están
        remaining_ids = [m["visible_id"] for m in mm.messages]
        self.assertNotIn(2, remaining_ids)
        self.assertNotIn(4, remaining_ids)
        self.assertNotIn(6, remaining_ids)
        self.assertNotIn(8, remaining_ids)
        
        # Verificar The Tape tiene registros de PRUNE
        with open(mm.tape_path, 'r') as f:
            tape_content = f.read()
        self.assertIn('"action": "PRUNE"', tape_content)
    
    def test_summarize_range_valid(self):
        """Test: Comprimir rango válido con summarize_range"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Añadir mensajes
        ids = []
        for i in range(10):
            msg_id = mm.add_message({
                "role": "user",
                "content": f"Mensaje detallado número {i} con contenido extenso"
            })
            ids.append(msg_id)
        
        initial_count = len(mm.messages)
        
        # Comprimir primeros 5 mensajes
        result = mm.summarize_range(
            start_id=ids[0],
            end_id=ids[4],
            summary_text="Resumen de los primeros 5 mensajes"
        )
        
        # Verificar éxito
        self.assertTrue(result["success"])
        self.assertEqual(result["removed_count"], 5)
        self.assertIn("new_summary_id", result)
        
        # Verificar que se redujo el número de mensajes
        self.assertEqual(len(mm.messages), initial_count - 5 + 1)  # -5 + 1 resumen
        
        # Verificar que el resumen está en la posición correcta
        summary_msg = mm.messages[0]  # Debería ser el primer mensaje ahora
        self.assertEqual(summary_msg["role"], "system")
        self.assertIn("[MEMORIA RESUMIDA", summary_msg["raw_msg"]["content"])
    
    def test_summarize_range_invalid(self):
        """Test: summarize_range con IDs inválidos"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Añadir algunos mensajes
        for i in range(3):
            mm.add_message({
                "role": "user",
                "content": f"Mensaje {i}"
            })
        
        # Intentar comprimir con IDs inválidos
        result = mm.summarize_range(
            start_id=10,  # ID que no existe
            end_id=20,
            summary_text="Resumen inválido"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Invalid IDs", result["error"])
    
    def test_recall_original(self):
        """Test: Recuperar mensaje original desde The Tape"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Añadir mensaje con contenido conocido
        test_content = "Contenido de prueba específico para recall_original"
        msg_id = mm.add_message({
            "role": "user",
            "content": test_content
        })
        
        # Recuperar el mensaje
        result = mm.recall_original(msg_id)
        
        # Verificar éxito
        self.assertTrue(result["success"])
        self.assertEqual(result["visible_id"], msg_id)
        self.assertIn("message", result)
        self.assertEqual(result["message"]["content"], test_content)
        self.assertEqual(result["message"]["role"], "user")
    
    def test_recall_original_nonexistent(self):
        """Test: recall_original con ID que no existe"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Intentar recuperar ID que no existe
        result = mm.recall_original(999)
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("No se encontró", result["error"])
    
    def test_metrics_calculation(self):
        """Test: Cálculo de métricas de presión"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=1000,  # Límite bajo
            target_pressure=0.5
        )
        
        # Añadir contenido que ocupe tokens
        for i in range(3):
            mm.add_message({
                "role": "user",
                "content": "X" * 100  # ~100 caracteres ≈ 28 tokens
            })
        
        metrics = mm.get_metrics()
        
        # Verificar estructura
        self.assertIn("total_tokens", metrics)
        self.assertIn("max_tokens", metrics)
        self.assertIn("pressure_percent", metrics)
        self.assertIn("message_count", metrics)
        self.assertIn("is_critical", metrics)
        
        # Verificar valores razonables
        self.assertGreater(metrics["total_tokens"], 0)
        self.assertEqual(metrics["max_tokens"], 1000)
        self.assertGreater(metrics["pressure_percent"], 0)
        self.assertLess(metrics["pressure_percent"], 100)
        self.assertEqual(metrics["message_count"], 3)
        
        # pressure_percent debería ser (total_tokens / max_tokens) * 100
        expected_pressure = (metrics["total_tokens"] / 1000) * 100
        self.assertAlmostEqual(metrics["pressure_percent"], expected_pressure, places=1)
    
    def test_pressure_critical_detection(self):
        """Test: Detección de presión crítica"""
        # Test con presión baja
        mm_low = MemoryManager(
            task_id=f"{self.task_id}-low",
            logs_dir=self.logs_dir,
            max_tokens=1000,
            target_pressure=0.5
        )
        
        metrics_low = mm_low.get_metrics()
        self.assertFalse(metrics_low["is_critical"])  # Presión 0% no es crítica
        
        # Test con presión alta (simulada)
        mm_high = MemoryManager(
            task_id=f"{self.task_id}-high",
            logs_dir=self.logs_dir,
            max_tokens=100,
            target_pressure=0.5
        )
        
        # Añadir contenido para subir presión
        for i in range(5):
            mm_high.add_message({
                "role": "user",
                "content": "Contenido extenso " * 20  # Muchos tokens
            })
        
        metrics_high = mm_high.get_metrics()
        # Si presión > target_pressure * 100 * 1.5 (75%) debería ser crítica
        if metrics_high["pressure_percent"] > 75:
            self.assertTrue(metrics_high["is_critical"])
        else:
            self.assertFalse(metrics_high["is_critical"])
    
    def test_token_estimation(self):
        """Test: Estimación de tokens"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Test con diferentes longitudes
        test_cases = [
            ("", 0),  # Vacío
            ("a", 1),  # Mínimo
            ("Hola mundo", 2),  # ~10 chars / 3.5 ≈ 3, pero redondeamos a 2
            ("X" * 100, 20),  # 100 / 3.5 ≈ 29, pero el método usa max(1, int(len/3.5))
        ]
        
        for text, expected_min in test_cases:
            estimated = mm._estimate_tokens(text)
            # La estimación es aproximada, verificar que sea razonable
            if text:
                # Verificar que está dentro de un rango razonable
                self.assertGreaterEqual(estimated, max(1, expected_min - 5))  # Margen inferior
                self.assertLessEqual(estimated, expected_min + 10)  # Margen superior
            else:
                self.assertEqual(estimated, 0)
    
    def test_get_active_messages(self):
        """Test: Obtener mensajes activos para LLM"""
        mm = MemoryManager(
            task_id=self.task_id,
            logs_dir=self.logs_dir,
            max_tokens=10000,
            target_pressure=0.5
        )
        
        # Añadir mensajes
        test_messages = [
            {"role": "system", "content": "Eres un asistente"},
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Hola, ¿cómo estás?"},
        ]
        
        for msg in test_messages:
            mm.add_message(msg)
        
        # Obtener mensajes activos
        active_messages = mm.get_active_messages_for_llm()
        
        # Verificar que son los mismos mensajes en orden
        self.assertEqual(len(active_messages), 3)
        for i, msg in enumerate(active_messages):
            # Pueden ser objetos o diccionarios
            if hasattr(msg, "role"):
                self.assertEqual(msg.role, test_messages[i]["role"])
            else:
                self.assertEqual(msg["role"], test_messages[i]["role"])

class TestSMMAIntegration(unittest.TestCase):
    """Test de integración SMMA"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="smma_integration_")
        self.logs_dir = os.path.join(self.test_dir, "logs")
    
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_complete_smma_workflow(self):
        """Test: Flujo completo SMMA (añadir, comprimir, recuperar)"""
        mm = MemoryManager(
            task_id="WORKFLOW-TEST",
            logs_dir=self.logs_dir,
            max_tokens=2000,  # Límite bajo
            target_pressure=0.4
        )
        
        # Fase 1: Añadir mensajes iniciales
        initial_ids = []
        for i in range(8):
            msg_id = mm.add_message({
                "role": "user",
                "content": f"Consulta detallada número {i} sobre un tema complejo"
            })
            initial_ids.append(msg_id)
        
        self.assertEqual(len(mm.messages), 8)
        
        # Fase 2: Comprimir primeros mensajes (simulando presión)
        compress_result = mm.summarize_range(
            start_id=initial_ids[0],
            end_id=initial_ids[3],
            summary_text="Resumen de consultas iniciales 1-4"
        )
        
        self.assertTrue(compress_result["success"])
        self.assertEqual(compress_result["removed_count"], 4)
        
        # Verificar que tenemos menos mensajes
        self.assertEqual(len(mm.messages), 8 - 4 + 1)  # -4 + 1 resumen = 5
        
        # Fase 3: Recuperar uno de los mensajes comprimidos
        recall_result = mm.recall_original(initial_ids[2])  # ID 2 fue comprimido
        
        self.assertTrue(recall_result["success"])
        self.assertEqual(recall_result["visible_id"], initial_ids[2])
        self.assertIn("Consulta detallada número 2", recall_result["message"]["content"])
        
        # Fase 4: Eliminar algunos mensajes restantes
        remaining_ids = [m["visible_id"] for m in mm.messages]
        if len(remaining_ids) >= 2:
            prune_result = mm.prune_messages([remaining_ids[0]])
            self.assertEqual(prune_result, 1)
        
        # Verificar estado final
        final_metrics = mm.get_metrics()
        self.assertLess(final_metrics["pressure_percent"], 100)  # No debería estar al 100%
        
        # Verificar The Tape tiene todos los registros
        self.assertTrue(os.path.exists(mm.tape_path))
        with open(mm.tape_path, 'r') as f:
            lines = f.readlines()
        
        # Debería tener: INIT + 8 ADD + 4 SUMMARIZED_OUT + 1 ADD (resumen) + 1 PRUNE
        self.assertGreaterEqual(len(lines), 15)

def run_tests():
    """Ejecutar todos los tests"""
    # Crear test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Añadir tests
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSMMAIntegration))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retornar código de salida
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    # Ejecutar tests unitarios
    sys.exit(run_tests())