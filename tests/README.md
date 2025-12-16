# Tests del Proyecto Dungeon

Este directorio contiene los tests unitarios del juego de dungeon.

## Estructura Actual

### ✅ Tests Activos (98 tests - 100% pasando)

**Tests de Modelos y Configuración:**
- `test_config.py` - Tests de configuración (31 tests)
- `test_cell.py` - Tests del modelo de celdas (14 tests)

**Tests Simplificados de Servicios:**
- `test_lighting_simple.py` - Tests básicos del sistema de iluminación (6 tests)
- `test_board_simple.py` - Tests básicos del generador de tableros (8 tests)
- `test_audio_simple.py` - Tests básicos del gestor de audio (12 tests)

**Tests Simplificados de Rendering:**
- `test_cell_renderer_simple.py` - Tests básicos del renderizador de celdas (12 tests)
- `test_decorations_simple.py` - Tests básicos del renderizador de decoraciones (8 tests)
- `test_effects_simple.py` - Tests básicos del renderizador de efectos (7 tests)

### 📦 Tests Archivados (*.old)

Los siguientes archivos fueron renombrados a `.old` porque asumen APIs incorrectas:
- `test_lighting_system.py.old` - Asume API legacy de Cell
- `test_board_generator.py.old` - Asume método generate() que no existe
- `test_audio_manager.py.old` - Asume métodos que no existen
- `test_decorations.py.old` - Constructores incorrectos
- `test_effects.py.old` - Constructores incorrectos
- `test_cell_renderer.py.old` - Constructores incorrectos

Estos archivos se mantienen como referencia pero no se ejecutan.

## Ejecutar Tests

```bash
# Todos los tests activos
pytest tests/

# Tests específicos
pytest tests/test_config.py
pytest tests/test_lighting_simple.py

# Con cobertura
pytest tests/ --cov=.

# Con reporte HTML de cobertura
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html

# Solo tests simplificados
pytest tests/test_*_simple.py

# Modo verbose
pytest tests/ -v
```

## Métricas Actuales

- **Tests totales:** 98
- **Tests pasando:** 98 (100% ✅)
- **Cobertura total:** 25%
- **Módulos al 100%:** config.py, models/cell.py

## Filosofía de Testing

Los tests simplificados (`*_simple.py`) siguen estos principios:

1. **Validan APIs reales** - No asumen interfaces ideales
2. **Sin mocking complejo** - Solo lo necesario
3. **Fáciles de mantener** - Código claro y directo
4. **Documentan el uso** - Sirven como ejemplos

## Configuración

Los tests usan pytest con los siguientes plugins:
- pytest-cov: Para cobertura de código
- pytest-mock: Para mocking

Ver `pytest.ini` para la configuración completa.

## Agregar Nuevos Tests

Para agregar tests a un módulo:

1. Usa los archivos `*_simple.py` como plantilla
2. Verifica la API real del módulo antes de escribir tests
3. Mantén los tests simples y enfocados
4. Ejecuta `pytest` para verificar que pasan
