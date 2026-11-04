#!/usr/bin/env python3
"""Descarga y recompone Antu desde una versión pública. Requiere Python 3 y OpenSSL.

Ejemplo: python descargar-antu.py --tag ETIQUETA --output antu-live.iso
La firma del manifiesto y todos los hashes se verifican antes de entregar la ISO.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.parse
import urllib.request

REPO = "bernaljeanp/antu-os"
PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEZtw8AwwnKbk+l0cxS7u0yNDlQ8Su
RpZIUmDrfU9lRn7q3BaHCCOxmd9a4qgVXssHz3X/Zj2IycNjItcp/Kw+Yg==
-----END PUBLIC KEY-----
"""


def fetch(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "Antu-Downloader/1"})
    with urllib.request.urlopen(request, timeout=90) as source, Path(path).open("wb") as target:
        shutil.copyfileobj(source, target, length=1024**2)


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def verify(manifest, signature, directory):
    key = Path(directory) / "antu-confianza.pub"; key.write_bytes(PUBLIC_KEY)
    subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(key), "-signature", str(signature), str(manifest)], check=True)
    data = json.loads(Path(manifest).read_text())
    if data.get("schema") != 1 or data.get("filename") != "antu-live.iso" or not re.fullmatch(r"[a-f0-9]{64}", data.get("sha256", "")):
        raise ValueError("Manifiesto no válido.")
    parts = data.get("parts")
    if not isinstance(parts, list) or not 1 <= len(parts) <= 32:
        raise ValueError("Lista de partes no válida.")
    for index, item in enumerate(parts, 1):
        if item.get("name") != f"antu-live.iso.parte-{index:02d}" or not re.fullmatch(r"[a-f0-9]{64}", item.get("sha256", "")) or type(item.get("size")) is not int or not 0 < item["size"] <= 2 * 1024**3:
            raise ValueError("Parte no válida.")
    if sum(item["size"] for item in parts) != data.get("size"):
        raise ValueError("Tamaño total no válido.")
    return data


def assemble(data, directory, output):
    output = Path(output)
    if output.exists():
        raise FileExistsError("El destino ya existe. No se sobrescribe: " + str(output))
    fd, temporary = tempfile.mkstemp(prefix=".antu-", suffix=".partial", dir=output.parent)
    import os
    try:
        with os.fdopen(fd, "wb") as target:
            for part in data["parts"]:
                path = Path(directory) / part["name"]
                if path.stat().st_size != part["size"] or digest(path) != part["sha256"]:
                    raise ValueError("Parte incompleta o alterada: " + part["name"])
                with path.open("rb") as source:
                    shutil.copyfileobj(source, target, length=1024**2)
            target.flush(); os.fsync(target.fileno())
        if digest(temporary) != data["sha256"]:
            raise ValueError("La ISO recompuesta no coincide con la firma del manifiesto.")
        # link crea el destino de forma exclusiva; un archivo creado mientras se descargaba no se pierde.
        os.link(temporary, output)
        Path(temporary).unlink()
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True); parser.add_argument("--output", type=Path, default=Path("antu-live.iso"))
    args = parser.parse_args()
    if not shutil.which("openssl"):
        parser.error("Necesitas OpenSSL para comprobar la firma. No se descarga una ISO sin verificarla.")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,100}", args.tag):
        parser.error("Etiqueta no válida.")
    args.output = args.output.resolve()
    if args.output.exists():
        parser.error("El archivo de salida ya existe. Elige otro nombre.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    directory = args.output.parent / (".antu-descarga-" + args.tag)
    directory.mkdir(exist_ok=True)
    base = f"https://github.com/{REPO}/releases/download/{urllib.parse.quote(args.tag)}/"
    manifest, signature = directory / "release.json", directory / "release.json.sig"
    fetch(base + manifest.name, manifest); fetch(base + signature.name, signature)
    data = verify(manifest, signature, directory)
    if shutil.disk_usage(args.output.parent).free < data["size"] * 2 + 1024**3:
        raise ValueError("Necesitas espacio para las partes y la ISO: aproximadamente el doble de su tamaño más 1 GB.")
    for index, part in enumerate(data["parts"], 1):
        path = directory / part["name"]
        if not path.exists() or path.stat().st_size != part["size"] or digest(path) != part["sha256"]:
            print(f"Descargando parte {index}/{len(data['parts'])}: {part['size'] / 10**6:.0f} MB", flush=True)
            fetch(base + part["name"], path)
        if digest(path) != part["sha256"]:
            raise ValueError("La descarga no superó la comprobación: " + part["name"])
    assemble(data, directory, args.output)
    print("Firma y SHA-256 verificados. ISO lista:", args.output)
    print("Puedes borrar las partes conservadas en", directory)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
