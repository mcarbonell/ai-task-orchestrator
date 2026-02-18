---
id: T-002
title: "Implementar componente Header con navegación"
status: pending
priority: high
dependencies: [T-001]
estimated_time: "1.5h"
---

## Descripción
Crear componente Header con logo, menú de navegación y carrito de compras.

## Criterios de Aceptación
- [ ] Logo visible en la izquierda
- [ ] Menú de navegación con links: Inicio, Productos, Carrito
- [ ] Icono de carrito con contador de items
- [ ] Diseño responsive (mobile menu)
- [ ] Links funcionan con React Router

## Tests Unitarios
```bash
npm test src/components/Header.test.tsx
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:5173
  
  - action: screenshot
    filename: header-desktop.png
    width: 1280
    height: 720
  
  - action: screenshot
    filename: header-mobile.png
    width: 375
    height: 812
  
  - action: eval
    code: document.querySelector('header') !== null
    expect: true

console_checks:
  - no_errors: true

performance_thresholds:
  lcp: 2500
  cls: 0.1
```

## Definition of Done
- [ ] Componente Header renderiza correctamente
- [ ] Tests unitarios pasan
- [ ] Screenshots desktop y mobile válidos
- [ ] Navegación funciona
- [ ] Console sin errores
