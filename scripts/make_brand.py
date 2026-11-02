"""Export original Antu artwork, CC-BY-SA-4.0.

python scripts/make_brand.py           # export frozen native optical renders
python scripts/make_brand.py --render  # rebuild 3D icons first (BLENDER_BIN)
Requires Pillow; optional rendering requires Blender 5.x.
The old flat icon generator has been retired. No raster master is repainted.
"""
import argparse
import base64
import os
from pathlib import Path
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "brand/previews"
MASTERS = ROOT / "brand/masters/icons"
INK, OBSIDIAN, LAVA, TRACK = "#F5F5F7", "#0B0B0E", "#FF5A1F", "#2E2E33"
NAMES = ("antu", "antu-inicio", "antu-instalador", "antu-eclipse", "antu-ia")
SIZES = (1024, 512, 256, 128, 64, 48, 32, 16)
FONT = ROOT / "files/system/usr/share/fonts/antu/Inter-Variable.ttf"


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def font(size, weight=550):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_axes([weight])
    return f


def symbol_svg(light=False):
    color = OBSIDIAN if light else INK
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n'
            f'  <path fill="{color}" d="M8 56 28.6 12.8Q32 6.6 35.4 12.8L56 56H48L32 23.6 16 56Z"/>\n'
            f'  <circle cx="32" cy="46" r="5.5" fill="{LAVA}"/>\n</svg>\n')


def symbol_png(size, light=False, sun=True):
    ss = 4 if size <= 1024 else 2
    n = size * ss
    im = Image.new("RGBA", (n, n))
    d, k = ImageDraw.Draw(im), n / 64
    points = [(8, 56), (28.6, 12.8)]
    for i in range(1, 33):
        t = i / 32
        points.append(((1-t)**2*28.6 + 2*(1-t)*t*32 + t*t*35.4,
                       (1-t)**2*12.8 + 2*(1-t)*t*6.6 + t*t*12.8))
    points += [(56, 56), (48, 56), (32, 23.6), (16, 56)]
    d.polygon([(x*k, y*k) for x, y in points], fill=OBSIDIAN if light else INK)
    if sun:
        r = 5.5
        d.ellipse(((32-r)*k, (46-r)*k, (32+r)*k, (46+r)*k), fill=LAVA)
    return im.resize((size, size), Image.Resampling.LANCZOS)


def plymouth():
    """Piezas de «Amanecer», la animación de arranque: la cumbre sin sol, el sol y su halo.

    Las tres comparten escala: 512 px equivalen a las 64 unidades del símbolo, y antu.script las escala juntas.
    """
    ply = ROOT/"files/system/usr/share/plymouth/themes/antu"
    symbol_png(512, sun=False).save(ply/"cumbre.png", optimize=True)
    n, r = 96 * 4, 5.5 / 64 * 512 * 4  # sol: 88 px de diámetro en un lienzo de 96, con supermuestreo
    sun = Image.new("RGBA", (n, n))
    ImageDraw.Draw(sun).ellipse((n/2-r, n/2-r, n/2+r, n/2+r), fill=LAVA)
    sun.resize((96, 96), Image.Resampling.LANCZOS).save(ply/"sol.png", optimize=True)
    # Halo: degradado radial suave que se apaga antes del borde, para que nunca se vea el cuadrado.
    dist = Image.radial_gradient("L").resize((512, 512), Image.Resampling.BICUBIC)
    alpha = dist.point(lambda v: round(255 * 0.75 * max(0.0, 1 - v / 250) ** 2.4))
    halo = Image.new("RGBA", (512, 512), LAVA)
    halo.putalpha(alpha)
    halo.save(ply/"halo.png", optimize=True)
    # Estrella: punto suave blanco azulado; antu.script la escala a tres tamaños.
    star = Image.new("RGBA", (32, 32), "#E8EEFF")
    star.putalpha(Image.radial_gradient("L").resize((32, 32), Image.Resampling.BICUBIC)
                  .point(lambda v: round(255 * max(0.0, 1 - v / 128) ** 1.5)))
    star.save(ply/"estrella.png", optimize=True)
    # Horizonte: línea de luz cálida, intensa al centro y que se apaga hacia los lados y arriba y abajo.
    hw, hh = 1024, 48
    line = Image.new("L", (hw, hh))
    line.putdata([round(255 * max(0.0, 1 - abs(x - hw/2) / (hw/2)) ** 1.6 * 2.718 ** -(((y - hh/2) / 5) ** 2))
                  for y in range(hh) for x in range(hw)])
    horizon = Image.new("RGBA", (hw, hh), "#FF8A3D")
    horizon.putalpha(line)
    horizon.save(ply/"horizonte.png", optimize=True)
    # Noche: tapa todo lo que queda bajo el horizonte, para que el sol nazca detrás de él.
    Image.new("RGBA", (1, 1), "#000000").save(ply/"noche.png")
    Image.new("RGBA", (1, 1), TRACK).save(ply/"track.png")
    Image.new("RGBA", (1, 1), LAVA).save(ply/"fill.png")


def logo(width, light=False):
    height = round(width / 3)
    im = Image.new("RGBA", (width, height))
    symbol = symbol_png(round(height * 0.80), light)
    f, d = font(round(height * 0.68), 600), ImageDraw.Draw(im)
    box = d.textbbox((0, 0), "Antu", font=f)
    ww, wh, gap = box[2]-box[0], box[3]-box[1], round(height*0.10)
    x = round((width-symbol.width-gap-ww)/2)
    im.alpha_composite(symbol, (x, round((height-symbol.height)/2-height*0.018)))
    d.text((x+symbol.width+gap-box[0], (height-wh)/2-box[1]+height*0.018),
           "Antu", font=f, fill=OBSIDIAN if light else INK)
    return im


