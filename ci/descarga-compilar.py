#!/usr/bin/env python3
"""Rutas absolutas para PyInstaller, también con unidades y nombres largos de Windows."""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "Antu-Descargas", "--icon", str(repo / "build-descarga/antu.ico"),
        "--distpath", str(repo / "entrega-descarga"), "--workpath", str(repo / "build-descarga"),
        "--specpath", str(repo / "build-descarga")]
for source, destination in [("scripts/descargar-antu.py", "."), ("brand/antu-icon-256.png", "."),
                            ("files/system/usr/share/fonts/antu/Inter-Variable.ttf", "."),
                            ("files/system/usr/share/fonts/antu/Inter-OFL.txt", "licencias"), ("LICENSE", "licencias")]:
    args += ["--add-data", str(repo / source) + ":" + destination]
for module in ("argparse", "hashlib", "subprocess", "tempfile", "urllib.parse"):
    args += ["--hidden-import", module]
args += ["--copy-metadata", "PyQt6", "--copy-metadata", "cryptography", str(repo / "scripts/descargar-antu-gui.py")]
subprocess.run(args, check=True)
