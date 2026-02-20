# Contributing to AI Task Orchestrator

¡Gracias por tu interés en contribuir! 🎉

## Cómo Contribuir

### Reportar Bugs

1. Verifica que el bug no esté ya reportado
2. Abre un [Issue](https://github.com/mcarbonell/ai-task-orchestrator/issues) con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Logs si aplica

### Sugerir Features

1. Abre un Issue con label `enhancement`
2. Describe el feature y su caso de uso
3. Explica por qué sería útil

### Pull Requests

1. **Fork** el repositorio
2. **Branch:** `git checkout -b feature/nombre-feature`
3. **Commit:** `git commit -m 'Add feature'`
4. **Push:** `git push origin feature/nombre-feature`
5. **PR:** Abre Pull Request con descripción clara

## Guías de Código

### Python
- PEP 8
- Type hints donde sea posible
- Docstrings para funciones públicas
- Tests para nueva funcionalidad

### Commits
- Mensajes claros y descriptivos
- Usa imperativo: "Add feature" no "Added feature"

## Desarrollo Local

```bash
# Setup
pip install -r requirements.txt

# Ejecutar tests
pytest

# Verificar estilo
flake8 task_runner/

# Type checking
mypy task_runner/
```

## Áreas de Contribución

- [ ] Mejorar documentación
- [ ] Añadir más templates de tareas
- [ ] Soportar más modelos de IA
- [ ] Integraciones CI/CD
- [ ] Tests unitarios
- [ ] Mejorar manejo de errores

## Preguntas?

Únete a las [Discusiones](https://github.com/mcarbonell/ai-task-orchestrator/discussions) o abre un Issue.

¡Gracias! 🙏
