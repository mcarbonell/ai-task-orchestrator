---
dependencies: []
estimated_time: 1h
id: T-001
priority: high
status: failed
title: Configurar estructura del proyecto y dependencias
---
## Descripción
Configurar la estructura base del proyecto React con TypeScript, Vite y Tailwind CSS.

## Criterios de Aceptación
- [ ] Proyecto Vite + React + TypeScript inicializado
- [ ] Tailwind CSS configurado y funcionando
- [ ] Estructura de carpetas creada según convenciones
- [ ] Vitest configurado para testing
- [ ] Scripts de package.json configurados

## Tests Unitarios
```bash
npm test
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:5173
  
  - action: screenshot
    filename: initial-load.png
    width: 1280
    height: 720
  
  - action: eval
    code: document.title
    expect: "Vite + React + TS"

console_checks:
  - no_errors: true

performance_thresholds:
  lcp: 2500
  cls: 0.1
```

## Definition of Done
- [ ] `npm run dev` funciona sin errores
- [ ] Tailwind styles se aplican correctamente
- [ ] Tests pasan (aunque sean vacíos inicialmente)
- [ ] Console sin errores
