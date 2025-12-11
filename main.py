import asyncio
import sys

# Importar el juego
from dungeon import DungeonBoard

async def main():
    """Punto de entrada principal para la versión web."""
    dungeon = DungeonBoard()
    await dungeon.run()

if __name__ == "__main__":
    asyncio.run(main())
