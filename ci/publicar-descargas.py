#!/usr/bin/env python3
"""Añade descargadores probados únicamente a una entrega que ya contiene una ISO firmada."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--version", required=True)
parser.add_argument("--key", required=True)
args = parser.parse_args()
if not re.fullmatch(r"antu-preview-[A-Za-z0-9._-]{1,80}", args.version):
    raise SystemExit("Versión no válida.")
release = json.loads(subprocess.check_output(["gh", "release", "view", args.version, "--json", "isDraft,isPrerelease,assets"]))
assert not release["isDraft"] and release["isPrerelease"], "Solo se amplía una entrega de prueba publicada"
assert {"release.json", "release.json.sig"} <= {a["name"] for a in release["assets"]}
out = Path("descarga-publicar"); out.mkdir()
subprocess.run(["gh", "release", "download", args.version, "-p", "release.json*", "-D", str(out)], check=True)
spec = importlib.util.spec_from_file_location("engine", "scripts/descargar-antu.py")
engine = importlib.util.module_from_spec(spec); spec.loader.exec_module(engine)
engine.verify(out / "release.json", out / "release.json.sig", out)
files = []
for folder, name in (("windows", "Antu-Descargas-Windows.exe"), ("linux", "Antu-Descargas-Linux.tar.gz")):
    source = Path("descarga-" + folder) / "entrega-descarga" / name
    target = out / name; target.write_bytes(source.read_bytes())
    files.append({"name": name, "size": target.stat().st_size, "sha256": engine.digest(target)})
manifest = out / "descargas.json"
manifest.write_text(json.dumps({"schema": 1, "iso_version": args.version,
    "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "files": files}, indent=2) + "\n", newline="\n")
subprocess.run(["openssl", "dgst", "-sha256", "-sign", args.key, "-out", str(manifest) + ".sig", str(manifest)], check=True)
subprocess.run(["openssl", "dgst", "-sha256", "-verify", "files/system/etc/pki/containers/antu.pub",
                "-signature", str(manifest) + ".sig", str(manifest)], check=True)
subprocess.run(["gh", "release", "upload", args.version, *(str(out / f["name"]) for f in files),
                str(manifest), str(manifest) + ".sig"], check=True)
