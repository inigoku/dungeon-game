# Dungeon Explorer 2D

[![Tests](https://github.com/inigoku/dungeon-game/actions/workflows/tests.yml/badge.svg)](https://github.com/inigoku/dungeon-game/actions/workflows/tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Un juego de exploración de mazmorras en 2D construido con Pygame, con sistema de audio dinámico, niebla de guerra, efectos atmosféricos y un innovador sistema de pensamientos narrativos.

**🎮 [Juega ahora en tu navegador](https://inigoku.github.io/dungeon-game/)** (sin instalación requerida)

## 📋 Tabla de Contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Instalación](#instalación)
- [Testing](#testing)
- [Desarrollo](#desarrollo)
- [Documentación](#documentación)

## Características

### Exploración
- **Generación procedural de mazmorras**: Tablero de 101x101 celdas generado dinámicamente
- **Verificación de conectividad**: Sistema BFS que garantiza un camino desde el inicio hasta la salida (hasta 10 intentos de regeneración)
- **Posicionamiento inteligente de la salida**: Ubicada entre 75%-100% de la distancia desde el centro hasta el borde
- **Niebla de guerra**: Solo las áreas visitadas permanecen visibles
- **Sistema de zoom**: 5 niveles de zoom (7x7, 11x11, 21x21, 51x51, 101x101)
- **Scroll suave**: Cámara con interpolación fluida que sigue al jugador
- **Manchas de sangre**: Indicadores visuales cerca de la salida (distancia 1-10), con probabilidad creciente (30% a 100%)

### Gráficos y Animaciones
- **Sprite de guerrero animado**: Personaje con animación de caminar, brazos, piernas y armas
- **Animación de inicio**: Secuencia de caída e introducción del personaje
- **Pantalla de título**: Imagen de bienvenida (titulo.png)
- **Textura de piedra procedural**: Paredes con variación visual
- **Antorchas animadas**: Iluminación dinámica con probabilidad progresiva (10%-40%)
- **Escalera espiral**: Visualización de la salida
- **Fuente decorativa**: En la celda de inicio
- **Manchas de sangre orgánicas**: 2-5 manchas irregulares por celda con tonos oscuros de rojo
- **Imagen final de Cthulhu**: Al alcanzar la salida, aparece una imagen de Cthulhu que bloquea el juego

### Sistema de Pensamientos
- **Arquitectura de pensamientos**: Sistema de audio y subtítulos que se reproduce en paralelo con la música de fondo
- **Subtítulos secuenciales**: Múltiples líneas de texto que aparecen consecutivamente durante el audio
- **Pensamientos implementados**:
  - **Pensamiento de introducción**: 4 subtítulos con tutorial del juego (34 segundos)
  - **Pensamiento de antorchas**: Reacción al descubrir la primera antorcha (7.5 segundos)
  - **Pensamiento de sangre**: Reacción de horror al ver las primeras manchas de sangre (10 segundos)
- **Sistema de interrupciones**: Los nuevos pensamientos detienen los anteriores
- **Detección contextual**: Los pensamientos solo se activan cuando el jugador observa los elementos correspondientes
- **Activación única**: Cada pensamiento solo se reproduce una vez por partida

### Sistema de Audio
- **Música dinámica por distancia**:
  - `adagio.ogg`: Música principal desde el inicio del juego
  - `cthulhu.ogg`: Música que aumenta al acercarse a la salida, máximo volumen en la celda de salida
  - Sistema de fade in/out al saltar la intro
- **Audio de pensamientos** (formato OGG Vorbis):
  - `intro.ogg`: Pensamiento tutorial al entrar al calabozo (523 KB, 34.24s)
  - `antorchas.ogg`: Reacción al descubrir antorchas (104 KB, 7.49s)
  - `sangre.ogg`: Reacción de horror a las manchas de sangre (166 KB, 9.92s)
- **Efectos de sonido**:
  - Pasos alternados (paso1.ogg, paso2.ogg) al caminar
  - Sonidos ambientales ponderados: 40% gota, 40% dos-gotas, 20% murciélago
- **Subtítulos avanzados**: 
  - Múltiples líneas secuenciales con duración individual
  - División automática en varias líneas si el texto es largo
  - Centrado horizontal con fondo semitransparente
  - Subtítulo final de Cthulhu: "PH'NGLUI MGLW'NAFH CTHULHU R'LYEH WGAH'NAGL FHTAGN"

### Controles e Interfaz
- **Sistema de zoom**: Teclas Z (acercar) y X (alejar)
- **Confirmación de salida**: Diálogo con ESC (S=Sí, N=No)
- **Modo debug**: F2 para auto-revelación, F3 para información de navegación, F4 para mostrar el camino completo
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
2. **Introducción**: Durante el pensamiento de introducción, lee los tutoriales en pantalla
3. **Exploración**: Navega por la mazmorra buscando la salida (escalera espiral)
4. **Descubrimientos**: Presta atención a los pensamientos del personaje al descubrir antorchas y señales perturbadoras
5. **Objetivo**: Alcanza la celda de salida donde se revelará el destino final

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
- **F2**: Toggle auto-revelación (activar/desactivar revelación automática de celdas adyacentes)
- **F3**: Toggle modo debug (muestra información de navegación)
- **F4**: Toggle mostrar camino completo (resalta todas las celdas del camino principal hasta la salida)
- **ESC**: Salir del juego (con confirmación)

## Estructura del proyecto

```
dungeon/
├── dungeon.py          # Archivo principal del juego (2311 líneas)
├── titulo.png          # Imagen de la pantalla de título
├── cthlulhu.png        # Imagen final de Cthulhu
├── sound/              # Carpeta de archivos de audio (formato OGG)
│   ├── intro.ogg       # Pensamiento tutorial (523 KB, 34.24s)
│   ├── antorchas.ogg   # Pensamiento de antorchas (104 KB, 7.49s)
│   ├── sangre.ogg      # Pensamiento de sangre (166 KB, 9.92s)
│   ├── adagio.ogg      # Música principal
│   ├── cthulhu.ogg     # Música de tensión final
│   ├── gota.ogg        # Efecto de gota de agua
│   ├── dos-gotas.ogg   # Efecto de dos gotas
│   ├── murcielago.ogg  # Efecto de murciélago
│   ├── paso1.ogg       # Sonido de paso 1
│   └── paso2.ogg       # Sonido de paso 2
├── .gitignore
└── README.md
```

## Características técnicas

### Motor de Juego
- Tablero de 101x101 celdas con generación procedural
- Sistema de verificación de conectividad BFS con hasta 10 intentos de regeneración
- Posicionamiento de salida a 75%-100% de distancia del centro al borde
- Sistema de cámara con interpolación suave (factor 0.03)
- Animación de movimiento del jugador (450ms de duración)
- Ventana fija de 630x630 píxeles

### Sistema de Pensamientos
- Arquitectura de estado para gestión de pensamientos activos
- Reproducción paralela de audio (pensamientos + música de fondo)
- Subtítulos secuenciales con duración individual
- División automática de texto largo en múltiples líneas
- Sistema de banderas para activación única (intro_thought_triggered, torch_thought_triggered, blood_thought_triggered)
- Detección contextual basada en el estado del juego:
  - **Antorchas**: Verifica count_torches() > 0
  - **Sangre**: Usa has_blood_stains() con semilla determinista (board_row * 100000 + board_col)
- Capacidad de interrupción (nuevos pensamientos detienen los anteriores)

### Sistema de Audio
- **Formato**: OGG Vorbis (compatibilidad web con Pygbag)
- **Conversión**: FFmpeg con codec libvorbis, calidad nivel 5
- Fade in/out de 1 segundo entre pistas
- Volumen dinámico basado en distancia euclidiana
- Mezcla de música y efectos de sonido simultáneos
- Efectos ambientales ponderados (80% gotas de agua, 20% murciélagos)
- Canal independiente para pensamientos (no interfiere con música)

### Renderizado
- Texturas procedurales con semillas deterministas
- Iluminación con gradiente radial en antorchas
- Sistema de niebla de guerra con celdas visitadas
- Animación de llamas con variación sinusoidal
- **Manchas de sangre**: 2-5 manchas irregulares por celda, colores (80,0,0), (100,10,10), (70,5,5)
- **Probabilidad de sangre**: Sistema seeded random, 30% a distancia 10, 100% a distancia 1
- **Imagen final escalada**: Cthulhu redimensionado manteniendo aspecto, reservando 120px para subtítulos

### Optimizaciones
- Solo se renderizan celdas visibles en el viewport actual
- Caché de texturas por celda

## 🏗️ Arquitectura

El proyecto ha sido refactorizado a una **arquitectura modular** con 8 módulos independientes:

### Módulos Core
- **models/cell.py** - Estructuras de datos (Cell, CellType, Direction)
- **config.py** - Constantes centralizadas del juego

### Services
- **services/lighting_system.py** - Sistema de iluminación y gradientes
- **services/board_generator.py** - Generación procedural y pathfinding
- **services/audio_manager.py** - Gestión de música, efectos y pensamientos

### Rendering
- **rendering/decorations.py** - Antorchas, sangre, fuente, escaleras
- **rendering/effects.py** - Líneas quebradas, texturas de piedra
- **rendering/cell_renderer.py** - Helpers de renderizado de celdas

### Características de la Arquitectura
- ✅ **Separación de responsabilidades** - Cada módulo tiene un propósito claro
- ✅ **Testabilidad** - Módulos independientes fáciles de probar
- ✅ **Backward compatibility** - Sistema dual con fallback automático
- ✅ **Zero breaking changes** - Migración sin interrupciones

Ver [ARCHITECTURE.md](ARCHITECTURE.md) para más detalles.

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests básicos (45 tests, 100% passing)
pytest tests/test_config.py tests/test_cell.py -v

# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Estado Actual

- **Total de tests**: 210
- **Pasando**: 63 (30%)
- **Módulos con 100%**: config.py, models/cell.py

Ver [TESTING_STATUS.md](TESTING_STATUS.md) para más detalles.

## 📦 Instalación

### Prerequisitos
- Python 3.11+
- pip

### Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/inigoku/dungeon-game.git
cd dungeon-game

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install pygame

# Ejecutar juego
python main.py
# o
python dungeon.py
```

### Instalación para Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-cov pytest-mock

# Ejecutar tests
pytest tests/ -v
```

## 🚀 Desarrollo

### Estructura del Proyecto

```
dungeon/
├── models/
│   ├── __init__.py
│   └── cell.py          # Cell, CellType, Direction
├── services/
│   ├── __init__.py
│   ├── lighting_system.py
│   ├── board_generator.py
│   └── audio_manager.py
├── rendering/
│   ├── __init__.py
│   ├── decorations.py
│   ├── effects.py
│   └── cell_renderer.py
├── tests/
│   ├── test_config.py
│   ├── test_cell.py
│   └── ...
├── images/
│   ├── titulo.png
│   ├── losa.png
│   └── cthlulhu.png
├── sound/
│   ├── intro.ogg
│   ├── adagio.ogg
│   └── ...
├── config.py            # Constantes
├── dungeon.py           # Código principal (legacy compatible)
├── main.py              # Punto de entrada modular
└── README.md
```

### Roadmap

Ver [ROADMAP.md](ROADMAP.md) para el plan de desarrollo futuro.

Próximas prioridades:
1. ✅ Completar suite de tests (objetivo: 100% passing)
2. ⏳ Configurar CI/CD con GitHub Actions
3. ⏳ Agregar type hints completos
4. ⏳ Generar documentación con Sphinx

## 📚 Documentación

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Documentación completa de la arquitectura modular
- **[TESTING_STATUS.md](TESTING_STATUS.md)** - Estado y roadmap de testing
- **[ROADMAP.md](ROADMAP.md)** - Plan de desarrollo futuro
- **[tests/README.md](tests/README.md)** - Guía de tests

## 🎮 Controles
- Actualización selectiva de volumen de música
- Sistema de banderas para evitar reproducción repetida de pensamientos

### Tecnología Web
- **Pygbag 0.9.2**: Conversión de Pygame a WebAssembly
- **Deployment**: GitHub Pages con GitHub Actions
- **Compatibilidad**: Navegadores modernos con soporte WebAssembly
- **Audio web**: OGG Vorbis para máxima compatibilidad

## Licencia

MIT
