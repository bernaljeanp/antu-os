#!/usr/bin/env python3
"""Ejecuta el empaquetado KDE real en una raíz temporal, sin tocar la sesión ni dispositivos."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("escritorio", REPO / "files/scripts/verificar-escritorio.py")
escritorio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(escritorio)


@unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "requiere Linux/bash para comprobar los enlaces reales")
class Integracion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="antu-escritorio-")
        cls.root = Path(cls.temp.name)
        shutil.copytree(REPO / "files/system", cls.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        subprocess.run(["bash", str(REPO / "files/scripts/kde-defaults.sh"), str(cls.root)], check=True)
        cls.system = escritorio.verificar(cls.root)
        (cls.root / "usr/share/antu/escritorio.json").write_text(json.dumps(cls.system), encoding="utf-8")
        shutil.copytree(REPO / "files/live", cls.root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_sistema_y_live_comparten_el_escritorio(self):
        live = escritorio.verificar(self.root, live=True)
        self.assertEqual(live["base_content_id"], self.system["content_id"])
        self.assertGreaterEqual(live["png_files_including_aliases"], 464)
        self.assertTrue((self.root / "usr/share/icons/Antu/32x32/places/inode-directory.png").is_symlink())
        self.assertEqual(live["style"], "not_checked_in_staging")

    def test_falla_si_falta_un_componente_compartido(self):
        path = self.root / "usr/lib/antu/inicio/AntuBackdrop.qml"
        before = path.read_bytes()
        try:
            path.unlink()
            with self.assertRaisesRegex(ValueError, "Falta en la imagen"):
                escritorio.verificar(self.root)
        finally:
            path.write_bytes(before)

    def test_falla_si_el_tema_no_se_selecciona(self):
        path = self.root / "etc/xdg/kdeglobals"
        before = path.read_text()
        try:
            path.write_text(before.replace("Theme=Antu", "Theme=breeze-dark"))
            with self.assertRaisesRegex(ValueError, "no es Antu"):
                escritorio.verificar(self.root)
        finally:
            path.write_text(before)

    def test_falla_si_el_live_cambia_la_base_sellada(self):
        path = self.root / "usr/lib/antu/inicio/Antu.qml"
        before = path.read_bytes()
        try:
            path.write_bytes(before + b"\n// diferencia de prueba\n")
            with self.assertRaisesRegex(ValueError, "difiere del escritorio"):
                escritorio.verificar(self.root, live=True)
        finally:
            path.write_bytes(before)

    def test_no_confunde_qt_del_anfitrion_con_la_imagen(self):
        with self.assertRaisesRegex(ValueError, "dentro de la imagen"):
            escritorio.verificar(self.root, runtime=True)


@unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "requiere Linux/bash")
class FiltrosISO(unittest.TestCase):
    def ejecutar(self, firma=True, revision="correcta", expected="correcta", image="registry.example:5000/antu:testing"):
        with tempfile.TemporaryDirectory(prefix="antu-iso-filtros-") as directory:
            root = Path(directory)
            tools = root / "bin"
            tools.mkdir()
            log = root / "calls"
            commands = {
                "id": "printf '0\\n'\n",
                "skopeo": 'printf "skopeo %s\\n" "$*" >> "$TEST_LOG"\n'
                          'if [ "$1" = inspect ]; then printf "sha256:abc\\n"; else exit "$TEST_SIGNATURE_EXIT"; fi\n',
                "podman": 'printf "podman %s\\n" "$*" >> "$TEST_LOG"\n'
                          'case "$*" in *usr/share/antu/revision) printf "%s\\n" "$TEST_REVISION";; '
                          '*usr/share/antu/escritorio.json) printf \'{"phase":"system","theme":"Antu","style":"kvantum_available","content_id":"prueba"}\\n\';; '
                          'build*) exit 73;; *) exit 90;; esac\n',
            }
            for name, body in commands.items():
                path = tools / name
                path.write_text("#!/bin/sh\n" + body)
                path.chmod(0o755)
            environment = dict(os.environ, PATH=str(tools) + os.pathsep + os.environ["PATH"],
                               TEST_LOG=str(log), TEST_REVISION=revision,
                               TEST_SIGNATURE_EXIT="0" if firma else "42", ANTU_EXPECTED_BASE_REVISION=expected)
            result = subprocess.run(["bash", str(REPO / "scripts/make-iso.sh"), image],
                                    cwd=root, env=environment, capture_output=True, text=True)
            calls = log.read_text() if log.exists() else ""
            policy = json.loads((root / "iso-build/politica.json").read_text())
            self.assertFalse((root / "iso-build/antu-live.iso").exists())
            return result, calls, policy

    def test_firma_invalida_no_ejecuta_la_imagen(self):
        result, calls, _ = self.ejecutar(firma=False)
        self.assertEqual(result.returncode, 42)
        self.assertNotIn("podman", calls)

    def test_revision_distinta_no_compila_el_live(self):
        result, calls, _ = self.ejecutar(revision="vieja")
        self.assertEqual(result.returncode, 1)
        self.assertIn("No se crea la ISO", result.stderr)
        self.assertNotIn("podman build", calls)

    def test_fija_digest_y_conserva_el_puerto_del_registro(self):
        for image in ("registry.example:5000/antu:testing", "registry.example:5000/antu@sha256:abc"):
            with self.subTest(image=image):
                result, calls, policy = self.ejecutar(image=image)
                self.assertEqual(result.returncode, 73)  # detenerse antes de una compilación real
                self.assertIn("BASE=registry.example:5000/antu@sha256:abc", calls)
                self.assertIn("registry.example:5000/antu", policy["transports"]["docker"])
                self.assertLess(calls.index("skopeo --policy"), calls.index("podman run"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
