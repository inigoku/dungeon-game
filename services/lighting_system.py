"""Sistema de iluminación para el dungeon."""
from models.cell import CellType
from config import (
    BASE_BRIGHTNESS_ENTRANCE,
    BASE_BRIGHTNESS_EXIT,
    BASE_BRIGHTNESS_LINES_ENTRANCE,
    BASE_BRIGHTNESS_LINES_EXIT,
    MAX_TORCH_BRIGHTNESS,
    TORCH_BRIGHTNESS_PER_UNIT,
    BLOOD_DARKENING_FACTOR
)


class LightingSystem:
    """Maneja todos los cálculos de iluminación del dungeon."""
    
    def __init__(self):
        self.lines_darkening_enabled = True
    
    def calculate_brightness(self, base_brightness, torch_count):
        """Calcula el brillo total combinando base y antorchas."""
        torch_brightness = min(MAX_TORCH_BRIGHTNESS, torch_count * TORCH_BRIGHTNESS_PER_UNIT)
        brightness = max(0, base_brightness + torch_brightness)
        return brightness
    
    def calculate_base_brightness(self, distance_from_start, total_distance):
        """Calcula el brillo base según la distancia desde la entrada."""
        if total_distance > 0:
            progress = distance_from_start / total_distance
        else:
            progress = 0.5
        
        # Base de luz: 20 en entrada, 0 en salida
        base_brightness = int(BASE_BRIGHTNESS_ENTRANCE * (1.0 - progress))
        return base_brightness
    
    def calculate_brightness_factor(self, brightness):
        """Convierte brillo (0-255) a factor (0.0-1.0)."""
        return brightness / 255.0
    
    def calculate_lines_brightness_factor(self, cell_type, distance_from_start=0, total_distance=1):
        """Calcula el factor de brillo para las líneas."""
        if cell_type in [CellType.PASILLO, CellType.HABITACION, CellType.SALIDA]:
            if total_distance > 0:
                progress = distance_from_start / total_distance
            else:
                progress = 0.5
            
            # Brillo base para líneas: 50 en entrada, 0 en salida
            base_brightness = int(BASE_BRIGHTNESS_LINES_ENTRANCE * (1.0 - progress))
            
            if self.lines_darkening_enabled:
                lines_brightness_factor = base_brightness / 255.0
            else:
                lines_brightness_factor = 1.0  # Sin oscurecimiento
        
        elif cell_type == CellType.INICIO:
            if self.lines_darkening_enabled:
                base_brightness = BASE_BRIGHTNESS_LINES_ENTRANCE
                lines_brightness_factor = base_brightness / 255.0
            else:
                lines_brightness_factor = 1.0  # Sin oscurecimiento
        else:
            lines_brightness_factor = 1.0
        
        return lines_brightness_factor
    
    def apply_blood_darkening(self, brightness_factor):
        """Aplica el oscurecimiento del 50% a la sangre."""
        return 1.0 - BLOOD_DARKENING_FACTOR * (1.0 - brightness_factor)
    
    def toggle_lines_darkening(self):
        """Toggle del oscurecimiento de líneas."""
        self.lines_darkening_enabled = not self.lines_darkening_enabled
        status = "activado" if self.lines_darkening_enabled else "desactivado"
        print(f"Oscurecimiento de líneas: {status}")
        return self.lines_darkening_enabled
