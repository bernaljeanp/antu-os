"""Dibuja los recursos de la pantalla de arranque de Antu (Plymouth): marca centrada y barra fina de lava.

Uso: python scripts/make_plymouth.py   (requiere Pillow)
Los recursos se dibujan para una pantalla de 1600 px de alto; antu.script los escala a la pantalla real.
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent.parent
OUT = ROOT / "files/system/usr/share/plymouth/themes/antu"
FONT = ROOT / "files/system/usr/share/fonts/antu/Inter-Variable.ttf"
SS = 4  # supermuestreo

INK, TRACK, LAVA = "#F5F5F7", "#2E2E33", "#FF5A1F"


def text(label, size, weight, color, name):
    font = ImageFont.truetype(str(FONT), size * SS)
    font.set_variation_by_axes([32, weight])  # ejes del archivo: opsz, wght
    left, top, right, bottom = font.getbbox(label)
    img = Image.new("RGBA", (right - left + 2 * SS, bottom - top + 2 * SS), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((SS - left, SS - top), label, font=font, fill=color)
    img.resize((img.width // SS, img.height // SS), Image.LANCZOS).save(OUT / name)


def pixel(color, name):
    Image.new("RGBA", (1, 1), color).save(OUT / name)


if __name__ == "__main__":
    for old in OUT.glob("*.png"):  # recursos de versiones anteriores del tema
        old.unlink()
    text("antu", 112, 700, INK, "wordmark.png")
    pixel(TRACK, "track.png")
    pixel(LAVA, "fill.png")
    print("recursos en", OUT.relative_to(ROOT))
