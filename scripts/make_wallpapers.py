"""Package original Antu landscapes. The old flat hill painter is retired.

python scripts/make_wallpapers.py                  # package approved 4K masters
python scripts/make_wallpapers.py --superresolve --upscaler /path/to/realesrgan-ncnn-vulkan
Requires Pillow. Optional reconstruction: official Real-ESRGAN ncnn Vulkan.
Frozen image_gen originals: brand/sources/wallpapers. The owner approved 4K
superresolution explicitly; these wallpaper masters are NOT native 4K renders.
The default export never repaints or regenerates these masters. CC-BY-SA-4.0.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
MASTERS = ROOT/"brand/masters/wallpapers"
PREVIEWS = ROOT/"brand/previews/wallpapers"
FONT = ROOT/"files/system/usr/share/fonts/antu/Inter-Variable.ttf"
PACKAGES = {
    "Antu": "Obsidiana volcánica, luz de lava y cielo del desierto.",
    "Paranal": "Cumbre del desierto y observatorios imaginarios bajo las estrellas.",
    "Salar": "Sal mineral, aire del altiplano y primera luz del amanecer.",
}


def superresolve(binary, work_dir=None):
    binary = Path(binary).resolve()
    model_path = binary.parent/"models"
    if not binary.is_file() or not (model_path/"realesrgan-x4plus.bin").is_file():
        raise ValueError("Use the official Real-ESRGAN executable and its sibling models directory.")
    MASTERS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="antu-superresolution-", dir=work_dir) as work:
        for name in PACKAGES:
            for variant in ("dark", "light"):
                source = ROOT/f"brand/sources/wallpapers/{name}-{variant}.png"
                dest = MASTERS/f"{name}-{variant}-3840x2160.png"
                if dest.exists():
                    print("Preserving approved 4K master:", dest.name, flush=True)
                    continue
                raw = Path(work)/f"{name}-{variant}-x4.png"
                print("Superresolution:", source.name, flush=True)
                result = subprocess.run([str(binary), "-i", str(source), "-o", str(raw),
                                         "-m", str(model_path), "-n", "realesrgan-x4plus",
                                         "-s", "4", "-t", "128", "-j", "1:1:1"],
                                        capture_output=True, text=True)
                if result.returncode:
                    raise RuntimeError(result.stderr[-4000:])
                image = Image.open(raw).convert("RGB")
                if image.width < 3840 or image.height < 2160:
                    raise ValueError("Upscaler output is smaller than the production frame.")
                ImageOps.fit(image, (3840, 2160), Image.Resampling.LANCZOS).save(dest, optimize=True)
                print("4K master:", dest.name, flush=True)


def preview(im, title, dest):
    # Review proof only. Production JPEGs contain no text, panels or dock.
    out = im.resize((1600, 900), Image.Resampling.LANCZOS).convert("RGB")
    rect = (490, 160, 1110, 740)
    mask = Image.new("L", out.size)
    ImageDraw.Draw(mask).rounded_rectangle(rect, 32, fill=255)
    glass = out.filter(ImageFilter.GaussianBlur(22))
    glass = Image.blend(glass, Image.new("RGB", out.size, "#0B0B0E"), 0.72)
    out.paste(glass, (0, 0), mask)
    d = ImageDraw.Draw(out)
    f = lambda size: ImageFont.truetype(str(FONT), size)
    d.rounded_rectangle(rect, 32, outline=(101, 101, 108), width=1)
    d.text((550, 220), "Antu", font=f(48), fill="#F5F5F7")
    d.text((550, 300), "Desde los cielos más claros\nde la Tierra", font=f(29), fill="#F5F5F7", spacing=8)
    d.text((550, 435), "Inicia tu próxima partida.", font=f(22), fill="#C7C7CC")
    d.rounded_rectangle((550, 565, 1050, 623), 14, fill="#FF5A1F")
    d.text((590, 578), "Continuar", font=f(23), fill="#0B0B0E")
    d.rounded_rectangle((618, 830, 982, 884), 18, fill=(18, 18, 22), outline=(63, 63, 68))
    names = ("antu", "antu-inicio", "antu-instalador", "antu-eclipse", "antu-ia")
    for i, name in enumerate(names):
        p = ROOT/f"files/system/usr/share/icons/hicolor/32x32/apps/{name}.png"
        if p.exists():
            icon = Image.open(p)
            out.paste(icon, (642+i*66, 841), icon)
    d.text((36, 34), title+" / prueba de vidrio", font=f(22), fill="#F5F5F7")
    d.text((36, 856), "Vista de revisión · arte final sin texto ni paneles", font=f(16), fill="#C7C7CC")
    out.save(dest, quality=92)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--superresolve", action="store_true")
    p.add_argument("--upscaler", default=os.environ.get("REAL_ESRGAN_BIN"))
    p.add_argument("--work-dir", default=None)
    a = p.parse_args()
    if a.superresolve:
        if not a.upscaler:
            raise SystemExit("Set REAL_ESRGAN_BIN or pass --upscaler. No binary is downloaded automatically.")
        superresolve(a.upscaler, a.work_dir)
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    for name, description in PACKAGES.items():
        pkg = ROOT/f"files/system/usr/share/wallpapers/{name}"
        pkg.mkdir(parents=True, exist_ok=True)
        meta = {"KPlugin": {"Authors": [{"Name": "Antu OS"}], "Id": name,
                            "License": "CC-BY-SA-4.0", "Name": name, "Description": description}}
        (pkg/"metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=4)+"\n", encoding="utf-8", newline="\n")
        for variant, folder in [("dark", "images_dark"), ("light", "images")]:
            source = MASTERS/f"{name}-{variant}-3840x2160.png"
            im = Image.open(source).convert("RGB")
            if im.size != (3840, 2160):
                raise ValueError(f"Expected approved 3840x2160 master: {source}: {im.size}")
            dest = pkg/"contents"/folder
            dest.mkdir(parents=True, exist_ok=True)
            for w, h in [(3840, 2160), (2560, 1600)]:
                image = im if (w, h) == im.size else ImageOps.fit(im, (w, h), Image.Resampling.LANCZOS)
                path = dest/f"{w}x{h}.jpg"
                image.save(path, quality=90, subsampling=0, optimize=True, progressive=True)
                if path.stat().st_size >= 4_000_000:
                    raise ValueError(f"Wallpaper exceeds 4 MB at JPEG quality 90: {path}")
                print(path.relative_to(ROOT), path.stat().st_size)
            preview(im, f"{name} / {'oscuro' if variant == 'dark' else 'claro'}", PREVIEWS/f"{name}-{variant}-glass.jpg")
            if variant == "dark":
                im.resize((960, 540), Image.Resampling.LANCZOS).save(pkg/"contents/screenshot.png", optimize=True)
        if name == "Antu":
            for folder in ("images", "images_dark"):
                (pkg/"contents"/folder/"3840x2160.png").unlink(missing_ok=True)
    thumbs = Image.new("RGB", (1920, 1620), "#0B0B0E")
    for row, name in enumerate(PACKAGES):
        for col, variant in enumerate(("dark", "light")):
            im = Image.open(PREVIEWS/f"{name}-{variant}-glass.jpg").resize((960, 540), Image.Resampling.LANCZOS)
            thumbs.paste(im, (col*960, row*540))
    thumbs.save(ROOT/"brand/previews/wallpaper-family.jpg", quality=92)


if __name__ == "__main__":
    main()
