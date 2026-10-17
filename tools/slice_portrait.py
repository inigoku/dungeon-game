#!/usr/bin/env python3
"""
Extrae un fotograma de una hoja 8×8 (por defecto el 63, el busto) como PNG recortado y transparente.

Uso:  python3 tools/slice_portrait.py hoja.jpg images/retrato_barbaro.png [indice] [--fondo-plano] [--busto]
"""
import sys

import numpy as np
from PIL import Image

import slice_atlas as sa

BUST_FRACTION = 0.6  # parte de la altura que se conserva con --busto


def main(src: str, dst: str, index: int = 63, flat: bool = False, bust: bool = False) -> None:
    sheet = Image.open(src).convert('RGB')
    pitch = sheet.width / sa.CELLS
    row, col = divmod(index, sa.CELLS)
    box = (round(col * pitch) + sa.INSET, round(row * pitch) + sa.INSET, round((col + 1) * pitch) - sa.INSET, round((row + 1) * pitch) - sa.INSET)
    rgb = np.array(sheet.crop(box))
    mask = sa.extract(rgb, flat)
    frame = Image.fromarray(np.dstack([rgb, (mask * 255).astype(np.uint8)]), 'RGBA')
    frame = frame.crop(frame.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
    if bust:
        # Busto: cabeza y hombros (la parte alta del personaje)
        frame = frame.crop((0, 0, frame.width, round(frame.height * BUST_FRACTION)))
    frame.save(dst, optimize=True)
    print(f'{dst}: {frame.size[0]}x{frame.size[1]}')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) not in (2, 3):
        sys.exit(__doc__)
    main(args[0], args[1], int(args[2]) if len(args) == 3 else 63, '--fondo-plano' in sys.argv, '--busto' in sys.argv)
