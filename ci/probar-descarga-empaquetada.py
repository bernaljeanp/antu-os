#!/usr/bin/env python3
"""Prueba el ejecutable real; la captura y el resultado deben existir y ser nuevos."""
import json
import os
from pathlib import Path
import subprocess

binary = Path("entrega-descarga/Antu-Descargas" + (".exe" if os.name == "nt" else ""))
output = Path(os.environ.get("ANTU_CAPTURAS", "capturas-descarga"))
output.mkdir(exist_ok=True)
report = output / "descarga-prueba.json"
report.unlink(missing_ok=True)
process = subprocess.Popen([str(binary.resolve()), "--autoprueba"])
try:
    result = process.wait(timeout=90)
    assert result == 0, f"La aplicación terminó con {result}"
    data = json.loads(report.read_text())
    assert data == {"firma": "correcta", "alteracion": "rechazada", "demo": True}, data
    # PNG: dimensiones físicas en IHDR, sin añadir Pillow a la aplicación.
    import struct
    image = (output / "descarga-4k.png").read_bytes()
    assert struct.unpack(">II", image[16:24]) == (3840, 2160)
    print("Aplicación empaquetada: abre, verifica firmas y rechaza alteraciones; captura 4K correcta.")
finally:
    if process.poll() is None:
        process.terminate(); process.wait(timeout=10)

version = os.environ.get("ANTU_VERSION")
if version and os.name != "nt":
    # La ISO viaja entre servidores de CI: no consume la conexión del equipo del usuario.
    env = dict(os.environ, ANTU_ISO_PRUEBA=str(Path("prueba-publica/antu.iso").resolve()))
    subprocess.run([str(binary.resolve()), "--verificar-version", version], env=env, check=True, timeout=900)
    report = json.loads((output / "descarga-publica.json").read_text())
    assert report["version"] == version and report["firma"] == "verificada" and report["bytes"] > 1024**3
    print("Descarga pública completa: firma, partes y SHA-256 de la ISO verificados por el ejecutable real.")
