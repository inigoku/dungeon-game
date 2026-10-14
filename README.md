# Dungeon Explorer 2D

[![Tests](https://github.com/inigoku/dungeon-game/actions/workflows/tests.yml/badge.svg)](https://github.com/inigoku/dungeon-game/actions/workflows/tests.yml)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Un juego de exploración de mazmorras en 2D escrito en **TypeScript** y dibujado sobre **Canvas 2D**, con audio dinámico (Web Audio), niebla de guerra, un barranco con puentes, monstruos y un sistema de pensamientos narrativos. Se ejecuta directamente en el navegador, sin instalación para quien juega.

**🎮 [Juega ahora en tu navegador](https://inigoku.github.io/dungeon-game/)**

> El juego nació como un proyecto de Pygame (Python). Esta versión es una conversión completa a TypeScript que conserva la lógica, la generación del mapa y el aspecto visual; la versión Python sigue disponible en el historial de git.

## Características

### Exploración
- **Generación procedural**: tablero de 101×101 celdas creado sobre la marcha.
- **Camino garantizado**: el camino principal (con BFS de verificación, hasta 10 intentos) lleva del inicio a la salida.
- **Barranco infranqueable**: una fila o columna entera divide el mapa; la salida está al otro lado y solo se llega cruzando un **puente volante** (hay dos, uno en el camino principal y otro opcional). Intentar cruzar el vacío es mortal.
- **Niebla de guerra**: solo se ven las celdas visitadas; el barranco y los puentes aparecen al acercarse.
- **Movimiento automático**: haz clic o toca una celda visible y el personaje irá hasta ella por el camino más corto (se detiene al ser herido o al empezar un pensamiento).
- **Zoom** de 8 niveles (de 3×3 hasta el mapa completo) y **cámara suave**.
- **Antorchas** cada vez menos frecuentes hacia la salida, **manchas de sangre** que anuncian el final y una fuente en la celda de inicio.

### Narrativa y secuencia final
- **Pensamientos**: audio + subtítulos + imágenes sincronizados (introducción, antorchas, sangre, la salida, el poder de la espada). Cada uno se activa una sola vez y puede cancelarse con cualquier tecla o toque.
- Al llegar a la salida las antorchas parpadean y se apagan, el mapa se aleja y aparecen los **Profundos**.
- Si vuelves al inicio tras ver la salida, obtienes el **poder de la espada**: los monstruos huyen y mueren a tu paso.
- **Salud**, daño con invulnerabilidad temporal, pantalla de **Game Over** con fundido y botón de reinicio.

### Audio
- Música dinámica: `adagio` cerca del inicio, `cthulhu` al acercarse a la salida, `alataque` con la espada y viento al acercarse al barranco.
- Pasos alternados, gotas y murciélagos aleatorios (con animación), gruñidos y pisadas húmedas de los monstruos.

## Controles

| Tecla | Acción |
| --- | --- |
| **W A S D** / **↑ ← ↓ →** | Moverse |
| **Clic / toque** en una celda visible | Ir andando hasta ella si hay camino; otro clic cambia el destino (o detiene el trayecto si no hay camino) y cualquier tecla lo cancela |
| **Arrastrar** con el dedo o el ratón | Desplazar la vista para ver zonas lejanas (la cámara vuelve al personaje cuando te mueves o pulsas una tecla) |
| **Z** / **X** | Acercar / alejar el zoom |
| **ESC** | Volver al menú (S = sí, N = no) |
| **Cualquier tecla / toque** | Cancela el pensamiento activo |
| **R** | Reiniciar tras el Game Over (o clic en el botón) |
| **Táctil** | Toque corto: ir a esa celda. Mantener pulsado o arrastrar poco en el cuadrante inferior izquierdo: aparece una cruceta bajo el dedo (desaparece al soltar). Arrastrar en el resto: desplazar la vista. Pellizco: zoom (separar acerca, juntar aleja) |
| **F2** | Revelación automática de celdas adyacentes (debug) |
| **F3** | Información de depuración |
| **F4** | Mostrar el camino principal y el barranco |
| **F5** | Alternar el contraste de las líneas de salida |
| **F6 / F7** | Teletransportarse al inicio / a la salida (debug) |

Con `?debug` en la URL, la partida queda expuesta en la consola como `window.__game`.

## Desarrollo

Requisitos: **Node.js 20+**.

```bash
npm install
npm run dev        # servidor de desarrollo con recarga (http://localhost:5173)
npm run typecheck  # comprobación de tipos (tsc, modo estricto)
npm test           # tests unitarios (Vitest)
npm run build      # compilación de producción en dist/
npm run preview    # sirve dist/ localmente
```

El audio del navegador solo puede sonar tras un gesto del usuario, por eso el juego muestra una pantalla de carga con un botón **Empezar** antes de la pantalla de título.

## Estructura del proyecto

```
├── index.html            # Página: lienzo 630×630 y pantalla de carga
├── src/
│   ├── main.ts           # Arranque: carga de recursos, gesto inicial y bucle de partidas
│   ├── game.ts           # Lógica: estado, movimiento, pensamientos, monstruos, bucle principal
│   ├── world.ts          # Mapa: barranco, puentes, camino principal, salidas de celdas
│   ├── renderer.ts       # Dibujado: celdas, sprites, superposiciones, pantallas
│   ├── effects.ts        # Líneas quebradas, suelo rugoso, piedras de pared, acantilado
│   ├── decorations.ts    # Antorchas, sangre, huellas, fuente, polvo, telarañas, escalera
│   ├── audio.ts          # Mezclador Web Audio y AudioManager (música, subtítulos, pensamientos)
│   ├── input.ts          # Teclado y ratón
│   ├── assets.ts         # Carga de imágenes y sonidos
│   ├── gfx.ts            # Primitivas de dibujo con la semántica de pygame.draw
│   ├── models.ts         # CellType, Direction, Cell
│   ├── rng.ts            # Aleatoriedad global y con semilla (determinista)
│   ├── config.ts, time.ts
├── tests/                # Vitest: rng, generación del mapa, entrada
├── images/, sound/       # Recursos (PNG y OGG Vorbis)
└── .github/workflows/    # CI (typecheck + tests + build) y despliegue en GitHub Pages
```

Consulta [ARCHITECTURE.md](ARCHITECTURE.md) para más detalle del diseño.

## Despliegue

Cada push a `main` compila el proyecto (`npm run build`) y publica `dist/` en GitHub Pages mediante `.github/workflows/deploy.yml`. La compilación usa rutas relativas, por lo que funciona tanto en la raíz de un dominio como en un subdirectorio.
