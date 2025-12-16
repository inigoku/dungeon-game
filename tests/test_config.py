"""Tests unitarios para config.py"""
import pytest
import config


class TestBoardConfiguration:
    """Tests para configuración del tablero."""
    
    def test_default_board_size(self):
        """Verificar tamaño de tablero por defecto."""
        assert config.DEFAULT_BOARD_SIZE == 101
        assert config.DEFAULT_BOARD_SIZE % 2 == 1  # Debe ser impar
    
    def test_default_view_size(self):
        """Verificar tamaño de vista por defecto."""
        assert config.DEFAULT_VIEW_SIZE == 7
        assert config.DEFAULT_VIEW_SIZE % 2 == 1  # Debe ser impar
    
    def test_default_cell_size(self):
        """Verificar tamaño de celda por defecto."""
        assert config.DEFAULT_CELL_SIZE == 90
        assert config.DEFAULT_CELL_SIZE > 0


class TestZoomLevels:
    """Tests para niveles de zoom."""
    
    def test_zoom_levels_count(self):
        """Verificar que hay 5 niveles de zoom."""
        assert len(config.ZOOM_LEVELS) == 5
    
    def test_zoom_levels_values(self):
        """Verificar valores de zoom."""
        assert config.ZOOM_LEVELS == [7, 11, 21, 51, 101]
    
    def test_zoom_levels_all_odd(self):
        """Verificar que todos los niveles son impares."""
        assert all(level % 2 == 1 for level in config.ZOOM_LEVELS)
    
    def test_zoom_levels_ascending(self):
        """Verificar que los niveles están en orden ascendente."""
        assert config.ZOOM_LEVELS == sorted(config.ZOOM_LEVELS)
    
    def test_default_zoom_index(self):
        """Verificar índice de zoom por defecto."""
        assert config.DEFAULT_ZOOM_INDEX == 0
        assert config.DEFAULT_ZOOM_INDEX < len(config.ZOOM_LEVELS)
    
    def test_zoom_includes_board_size(self):
        """Verificar que el zoom máximo es el tamaño del tablero."""
        assert config.DEFAULT_BOARD_SIZE in config.ZOOM_LEVELS
        assert config.ZOOM_LEVELS[-1] == config.DEFAULT_BOARD_SIZE


class TestRendering:
    """Tests para configuración de renderizado."""
    
    def test_fixed_window_size(self):
        """Verificar tamaño de ventana fijo."""
        expected_size = config.DEFAULT_VIEW_SIZE * config.DEFAULT_CELL_SIZE
        assert config.FIXED_WINDOW_SIZE == expected_size
        assert config.FIXED_WINDOW_SIZE == 630  # 7 * 90
    
    def test_window_size_positive(self):
        """Verificar que el tamaño de ventana es positivo."""
        assert config.FIXED_WINDOW_SIZE > 0


class TestColors:
    """Tests para constantes de color."""
    
    def test_color_black(self):
        """Verificar color negro."""
        assert config.COLOR_BLACK == (0, 0, 0)
        assert len(config.COLOR_BLACK) == 3
    
    def test_color_white(self):
        """Verificar color blanco."""
        assert config.COLOR_WHITE == (255, 255, 255)
        assert len(config.COLOR_WHITE) == 3
    
    def test_color_gray_dark(self):
        """Verificar gris oscuro."""
        assert config.COLOR_GRAY_DARK == (80, 80, 80)
        assert len(config.COLOR_GRAY_DARK) == 3
    
    def test_color_gray_light(self):
        """Verificar gris claro."""
        assert config.COLOR_GRAY_LIGHT == (150, 150, 150)
        assert len(config.COLOR_GRAY_LIGHT) == 3
    
    def test_color_rgb_ranges(self):
        """Verificar que todos los valores RGB están en rango válido."""
        colors = [
            config.COLOR_BLACK,
            config.COLOR_WHITE,
            config.COLOR_GRAY_DARK,
            config.COLOR_GRAY_LIGHT
        ]
        for color in colors:
            for component in color:
                assert 0 <= component <= 255
    
    def test_gray_hierarchy(self):
        """Verificar jerarquía de grises."""
        # Negro < Gris oscuro < Gris claro < Blanco
        assert config.COLOR_BLACK[0] < config.COLOR_GRAY_DARK[0]
        assert config.COLOR_GRAY_DARK[0] < config.COLOR_GRAY_LIGHT[0]
        assert config.COLOR_GRAY_LIGHT[0] < config.COLOR_WHITE[0]


