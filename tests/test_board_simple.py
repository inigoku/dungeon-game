"""Tests simplificados para services/board_generator.py"""
import pytest
from services.board_generator import BoardGenerator
from models.cell import Cell, CellType, Direction


class TestBoardGeneratorBasics:
    """Tests básicos del generador de tableros."""
    
    def test_initialization(self):
        """Verificar inicialización con tamaño."""
        generator = BoardGenerator(21)
        assert generator is not None
        assert generator.size == 21
    
    def test_different_sizes(self):
        """Verificar que acepta diferentes tamaños."""
        sizes = [11, 21, 51, 101]
        for size in sizes:
            generator = BoardGenerator(size)
            assert generator.size == size
    
    def test_has_check_connectivity(self):
        """Verificar que tiene método check_connectivity."""
        generator = BoardGenerator(21)
        assert hasattr(generator, 'check_connectivity')
        assert callable(generator.check_connectivity)
    
    def test_has_generate_exit_position(self):
        """Verificar que tiene método generate_exit_position."""
        generator = BoardGenerator(11)
        assert hasattr(generator, 'generate_exit_position')
        assert callable(generator.generate_exit_position)
    
    def test_has_calculate_main_path(self):
        """Verificar que tiene método calculate_main_path."""
        generator = BoardGenerator(11)
        assert hasattr(generator, 'calculate_main_path')
        assert callable(generator.calculate_main_path)
    
    def test_generate_exit_position_returns_tuple(self):
        """Verificar que generate_exit_position retorna tupla."""
        generator = BoardGenerator(11)
        center = 5
        exit_pos = generator.generate_exit_position(center)
        assert isinstance(exit_pos, tuple)
        assert len(exit_pos) == 2
    
    def test_generate_exit_position_valid_coordinates(self):
        """Verificar que las coordenadas de salida son válidas."""
        generator = BoardGenerator(11)
        center = 5
        exit_pos = generator.generate_exit_position(center)
        assert 0 <= exit_pos[0] < 11
        assert 0 <= exit_pos[1] < 11
    
    def test_calculate_main_path_exists(self):
        """Verificar que calculate_main_path existe y es callable."""
        generator = BoardGenerator(11)
        start = (0, 0)
        end = (10, 10)
        path = generator.calculate_main_path(start, end)
        assert isinstance(path, list)
