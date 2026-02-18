---
dependencies: []
estimated_time: 30m
id: T-001
priority: high
status: failed
title: Crear estructura HTML base
---
## Descripción
Crear el archivo index.html con estructura semántica básica: header, main con hero section, y footer.

## Criterios de Aceptación
- [ ] Archivo index.html creado
- [ ] Estructura semántica HTML5 correcta
- [ ] Header con titulo del sitio
- [ ] Main con sección hero (h1 + p)
- [ ] Footer con copyright
- [ ] Link a styles.css

## Tests Unitarios
```bash
test -f index.html && echo "HTML exists"
```

## Tests E2E (CDP)
```yaml
steps:
  - action: navigate
    url: file://C:/Users/mrcm_/Local/proj/ai-task-orchestrator/test-real-project/index.html
  
  - action: screenshot
    filename: html-structure.png
    width: 1280
    height: 720
  
  - action: eval
    code: document.querySelector('header') !== null && document.querySelector('main') !== null && document.querySelector('footer') !== null
    expect: true

console_checks:
  - no_errors: true
```

## Definition of Done
- [ ] index.html existe y es válido
- [ ] Estructura HTML semántica correcta
- [ ] Screenshot muestra estructura básica
- [ ] No hay errores en console
