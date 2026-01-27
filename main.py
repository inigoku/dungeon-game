#!/usr/bin/env python3
"""
Dungeon Game - Punto de entrada principal

Este es el punto de entrada del juego compatible con web (Pygbag) y escritorio.
Utiliza la arquitectura modular refactorizada cuando está disponible.

Arquitectura modular:
- models/: Estructuras de datos (Cell, CellType, Direction)
- config.py: Constantes del juego
- services/: Lógica de negocio (iluminación, audio, generación)
- rendering/: Renderizado visual (decoraciones, efec    tos, celdas)

La clase DungeonBoard en dungeon.py automáticamente detecta y usa
los módulos refactorizados si están disponibles, cayendo a la versión
legacy si hay algún problema.

Uso:
    # Escritorio
    python main.py
    
    # Web (Pygbag)
    pygbag main.py
"""

import asyncio
import sys
import pygame

# Importaciones explícitas para asegurar que Pygbag empaquete estos módulos
import models.cell
import game.input_handler

# Importar el juego
import dungeon


async def main():
    """Punto de entrada principal del juego."""
    try:
        while True:
            # Crear instancia del juego
            # DungeonBoard automáticamente usa los módulos refactorizados
            game = dungeon.DungeonBoard()
            
            # Ejecutar el loop principal del juego
            # Si retorna True, reiniciamos el juego. Si retorna False, salimos.
            if not await game.run():
                break
        
        pygame.quit()
        
    except KeyboardInterrupt:
        print("\n¡Juego interrumpido por el usuario!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("🎮 Dungeon Game")
    print("=" * 50)
    print("=== INICIO main.py ===")
    # Ejecutar el juego
    asyncio.run(main())
