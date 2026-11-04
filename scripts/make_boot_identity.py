"""Título estático a doble resolución; no regenera la secuencia ni el arte aprobado."""
from PIL import Image, ImageDraw, ImageFont
from make_brand import FONT, ROOT

text = "ANTU OS"
font = ImageFont.truetype(str(FONT), 152)
font.set_variation_by_axes([32, 700])
image = Image.new("RGBA", (1280, 220))
draw = ImageDraw.Draw(image)
width = sum(font.getlength(char) + 40 for char in text) - 40
x = (1280 - width) / 2
for char in text:
    draw.text((x, 0), char, font=font, fill="#F5F5F7")
    x += font.getlength(char) + 40
image.save(ROOT / "files/system/usr/share/plymouth/themes/antu/titulo-estatico-2x.png", optimize=True)
