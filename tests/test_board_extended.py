"""Tests extendidos para services/board_generator.py - Cobertura 75%+"""
import pytest
from services.board_generator import BoardGenerator
from models.cell import Cell, CellType, Direction


class TestBoardGeneratorExtended:
    """Tests adicionales para alcanzar 75% de cobertura."""
    
    def test_check_connectivity_simple_path(self):
        """Test conectividad con camino simple."""
        generator = BoardGenerator(5)
        
        # Crear tablero con camino directo
        board = [[Cell(CellType.EMPTY, set()) for _ in range(5)] for _ in range(5)]
        
        # Crear camino: (0,0) -> (0,1) -> (0,2)
        board[0][0] = Cell(CellType.INICIO, {Direction.E})
        board[0][1] = Cell(CellType.PASILLO, {Direction.O, Direction.E})
        board[0][2] = Cell(CellType.SALIDA, {Direction.O})
        
        assert generator.check_connectivity(board, (0, 0), (0, 2)) == True
    
    def test_check_connectivity_no_path(self):
        """Test conectividad sin camino."""
        generator = BoardGenerator(5)
        
        # Crear tablero sin conexión
        board = [[Cell(CellType.EMPTY, set()) for _ in range(5)] for _ in range(5)]
        
        board[0][0] = Cell(CellType.INICIO, set())  # Sin salidas
        board[0][2] = Cell(CellType.SALIDA, set())
        
        assert generator.check_connectivity(board, (0, 0), (0, 2)) == False
    
    def test_check_connectivity_blocked_by_empty(self):
        """Test que celdas EMPTY bloquean el camino."""
        generator = BoardGenerator(5)
        
        board = [[Cell(CellType.EMPTY, set()) for _ in range(5)] for _ in range(5)]
        
        # Camino con celda EMPTY en medio
        board[0][0] = Cell(CellType.INICIO, {Direction.E})
        board[0][1] = Cell(CellType.EMPTY, {Direction.O, Direction.E})  # Bloqueado
        board[0][2] = Cell(CellType.SALIDA, {Direction.O})
        
        assert generator.check_connectivity(board, (0, 0), (0, 2)) == False
    
    def test_check_connectivity_mismatched_exits(self):
        """Test que salidas no coincidentes bloquean el camino."""
        generator = BoardGenerator(5)
        
        board = [[Cell(CellType.EMPTY, set()) for _ in range(5)] for _ in range(5)]
        
        # Camino con salidas no coincidentes
        board[0][0] = Cell(CellType.INICIO, {Direction.E})
        board[0][1] = Cell(CellType.PASILLO, {Direction.E})  # No tiene O
        board[0][2] = Cell(CellType.SALIDA, {Direction.O})
        
        assert generator.check_connectivity(board, (0, 0), (0, 2)) == False
    
    def test_check_connectivity_out_of_bounds(self):
        """Test que no se sale de los límites del tablero."""
        generator = BoardGenerator(3)
        
        board = [[Cell(CellType.EMPTY, set()) for _ in range(3)] for _ in range(3)]
        
        # Celda en el borde con salida hacia afuera
        board[0][0] = Cell(CellType.INICIO, {Direction.N})  # Intenta ir fuera
        board[2][2] = Cell(CellType.SALIDA, set())
        
        assert generator.check_connectivity(board, (0, 0), (2, 2)) == False
    
    def test_check_connectivity_start_equals_end(self):
        """Test conectividad cuando inicio = fin."""
        generator = BoardGenerator(5)
        
        board = [[Cell(CellType.EMPTY, set()) for _ in range(5)] for _ in range(5)]
        board[0][0] = Cell(CellType.INICIO, set())
        
        assert generator.check_connectivity(board, (0, 0), (0, 0)) == True
    
    def test_check_connectivity_complex_path(self):
        """Test conectividad con camino complejo."""
        generator = BoardGenerator(5)
        
        board = [[Cell(CellType.EMPTY, set()) for _ in range(5)] for _ in range(5)]
        
        # Camino en L: (0,0) -> (1,0) -> (1,1)
        board[0][0] = Cell(CellType.INICIO, {Direction.S})
        board[1][0] = Cell(CellType.PASILLO, {Direction.N, Direction.E})
        board[1][1] = Cell(CellType.SALIDA, {Direction.O})
        
        assert generator.check_connectivity(board, (0, 0), (1, 1)) == True
    
    def test_check_connectivity_all_directions(self):
        """Test conectividad usando todas las direcciones."""
        generator = BoardGenerator(3)
        
        board = [[Cell(CellType.EMPTY, set()) for _ in range(3)] for _ in range(3)]
        
        # Centro conectado en todas direcciones
        board[1][1] = Cell(CellType.PASILLO, {Direction.N, Direction.S, Direction.E, Direction.O})
        board[0][1] = Cell(CellType.INICIO, {Direction.S})
        board[2][1] = Cell(CellType.SALIDA, {Direction.N})
        
        assert generator.check_connectivity(board, (0, 1), (2, 1)) == True
    
    def test_generate_exit_position_returns_valid_coords(self):
        """Test que generate_exit_position retorna coordenadas válidas."""
        generator = BoardGenerator(21)
        center = 10
        
        for _ in range(10):  # Probar varias veces
            exit_pos = generator.generate_exit_position(center)
            assert isinstance(exit_pos, tuple)
            assert len(exit_pos) == 2
            assert 0 <= exit_pos[0] < 21
            assert 0 <= exit_pos[1] < 21
    
    def test_generate_exit_position_away_from_center(self):
        """Test que la salida está alejada del centro."""
        generator = BoardGenerator(21)
        center = 10
        
        exit_pos = generator.generate_exit_position(center)
        distance = abs(exit_pos[0] - center) + abs(exit_pos[1] - center)
        
        # Debería estar al menos a cierta distancia
        assert distance >= 3
    
    def test_calculate_main_path_direct(self):
        """Test cálculo de camino directo."""
        generator = BoardGenerator(11)
        
        path = generator.calculate_main_path((0, 0), (2, 2))
        
        assert isinstance(path, list)
        assert len(path) >= 2
        assert path[0] == (0, 0)
        assert path[-1] == (2, 2)
    
    def test_calculate_main_path_straight_line(self):
        """Test camino en línea recta."""
        generator = BoardGenerator(11)
        
        path = generator.calculate_main_path((0, 0), (0, 5))
        
        assert path[0] == (0, 0)
        assert path[-1] == (0, 5)
        assert len(path) == 6  # 0 a 5 = 6 pasos
    
    def test_calculate_main_path_same_point(self):
        """Test camino cuando inicio = fin."""
        generator = BoardGenerator(11)
        
        path = generator.calculate_main_path((5, 5), (5, 5))
        
        assert path == [(5, 5)]
    
    def test_calculate_main_path_only_adjacents(self):
        """Test que el camino solo usa movimientos adyacentes."""
        generator = BoardGenerator(11)
        
        path = generator.calculate_main_path((0, 0), (3, 3))
        
        # Verificar que cada paso es adyacente al anterior
        for i in range(len(path) - 1):
            row_diff = abs(path[i+1][0] - path[i][0])
            col_diff = abs(path[i+1][1] - path[i][1])
            
            # Solo puede moverse 1 casilla en una dirección
            assert (row_diff == 1 and col_diff == 0) or (row_diff == 0 and col_diff == 1)
    
    def test_different_sizes(self):
        """Test generador con diferentes tamaños."""
        for size in [7, 11, 15, 21]:
            generator = BoardGenerator(size)
            assert generator.size == size
    
    def test_generate_exit_position_small_board(self):
        """Test generar salida en tablero pequeño."""
        generator = BoardGenerator(11)
        center = 5
        
        exit_pos = generator.generate_exit_position(center)
        
        assert 0 <= exit_pos[0] < 11
        assert 0 <= exit_pos[1] < 11
