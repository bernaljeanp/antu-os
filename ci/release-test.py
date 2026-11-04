#!/usr/bin/env python3
"""Firma, alteración y recomposición con datos pequeños y una llave efímera, nunca la de Antu."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


publisher = load("publisher", "scripts/preparar-release.py")
downloader = load("downloader", "scripts/descargar-antu.py")


@unittest.skipUnless(shutil.which("openssl"), "requiere OpenSSL")
class Publicacion(unittest.TestCase):
    def test_firma_recomposicion_y_rechazo_de_manipulacion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); key = root / "efimera.pem"; public = root / "efimera.pub"
            subprocess.run(["openssl", "genpkey", "-algorithm", "EC", "-pkeyopt", "ec_paramgen_curve:P-256", "-out", str(key)], check=True, capture_output=True)
            subprocess.run(["openssl", "pkey", "-in", str(key), "-pubout", "-out", str(public)], check=True, capture_output=True)
            iso = root / "original.iso"; iso.write_bytes(bytes(range(256)) * 100)
            output = root / "release"
            result = publisher.prepare(iso, output, "a" * 40, "sha256:" + "b" * 64, key, 5000, public)
            with patch.object(downloader, "PUBLIC_KEY", public.read_bytes()):
                verified = downloader.verify(output / "release.json", output / "release.json.sig", root)
                target = root / "descargada.iso"
                downloader.assemble(verified, output, target)
                self.assertEqual(target.read_bytes(), iso.read_bytes())
                with self.assertRaises(FileExistsError):
                    downloader.assemble(verified, output, target)
                first = output / result["parts"][0]["name"]; first.write_bytes(b"alterada")
                with self.assertRaises(ValueError):
                    downloader.assemble(verified, output, root / "otra.iso")
                self.assertFalse((root / "otra.iso").exists())
                manifest = output / "release.json"; manifest.write_text(manifest.read_text() + " ")
                with self.assertRaises(subprocess.CalledProcessError):
                    downloader.verify(manifest, output / "release.json.sig", root)

    def test_llave_publica_del_descargador_es_la_de_la_distro(self):
        self.assertEqual(b"".join(downloader.PUBLIC_KEY.splitlines()), b"".join((REPO / "files/system/etc/pki/containers/antu.pub").read_bytes().splitlines()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