class TestLighting:
    """Tests para configuración de iluminación."""
    
    def test_base_brightness_entrance(self):
        """Verificar brillo base en entrada."""
        assert config.BASE_BRIGHTNESS_ENTRANCE == 20
        assert config.BASE_BRIGHTNESS_ENTRANCE >= 0
    
    def test_base_brightness_exit(self):
        """Verificar brillo base en salida."""
        assert config.BASE_BRIGHTNESS_EXIT == 0
    
    def test_base_brightness_lines_entrance(self):
        """Verificar brillo de líneas en entrada."""
        assert config.BASE_BRIGHTNESS_LINES_ENTRANCE == 50
        assert config.BASE_BRIGHTNESS_LINES_ENTRANCE >= 0
    
    def test_base_brightness_lines_exit(self):
        """Verificar brillo de líneas en salida."""
        assert config.BASE_BRIGHTNESS_LINES_EXIT == 0
    
    def test_max_torch_brightness(self):
        """Verificar brillo máximo de antorchas."""
        assert config.MAX_TORCH_BRIGHTNESS == 130
        assert config.MAX_TORCH_BRIGHTNESS <= 255
    
    def test_torch_brightness_per_unit(self):
        """Verificar brillo por antorcha."""
        assert config.TORCH_BRIGHTNESS_PER_UNIT == 31
        assert config.TORCH_BRIGHTNESS_PER_UNIT > 0
    
    def test_brightness_hierarchy(self):
        """Verificar jerarquía de brillo."""
        # Entrada debe ser más brillante que salida
        assert config.BASE_BRIGHTNESS_ENTRANCE > config.BASE_BRIGHTNESS_EXIT
        assert config.BASE_BRIGHTNESS_LINES_ENTRANCE > config.BASE_BRIGHTNESS_LINES_EXIT
    
    def test_torch_calculations(self):
        """Verificar que los cálculos de antorchas son razonables."""
        # Con 4 antorchas: 4 * 31 = 124 < 130 (max)
        brightness_4_torches = 4 * config.TORCH_BRIGHTNESS_PER_UNIT
        assert brightness_4_torches < config.MAX_TORCH_BRIGHTNESS
        
        # Con 5 antorchas: 5 * 31 = 155 > 130 (debe limitarse)
        brightness_5_torches = 5 * config.TORCH_BRIGHTNESS_PER_UNIT
        assert brightness_5_torches > config.MAX_TORCH_BRIGHTNESS


class TestBloodAndEffects:
    """Tests para efectos visuales."""
    
    def test_blood_darkening_factor(self):
        """Verificar factor de oscurecimiento de sangre."""
        assert config.BLOOD_DARKENING_FACTOR == 0.5
        assert 0.0 <= config.BLOOD_DARKENING_FACTOR <= 1.0
    
    def test_blood_darkening_percentage(self):
        """Verificar que el factor corresponde al 50%."""
        assert config.BLOOD_DARKENING_FACTOR * 100 == 50


class TestGeneration:
    """Tests para configuración de generación."""
    
    def test_max_generation_attempts(self):
        """Verificar intentos máximos de generación."""
        assert config.MAX_GENERATION_ATTEMPTS == 10
        assert config.MAX_GENERATION_ATTEMPTS > 0
    
    def test_generation_attempts_reasonable(self):
        """Verificar que los intentos son razonables."""
        assert 1 <= config.MAX_GENERATION_ATTEMPTS <= 100


class TestConstantsImmutability:
    """Tests para verificar que las constantes no cambian."""
    
    def test_constants_exist(self):
        """Verificar que todas las constantes esperadas existen."""
        required_constants = [
            'DEFAULT_BOARD_SIZE',
            'DEFAULT_VIEW_SIZE',
            'DEFAULT_CELL_SIZE',
            'ZOOM_LEVELS',
            'DEFAULT_ZOOM_INDEX',
            'FIXED_WINDOW_SIZE',
            'COLOR_BLACK',
            'COLOR_WHITE',
            'BASE_BRIGHTNESS_ENTRANCE',
            'MAX_TORCH_BRIGHTNESS',
            'BLOOD_DARKENING_FACTOR',
            'MAX_GENERATION_ATTEMPTS'
        ]
        for const in required_constants:
            assert hasattr(config, const), f"Falta constante: {const}"
    
    def test_types(self):
        """Verificar tipos de datos de constantes."""
        assert isinstance(config.DEFAULT_BOARD_SIZE, int)
        assert isinstance(config.DEFAULT_VIEW_SIZE, int)
        assert isinstance(config.DEFAULT_CELL_SIZE, int)
        assert isinstance(config.ZOOM_LEVELS, list)
        assert isinstance(config.DEFAULT_ZOOM_INDEX, int)
        assert isinstance(config.FIXED_WINDOW_SIZE, int)
        assert isinstance(config.COLOR_BLACK, tuple)
        assert isinstance(config.BLOOD_DARKENING_FACTOR, float)
        assert isinstance(config.MAX_GENERATION_ATTEMPTS, int)
