---
id: T-XXX
title: "Título de la tarea"
status: pending
priority: medium
dependencies: []
estimated_time: "2h"
---

## Descripción
Describe aquí la funcionalidad a implementar. Sé específico sobre qué se espera lograr.

## Criterios de Aceptación
- [ ] [Criterio específico y medible 1]
- [ ] [Criterio específico y medible 2]
- [ ] [Criterio específico y medible 3]

## Tests Unitarios
```bash
# Comando para ejecutar tests específicos de esta tarea
npm test src/components/MiComponente.test.tsx
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:3000/ruta-de-prueba
  
  - action: screenshot
    filename: step-1-initial.png
    width: 1280
    height: 720
  
  - action: eval
    code: |
      // Interacción con la página
      document.querySelector('#input-campo').value = 'test';
      document.querySelector('#boton-submit').click();
  
  - action: wait
    milliseconds: 1000
  
  - action: screenshot
    filename: step-2-after-interaction.png
  
  - action: eval
    code: window.location.pathname
    expect: /ruta-esperada

console_checks:
  - no_errors: true
  - allowed_warnings: ["React.StrictMode"]

performance_thresholds:
  lcp: 2500  # ms
  cls: 0.1
  fcp: 1800  # ms
  ttfb: 800  # ms
```

## Definition of Done
- [ ] Todos los criterios de aceptación cumplidos
- [ ] Tests unitarios pasan (coverage > 80%)
- [ ] Screenshots generados y validados visualmente
- [ ] Console del navegador sin errores
- [ ] Métricas de performance dentro de umbrales
- [ ] Código sigue convenciones del proyecto

## Notas Adicionales
- [Información adicional relevante]
- [Links a documentación]
- [Consideraciones especiales]
