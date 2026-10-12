# Arquitectura

El juego es una aplicación TypeScript sin framework: **Vite** compila y sirve, **Canvas 2D** dibuja, **Web Audio** reproduce el sonido y **Vitest** ejecuta los tests. No hay dependencias en tiempo de ejecución.

## Capas

```
main.ts ──► Game ──► World         (datos del mapa y generación)
              │ ├──► Renderer ──► effects / decorations / gfx
              │ ├──► AudioManager ──► Mixer (Sound / Channel)
              │ └──► InputHandler
              └──► assets (imágenes y buffers de audio)
```

- **`world.ts` — `World`**: tablero `Cell[][]`, barranco (eje y posición), puentes, camino principal ordenado, salida y las reglas de generación de celdas (`generateRandomExits`). No depende del navegador, por eso es fácil de probar.
- **`game.ts` — `Game`**: todo el estado mutable de la partida y las reglas: movimiento (`placeCellInDirection`), pensamientos con retardo, daño y Game Over, caída por el barranco, música por distancia, sonidos ambientales, IA de los Profundos y la secuencia de la ráfaga. `run()` devuelve una `Promise<boolean>` (`true` = reiniciar, `false` = salir).
- **`renderer.ts` — `Renderer`**: lee el estado de `Game` y dibuja cada fotograma. Las texturas de suelo y paredes de cada celda se hornean en canvases fuera de pantalla y se cachean (con tope), igual que en la versión original.
- **`audio.ts`**: `Mixer`/`Sound`/`Channel` reproducen buffers con volumen, bucles y *fade-out*; `AudioManager` gestiona la música, los subtítulos y los **pensamientos** (línea de tiempo de sonidos, imágenes y subtítulos que avanza en cada fotograma).
- **`input.ts`**: `InputHandler` decide qué hace cada tecla según el estado (Game Over, diálogos, título, juego). Depende de la interfaz `GameInput`, no de `Game`.
- **`gfx.ts`**: envoltorios de Canvas con la semántica de `pygame.draw` (bordes interiores, arcos antihorarios...), de modo que el código de dibujo se porta casi línea a línea.

## Decisiones de diseño

- **Tiempo**: `ticks()` (ms desde el arranque) equivale a `pygame.time.get_ticks()`. La cámara usa un factor de interpolación ajustado a los fotogramas transcurridos, así que la velocidad no depende de la tasa de refresco.
- **Asincronía**: los `asyncio.sleep` de Python son `await sleep(ms)`; tras cada espera se comprueba `disposed` para que una partida descartada no dispare efectos.
- **Aleatoriedad**: `random` (global) para lo que debe variar cada partida y `seeded(semilla)` (mulberry32) para lo que debe ser estable por celda: piedras, ruido del suelo, sangre, antorchas, telarañas... Las semillas siguen la fórmula `fila * 100000 + columna`, así que cada celda se ve igual en todos los fotogramas.
- **Posiciones**: se representan como `[fila, columna]`; los conjuntos usan la clave numérica `posKey(fila, columna) = fila * 1000 + columna`.
- **Audio y autoplay**: el navegador exige un gesto del usuario antes de reproducir sonido, por lo que `main.ts` espera un clic o tecla (pantalla «Empezar») antes de reanudar el `AudioContext` y crear la partida.
- **Pensamientos**: un pensamiento nuevo interrumpe al anterior; los sonidos son secuenciales, las imágenes con duración `0` duran lo que el sonido, y el último subtítulo o imagen permanece hasta el final del pensamiento.

## Tests

`npm test` ejecuta Vitest en entorno Node (sin DOM): generador de números aleatorios, propiedades del mapa generado (conectividad, salida al otro lado del barranco, cruce solo por el puente, conexiones bidireccionales) y el manejador de entrada con un juego simulado.
