#!/usr/bin/env python3
"""
Recorta de una hoja 8×8 los fotogramas con expresión que usan los pensamientos y la pantalla de título,
a su resolución original, y los coloca en una tira de celdas de 256×256 (alineados abajo y al centro).

Uso:  python3 tools/slice_faces.py art/guerrero-hoja-origen.jpg images/caras_guerrero.png [--fondo-plano] [--sin-texto]
Los fotogramas, en orden: 0 en guardia, 48 grito, 54 susto, 55 asombro, 58 poder, 60 mirando alrededor.
"""
import sys

import numpy as np
from PIL import Image

import slice_atlas as sa

FRAMES = [0, 48, 54, 55, 58, 60]
CELL = 256


def main(src: str, dst: str, flat: bool, no_text: bool) -> None:
    sheet = Image.open(src).convert('RGB')
    pitch = sheet.width / sa.CELLS
    strip = Image.new('RGBA', (CELL * len(FRAMES), CELL), (0, 0, 0, 0))
    for slot, index in enumerate(FRAMES):
        row, col = divmod(index, sa.CELLS)
        box = (round(col * pitch) + sa.INSET, round(row * pitch) + sa.INSET, round((col + 1) * pitch) - sa.INSET, round((row + 1) * pitch) - sa.INSET)
        rgb = np.array(sheet.crop(box))
        mask = sa.extract(rgb, flat)
        if no_text and row >= 6:
            mask[int(mask.shape[0] * 0.88):, :] = 0
        frame = Image.fromarray(np.dstack([rgb, (mask * 255).astype(np.uint8)]), 'RGBA')
        frame = frame.crop(frame.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
        if frame.width > CELL or frame.height > CELL:
            k = min(CELL / frame.width, CELL / frame.height)
            frame = frame.resize((round(frame.width * k), round(frame.height * k)), Image.LANCZOS)
        strip.alpha_composite(frame, (slot * CELL + (CELL - frame.width) // 2, CELL - frame.height))
    strip.save(dst, optimize=True)
    print(f'{dst}: {strip.size[0]}x{strip.size[1]}')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], '--fondo-plano' in sys.argv, '--sin-texto' in sys.argv)
