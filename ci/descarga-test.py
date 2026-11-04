#!/usr/bin/env python3
"""Descargas por HTTP local, firmas reales y cancelación; sin ISO ni discos del usuario."""
import functools
import http.server
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gui", REPO / "scripts/descargar-antu-gui.py")
gui = importlib.util.module_from_spec(spec); spec.loader.exec_module(gui)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

    def do_GET(self):
        header = self.headers.get("Range")
        if not header:
            return super().do_GET()
        start = int(header.removeprefix("bytes=").removesuffix("-"))
        path = Path(self.translate_path(self.path))
        data = path.read_bytes()
        self.server.ranges.append((self.path, start))
        self.send_response(206)
        self.send_header("Content-Range", f"bytes {start}-{len(data) - 1}/{len(data)}")
        self.send_header("Content-Length", str(len(data) - start))
        self.end_headers(); self.wfile.write(data[start:])


class Descarga(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.served = self.root / "servidor"; self.served.mkdir()
        self.out = self.root / "destino"; self.out.mkdir()
        self.tag = "antu-preview-ensayo"
        self.assets = self.served / "download" / self.tag; self.assets.mkdir(parents=True)
        self.original = bytes(range(256)) * 300
        parts = []
        for number, start in enumerate(range(0, len(self.original), 20000), 1):
            data = self.original[start:start + 20000]; name = f"antu-live.iso.parte-{number:02d}"
            (self.assets / name).write_bytes(data)
            parts.append({"name": name, "size": len(data), "sha256": gui.engine.digest(self.assets / name)})
        import hashlib
        manifest = json.dumps({"schema": 1, "filename": "antu-live.iso", "size": len(self.original),
                              "sha256": hashlib.sha256(self.original).hexdigest(), "parts": parts}).encode()
        (self.assets / "release.json").write_bytes(manifest)
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.public = self.key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        (self.assets / "release.json.sig").write_bytes(self.key.sign(manifest, ec.ECDSA(hashes.SHA256())))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(self.served)))
        self.server.ranges = []
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.patches = [patch.object(gui, "RELEASES", f"http://127.0.0.1:{self.server.server_port}"),
                        patch.object(gui.engine, "PUBLIC_KEY", self.public)]
        for item in self.patches: item.start()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.temp.cleanup()

    def test_descarga_firma_y_recomposicion_sin_openssl_externo(self):
        target = self.out / "antu.iso"; progress = []
        with patch.object(gui.engine.subprocess, "run", side_effect=AssertionError("No se permiten programas externos")):
            result = gui.download(self.tag, target, lambda *p: progress.append(p), threading.Event())
        self.assertEqual(result, target.resolve())
        self.assertEqual(target.read_bytes(), self.original)
        self.assertTrue(any("Reuniendo" in p[0] for p in progress))
        with self.assertRaises(FileExistsError):
            gui.download(self.tag, target, lambda *_: None, threading.Event())

    def test_firma_manipulada_no_entrega_iso(self):
        with (self.assets / "release.json").open("ab") as f: f.write(b" ")
        target = self.out / "antu.iso"
        with self.assertRaisesRegex(ValueError, "firma"):
            gui.download(self.tag, target, lambda *_: None, threading.Event())
        self.assertFalse(target.exists())
        self.assertFalse(list(self.out.glob(".antu-descarga-*/*.parte-*")))

    def test_cancelar_y_reanudar_conserva_partes_validas(self):
        cancel = threading.Event(); target = self.out / "antu.iso"
        def progress(text, *_):
            if "Comprobando parte 2" in text: cancel.set()
        with self.assertRaises(gui.Cancelled):
            gui.download(self.tag, target, progress, cancel)
        self.assertFalse(target.exists())
        first = self.out / (".antu-descarga-" + self.tag) / "antu-live.iso.parte-01"
        before = first.stat().st_mtime_ns
        gui.download(self.tag, target, lambda *_: None, threading.Event())
        self.assertEqual(first.stat().st_mtime_ns, before)
        self.assertEqual(target.read_bytes(), self.original)

    def test_limite_de_descarga_corta_respuesta_excesiva(self):
        url = f"http://127.0.0.1:{self.server.server_port}/download/{self.tag}/release.json"
        with self.assertRaisesRegex(ValueError, "tamaño"):
            gui.engine.fetch(url, self.out / "exceso", limit=1)

    def test_reanuda_parte_interrumpida_y_rechaza_prefijo_alterado(self):
        directory = self.out / (".antu-descarga-" + self.tag); directory.mkdir()
        first = directory / "antu-live.iso.parte-01"
        first.write_bytes(self.original[:4000])
        target = self.out / "antu.iso"
        gui.download(self.tag, target, lambda *_: None, threading.Event())
        self.assertEqual(target.read_bytes(), self.original)
        self.assertEqual(self.server.ranges, [(f"/download/{self.tag}/antu-live.iso.parte-01", 4000)])
        first.write_bytes(b"x" * 4000)
        with self.assertRaisesRegex(ValueError, "parte"):
            gui.download(self.tag, self.out / "otra.iso", lambda *_: None, threading.Event())
        self.assertFalse((self.out / "otra.iso").exists())
        gui.download(self.tag, self.out / "otra.iso", lambda *_: None, threading.Event())
        self.assertEqual((self.out / "otra.iso").read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
