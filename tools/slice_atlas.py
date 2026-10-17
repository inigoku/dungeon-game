#!/usr/bin/env python3
"""
Convierte una hoja de sprites 8×8 generada con IA (fondo de tablero gris pintado, con los números de cada celda) en un
atlas limpio con transparencia: 8×8 fotogramas de 128×128 con los pies anclados en el mismo punto.

Uso:  python3 tools/slice_atlas.py art/barbaro-hoja-origen.jpg images/atlas_barbaro.png [--fondo-plano] [--sin-texto] [--sin-acantilado]
      (--sin-texto: borra los rótulos al pie de cada celda; --sin-acantilado: quita el borde de roca de los fotogramas 56 y 57)
      (--fondo-plano: cada celda tiene un gris liso en vez del tablero)
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
SCALE = 0.5          # factor sobre el tamaño nativo de la celda (≈250 px → 128)
INSET = 6            # margen que se descarta en cada celda (bordes de la cuadrícula)
FLAT_EDGE = 14       # gradiente máximo dentro de una región plana (fondo liso)
UNANCHORED = {56, 57, 63}  # retrato y caídas en el aire: se encajan enteros, sin anclar los pies


def extract(rgb: np.ndarray, flat: bool = False) -> np.ndarray:
    """Máscara (float 0..1) del personaje dentro de una celda.

    El fondo de la hoja es un tablero gris (dos tonos casi sin color) pintado en la imagen: se detecta
    como gris poco saturado y claridad media, y solo cuenta si está conectado con el borde de la celda.
    """
    if flat:
        # Fondo liso (un gris por celda, a veces con dos tonos): se parte la imagen en regiones planas separadas
        # por bordes, y es fondo toda región grande que toque el borde de la celda. El acero gris del personaje
        # queda dentro de su contorno oscuro, así que no se confunde con el fondo.
        f = ndi.gaussian_filter(rgb.astype(float), sigma=(0.8, 0.8, 0))
        grad = np.max([np.hypot(ndi.sobel(f[:, :, c], axis=0), ndi.sobel(f[:, :, c], axis=1)) for c in range(3)], axis=0)
        flat_px = grad < FLAT_EDGE
        regions, n_regions = ndi.label(flat_px)
        touching = np.zeros(n_regions + 1, bool)
        edge_ids = np.unique(np.concatenate([regions[:3].ravel(), regions[-3:].ravel(), regions[:, :3].ravel(), regions[:, -3:].ravel()]))
        touching[edge_ids] = True
        touching[0] = False
        sizes = np.bincount(regions.ravel(), minlength=n_regions + 1)
        border_color = np.median(np.concatenate([rgb[:6].reshape(-1, 3), rgb[-6:].reshape(-1, 3), rgb[:, :6].reshape(-1, 3), rgb[:, -6:].reshape(-1, 3)]), axis=0)
        region_ids = np.arange(n_regions + 1)
        counts = np.maximum(sizes, 1)
        region_mean = np.stack([np.bincount(regions.ravel(), weights=rgb[:, :, c].ravel().astype(float), minlength=n_regions + 1) / counts for c in range(3)], axis=1)
        # También es fondo el hueco encerrado (el interior de un arco) con el color liso del fondo
        enclosed = (np.abs(region_mean - border_color).max(axis=1) < 8) & (sizes > 60) & (region_ids > 0)
        bg = (touching & (sizes > 250) | enclosed)[regions]
        lum_px = rgb.astype(float).mean(axis=2)
        # La franja de transición entre el fondo y el contorno oscuro también es fondo
        bg = ndi.binary_dilation(bg, iterations=3, mask=lum_px > 75) | bg
        fg = ~bg
    else:
        pix = rgb.astype(int)
        sat = pix.max(axis=2) - pix.min(axis=2)
        lum = pix.mean(axis=2)
        checker = (sat < 18) & (lum > 90) & (lum < 150)
        checker = ndi.binary_closing(checker, structure=np.ones((3, 3)), iterations=1) | checker
        seeds = np.zeros_like(checker)
        seeds[0, :] = seeds[-1, :] = seeds[:, 0] = seeds[:, -1] = True
        bg = ndi.binary_propagation(seeds & checker, mask=checker)
        # Los cuadros blancos del borde de la cuadrícula
        fg = ~ndi.binary_dilation(bg, iterations=1)
    # Quita los números de la esquina y las motas sueltas: solo se conservan componentes grandes
    labels, n = ndi.label(fg)
    keep = np.zeros_like(fg)
    sizes = ndi.sum(fg, labels, range(1, n + 1))
    biggest = max(sizes) if n else 0
    for i, size in enumerate(sizes, start=1):
        ys, xs = np.where(labels == i)
        in_label_box = xs.max() < 70 and ys.max() < 44
        in_text_band = False
        if size >= max(60, biggest * 0.01) and not in_label_box and not in_text_band:
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
        if xs.max() < 70 and ys.max() < 44:
            keep[labels == i] = False
            continue
        # Salpicaduras de sangre sueltas (rojizas y pequeñas)
        pix = rgb[ys, xs].astype(int)
        if len(xs) < 200 and (pix[:, 0] - pix[:, 1]).mean() > 40:
            keep[labels == i] = False
            continue
        # Trozos de escenario (el borde de musgo del barranco): verdosos y nada que ver con la piel
        if len(xs) > 200 and (pix[:, 1] - pix[:, 0]).mean() > 6 and pix[:, 1].mean() > 70:
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


def main(src: str, dst: str, flat: bool = False, options: frozenset[str] = frozenset()) -> None:
    sheet = Image.open(src).convert('RGBA')
    pitch = sheet.width / CELLS
    atlas = Image.new('RGBA', (OUT * CELLS, OUT * CELLS), (0, 0, 0, 0))
    report = []
    for index in range(CELLS * CELLS):
        row, col = divmod(index, CELLS)
        x0, y0 = round(col * pitch) + INSET, round(row * pitch) + INSET
        x1, y1 = round((col + 1) * pitch) - INSET, round((row + 1) * pitch) - INSET
        rgb = np.array(sheet.convert('RGB').crop((x0, y0, x1, y1)))
        mask = extract(rgb, flat)
        if 'sin-texto' in options and row >= 6:
            # Rótulos al pie de las dos últimas filas ("Muriendo 1"...): se descarta la franja inferior de la celda
            mask[int(mask.shape[0] * 0.88):, :] = 0
        if 'sin-acantilado' in options and index in (56, 57):
            mask[int(mask.shape[0] * 0.72):, : int(mask.shape[1] * 0.38)] = 0
            # Y lo que quede suelto de la roca: solo se conserva el personaje (el trozo más grande)
            parts, count = ndi.label(mask > 0.3)
            if count > 1:
                biggest_part = int(np.argmax(ndi.sum(mask > 0.3, parts, range(1, count + 1)))) + 1
                mask[parts != biggest_part] = 0
        if index == 56:  # el borde del barranco que asoma en la esquina
            h, w = mask.shape
            mask[int(h * 0.68):, : int(w * 0.42)] = 0
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
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], '--fondo-plano' in sys.argv, frozenset(a[2:] for a in sys.argv[1:] if a in ('--sin-texto', '--sin-acantilado')))
