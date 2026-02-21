#!/usr/bin/env python3
"""
Runner de tests SMMA - Ejecuta todos los tests y genera reporte consolidado
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SMMATestRunner:
    """Runner para ejecutar todos los tests SMMA"""
    
    def __init__(self):
        self.results_dir = tempfile.mkdtemp(prefix="smma_test_results_")
        self.report_file = os.path.join(self.results_dir, "smma_test_report.json")
        self.all_results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def cleanup(self):
        """Limpieza de recursos"""
        if os.path.exists(self.results_dir):
            shutil.rmtree(self.results_dir)
    
    def run_test(self, test_file: str, test_name: str, description: str, 
                 args: List[str] = None) -> Dict[str, Any]:
        """Ejecutar un test individual"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🧪 EJECUTANDO: {test_name}")
        logger.info(f"📝 {description}")
        logger.info(f"{'='*60}")
        
        test_path = os.path.join(os.path.dirname(__file__), test_file)
        
        if not os.path.exists(test_path):
            logger.error(f"❌ Test no encontrado: {test_path}")
            return {
                "test": test_name,
                "file": test_file,
                "status": "error",
                "error": f"Archivo no encontrado: {test_file}"
            }
        
        # Construir comando
        cmd = [sys.executable, test_path]
        if args:
            cmd.extend(args)
        
        try:
            # Ejecutar test
            logger.info(f"📋 Comando: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutos máximo por test
                cwd=os.path.dirname(__file__)
            )
            
            # Analizar resultado
            test_result = {
                "test": test_name,
                "file": test_file,
                "command": ' '.join(cmd),
                "return_code": result.returncode,
                "stdout": result.stdout[-1000:],  # Últimos 1000 chars
                "stderr": result.stderr[-500:],   # Últimos 500 chars
                "timestamp": datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                logger.info("✅ TEST PASADO")
                test_result["status"] = "passed"
            else:
                logger.info("❌ TEST FALLIDO")
                test_result["status"] = "failed"
                if result.stderr:
                    logger.error(f"   Error: {result.stderr[:200]}...")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            logger.error("⏰ TEST TIMEOUT (5 minutos)")
            return {
                "test": test_name,
                "file": test_file,
                "status": "timeout",
                "error": "Timeout de 5 minutos excedido"
            }
        except Exception as e:
            logger.error(f"❌ ERROR EJECUTANDO TEST: {str(e)}")
            return {
                "test": test_name,
                "file": test_file,
                "status": "error",
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests SMMA"""
        logger.info("=" * 80)
        logger.info("🚀 RUNNER DE TESTS SMMA")
        logger.info("=" * 80)
        logger.info(f"Directorio de resultados: {self.results_dir}")
        logger.info("=" * 80)
        
        # Lista de tests a ejecutar
        tests = [
            {
                "file": "test_smma_unit.py",
                "name": "Test Unitario SMMA",
                "description": "Pruebas unitarias de MemoryManager (sin API)",
                "args": []
            },
            {
                "file": "test_smma_forced_pressure.py",
                "name": "Test de Presión Forzada",
                "description": "Simula presión de memoria y uso de herramientas SMMA",
                "args": ["--iterations", "6", "--max-tokens", "2000"]
            },
            {
                "file": "test_smma_integration.py", 
                "name": "Test de Integración",
                "description": "Integración SMMA con ToolCallingAgent (simulado)",
                "args": ["--iterations", "5", "--max-tokens", "2500"]
            }
        ]
        
        # Opcional: Test con API real (requiere API key)
        include_api_test = False
        if include_api_test and os.getenv("ZEN_API_KEY"):
            tests.append({
                "file": "test_smma_simple.py",
                "name": "Test Simple con API",
                "description": "Test con modelo real usando prompting estructurado",
                "args": []
            })
        
        # Ejecutar cada test
        for test_config in tests:
            result = self.run_test(
                test_config["file"],
                test_config["name"],
                test_config["description"],
                test_config["args"]
            )
            
            self.all_results["tests"].append(result)
            
            # Actualizar resumen
            self.all_results["summary"]["total"] += 1
            if result.get("status") == "passed":
                self.all_results["summary"]["passed"] += 1
            elif result.get("status") in ["failed", "error", "timeout"]:
                self.all_results["summary"]["failed"] += 1
            else:
                self.all_results["summary"]["skipped"] += 1
        
        # Generar reporte
        self.generate_report()
        
        return self.all_results
    
    def generate_report(self):
        """Generar reporte consolidado"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 REPORTE CONSOLIDADO DE TESTS SMMA")
        logger.info("=" * 80)
        
        summary = self.all_results["summary"]
        logger.info(f"\n📈 RESUMEN:")
        logger.info(f"  Total tests: {summary['total']}")
        logger.info(f"  ✅ Pasados:  {summary['passed']}")
        logger.info(f"  ❌ Fallidos: {summary['failed']}")
        logger.info(f"  ⏭️  Saltados: {summary['skipped']}")
        
        if summary['total'] > 0:
            success_rate = (summary['passed'] / summary['total']) * 100
            logger.info(f"  📊 Tasa de éxito: {success_rate:.1f}%")
        
        logger.info(f"\n🧪 DETALLE DE TESTS:")
        for i, test in enumerate(self.all_results["tests"], 1):
            status_icon = "✅" if test.get("status") == "passed" else "❌"
            logger.info(f"\n  {i}. {test['test']} {status_icon}")
            logger.info(f"     Estado: {test.get('status', 'unknown')}")
            logger.info(f"     Archivo: {test['file']}")
            
            if test.get("return_code") is not None:
                logger.info(f"     Código salida: {test['return_code']}")
            
            if test.get("error"):
                logger.info(f"     Error: {test['error']}")
        
        # Evaluación general
        logger.info("\n" + "=" * 80)
        if summary['failed'] == 0 and summary['total'] > 0:
            logger.info("🎉 ¡TODOS LOS TESTS PASARON!")
            logger.info("   La implementación SMMA está funcionando correctamente")
        elif summary['passed'] > 0:
            logger.info("⚠️  TESTS PARCIALMENTE EXITOSOS")
            logger.info(f"   {summary['passed']}/{summary['total']} tests pasaron")
        else:
            logger.info("❌ TESTS FALLIDOS")
            logger.info("   Revisa los errores detallados arriba")
        
        logger.info("=" * 80)
        
        # Guardar reporte JSON
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(self.all_results, f, indent=2, ensure_ascii=False)
            logger.info(f"\n📄 Reporte guardado en: {self.report_file}")
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
    
    def print_recommendations(self):
        """Imprimir recomendaciones basadas en resultados"""
        logger.info("\n" + "=" * 80)
        logger.info("💡 RECOMENDACIONES PARA SMMA")
        logger.info("=" * 80)
        
        # Analizar resultados para recomendaciones
        passed_tests = [t for t in self.all_results["tests"] if t.get("status") == "passed"]
        failed_tests = [t for t in self.all_results["tests"] if t.get("status") in ["failed", "error"]]
        
        if not passed_tests:
            logger.info("\n🚨 PROBLEMAS CRÍTICOS DETECTADOS:")
            logger.info("1. Ningún test pasó - Revisa la implementación base")
            logger.info("2. Verifica que MemoryManager esté correctamente implementado")
            logger.info("3. Comprueba las dependencias (openai, etc.)")
            return
        
        # Verificar cobertura de tests
        test_names = [t["test"] for t in passed_tests]  # Cambiado de "name" a "test"
        
        recommendations = []
        
        if "Test Unitario SMMA" not in test_names:
            recommendations.append("🔧 Implementar tests unitarios para MemoryManager")
        
        if "Test de Presión Forzada" not in test_names:
            recommendations.append("📈 Mejorar tests de presión para forzar uso de herramientas SMMA")
        
        if "Test de Integración" not in test_names:
            recommendations.append("🔄 Crear tests de integración real con ToolCallingAgent")
        
        # Verificar herramientas SMMA usadas
        smma_tools_used = False
        for test in passed_tests:
            if "smma" in test.get("stdout", "").lower() or "smma" in test.get("test", "").lower():
                smma_tools_used = True
                break
        
        if not smma_tools_used:
            recommendations.append("🛠️  Asegurar que las herramientas SMMA se usan cuando hay presión")
        
        # Verificar The Tape
        tape_mentioned = False
        for test in passed_tests:
            if "tape" in test.get("stdout", "").lower():
                tape_mentioned = True
                break
        
        if not tape_mentioned:
            recommendations.append("📼 Verificar que The Tape registra todas las acciones SMMA")
        
        # Imprimir recomendaciones
        if recommendations:
            logger.info("\n📋 RECOMENDACIONES DE MEJORA:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. {rec}")
        else:
            logger.info("\n✅ IMPLEMENTACIÓN SMMA COMPLETA")
            logger.info("   Todos los aspectos críticos están cubiertos")
        
        # Próximos pasos
        logger.info("\n🚀 PRÓXIMOS PASOS SUGERIDOS:")
        logger.info("1. Integrar MemoryManager con ToolCallingAgent real")
        logger.info("2. Añadir dashboard de presión al system prompt")
        logger.info("3. Implementar memoria semántica (LTM) para Fase 2")
        logger.info("4. Crear tests de rendimiento con muchos mensajes")
        
        logger.info("=" * 80)

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Runner de tests SMMA')
    parser.add_argument('--keep-results', action='store_true',
                       help='Mantener directorio de resultados después de ejecutar')
    parser.add_argument('--test-only', type=str,
                       help='Ejecutar solo un test específico (nombre del archivo)')
    
    args = parser.parse_args()
    
    # Ejecutar runner
    runner = SMMATestRunner()
    
    try:
        if args.test_only:
            # Ejecutar solo un test
            test_file = args.test_only
            test_name = os.path.basename(test_file).replace('.py', '').replace('_', ' ').title()
            
            result = runner.run_test(
                test_file,
                test_name,
                f"Test individual: {test_name}",
                []
            )
            
            runner.all_results["tests"].append(result)
            runner.generate_report()
        else:
            # Ejecutar todos los tests
            runner.run_all_tests()
        
        # Imprimir recomendaciones
        runner.print_recommendations()
        
        # Determinar código de salida
        summary = runner.all_results["summary"]
        if summary.get("failed", 0) > 0:
            return 1
        elif summary.get("total", 0) == 0:
            return 2  # No se ejecutaron tests
        else:
            return 0
            
    finally:
        if not args.keep_results:
            runner.cleanup()
            logger.info(f"\n🧹 Directorio de resultados limpiado")
        else:
            logger.info(f"\n💾 Resultados guardados en: {runner.results_dir}")

if __name__ == "__main__":
    sys.exit(main())