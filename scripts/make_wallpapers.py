"""Dibuja los fondos de Antu: colinas de obsidiana superpuestas con la cresta encendida en lava.

Uso: python scripts/make_wallpapers.py   (requiere Pillow y numpy)
Escribe images_dark/ (Obsidiana, noche) e images/ (Salar, día) del paquete de fondo «Antu», y su vista previa.
"""
import pathlib

import numpy as np
from PIL import Image, ImageFilter

ROOT = pathlib.Path(__file__).parent.parent
PKG = ROOT / "files/system/usr/share/wallpapers/Antu/contents"
W, H = 3840, 2160
X = np.linspace(0.0, 1.0, W)
Y = np.linspace(0.0, 1.0, H)[:, None]

# Cada colina: altura base, ondulaciones (amplitud, frecuencia, fase) e intensidad de su cresta de lava.
# De atrás hacia adelante; las de atrás son más claras y su brasa más tenue.
HILLS = [
    (0.42, [(0.045, 1.3, 0.2), (0.015, 3.1, 1.0)], 0.35),
    (0.54, [(0.050, 1.0, 2.1), (0.018, 2.7, 0.4)], 0.55),
    (0.66, [(0.045, 1.6, 4.0), (0.020, 3.6, 2.2)], 0.80),
    (0.80, [(0.040, 1.2, 1.3), (0.012, 4.2, 3.3)], 1.00),
]
HAZE = 0.65  # cuánto se funden con el cielo las colinas del fondo

THEMES = {
    "images_dark": dict(sky=("#08080B", "#141018"), hill=("#1B1A21", "#0B0B0E"), rim=("#FF5A1F", "#FFB020"),
                        glow=1.0),
    "images": dict(sky=("#F7F5F2", "#ECE7E2"), hill=("#E4DFDA", "#F6F3F0"), rim=("#FF5A1F", "#FF9A3C"),
                   glow=0.55),
}


def rgb(hex_color):
    h = hex_color.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def mix(a, b, t):
    return a * (1 - t) + b * t


def crest(base, waves):
    y = np.full(W, base, dtype=np.float32)
    for amp, freq, phase in waves:
        y += amp * np.sin(2 * np.pi * freq * X + phase)
    return y


def render(folder, t):
    sky_top, sky_bottom = rgb(t["sky"][0]), rgb(t["sky"][1])
    img = mix(sky_top, sky_bottom, Y[..., None] * np.ones((1, W, 1)))
    rim_a, rim_b = rgb(t["rim"][0]), rgb(t["rim"][1])
    # Resplandor cálido bajo el horizonte, detrás de la colina del fondo, como un volcán que no se ve.
    ember = np.exp(-(((X[None, :] - 0.55) / 0.30) ** 2 + ((Y - 0.46) / 0.10) ** 2))
    img = mix(img, rim_a[None, None, :], (ember * 0.22 * t["glow"])[..., None])
    glow_layer = np.zeros((H, W, 3), dtype=np.float32)

    for i, (base, waves, heat) in enumerate(HILLS):
        c = crest(base, waves)
        depth = i / (len(HILLS) - 1)  # 0 atrás, 1 adelante
        below = Y >= c[None, :]
        # Relleno: más claro arriba de la colina, más oscuro hacia abajo; las de atrás, más neblinosas.
        local = np.clip((Y - c[None, :]) / 0.35, 0, 1)
        top_color = mix(rgb(t["hill"][0]), sky_bottom, HAZE * (1 - depth))
        fill = mix(top_color, rgb(t["hill"][1]), local[..., None])
        img = np.where(below[..., None], fill, img)
        # Cresta de lava: color que cambia a lo largo de la colina, con una línea fina y un halo suave.
        line_color = mix(rim_a, rim_b, (0.5 + 0.5 * np.sin(2 * np.pi * (X * 0.8 + 0.3 * i)))[:, None])
        dist = (Y - c[None, :]) * H  # píxeles respecto de la cresta (positivo = dentro de la colina)
        line = np.exp(-(dist / 2.2) ** 2) * heat
        img = mix(img, line_color[None, :, :], np.clip(line, 0, 1)[..., None])
        halo = np.exp(-np.maximum(-dist, 0) / 60.0) * (dist < 0) * heat * 0.45 * t["glow"]
        glow_layer += line_color[None, :, :] * halo[..., None]

    glow = Image.fromarray(np.clip(glow_layer, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(24))
    out = np.clip(img + np.asarray(glow, dtype=np.float32) * (1.0 if folder == "images_dark" else -0.15), 0, 255)
    # Grano muy leve para evitar bandas en los degradados.
    out = np.clip(out + np.random.default_rng(7).normal(0, 1.2, out.shape), 0, 255).astype(np.uint8)
    path = PKG / folder / f"{W}x{H}.png"
    Image.fromarray(out).save(path, optimize=True)
    return path


if __name__ == "__main__":
    for folder, theme in THEMES.items():
        print("escrito", render(folder, theme).relative_to(ROOT))
    Image.open(PKG / "images_dark" / f"{W}x{H}.png").resize((960, 540), Image.LANCZOS).save(PKG / "screenshot.png")
