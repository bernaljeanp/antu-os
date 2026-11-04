#!/usr/bin/env python3
"""Fallos de firmware y persistencia: nunca toca sysfs real."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

repo = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("zenit", repo / "files/system/usr/lib/antu/zenit/zenit.py")
z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(z)


class Zenit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        z.RAIZ = self.temp.name
        self.profile = "/sys/class/platform-profile/platform-profile-0/"
        for key, value in {"name": "alienware-wmi", "profile": "balanced", "choices": "balanced performance quiet"}.items():
            self.write(self.profile + key, value)
        self.service = z.Zenit(procesos=lambda: [])

    def tearDown(self):
        z.RAIZ = ""
        self.temp.cleanup()

    def write(self, name, value):
        path = Path(z.ruta(name))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def test_no_guarda_un_perfil_que_el_firmware_rechaza(self):
        self.service.guardar()
        before = Path(z.ruta(z.ESTADO)).read_bytes()
        with patch.object(z, "escribir", side_effect=OSError("firmware rechazó")):
            result = self.service.orden(["perfil", "performance"])
        self.assertFalse(result["ok"])
        self.assertEqual(self.service.estado["modo"], "auto")
        self.assertEqual(Path(z.ruta(z.ESTADO)).read_bytes(), before)

    def test_no_confirma_una_escritura_ignorada(self):
        with patch.object(z, "escribir"):
            self.assertFalse(self.service.orden(["perfil", "performance"])["ok"])

    def test_un_perfil_manual_cancela_boost_y_sigilo(self):
        self.service.boost = True
        self.assertTrue(self.service.orden(["perfil", "quiet"])["ok"])
        self.assertFalse(self.service.boost or self.service.sigilo)
        self.assertEqual(z.leer(z.ruta(self.profile + "profile")), "quiet")

    def test_no_ofrece_perfiles_ausentes(self):
        self.assertFalse(self.service.orden(["perfil", "cool"])["ok"])

    def test_guardado_fallido_conserva_el_anterior(self):
        self.service.guardar()
        before = Path(z.ruta(z.ESTADO)).read_bytes()
        with patch.object(z.os, "replace", side_effect=OSError("disco lleno")):
            result = self.service.orden(["perfil", "quiet"])
        self.assertFalse(result["ok"])
        self.assertEqual(Path(z.ruta(z.ESTADO)).read_bytes(), before)
        self.assertEqual(list(Path(z.ruta(z.ESTADO)).parent.glob(".estado-*")), [])

    def test_estado_corrupto_no_impide_arrancar(self):
        for value in ("{", "[]", '{"modo":"turbo","luces":42}', '{"juegos":[]}'):
            self.write(z.ESTADO, value)
            service = z.Zenit(procesos=lambda: [])
            self.assertIn(service.estado["modo"], {"auto", *z.PERFILES})
            self.assertIsInstance(service.estado["luces"], dict)

    def test_limite_no_confirmado_es_error(self):
        self.write("/sys/class/power_supply/BAT0/charge_control_end_threshold", "100")
        with patch.object(z, "escribir"):
            self.assertFalse(self.service.orden(["carga", "80"])["ok"])
        self.assertNotIn("carga", self.service.estado)

    def test_bateria_sin_adaptativa_no_finge_soportarla(self):
        self.write("/sys/class/power_supply/BAT0/charge_control_end_threshold", "80")
        self.assertFalse(self.service.orden(["carga", "adaptativa"])["ok"])
        self.assertFalse(z.capacidades()["carga_adaptativa"])

    def test_error_de_tic_se_expone_sin_caer(self):
        with patch.object(self.service, "aplicar", side_effect=OSError("ocupado")):
            self.service.tic()
        self.assertIn("ocupado", self.service.orden(["estado"])["ultimo_error"])

    def test_salud_de_bateria_y_limite_sin_inventar(self):
        for key, value in {"energy_full": "75000", "energy_full_design": "100000", "capacity": "80"}.items():
            self.write("/sys/class/power_supply/BAT0/" + key, value)
        b = z.bateria()[0]
        self.assertEqual(b["salud_porcentaje"], 75)
        self.assertIsNone(b["ciclos"])
        self.assertEqual(z.limites_termicos(), {})

    def test_no_consulta_nvidia_en_reposo_o_sin_juego(self):
        path = "/sys/bus/pci/devices/0000:01:00.0/"
        for name, value in {"vendor": "0x10de", "class": "0x030000", "power/runtime_status": "suspended"}.items():
            self.write(path + name, value)
        with patch.object(z.subprocess, "run") as run:
            self.assertEqual(z.datos_nvidia(True)["dispositivos"], [])
            self.write(path + "power/runtime_status", "active")
            self.assertEqual(z.datos_nvidia(False)["dispositivos"], [])
            run.assert_not_called()

    def test_nvidia_no_inventa_datos_ausentes(self):
        path = "/sys/bus/pci/devices/0000:01:00.0/"
        for name, value in {"vendor": "0x10de", "class": "0x030000", "power/runtime_status": "active"}.items():
            self.write(path + name, value)
        result = type("Result", (), {"stdout": "65, 99, N/A, 4000, 2100\n"})()
        with patch.object(z.subprocess, "run", return_value=result):
            device = z.datos_nvidia(True)["dispositivos"][0]
        self.assertEqual(device["temperatura"], 65)
        self.assertIsNone(device["vatios"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
