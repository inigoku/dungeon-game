# main.py - Entry point for web version
import asyncio
import pygame
import sys

# Import game after pygame init
import dungeon

async def main():
    """Main entry point for Pygbag web version."""
    game = dungeon.DungeonBoard()
    await game.run()

# Run the game
asyncio.run(main())
