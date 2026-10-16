#!/usr/bin/env python3
"""
Extrae un fotograma de una hoja 8×8 (por defecto el 63, el busto) como PNG recortado y transparente.

Uso:  python3 tools/slice_portrait.py hoja.jpg images/retrato_barbaro.png [indice]
"""
import sys

import numpy as np
from PIL import Image

import slice_atlas as sa


def main(src: str, dst: str, index: int = 63) -> None:
    sheet = Image.open(src).convert('RGB')
    pitch = sheet.width / sa.CELLS
    row, col = divmod(index, sa.CELLS)
    box = (round(col * pitch) + sa.INSET, round(row * pitch) + sa.INSET, round((col + 1) * pitch) - sa.INSET, round((row + 1) * pitch) - sa.INSET)
    rgb = np.array(sheet.crop(box))
    mask = sa.extract(rgb)
    frame = Image.fromarray(np.dstack([rgb, (mask * 255).astype(np.uint8)]), 'RGBA')
    frame = frame.crop(frame.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
    frame.save(dst, optimize=True)
    print(f'{dst}: {frame.size[0]}x{frame.size[1]}')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) == 4 else 63)
