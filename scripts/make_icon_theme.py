"""Package the new Antu system icon theme without changing approved Antu artwork.

python scripts/make_icon_theme.py --render  # native Blender scenes, then export
python scripts/make_icon_theme.py           # export existing scene renders
python scripts/make_icon_theme.py --check   # validate and record the installed theme
Requires Pillow. Rendering: Blender 5.2 via BLENDER_BIN or the system installation.
All new artwork: Antu OS, CC-BY-SA-4.0.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, PngImagePlugin

from antu_icon_catalog import ALIASES, CATALOG, CONTEXTS, SIZES
from make_brand import symbol_png

ROOT=Path(__file__).resolve().parent.parent
THEME=ROOT/"files/system/usr/share/icons/Antu"
MASTERS=ROOT/"brand/masters/icon-theme"
REVIEW=ROOT/"brand/previews/icon-theme"
DEFAULTS=[ROOT/f"files/system/usr/share/plasma/look-and-feel/{name}/contents/defaults"
          for name in ("org.antuos.desktop","org.antuos.mac")]


def metadata():
    meta=PngImagePlugin.PngInfo()
    meta.add_text("Author","Antu OS")
    meta.add_text("License","CC-BY-SA-4.0")
    meta.add_text("Copyright","Original Antu OS artwork; attribution required")
    return meta


def index():
    directories=[f"{size}x{size}/{context}" for size in SIZES for context in CATALOG]
    text=("[Icon Theme]\nName=Antu\n"
          "Comment=Obsidiana pulida, plata anodizada y luz de lava\n"
          "Inherits=breeze-dark,hicolor\nExample=folder\n"
          "X-KDE-License=CC-BY-SA-4.0\nDirectories="+",".join(directories)+"\n")
    for size in SIZES:
        for context in CATALOG:
            text+=f"\n[{size}x{size}/{context}]\nSize={size}\nType=Fixed\nContext={CONTEXTS[context]}\n"
    (THEME/"index.theme").write_text(text,encoding="utf-8",newline="\n")
    (THEME/"COPYING").write_text(
        "Antu system icon theme\nOriginal artwork © Antu OS.\n\n"
        "Licensed under Creative Commons Attribution-ShareAlike 4.0 International.\n"
        "SPDX-License-Identifier: CC-BY-SA-4.0\n"
        "https://creativecommons.org/licenses/by-sa/4.0/\n\n"
        "Attribution: Antu OS. Changes must be indicated and shared under the same license.\n"
        "No stock icons or third-party brand logos are included.\n",
        encoding="utf-8",newline="\n")


def export():
    # Check every source before writing the theme or selecting it in defaults.
    missing=[MASTERS/context/name/f"{size}.png" for context,icons in CATALOG.items()
             for name in icons if name not in ALIASES and name!="start-here" for size in SIZES
             if not (MASTERS/context/name/f"{size}.png").is_file()]
    if missing:raise SystemExit(f"{len(missing)} native optical renders missing. First: {missing[0]}. Run --render.")
    meta=metadata()
    for context,icons in CATALOG.items():
        for size in SIZES:
            dest=THEME/f"{size}x{size}"/context
            dest.mkdir(parents=True,exist_ok=True)
            for name in icons:
                if name in ALIASES:continue
                if name=="start-here":image=symbol_png(size)
                else:
                    source=Image.open(MASTERS/context/name/f"{size}.png").convert("RGBA")
                    if source.width<size or source.height<size:raise ValueError(f"Refusing upscale: {name} {size}")
                    image=source.resize((size,size),Image.Resampling.LANCZOS)
                image.save(dest/f"{name}.png",optimize=True,pnginfo=meta)
            for alias,original in ALIASES.items():
                if alias in icons:shutil.copyfile(dest/f"{original}.png",dest/f"{alias}.png")
    index()
    before="[kdeglobals][Icons]\nTheme=breeze-dark"
    after="[kdeglobals][Icons]\nTheme=Antu"
    for path in DEFAULTS:
        text=path.read_text(encoding="utf-8")
        if after not in text:
            if text.count(before)!=1:raise ValueError(f"Unexpected icon theme setting: {path}")
            path.write_text(text.replace(before,after,1),encoding="utf-8",newline="\n")


def check():
    cp=configparser.ConfigParser(interpolation=None)
    cp.read(THEME/"index.theme",encoding="utf-8")
    assert cp["Icon Theme"]["Name"]=="Antu"
    assert cp["Icon Theme"]["Inherits"]=="breeze-dark,hicolor"
    declared=cp["Icon Theme"]["Directories"].split(",")
    expected_dirs={f"{s}x{s}/{c}" for s in SIZES for c in CATALOG}
    assert set(declared)==expected_dirs and len(declared)==len(expected_dirs)
    records=[]
    for size in SIZES:
        for context,icons in CATALOG.items():
            folder=f"{size}x{size}/{context}"
            assert cp[folder]["Size"]==str(size)
            assert cp[folder]["Type"]=="Fixed" and cp[folder]["Context"]==CONTEXTS[context]
            assert {p.stem for p in (THEME/folder).glob("*.png")}==set(icons)
            for name in icons:
                path=THEME/folder/f"{name}.png"
                im=Image.open(path);im.load()
                assert im.mode=="RGBA" and im.size==(size,size),(path,im.mode,im.size)
                assert im.getextrema()[3]==(0,255),(path,"alpha")
                assert im.info.get("License")=="CC-BY-SA-4.0"
                assert im.getpixel((0,0))[3]==0 and im.getpixel((size-1,size-1))[3]==0
                records.append({"path":path.relative_to(ROOT).as_posix(),"size":size,
                                "context":context,"bytes":path.stat().st_size,
                                "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    for path in DEFAULTS:assert "[kdeglobals][Icons]\nTheme=Antu" in path.read_text(encoding="utf-8")
    assert len(records)==sum(len(v) for v in CATALOG.values())*len(SIZES)==464
    assert not any((THEME/d).exists() for d in ("actions","status","scalable"))
    for path in [THEME/"index.theme",THEME/"COPYING",*DEFAULTS]:assert b"\r" not in path.read_bytes()
    result={"theme":"Antu","icons":58,"png_files":464,"directories":32,"sizes":SIZES,
            "inherits":["breeze-dark","hicolor"],"license":"CC-BY-SA-4.0",
            "checks":"Names, dimensions, RGBA transparency, metadata, directory contexts, defaults and LF passed.",
            "runtime_limit":"Static validation on Windows; Linux/Dolphin session not executed.",
            "optical_edits":{
                "16":"Larger inlays, heavier strokes; 1 sheet in full trash; 5 keyboard columns; no thumbsticks or small screws.",
                "22":"Heavy strokes, larger app motif; remove film perforations, bin grooves and small device machining.",
                "24":"Heavy strokes, larger app motif; simplified graph, optical media, spreadsheet and terminal.",
                "32":"Intermediate stroke, enlarged marks; simplified small features, retained two-note music and folder silhouettes."},
            "assets":records}
    (ROOT/"brand/icon-theme-validation.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("Antu: 58 names × 8 sizes = 464 transparent PNGs; 32 fixed directories; validation passed.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--render",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args()
    if a.check:check();return
    if a.render:
        blender=os.environ.get("BLENDER_BIN") or shutil.which("blender")
        if not blender:
            found=list(Path("C:/Program Files/Blender Foundation").glob("Blender */blender.exe"))
            blender=str(sorted(found)[-1]) if found else None
        if not blender:raise SystemExit("Set BLENDER_BIN to Blender 5.2.")
        subprocess.run([blender,"-b","-t","8","--python-exit-code","1","-P",str(ROOT/"scripts/render_icon_theme.py"),"--"],check=True)
    export()
    from preview_icon_theme import create_previews
    create_previews()
    check()


if __name__=="__main__":main()
