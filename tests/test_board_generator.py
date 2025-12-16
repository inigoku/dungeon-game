"""Tests unitarios para services/board_generator.py"""
import pytest
from models.cell import Cell, CellType, Direction
from services.board_generator import BoardGenerator
import config


class TestBoardGeneratorInitialization:
    """Tests para la inicialización del generador."""
    
    def test_initialization_default(self):
        """Verificar inicialización con tamaño por defecto."""
        generator = BoardGenerator()
        assert generator.board_size == config.DEFAULT_BOARD_SIZE
    
    def test_initialization_custom_size(self):
        """Verificar inicialización con tamaño personalizado."""
        generator = BoardGenerator(board_size=51)
        assert generator.board_size == 51
    
    def test_initialization_odd_size(self):
        """Verificar que el tamaño debe ser impar."""
        # Tamaños impares deben funcionar
        generator = BoardGenerator(board_size=21)
        assert generator.board_size == 21


class TestBoardGeneration:
    """Tests para la generación del tablero."""
    
    @pytest.fixture
    def generator(self):
        """Fixture para crear generador pequeño para tests."""
        return BoardGenerator(board_size=21)
    
    def test_generate_returns_board(self, generator):
        """Verificar que generate devuelve un tablero."""
        board, entrance, exit_pos = generator.generate()
        assert board is not None
        assert isinstance(board, list)
    
    def test_board_dimensions(self, generator):
        """Verificar dimensiones del tablero."""
        board, entrance, exit_pos = generator.generate()
        assert len(board) == generator.board_size
        assert all(len(row) == generator.board_size for row in board)
    
    def test_board_contains_cells(self, generator):
        """Verificar que el tablero contiene objetos Cell."""
        board, entrance, exit_pos = generator.generate()
        # Verificar algunas celdas aleatorias
        assert isinstance(board[0][0], Cell)
        assert isinstance(board[10][10], Cell)
        assert isinstance(board[generator.board_size-1][generator.board_size-1], Cell)
    
    def test_entrance_exists(self, generator):
        """Verificar que existe una posición de entrada."""
        board, entrance, exit_pos = generator.generate()
        assert entrance is not None
        assert isinstance(entrance, tuple)
        assert len(entrance) == 2
    
    def test_exit_exists(self, generator):
        """Verificar que existe una posición de salida."""
        board, entrance, exit_pos = generator.generate()
        assert exit_pos is not None
        assert isinstance(exit_pos, tuple)
        assert len(exit_pos) == 2
    
    def test_entrance_is_centro(self, generator):
        """Verificar que la entrada está en el centro."""
        board, entrance, exit_pos = generator.generate()
        center = generator.board_size // 2
        assert entrance == (center, center)
    
    def test_entrance_cell_type(self, generator):
        """Verificar que la celda de entrada tiene tipo INICIO."""
        board, entrance, exit_pos = generator.generate()
        row, col = entrance
        assert board[row][col].tipo == CellType.INICIO
    
    def test_exit_cell_type(self, generator):
        """Verificar que la celda de salida tiene tipo SALIDA."""
        board, entrance, exit_pos = generator.generate()
        row, col = exit_pos
        assert board[row][col].tipo == CellType.SALIDA
    
    def test_entrance_and_exit_different(self, generator):
        """Verificar que entrada y salida son diferentes."""
        board, entrance, exit_pos = generator.generate()
        assert entrance != exit_pos
    
    def test_positions_within_bounds(self, generator):
        """Verificar que las posiciones están dentro del tablero."""
        board, entrance, exit_pos = generator.generate()
        
        for pos in [entrance, exit_pos]:
            row, col = pos
            assert 0 <= row < generator.board_size
            assert 0 <= col < generator.board_size


class TestPathFinding:
    """Tests para el sistema de pathfinding."""
    
    @pytest.fixture
    def generator(self):
        """Fixture para crear generador."""
        return BoardGenerator(board_size=21)
    
    def test_find_path_exists(self, generator):
        """Verificar que find_path existe como método."""
        assert hasattr(generator, 'find_path')
    
    def test_find_path_returns_list(self, generator):
        """Verificar que find_path devuelve una lista."""
        board, entrance, exit_pos = generator.generate()
        current_pos = entrance
        
        path = generator.find_path(board, current_pos, exit_pos)
        assert isinstance(path, list)
    
    def test_find_path_from_entrance_to_exit(self, generator):
        """Verificar que existe camino de entrada a salida."""
        board, entrance, exit_pos = generator.generate()
        
        path = generator.find_path(board, entrance, exit_pos)
        assert len(path) > 0  # Debe haber un camino
    
    def test_path_starts_at_current(self, generator):
        """Verificar que el camino empieza en la posición actual."""
        board, entrance, exit_pos = generator.generate()
        
        path = generator.find_path(board, entrance, exit_pos)
        if len(path) > 0:
            assert path[0] == entrance
    
    def test_path_ends_at_exit(self, generator):
        """Verificar que el camino termina en la salida."""
        board, entrance, exit_pos = generator.generate()
        
        path = generator.find_path(board, entrance, exit_pos)
        if len(path) > 0:
            assert path[-1] == exit_pos
    
    def test_path_positions_valid(self, generator):
        """Verificar que todas las posiciones del camino son válidas."""
        board, entrance, exit_pos = generator.generate()
        
        path = generator.find_path(board, entrance, exit_pos)
        for pos in path:
            row, col = pos
            assert 0 <= row < generator.board_size
            assert 0 <= col < generator.board_size


