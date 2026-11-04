#!/usr/bin/env python3
"""Datos reales en directorios temporales; nunca usa discos del anfitrión."""
import importlib.util
from importlib.machinery import SourceFileLoader
import hashlib
import fcntl
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "files/system/usr/lib/antu/centro"))
from catalogo import seleccionar
from rendimiento import analizar, comparar
from respaldo import Restic, destination

spec = importlib.util.spec_from_file_location("storage", REPO / "files/live/usr/lib/antu/instalador/almacenamiento.py")
storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)
loader = SourceFileLoader("preparer", str(REPO / "files/system/usr/lib/antu/preparar-helper"))
spec = importlib.util.spec_from_loader("preparer", loader)
preparer = importlib.util.module_from_spec(spec); loader.exec_module(preparer)
spec = importlib.util.spec_from_file_location("dracut_fix", REPO / "files/scripts/corregir-dracut.py")
dracut_fix = importlib.util.module_from_spec(spec); spec.loader.exec_module(dracut_fix)


class ArranqueYRed(unittest.TestCase):
    def test_sin_red_o_red_medida_no_descarga_automaticamente(self):
        for state, metered, expected in ((20, 0, False), (70, 1, False), (70, 3, False), (70, 2, True)):
            def bus(args, **_):
                return subprocess.CompletedProcess(args, 0, "u " + str(state if args[-1] == "State" else metered))
            with patch.object(preparer.subprocess, "run", side_effect=bus):
                self.assertEqual(preparer.network_status()[0], expected)

    def test_espera_no_pisa_el_progreso_manual(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); state = base / "estado.json"; lock = base / "descarga.lock"
            original = {"apps": {"com.brave.Browser": {"status": "descargando", "percent": 42}, "otra": {"status": "instalada"}}}
            state.write_text(json.dumps(original))
            with patch.object(preparer, "STATE", state), patch.object(preparer, "LOCK", lock):
                with lock.open("w") as held:
                    fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    preparer.waiting("com.brave.Browser", "Esperando conexión")
                    self.assertEqual(json.loads(state.read_text()), original)
                preparer.waiting("com.brave.Browser", "Esperando conexión")
                self.assertEqual(json.loads(state.read_text())["apps"]["otra"], {"status": "instalada"})

    @unittest.skipUnless(shutil.which("bash"), "requiere bash")
    def test_generador_no_sale_con_error_por_return_global(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "generador.sh"
            source = "set -e\n" + "\n".join(before.rstrip("\n") for before, _ in dracut_fix.CHANGES) + "\n"
            path.write_text(source)
            self.assertNotEqual(subprocess.run(["bash", str(path)], capture_output=True).returncode, 0)
            self.assertTrue(dracut_fix.fix(path, hashlib.sha256(source.encode()).hexdigest()))
            self.assertEqual(subprocess.run(["bash", str(path)], capture_output=True).returncode, 0)
            self.assertFalse(dracut_fix.fix(path))
            path.write_text(source + "\n")
            with self.assertRaises(RuntimeError): dracut_fix.fix(path)


class Instalacion(unittest.TestCase):
    def table(self, sector=512):
        return {"label": "gpt", "sectorsize": sector, "firstlba": 34, "lastlba": 128 * 1024**3 // sector - 34,
                "partitions": [{"start": 1024**2 // sector, "size": 1024**3 // sector},
                               {"start": 2 * 1024**3 // sector, "size": 32 * 1024**3 // sector}]}

    def test_espacio_gpt_no_invade_particiones(self):
        for sector in (512, 4096):
            table = self.table(sector)
            free = storage.free_plan(table)
            self.assertEqual(free["start"] * sector % 1024**2, 0)
            for part in table["partitions"]:
                self.assertTrue(free["start"] >= part["start"] + part["size"] or
                                free["start"] + free["sectors"] <= part["start"])

    def test_sin_espacio_o_mbr_no_redimensiona(self):
        for table in ({"label": "dos"}, {**self.table(), "lastlba": 35 * 1024**3 // 512}):
            with self.assertRaises(ValueError):
                storage.free_plan(table)

    def test_cambio_de_plan_impide_cualquier_escritura(self):
        with patch.object(storage, "plan", return_value={"id": "nuevo"}), patch.object(storage, "run") as run:
            with self.assertRaisesRegex(ValueError, "cambió"):
                storage.install("/dev/nvme0n1", "identidad", "conservar", "luks2", "viejo", "frase valida de prueba")
            run.assert_not_called()

    def test_clave_invalida_no_toca_disco(self):
        with patch.object(storage, "run") as run:
            with self.assertRaises(ValueError):
                storage.install("/dev/nvme0n1", "identidad", "borrar", "luks2", "id", "corta")
            run.assert_not_called()

    def test_busca_montajes_en_toda_la_jerarquia(self):
        node = {"children": [{"children": [{"mountpoints": ["/home"]}]}]}
        self.assertTrue(any(m for p in storage.descendants(node) for m in p.get("mountpoints") or []))

    @unittest.skipUnless(shutil.which("sfdisk"), "requiere util-linux")
    def test_plan_sobre_tabla_gpt_real_en_archivo_temporal(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "disco-prueba.img"
            with image.open("wb") as f:
                f.truncate(64 * 1024**3)
            subprocess.run(["sfdisk", str(image)], input="label: gpt\nstart=2048,size=524288,type=EBD0A0A2-B9E5-4433-87C0-68B6B72699C7\n", text=True, check=True, capture_output=True)
            table = json.loads(subprocess.check_output(["sfdisk", "--json", str(image)]))["partitiontable"]
            free = storage.free_plan(table)
            self.assertGreater(free["start"], table["partitions"][0]["start"])
            self.assertGreater(free["bytes"], storage.MINIMUM)

    @unittest.skipUnless(shutil.which("mkfs.ext4") and shutil.which("dumpe2fs"), "requiere e2fsprogs")
    def test_raiz_ext4_admite_verity_sin_desactivar_integridad(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "raiz-temporal.img"
            with image.open("wb") as f:
                f.truncate(256 * 1024**2)
            storage.format_root(str(image))
            info = subprocess.check_output(["dumpe2fs", "-h", str(image)], stderr=subprocess.DEVNULL, text=True)
            features = next(line for line in info.splitlines() if line.startswith("Filesystem features:"))
            self.assertIn("verity", features.split())


class CatalogoYMedicion(unittest.TestCase):
    def test_catalogo_no_admite_argumentos_ni_otros_remotos(self):
        for ids in (["--system"], ["malicioso.app"], ["com.brave.Browser;rm"], [], "com.brave.Browser"):
            with self.assertRaises(ValueError):
                seleccionar(ids)
        self.assertEqual(seleccionar(["com.brave.Browser"] * 2), ["com.brave.Browser"])

    def test_csv_cuadros_y_tirones_conservados(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mango.csv"
            path.write_text("os,cpu\nLinux,Intel\nfps,frametime\n" + "100,10\n" * 990 + "10,100\n" * 10)
            result = analizar(path)
            self.assertEqual(result["frames"], 1000)
            self.assertEqual(result["one_percent_low_fps"], 10)
            self.assertEqual(result["frames_over_50_ms"], 10)
            self.assertAlmostEqual(result["fps"], 1000000 / 10900)
            with self.assertRaises(ValueError):
                comparar(path, path, "1080p alto con cargador", "4K ultra con batería")
            path.write_text("MsBetweenPresents\n" + "16\n" * 300 + "NaN\n0\n")
            self.assertEqual(analizar(path)["discarded"], 2)


@unittest.skipUnless(shutil.which("restic"), "requiere restic para respaldo/restauración reales")
class Copias(unittest.TestCase):
    def test_copia_cifrada_y_restauracion_sin_sobrescribir(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); home = base / "cuenta"; home.mkdir()
            (home / "documento.txt").write_text("contenido original")
            (home / ".cache").mkdir(); (home / ".cache/temporal").write_text("no incluir")
            (home / "partida.sav").write_bytes(bytes(range(256)))
            repo = base / "otro-disco"; repo.mkdir()
            restic = Restic(destination(repo, home), "frase de respaldo de prueba")
            snapshots = restic.backup(home)
            self.assertEqual(len(snapshots), 1)
            (home / "documento.txt").write_text("actual que no debe perderse")
            restored = restic.restore(snapshots[0]["id"], base)
            original_path = restored / str(home).lstrip("/")
            self.assertEqual((original_path / "documento.txt").read_text(), "contenido original")
            self.assertEqual((original_path / "partida.sav").read_bytes(), bytes(range(256)))
            self.assertFalse((original_path / ".cache/temporal").exists())
            self.assertEqual((home / "documento.txt").read_text(), "actual que no debe perderse")
            with self.assertRaisesRegex(RuntimeError, "frase de cifrado"):
                Restic(restic.repository, "frase incorrecta de prueba").snapshots()
            with self.assertRaises(ValueError):
                restic.restore("../fuera", base)

    def test_no_respalda_dentro_del_mismo_origen(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with self.assertRaises(ValueError):
                destination(home, home)
            with self.assertRaises(ValueError):
                Restic(home / "backup", "frase valida de prueba").backup(home)

    def test_cancelar_antes_de_escribir_no_crea_repositorio(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); home = base / "cuenta"; home.mkdir()
            restic = Restic(base / "repo", "frase valida de prueba")
            restic.cancel()
            with self.assertRaisesRegex(RuntimeError, "cancelada"):
                restic.backup(home)
            self.assertFalse(restic.repository.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