def export_icons():
    for name in NAMES:
        for size in SIZES:
            src = Image.open(MASTERS/name/f"{size}.png").convert("RGBA")
            if src.width < size or src.height < size:
                raise ValueError(f"Refusing to upscale {name} {size}")
            # Each small source is a separate 3D render with optical geometry edits.
            out = src.resize((size, size), Image.Resampling.LANCZOS) if src.size != (size, size) else src
            dest = ROOT / f"files/system/usr/share/icons/hicolor/{size}x{size}/apps/{name}.png"
            dest.parent.mkdir(parents=True, exist_ok=True)
            out.save(dest, optimize=True)
            if size in (16, 32, 64, 256):
                p = PREVIEW / "icons" / f"{name}-{size}.png"
                p.parent.mkdir(parents=True, exist_ok=True)
                out.save(p)
    shutil.copyfile(ROOT/"files/system/usr/share/icons/hicolor/256x256/apps/antu.png", ROOT/"brand/antu-icon-256.png")
    raster = (ROOT/"files/system/usr/share/icons/hicolor/1024x1024/apps/antu.png").read_bytes()
    # Raster container for the README; only the tiny symbol uses vector artwork.
    encoded = base64.b64encode(raster).decode("ascii")
    write(ROOT/"brand/antu-icon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">\n'
          f'  <image width="1024" height="1024" href="data:image/png;base64,{encoded}"/>\n</svg>\n')


def previews():
    PREVIEW.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (1440, 930), OBSIDIAN)
    d = ImageDraw.Draw(sheet)
    d.text((52, 36), "ANTU / MATERIAL Y LUZ", font=font(27, 600), fill=INK)
    d.text((52, 80), "Tamaños reales · 16 / 32 / 64 / 256 px", font=font(19), fill="#C7C7CC")
    for i, name in enumerate(NAMES):
        x = 52+i*280
        d.text((x, 140), name, font=font(19), fill=INK)
        for size, y in [(16, 205), (32, 275), (64, 365), (256, 520)]:
            icon = Image.open(PREVIEW/"icons"/f"{name}-{size}.png")
            sheet.paste(icon, (x, y), icon)
            d.text((x, y+size+12), f"{size} px · 1:1", font=font(15), fill="#C7C7CC")
    d.text((52, 866), "Obsidiana / plata anodizada / esmalte lava   ·   Másteres 4096 × 4096", font=font(18), fill="#C7C7CC")
    sheet.save(PREVIEW/"icon-family.png")
    sym = Image.new("RGB", (1400, 750), OBSIDIAN)
    sd = ImageDraw.Draw(sym)
    sd.rectangle((700, 0, 1400, 750), fill=INK)
    for light in (False, True):
        ox, color = (700, OBSIDIAN) if light else (0, INK)
        sd.text((ox+40, 30), "CUMBRE / NÚCLEO SOLAR", font=font(23, 600), fill=color)
        for size, x in [(16, 50), (24, 145), (32, 240), (48, 350), (256, 425)]:
            im = symbol_png(size, light)
            folder = PREVIEW/"symbols"
            folder.mkdir(exist_ok=True)
            im.save(folder/f"symbol-{'light' if light else 'dark'}-{size}.png")
            sym.paste(im, (ox+x, 130), im)
            sd.text((ox+x, 130+size+16), str(size), font=font(16), fill=color)
        mark = symbol_png(16, light).resize((192, 192), Image.Resampling.NEAREST)
        sym.paste(mark, (ox+50, 475), mark)
        sd.text((ox+270, 550), "16 px / ampliación ×12\npara revisar la retícula", font=font(20), fill=color)
    sym.save(PREVIEW/"symbol-sizes.png")
    lockups = Image.new("RGB", (1440, 720), OBSIDIAN)
    lockups.paste(INK, (0, 360, 1440, 720))
    for light, y in [(False, 20), (True, 380)]:
        im = logo(960, light)
        lockups.paste(im, (240, y), im)
    lockups.save(PREVIEW/"logo-variants.png")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--render", action="store_true")
    a = p.parse_args()
    if a.render:
        blender = os.environ.get("BLENDER_BIN") or shutil.which("blender")
        if not blender:
            raise SystemExit("Set BLENDER_BIN to Blender 5.x.")
        subprocess.run([blender, "-b", "-t", "8", "--python-exit-code", "1", "-P", str(ROOT/"scripts/render_art.py"), "--", "icons"], check=True)
    write(ROOT/"files/system/usr/share/antu/antu-symbol.svg", symbol_svg())
    write(ROOT/"files/system/usr/share/antu/antu-symbol-light.svg", symbol_svg(True))
    for light, suffix in [(False, ""), (True, "-light")]:
        logo(2400, light).save(ROOT/f"brand/antu-logo{suffix}.png", optimize=True)
        logo(3840, light).save(ROOT/f"brand/antu-logo{suffix}-4k.png", optimize=True)
    plymouth()
    export_icons()
    previews()
    print("Exact symbol, Inter lockups, native optical icons and the Plymouth sunrise exported.")


if __name__ == "__main__":
    main()
