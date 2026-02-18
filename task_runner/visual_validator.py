"""
Visual Validator - Valida screenshots usando IA con visión
"""

import logging
from typing import Dict, List
from .opencode_runner import OpenCodeRunner


class VisualValidator:
    """Valida screenshots visualmente usando OpenCode con modelos de visión"""
    
    def __init__(self, config: Dict, opencode_config: Dict):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.model = config.get("model", "anthropic/claude-3.5-sonnet")
        self.timeout = config.get("timeout", 60)
        self.opencode = OpenCodeRunner(opencode_config)
        self.logger = logging.getLogger("VisualValidator")
    
    def validate(
        self,
        screenshot_path: str,
        context: str,
        criteria: List[str]
    ) -> Dict:
        """
        Valida un screenshot visualmente
        
        Args:
            screenshot_path: Ruta al archivo PNG
            context: Descripción del contexto/propósito
            criteria: Lista de criterios a verificar
        
        Returns:
            Dict con:
                - valid: bool
                - feedback: str
                - raw_response: str
        """
        if not self.enabled:
            return {
                "valid": True,
                "feedback": "Validación visual deshabilitada",
                "raw_response": ""
            }
        
        self.logger.info(f"👁️  Validando visualmente: {screenshot_path}")
        
        # Construir prompt detallado
        criteria_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(criteria)])
        
        prompt = f"""Analiza esta captura de pantalla de una aplicación web y evalúa su calidad visual.

## Contexto
{context}

## Criterios de Validación
{criteria_text}

## Instrucciones de Análisis
Por favor, analiza la imagen y verifica:
1. Que todos los elementos mencionados en los criterios estén presentes
2. Que el layout sea correcto (sin elementos desalineados o cortados)
3. Que los colores y estilos sean consistentes
4. Que no haya errores visuales evidentes
5. Que la interfaz sea usable (tamaños de botones adecuados, contraste legible)

## Formato de Respuesta OBLIGATORIO
Responde EXACTAMENTE en este formato:

```
VALIDATION: PASS o FAIL

OBSERVACIONES:
- [Elemento 1]: Estado (presente/ausente/correcto/incorrecto)
- [Elemento 2]: Estado
...

FEEDBACK:
[Explicación detallada de lo que observas y por qué pasa o falla la validación]
```
"""
        
        try:
            # Ejecutar validación con OpenCode incluyendo el archivo
            result = self.opencode.validate_screenshot(
                screenshot_path,
                context,
                criteria
            )
            
            self.logger.info(f"✅ Validación completada: {'PASS' if result['valid'] else 'FAIL'}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error en validación visual: {e}")
            return {
                "valid": False,
                "feedback": f"Error durante validación: {str(e)}",
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
