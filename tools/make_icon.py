#!/usr/bin/env python3
"""
Genera los iconos de la aplicación (images/icon-512.png, icon-192.png, apple-touch-icon.png y favicon.png)
con el busto del caballero sobre un fondo rojo oscuro. Parte de la hoja del caballero (art/guerrero-hoja-origen.jpg).

Uso:  python3 tools/make_icon.py
"""
import numpy as np
from PIL import Image, ImageFilter

import slice_atlas as sa

SHEET = 'art/guerrero-hoja-origen.jpg'
FRAME = 8        # fotograma neutro de frente
SIZE = 1024
BUST_WIDTH = 940  # ancho del caballero en el icono maestro (los hombros llegan casi a los bordes)


def main() -> None:
    sheet = Image.open(SHEET).convert('RGB')
    pitch = sheet.width / sa.CELLS
    row, col = divmod(FRAME, sa.CELLS)
    box = (round(col * pitch) + sa.INSET, round(row * pitch) + sa.INSET, round((col + 1) * pitch) - sa.INSET, round((row + 1) * pitch) - sa.INSET)
    rgb = np.array(sheet.crop(box))
    mask = sa.extract(rgb, True)
    frame = Image.fromarray(np.dstack([rgb, (mask * 255).astype(np.uint8)]), 'RGBA')
    frame = frame.crop(frame.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
    frame = frame.crop((0, 0, frame.width, round(frame.height * 0.66)))  # cabeza y torso

    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    t = np.clip(np.hypot(xx - SIZE / 2, yy - SIZE * 0.42) / (SIZE * 0.75), 0, 1)[..., None]
    base = Image.fromarray((np.array([88, 18, 24]) * (1 - t) + np.array([8, 4, 6]) * t).astype(np.uint8), 'RGB').convert('RGBA')

    k = BUST_WIDTH / frame.width
    knight = frame.resize((round(frame.width * k), round(frame.height * k)), Image.LANCZOS)
    x, y = (SIZE - knight.width) // 2, SIZE - knight.height + 10  # el corte inferior queda fuera del icono
    shadow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    shadow.paste(Image.new('RGBA', knight.size, (0, 0, 0, 170)), (x + 8, y + 14), knight.getchannel('A'))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14)))
    base.alpha_composite(knight, (x, y))
    icon = base.convert('RGB')
    for name, size in (('icon-512', 512), ('icon-192', 192), ('apple-touch-icon', 180), ('favicon', 64)):
        icon.resize((size, size), Image.LANCZOS).save(f'images/{name}.png', optimize=True)
        print(f'images/{name}.png')


if __name__ == '__main__':
    main()
