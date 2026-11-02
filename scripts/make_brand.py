"""Marca de Antu desde una sola geometría: el símbolo «A solar» (una A con forma de cumbre y un sol de lava dentro).

Uso: python scripts/make_brand.py   (requiere Pillow)
Escribe el símbolo en SVG, el icono de app para el README y los recursos de la pantalla de arranque (Plymouth).
"""
import pathlib

from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).parent.parent
SS = 4  # supermuestreo para los PNG

INK, LAVA, TRACK = "#F5F5F7", "#FF5A1F", "#2E2E33"
TILE, TILE_EDGE = "#1C1B21", "#3C3A42"

# Geometría en un lienzo de 512: los tres vértices de la A, su grosor y el sol.
A_POINTS = [(128, 389), (256, 123), (384, 389)]
A_STROKE = 38.4
SUN = (256, 297, 38.4)  # centro x, centro y, radio


def svg_symbol():
    pts = " ".join(f"{x},{y}" for x, y in A_POINTS)
    cx, cy, r = SUN
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="96 96 320 320">'
            f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="{A_STROKE}" stroke-linejoin="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{LAVA}"/></svg>\n')


def svg_icon():
    pts = " ".join(f"{x},{y}" for x, y in A_POINTS)
    cx, cy, r = SUN
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">'
            f'<rect x="30.7" y="30.7" width="450.6" height="450.6" rx="112.6" fill="{TILE}" stroke="{TILE_EDGE}" stroke-width="6"/>'
            f'<polyline points="{pts}" fill="none" stroke="{INK}" stroke-width="{A_STROKE}" stroke-linejoin="round"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{LAVA}"/></svg>\n')


def draw_symbol(d, scale, ox=0.0, oy=0.0):
    pts = [(ox + x * scale, oy + y * scale) for x, y in A_POINTS]
    d.line(pts, fill=INK, width=round(A_STROKE * scale), joint="curve")
    cx, cy, r = SUN
    cx, cy, r = ox + cx * scale, oy + cy * scale, r * scale
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=LAVA)


def icon_png(size):
    n = size * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = n / 512
    d.rounded_rectangle([30.7 * k, 30.7 * k, 481.3 * k, 481.3 * k], radius=112.6 * k, fill=TILE,
                        outline=TILE_EDGE, width=max(1, round(6 * k)))
    draw_symbol(d, k)
    return img.resize((size, size), Image.LANCZOS)


def symbol_png(height):
    """Símbolo sin fondo, recortado a la región 96..416 del lienzo (la misma vista que el SVG)."""
    n = height * SS
    k = n / 320
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    draw_symbol(ImageDraw.Draw(img), k, -96 * k, -96 * k)
    return img.resize((height, height), Image.LANCZOS)


if __name__ == "__main__":
    (ROOT / "files/system/usr/share/antu/antu-symbol.svg").write_text(svg_symbol(), encoding="utf-8", newline="\n")
    (ROOT / "brand").mkdir(exist_ok=True)
    (ROOT / "brand/antu-icon.svg").write_text(svg_icon(), encoding="utf-8", newline="\n")
    icon_png(256).save(ROOT / "brand/antu-icon-256.png")

    ply = ROOT / "files/system/usr/share/plymouth/themes/antu"
    for old in ply.glob("*.png"):  # recursos de versiones anteriores del tema
        old.unlink()
    symbol_png(200).save(ply / "symbol.png")  # dibujado para pantallas de 1600 px de alto
    Image.new("RGBA", (1, 1), TRACK).save(ply / "track.png")
    Image.new("RGBA", (1, 1), LAVA).save(ply / "fill.png")
    print("marca y recursos de arranque escritos")
