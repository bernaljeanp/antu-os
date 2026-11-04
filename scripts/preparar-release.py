#!/usr/bin/env python3
"""Divide la ISO para GitHub Releases y firma un manifiesto con la llave de Antu de CI."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

CHUNK = 1900 * 1024**2  # GitHub limita cada recurso; la ISO se recompone y verifica sin modificarla.


def prepare(iso, output, revision, digest, key, chunk_size=CHUNK, public=None):
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("Revisión no válida.")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise ValueError("Digest de imagen no válido.")
    iso, output, key = Path(iso), Path(output), Path(key)
    output.mkdir(parents=True, exist_ok=True)
    whole, parts = hashlib.sha256(), []
    with iso.open("rb") as source:
        index = 1
        while True:
            first = source.read(min(1024**2, chunk_size))
            if not first:
                break
            path = output / f"antu-live.iso.parte-{index:02d}"
            part, size = hashlib.sha256(), 0
            with path.open("wb") as dest:
                data = first
                while data:
                    dest.write(data); part.update(data); whole.update(data); size += len(data)
                    data = source.read(min(1024**2, chunk_size - size)) if size < chunk_size else b""
            parts.append({"name": path.name, "size": size, "sha256": part.hexdigest()})
            index += 1
    if not parts:
        raise ValueError("La ISO está vacía.")
    manifest = {"schema": 1, "status": "preview", "revision": revision, "image_digest": digest,
                "filename": "antu-live.iso", "size": iso.stat().st_size, "sha256": whole.hexdigest(), "parts": parts}
    path = output / "release.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    subprocess.run(["openssl", "dgst", "-sha256", "-sign", str(key), "-out", str(path) + ".sig", str(path)], check=True)
    public = public or Path(__file__).resolve().parents[1] / "files/system/etc/pki/containers/antu.pub"
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(public), "-signature", str(path) + ".sig", str(path)], check=True)
    shutil.copyfile(public, output / "antu.pub")
    shutil.copyfile(Path(__file__).with_name("descargar-antu.py"), output / "descargar-antu.py")
    (output / "antu-live.iso.sha256").write_text(whole.hexdigest() + "  antu-live.iso\n", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", required=True); parser.add_argument("--output", required=True)
    parser.add_argument("--revision", required=True); parser.add_argument("--digest", required=True)
    parser.add_argument("--key", required=True)
    args = parser.parse_args()
    result = prepare(args.iso, args.output, args.revision, args.digest, args.key)
    print(json.dumps({k: v for k, v in result.items() if k != "parts"}))