class TestBoardConnectivity:
    """Tests para verificar conectividad del tablero."""
    
    @pytest.fixture
    def generator(self):
        """Fixture para crear generador."""
        return BoardGenerator(board_size=21)
    
    def test_entrance_has_exits(self, generator):
        """Verificar que la entrada tiene al menos una salida."""
        board, entrance, exit_pos = generator.generate()
        row, col = entrance
        cell = board[row][col]
        
        # La entrada debe tener al menos una salida abierta
        assert any(cell.salidas)
    
    def test_cells_have_valid_exits(self, generator):
        """Verificar que las celdas tienen salidas válidas."""
        board, entrance, exit_pos = generator.generate()
        
        # Verificar algunas celdas
        for i in range(0, generator.board_size, 5):
            for j in range(0, generator.board_size, 5):
                cell = board[i][j]
                assert isinstance(cell.salidas, list)
                assert len(cell.salidas) == 4
                assert all(isinstance(exit, bool) for exit in cell.salidas)


class TestCellTypes:
    """Tests para verificar tipos de celdas."""
    
    @pytest.fixture
    def generator(self):
        """Fixture para crear generador."""
        return BoardGenerator(board_size=21)
    
    def test_board_has_multiple_cell_types(self, generator):
        """Verificar que el tablero tiene varios tipos de celdas."""
        board, entrance, exit_pos = generator.generate()
        
        cell_types = set()
        for row in board:
            for cell in row:
                cell_types.add(cell.tipo)
        
        # Debe haber al menos entrada y salida
        assert CellType.INICIO in cell_types
        assert CellType.SALIDA in cell_types
    
    def test_only_one_entrance(self, generator):
        """Verificar que solo hay una entrada."""
        board, entrance, exit_pos = generator.generate()
        
        entrance_count = 0
        for row in board:
            for cell in row:
                if cell.tipo == CellType.INICIO:
                    entrance_count += 1
        
        assert entrance_count == 1
    
    def test_only_one_exit(self, generator):
        """Verificar que solo hay una salida."""
        board, entrance, exit_pos = generator.generate()
        
        exit_count = 0
        for row in board:
            for cell in row:
                if cell.tipo == CellType.SALIDA:
                    exit_count += 1
        
        assert exit_count == 1


class TestTorches:
    """Tests para la generación de antorchas."""
    
    @pytest.fixture
    def generator(self):
        """Fixture para crear generador."""
        return BoardGenerator(board_size=21)
    
    def test_torches_are_non_negative(self, generator):
        """Verificar que el número de antorchas nunca es negativo."""
        board, entrance, exit_pos = generator.generate()
        
        for row in board:
            for cell in row:
                assert cell.num_antorchas >= 0
    
    def test_some_cells_have_torches(self, generator):
        """Verificar que algunas celdas tienen antorchas."""
        board, entrance, exit_pos = generator.generate()
        
        total_torches = sum(cell.num_antorchas for row in board for cell in row)
        # Debe haber al menos algunas antorchas en el tablero
        assert total_torches > 0


class TestBoardRegeneration:
    """Tests para verificar que se pueden generar múltiples tableros."""
    
    @pytest.fixture
    def generator(self):
        """Fixture para crear generador."""
        return BoardGenerator(board_size=21)
    
    def test_can_generate_multiple_boards(self, generator):
        """Verificar que se pueden generar múltiples tableros."""
        board1, entrance1, exit1 = generator.generate()
        board2, entrance2, exit2 = generator.generate()
        
        # Ambos tableros deben ser válidos
        assert board1 is not None
        assert board2 is not None
    
    def test_multiple_generations_different(self, generator):
        """Verificar que generaciones múltiples pueden ser diferentes."""
        board1, entrance1, exit1 = generator.generate()
        board2, entrance2, exit2 = generator.generate()
        
        # Las salidas pueden ser diferentes (aunque no siempre)
        # Solo verificamos que el método funciona múltiples veces
        assert isinstance(exit1, tuple)
        assert isinstance(exit2, tuple)


class TestEdgeCases:
    """Tests para casos especiales."""
    
    def test_small_board(self):
        """Verificar generación con tablero pequeño."""
        generator = BoardGenerator(board_size=11)
        board, entrance, exit_pos = generator.generate()
        
        assert len(board) == 11
        assert entrance is not None
        assert exit_pos is not None
    
    def test_medium_board(self):
        """Verificar generación con tablero mediano."""
        generator = BoardGenerator(board_size=51)
        board, entrance, exit_pos = generator.generate()
        
        assert len(board) == 51
        assert entrance is not None
        assert exit_pos is not None
