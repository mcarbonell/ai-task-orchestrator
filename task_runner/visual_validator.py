"""
Visual Validator - Valida screenshots usando IA con visión
"""

import os
import base64
import logging
from typing import Dict, List
from .tool_calling_agent import ToolCallingAgent

class VisualValidator:
    """Valida screenshots visualmente usando el ToolCallingAgent API"""
    
    def __init__(self, config: Dict, opencode_config: Dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        
        self.logger = logging.getLogger("VisualValidator")
        
        # Inicializar el Agente nativo
        self.agent = ToolCallingAgent(
            model=config.get("model", opencode_config.get("model", "kimi-k2.5-free")),
            provider=opencode_config.get("provider", "zen"),
            max_iterations=3 # Solo necesitamos validacion directa, no herramientas
        )
    
    def _encode_image(self, image_path: str) -> str:
        """Convierte una imagen a base64 para la API de OpenAI/OpenRouter"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def validate(
        self,
        screenshot_path: str,
        context: str,
        criteria: List[str]
    ) -> Dict:
        """
        Valida un screenshot visualmente usando API
        """
        if not self.enabled:
            return {
                "valid": True,
                "feedback": "Validación visual deshabilitada",
                "raw_response": ""
            }
            
        if not os.path.exists(screenshot_path):
            return {
                "valid": False,
                "feedback": f"Screenshot no encontrado: {screenshot_path}",
                "raw_response": ""
            }
        
        self.logger.info(f"👁️  Validando visualmente: {screenshot_path}")
        
        # Construir prompt
        criteria_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(criteria)])
        
        system_prompt = "Eres un QA visual experto. Analiza la imagen, evalúa los criterios y finaliza OBLIGATORIAMENTE usando la herramienta 'finish_task' indicando en status 'completed' si pasa, o 'failed' si no pasa la validación visual, y pon tus observaciones en summary."
        
        task_prompt = f"""Analiza esta captura de pantalla de una aplicación web y evalúa su calidad visual.

## Contexto
{context}

## Criterios de Validación
{criteria_text}

## Instrucciones de Análisis
Verifica que los elementos presentes cumplan el layout, color y tamaño adecuados sin superponerse.
"""     
        # Configurar mensaje con multimodalidad nativa
        try:
            base64_img = self._encode_image(screenshot_path)
            
            # Formato estándar de Chat Completion para imágenes
            image_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": task_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_img}"
                        }
                    }
                ]
            }
            
            # Ejecutar loop del agente inyectando la imagen manualmente a los mensajes iniciales
            self.agent.messages = [
                {"role": "system", "content": system_prompt},
                image_message
            ]
            
            # Truco: Invocamos el loop interno pasando por alto el setting default del prompt
            result = self.agent.run_task(system_prompt=system_prompt, task_prompt="Evalúa la imagen enviada.")
            
            # Parseamos resultado
            passed = result.get("status") == "completed"
            
            self.logger.info(f"✅ Validación completada: {'PASS' if passed else 'FAIL'}")
            
            return {
                "valid": passed,
                "feedback": result.get("summary", ""),
                "raw_response": result.get("summary", "")
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error en validación visual: {e}")
            return {
                "valid": False,
                "feedback": f"Error durante validación API: {str(e)}",
                "raw_response": "",
                "error": str(e)
            }
    
    def validate_multiple(
        self,
        screenshots: List[str],
        context: str,
        criteria: List[str]
    ) -> Dict:
        """
        Valida múltiples screenshots
        
        Returns:
            Dict con validaciones individuales y resultado global
        """
        self.logger.info(f"👁️  Validando {len(screenshots)} screenshots")
        
        results = []
        for screenshot in screenshots:
            result = self.validate(screenshot, context, criteria)
            results.append({
                "screenshot": screenshot,
                **result
            })
        
        all_valid = all(r["valid"] for r in results)
        
        return {
            "valid": all_valid,
            "validations": results,
            "passed": len([r for r in results if r["valid"]]),
            "failed": len([r for r in results if not r["valid"]])
        }
