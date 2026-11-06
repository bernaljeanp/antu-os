#!/usr/bin/env python3
"""Mantenimiento sin red ni privilegios: protege cambios locales y archivos ajenos."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / "files/system/usr/lib/antu/zenit/mantenimiento.py"
spec = importlib.util.spec_from_file_location("maintenance", source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Maintenance(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "data/zenit"
        self.base.mkdir(parents=True)
        self.info = {"repositorio": str(self.root / "repo"), "servicio": False,
                     "menu": str(self.root / "menu.desktop"), "autostart": str(self.root / "autostart.desktop")}
        script = self.root / "repo/scripts/install-zenit-bazzite.sh"
        script.parent.mkdir(parents=True)
        script.touch()

    def test_cancelar_no_elimina_instalacion(self):
        with patch("builtins.input", return_value="no"):
            m.desinstalar(self.base, self.info)
        self.assertTrue(self.base.exists())

    def test_desinstalar_sin_servicio_conserva_entradas_ajenas(self):
        Path(self.info["menu"]).write_text("X-Zenit-Installer=true\n")
        Path(self.info["autostart"]).write_text("entrada de otro programa")
        with patch("builtins.input", return_value="DESINSTALAR"), patch.object(m, "run") as run:
            m.desinstalar(self.base, self.info)
            run.assert_not_called()
        self.assertFalse(self.base.exists())
        self.assertFalse(Path(self.info["menu"]).exists())
        self.assertTrue(Path(self.info["autostart"]).exists())

    def test_actualizar_rechaza_cambios_locales(self):
        with patch.object(m.subprocess, "check_output", return_value=" M archivo"), patch.object(m, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "cambios locales"):
                m.actualizar(self.base, self.info)
            run.assert_not_called()

    def test_actualizar_rechaza_origen_ajeno(self):
        with patch.object(m.subprocess, "check_output", side_effect=["", "main", "https://example.com/otro"]), patch.object(m, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "origen"):
                m.actualizar(self.base, self.info)
            run.assert_not_called()

    def test_actualizar_ff_only_y_respeta_instalacion_sin_servicio(self):
        with patch.object(m.subprocess, "check_output", side_effect=["", "main", "https://github.com/bernaljeanp/antu-os.git"]), patch.object(m, "run") as run:
            m.actualizar(self.base, self.info)
        self.assertEqual(run.call_args_list[0].args[-4:], ("pull", "--ff-only", "origin", "main"))
        self.assertEqual(run.call_args_list[1].args[-1], "--sin-servicio")


if __name__ == "__main__":
    unittest.main(verbosity=2)
