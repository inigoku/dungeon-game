# Tests Unitarios - Dungeon Game

## Estado Actual

Los tests están configurados para los módulos refactorizados, pero algunos módulos tienen API diferentes entre el código legacy (`dungeon.py`) y los módulos refactorizados.

### Módulos Completamente Refactorizados

Estos módulos tienen implementaciones independientes y tests completos:

1. **models/cell.py** ✅
   - Estructura: dataclass con `CellType` (Enum) y `Direction` (Enum)
   - Tests: `tests/test_cell.py` (adaptados a la API real)

2. **config.py** ✅
   - Tests: `tests/test_config.py` (completos)

3. **services/lighting_system.py** ✅
   - Tests: `tests/test_lighting_system.py` (completos)

4. **rendering/decorations.py** ✅
   - Tests: `tests/test_decorations.py` (con mocks de pygame)

5. **rendering/effects.py** ✅
   - Tests: `tests/test_effects.py` (con mocks de pygame)

6. **rendering/cell_renderer.py** ✅
   - Tests: `tests/test_cell_renderer.py` (con mocks de pygame)

### Módulos Parcialmente Refactorizados

Estos módulos necesitan ajustes en los tests:

7. **services/board_generator.py** ⚠️
   - Problema: El generador usa estructura legacy de Cell
   - Solución: Necesita adaptarse a la nueva estructura

8. **services/audio_manager.py** ⚠️
   - Problema: API real difiere de los tests
   - Solución: Revisar métodos reales y ajustar tests

## Ejecutar Tests

### Todos los tests
```bash
pytest tests/ -v
```

### Un módulo específico
```bash
pytest tests/test_config.py -v
```

### Con cobertura
```bash
pytest tests/ --cov=. --cov-report=html
```

### Tests que deberían pasar ahora

```bash
# Config (todos pasan)
pytest tests/test_config.py -v

# Cell (adaptados a API real)
pytest tests/test_cell.py -v

# Lighting System
pytest tests/test_lighting_system.py -v
```

## Próximos Pasos

1. **Revisar board_generator.py** - Adaptar para usar nueva estructura de Cell
2. **Revisar audio_manager.py** - Verificar métodos reales y actualizar tests
3. **Agregar tests de integración** - Verificar que los módulos funcionan juntos
4. **Aumentar cobertura** - Agregar casos edge más complejos

## Notas Importantes

- Los tests de rendering usan mocks de pygame para no requerir display
- Los tests de audio usan mocks para no requerir archivos de sonido
- La estructura legacy en dungeon.py usa arrays para salidas, mientras que la nueva usa sets
- Algunos módulos necesitan refactorización adicional para ser completamente independientes
