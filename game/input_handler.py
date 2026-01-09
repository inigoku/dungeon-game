"""
game/input_handler.py
Manejador de entrada desacoplado para Dungeon Game.
"""
import pygame
from models.cell import Direction

class InputHandler:
    def __init__(self, game):
        self.game = game
        # Mapeo de teclas a direcciones
        self.dir_map = {
            pygame.K_UP: Direction.N,
            pygame.K_DOWN: Direction.S,
            pygame.K_RIGHT: Direction.E,
            pygame.K_LEFT: Direction.O,
            pygame.K_w: Direction.N,
            pygame.K_s: Direction.S,
            pygame.K_d: Direction.E,
            pygame.K_a: Direction.O,
        }

    def handle_input(self, event):
        """Procesa un evento individual de Pygame. Retorna False si el juego debe terminar."""
        
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)
            
        return True

    def _handle_keydown(self, event):
        # 1. Confirmaciones modales (tienen prioridad)
        if self.game.asking_exit_confirmation:
            if event.key == pygame.K_s:
                return False # Salir del juego
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                self.game.asking_exit_confirmation = False
            return True

        if self.game.asking_main_menu_confirmation:
            if event.key == pygame.K_s:
                self._return_to_main_menu()
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                self.game.asking_main_menu_confirmation = False
            return True

        # 2. Pantalla de título
        if self.game.showing_title:
            if event.key == pygame.K_ESCAPE:
                return False
            self._start_game()
            return True

        # 3. Controles generales In-Game
        if event.key == pygame.K_ESCAPE:
            self._handle_escape()
            return True

        # Teclas de función y utilidades
        if event.key == pygame.K_F2:
            self.game.auto_reveal_mode = not self.game.auto_reveal_mode
        elif event.key == pygame.K_F3:
            self.game.debug_mode = not self.game.debug_mode
        elif event.key == pygame.K_F4:
            self.game.show_path = not self.game.show_path
        elif event.key == pygame.K_F5:
            self.game.lighting.toggle_lines_darkening()
        elif event.key == pygame.K_z:
            self.game.zoom_in()
        elif event.key == pygame.K_x:
            self.game.zoom_out()
        
        # 4. Movimiento
        # Bloquear movimiento durante animaciones específicas
        if not self.game.intro_anim_active:
            if event.key in self.dir_map:
                self.game.place_cell_in_direction(self.dir_map[event.key])
        
        return True

    def _return_to_main_menu(self):
        self.game.showing_title = True
        self.game.asking_main_menu_confirmation = False
        self.game.audio.stop_music()
        if self.game.audio.thought_active:
            self.game.audio.cancel_thought()

    def _start_game(self):
        self.game.showing_title = False
        self.game.intro_anim_active = True
        self.game.intro_anim_start_time = pygame.time.get_ticks()

    def _handle_escape(self):
        if self.game.audio.thought_active:
            self.game.audio.cancel_thought()
        else:
            self.game.asking_main_menu_confirmation = True
