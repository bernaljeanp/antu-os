"""Contraste sobre el PNG final compuesto, sin confundir el grabado con la silueta.

P90 = mínimo del décimo más claro de una máscara (percentil discreto). El borde es la máscara alfa>=128 menos una
erosión 3×3. No es una certificación WCAG: se publica el método y se revisan también las formas al tamaño real.
"""
from functools import lru_cache
from PIL import Image, ImageFilter

BACKGROUNDS = {"panel": (20, 20, 24), "window": (28, 28, 33), "light": (245, 245, 247)}


@lru_cache(maxsize=131072)
def luminance(rgb):
    values = [v / 255 for v in rgb]
    values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(v * w for v, w in zip(values, (0.2126, 0.7152, 0.0722)))


def p90(values):
    values = sorted(values)
    return values[int((len(values) - 1) * 0.9)] if values else 0


def measure(image):
    image = image.convert("RGBA")
    mask = image.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    visible = list(mask.getdata())
    eroded = list(mask.filter(ImageFilter.MinFilter(3)).getdata())
    edge = [a and not b for a, b in zip(visible, eroded)]
    result = {}
    for name, background in BACKGROUNDS.items():
        pixels = Image.alpha_composite(Image.new("RGBA", image.size, (*background, 255)), image).convert("RGB")
        base = luminance(background)
        ratios = [(max(luminance(rgb), base) + 0.05) / (min(luminance(rgb), base) + 0.05) for rgb in pixels.getdata()]
        boundary = [r for r, yes in zip(ratios, edge) if yes]
        body = [r for r, yes in zip(ratios, visible) if yes]
        result[name] = {"outline_p90": round(p90(boundary), 4), "visible_p90": round(p90(body), 4),
                        "outline_percent_at_least_3": round(100 * sum(v >= 3 for v in boundary) / max(1, len(boundary)), 2),
                        "pass": p90(body) >= 3 and (name == "light" or p90(boundary) >= 3)}
    return result
