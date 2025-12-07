# Dungeon Explorer 2D

Un juego de exploración de mazmorras en 2D construido con Pygame.

## Características

- **Generación procedural de mazmorras**: Las mazmorras se generan dinámicamente a medida que exploras
- **Sprite de guerrero animado**: Personaje con animación de caminar suave
- **Textura de piedra**: Paredes con textura procedural de piedra
- **Scroll suave**: La cámara se centra instantáneamente y el personaje se anima suavemente
- **Tipos de celdas**: Inicio, pasillos, habitaciones y paredes
- **Fuente decorativa**: En la celda de inicio

## Requisitos

- Python 3.13+
- Pygame 2.6.1+

## Instalación

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar entorno virtual
source .venv/bin/activate  # En macOS/Linux
# o
.venv\Scripts\activate  # En Windows

# Instalar dependencias
pip install pygame
```

**Nota**: El entorno virtual (`.venv`) no está incluido en el repositorio. Cada usuario debe crear su propio entorno virtual localmente siguiendo los pasos anteriores.

## Cómo jugar

```bash
python dungeon.py
```

### Controles

- **W** o **↑**: Moverse al norte
- **S** o **↓**: Moverse al sur
- **D** o **→**: Moverse al este
- **A** o **←**: Moverse al oeste

## Estructura del proyecto

- `dungeon.py`: Archivo principal del juego
- `.gitignore`: Archivos ignorados por git
- `README.md`: Este archivo

## Características técnicas

- Sistema de scroll instantáneo + animación suave del jugador
- Generación determinista de texturas (misma celda = misma textura)
- Animación de caminar solo cuando el personaje se mueve
- Paleta de colores configurable para el sprite del guerrero
- Habitaciones amplias con grandes áreas explorables
- Puertas con apertura visual entre celdas conectadas

## Licencia

MIT
