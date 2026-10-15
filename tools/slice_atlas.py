#!/usr/bin/env python3
"""
Convierte una hoja de sprites 8×8 generada con IA (fondo gris, con los números de cada celda) en un
atlas limpio con transparencia: 8×8 fotogramas de 128×128 con los pies anclados en el mismo punto.

Uso:  python3 tools/slice_atlas.py art/barbaro-hoja-origen.webp images/atlas_barbaro.png
Necesita: pip install pillow numpy scipy
"""
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

CELLS = 8
OUT = 128            # lado de cada fotograma de salida
BASELINE = 122       # fila donde apoyan los pies
CENTER_X = 64        # columna donde se centra el personaje
SCALE = 1.15         # factor sobre el tamaño nativo de la celda
INSET = 3            # margen que se descarta en cada celda (bordes de la cuadrícula)
THRESHOLD = 34       # distancia de color al fondo para considerarlo personaje
UNANCHORED = {63}    # el retrato se encaja sin anclar los pies


def background_color(rgb: np.ndarray) -> np.ndarray:
    h, w, _ = rgb.shape
    ring = np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)])
    return np.median(ring, axis=0)


def extract(rgb: np.ndarray) -> np.ndarray:
    """Máscara (float 0..1) del personaje dentro de una celda."""
    bg = background_color(rgb)
    dist = np.sqrt(((rgb.astype(float) - bg) ** 2).sum(axis=2))
    fg = dist > THRESHOLD
    # Quita los números de la esquina y las motas sueltas: solo se conservan componentes grandes
    labels, n = ndi.label(fg)
    keep = np.zeros_like(fg)
    sizes = ndi.sum(fg, labels, range(1, n + 1))
    biggest = max(sizes) if n else 0
    for i, size in enumerate(sizes, start=1):
        ys, xs = np.where(labels == i)
        in_label_box = xs.max() < 40 and ys.max() < 26
        if size >= max(60, biggest * 0.01) and not in_label_box:
            keep |= labels == i
    # Rellena los huecos pequeños (reflejos dentro de la ropa) pero no los grandes (entre brazo y cuerpo)
    filled = ndi.binary_fill_holes(keep)
    holes = filled & ~keep
    hl, hn = ndi.label(holes)
    for i in range(1, hn + 1):
        region = hl == i
        if region.sum() < 90:
            keep |= region
    # Cierra las grietas del borde (reflejos grises en la capucha) y alisa la silueta
    keep = ndi.binary_closing(keep, structure=np.ones((3, 3)), iterations=2)
    keep = ndi.binary_opening(keep, iterations=1)
    # De nuevo, sin números sueltos
    labels, n = ndi.label(keep)
    for i in range(1, n + 1):
        ys, xs = np.where(labels == i)
        if xs.max() < 40 and ys.max() < 26:
            keep[labels == i] = False
            continue
        # Salpicaduras de sangre sueltas (rojizas y pequeñas)
        pix = rgb[ys, xs].astype(int)
        if len(xs) < 200 and (pix[:, 0] - pix[:, 1]).mean() > 40:
            keep[labels == i] = False
    soft = ndi.gaussian_filter(keep.astype(float), 0.6)
    return np.clip((soft - 0.3) / 0.5, 0, 1)


def anchor(mask: np.ndarray) -> tuple[float, float]:
    """(x de los pies, y de la planta de los pies) de la silueta."""
    solid = mask > 0.5
    widths = solid.sum(axis=1)
    rows = np.where(widths >= 8)[0]
    base = rows.max() if len(rows) else solid.any(axis=1).nonzero()[0].max()
    band = solid[max(0, base - 22): base + 1]
    xs = np.where(band.any(axis=0))[0]
    cx = (np.average(np.where(band)[1]) if band.any() else (xs.min() + xs.max()) / 2)
    return float(cx), float(base)


def main(src: str, dst: str) -> None:
    sheet = Image.open(src).convert('RGBA')
    pitch = sheet.width / CELLS
    atlas = Image.new('RGBA', (OUT * CELLS, OUT * CELLS), (0, 0, 0, 0))
    report = []
    for index in range(CELLS * CELLS):
        row, col = divmod(index, CELLS)
        x0, y0 = round(col * pitch) + INSET, round(row * pitch) + INSET
        x1, y1 = round((col + 1) * pitch) - INSET, round((row + 1) * pitch) - INSET
        rgb = np.array(sheet.convert('RGB').crop((x0, y0, x1, y1)))
        mask = extract(rgb)
        rgba = np.dstack([rgb, (mask * 255).astype(np.uint8)])
        frame = Image.fromarray(rgba, 'RGBA')
        if index in UNANCHORED:
            scale = min(OUT / frame.width, OUT / frame.height)
            offset = ((OUT - frame.width * scale) / 2, (OUT - frame.height * scale) / 2)
        else:
            fx, fy = anchor(mask)
            scale = SCALE
            offset = (CENTER_X - fx * scale, BASELINE - fy * scale)
        scaled = frame.resize((round(frame.width * scale), round(frame.height * scale)), Image.LANCZOS)
        cell = Image.new('RGBA', (OUT, OUT), (0, 0, 0, 0))
        cell.alpha_composite(scaled, (round(offset[0]), round(offset[1])), source=(0, 0)) if offset[0] >= 0 and offset[1] >= 0 else paste_clipped(cell, scaled, offset)
        atlas.alpha_composite(cell, (col * OUT, row * OUT))
        report.append({'index': index, 'opaque': round(float((mask > 0.5).mean()), 3)})
    atlas.save(dst, optimize=True)
    with open(dst.rsplit('.', 1)[0] + '.json', 'w') as f:
        json.dump({'cell': OUT, 'columns': CELLS, 'baseline': BASELINE, 'centerX': CENTER_X, 'frames': report}, f, indent=1)
    print(f'{dst}: {atlas.size[0]}x{atlas.size[1]}')


def paste_clipped(cell: Image.Image, img: Image.Image, offset: tuple[float, float]) -> None:
    layer = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    layer.paste(img, (round(offset[0]), round(offset[1])))
    cell.alpha_composite(layer)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
