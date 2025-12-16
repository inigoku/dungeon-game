"""
Refactorización del proyecto Dungeon Game

Estructura propuesta:
===================

dungeon/
├── main.py                      # Punto de entrada
├── config.py                    # Constantes y configuración
├── models/
│   ├── __init__.py
│   ├── cell.py                  # Cell, CellType, Direction
│   └── board.py                 # DungeonBoard (solo datos)
├── services/
│   ├── __init__.py
│   ├── board_generator.py       # Generación y pathfinding
│   ├── lighting_system.py       # Cálculos de iluminación
│   └── audio_manager.py         # Gestión de sonidos
├── rendering/
│   ├── __init__.py
│   ├── renderer.py              # DungeonRenderer principal
│   ├── cell_renderer.py         # Renderizado de celdas
│   ├── decorations.py           # Antorchas, fuente, escaleras, sangre
│   └── effects.py               # Líneas quebradas, piedras
├── game/
│   ├── __init__.py
│   ├── game_state.py            # Estado del juego
│   └── input_handler.py         # Manejo de entrada
└── utils/
    ├── __init__.py
    └── helpers.py               # Funciones auxiliares

Principios de desacoplamiento:
===============================

1. **Separación de responsabilidades**:
   - Models: Solo datos, sin lógica de negocio
   - Services: Lógica de negocio sin UI
   - Rendering: Solo renderizado, sin lógica
   - Game: Coordinación entre componentes

2. **Inyección de dependencias**:
   - Los servicios reciben las dependencias que necesitan
   - No acceden directamente a state global

3. **Interfaces claras**:
   - Cada clase expone una API pública mínima
   - Las dependencias se pasan como parámetros

4. **Single Responsibility**:
   - Cada clase tiene una única responsabilidad
   - Facilita testing y mantenimiento

Migración gradual:
==================

Paso 1: Crear modelos básicos (✓ Cell, CellType, Direction ya creados)
Paso 2: Extraer servicios (generación, iluminación, audio)
Paso 3: Separar rendering en componentes
Paso 4: Crear game state y coordinador
Paso 5: Actualizar main.py para usar nuevos módulos
Paso 6: Testing y validación
Paso 7: Eliminar dungeon.py original

Ejemplo de uso después de refactorización:
==========================================

# main.py
from game import DungeonGame

def main():
    game = DungeonGame()
    game.run()

if __name__ == "__main__":
    main()

# game/game_state.py
class DungeonGame:
    def __init__(self):
        self.board_generator = BoardGenerator(size=101)
        self.lighting = LightingSystem()
        self.renderer = DungeonRenderer(screen, lighting)
        self.audio = AudioManager()
        self.state = GameState()
    
    def run(self):
        # Game loop usando los componentes desacoplados
        ...
"""
