#!/usr/bin/env python3
"""Empaqueta PNG aprobados en ICO, sin redibujar ni reescalar ningún píxel."""
from pathlib import Path
import struct

sizes = (16, 32, 48, 64, 128, 256)
images = [(size, Path(f"files/system/usr/share/icons/hicolor/{size}x{size}/apps/antu.png").read_bytes()) for size in sizes]
offset = 6 + 16 * len(images)
entries = []
for size, data in images:
    entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
    offset += len(data)
Path("build-descarga").mkdir(exist_ok=True)
Path("build-descarga/antu.ico").write_bytes(struct.pack("<HHH", 0, 1, len(images)) + b"".join(entries) + b"".join(data for _, data in images))
