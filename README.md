# Dungeon Explorer 2D

Un juego de exploración de mazmorras en 2D construido con Pygame, con sistema de audio dinámico, niebla de guerra y efectos atmosféricos.

**🎮 [Juega ahora en tu navegador](https://inigoku.github.io/dungeon-game/)** (sin instalación requerida)

## Características

### Exploración
- **Generación procedural de mazmorras**: Tablero de 101x101 celdas generado dinámicamente
- **Niebla de guerra**: Solo las áreas visitadas permanecen visibles
- **Sistema de zoom**: 5 niveles de zoom (7x7, 11x11, 21x21, 51x51, 101x101)
- **Camino principal**: Ruta garantizada desde el inicio hasta la salida
- **Scroll suave**: Cámara con interpolación fluida que sigue al jugador

### Gráficos y Animaciones
- **Sprite de guerrero animado**: Personaje con animación de caminar, brazos, piernas y armas
- **Animación de inicio**: Secuencia de caída e introducción del personaje
- **Pantalla de título**: Imagen de bienvenida (titulo.png)
- **Textura de piedra procedural**: Paredes con variación visual
- **Antorchas animadas**: Iluminación dinámica con probabilidad progresiva (10%-40%)
- **Escalera espiral**: Visualización de la salida
- **Fuente decorativa**: En la celda de inicio

### Sistema de Audio
- **Música dinámica por distancia**:
  - `intro.mp3`: Audio de introducción con subtítulos
  - `adagio.mp3`: Música principal que disminuye con la distancia del inicio (5 celdas)
  - `cthulhu.mp3`: Música que aumenta al acercarse a la salida, máximo volumen en la celda de salida
  - Sistema de fade in/out al saltar la intro
- **Efectos de sonido**:
  - Pasos alternados (paso1.mp3, paso2.mp3) al caminar
  - Sonidos ambientales aleatorios: gotas de agua (gota.mp3, dos-gotas.mp3) y murciélagos (murcielago.mp3)
- **Subtítulos**: Sistema de subtítulos para el audio de introducción

### Controles e Interfaz
- **Sistema de zoom**: Teclas Z (acercar) y X (alejar)
- **Confirmación de salida**: Diálogo con ESC (S=Sí, N=No)
- **Modo debug**: F3 para información de navegación
- **Iluminación progresiva**: Las antorchas aumentan en densidad hacia la salida

## Jugar en el Navegador

El juego está disponible para jugar directamente en tu navegador sin necesidad de instalación:

**🎮 [https://inigoku.github.io/dungeon-game/](https://inigoku.github.io/dungeon-game/)**

La versión web utiliza Pygbag para ejecutar Pygame en el navegador mediante WebAssembly.

## Instalación Local

### Requisitos

- Python 3.11+
- Pygame 2.6.1+

### Instalación

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

1. **Pantalla de título**: Presiona cualquier tecla para comenzar
2. **Introducción**: Durante el audio intro, presiona cualquier tecla para saltarlo
3. **Exploración**: Navega por la mazmorra hasta encontrar la salida (escalera espiral)
4. **Objetivo**: Alcanza la celda de salida donde la música sonará al máximo volumen

### Controles

#### Movimiento
- **W** o **↑**: Moverse al norte
- **S** o **↓**: Moverse al sur
- **D** o **→**: Moverse al este
- **A** o **←**: Moverse al oeste

#### Cámara
- **Z**: Acercar zoom (5 niveles disponibles)
- **X**: Alejar zoom

#### Sistema
- **F3**: Toggle modo debug (muestra información de navegación)
- **ESC**: Salir del juego (con confirmación)

## Estructura del proyecto

```
dungeon/
├── dungeon.py          # Archivo principal del juego
├── titulo.png          # Imagen de la pantalla de título
├── sound/              # Carpeta de archivos de audio
│   ├── intro.mp3       # Audio de introducción
│   ├── adagio.mp3      # Música principal (cerca del inicio)
│   ├── cthulhu.mp3     # Música de tensión (cerca de la salida)
│   ├── gota.mp3        # Efecto de gota de agua
│   ├── dos-gotas.mp3   # Efecto de dos gotas
│   ├── murcielago.mp3  # Efecto de murciélago
│   ├── paso1.mp3       # Sonido de paso 1
│   └── paso2.mp3       # Sonido de paso 2
├── .gitignore
└── README.md
```

## Características técnicas

### Motor de Juego
- Tablero de 101x101 celdas con generación procedural
- Sistema de cámara con interpolación suave (factor 0.03)
- Animación de movimiento del jugador (450ms de duración)
- Ventana fija de 630x630 píxeles

### Sistema de Audio
- Fade in/out de 1 segundo entre pistas
- Volumen dinámico basado en distancia euclidiana
- Mezcla de música y efectos de sonido simultáneos
- Efectos ambientales con intervalos aleatorios (3-20 segundos)

### Renderizado
- Texturas procedurales con semillas deterministas
- Iluminación con gradiente radial en antorchas
- Sistema de niebla de guerra con celdas visitadas
- Animación de llamas con variación sinusoidal

### Optimizaciones
- Solo se renderizan celdas visibles en el viewport actual
- Caché de texturas por celda
- Actualización selectiva de volumen de música

## Licencia

MIT
